"""
Speckit CLI — spec lifecycle on top of spec_validate.py (stdlib only).

    new <slug> [--size S|M]          create specs/NNN-<slug>/ from .agents/templates
    new --from-issue <file>          same, with slug, size and brief from a GitHub issue form body
    status [<spec>]                  table of specs (+ errors/warnings for one spec)
    design ready <spec>              mark completed design as awaiting approval
    design revise <spec> --by <name> --reason <text>   invalidate a pre-implementation approval
    approve <spec> [--by <name>]     GATE 1: record the user's approval of spec + plan
    ready <spec>                     GATE 2: validate planning without starting implementation
    task start|done <spec> TASK-NNN  start a task / run its checks and record evidence
    resume <spec> --by <name> --reason <text>   authorize another attempt after blocking
    close <spec> [--base <ref>]      final checks, fingerprint, status=completed and retro.md
    ci-guard --branch ... [--base ...] [--head ...]   verify an SDD spec/CLOSE or a quick diff
    handoff [<spec>] [--note "..."]  session summary to .agents/SESSION_STATE.md
    archive <spec>                   move a completed spec to specs/.archive/
    report [--json]                  creation-to-close, gate, task, FAIL and block history metrics
    worktree <spec>                  git worktree ../<repo>-<spec> on branch feat/<spec>
    migrate [<spec>] [--check]       migrate state.json files to the current schema
    template export <destination>    build the clean GitHub Template projection

Every state change is validated; if the result is invalid it is rolled back.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec_validate as sv  # noqa: E402

ROOT = sv.ROOT
MAX_ATTEMPTS = 3  # AGENTS.md §F: retry budget per failing task
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SPEC_DIR_NAME = re.compile(r"^(\d{3,})-")
FEATURE_BRANCH = re.compile(r"^feat/(\d{3,}-[a-z0-9]+(?:-[a-z0-9]+)*)$")
QUICK_BRANCH = re.compile(r"^quick/([a-z0-9]+(?:-[a-z0-9]+)*)$")
TAIL_LINES = 20
EVIDENCE_ENTRY = re.compile(r"^##\s+(TASK-\d+|CLOSE)\s+[-—]\s+(PASS|FAIL)\s+[-—]\s+(\S+)", re.MULTILINE)
CI_FINGERPRINT = re.compile(r"^- CI fingerprint:\s*([a-f0-9]{64})\s*$", re.MULTILINE)
CI_MUTABLE_SPEC_FILES = {"state.json", "tasks.md", "evidence.md", "retro.md"}
TRANSITIONS = {
    "design_ready": {("planning", "spec"), ("planning", "plan")},
    "design_revise": {("planning", "tasks"), ("planning", "test_plan"), ("ready", "ready")},
    "approve": {("awaiting_approval", "plan")},
    "ready": {("planning", "tasks"), ("planning", "test_plan")},
    "task_start": {
        ("ready", "ready"),
        ("in_progress", "implementation"),
        ("in_progress", "validation"),
        ("completed", "validation"),
    },
    "task_done": {("in_progress", "implementation")},
    "resume": {("blocked", "implementation")},
    "close": {("in_progress", "validation"), ("completed", "validation")},
    "archive": {("completed", "validation")},
}
TEMPLATE_MANIFEST = ".agents/template-manifest.json"
TEMPLATE_OWNER = "template-owned"
PROJECT_OWNER = "project-owned"
MANIFEST_TEMPLATE_FILES = {
    ".agents/AGENT_PROMPT.md", ".agents/README.md", ".agents/requirements-dev.txt",
    ".agents/version.json", "AGENTS.md", "CLAUDE.md", "speckit",
}
MANIFEST_PROJECT_FILES = {".agents/project.json", ".env.example", ".gitignore", "README.md"}
MANIFEST_TEMPLATE_TREES = (
    ".agents/bin", ".agents/examples", ".agents/roles", ".agents/rules",
    ".agents/schemas", ".agents/skills", ".agents/templates", ".agents/tests", ".github",
)
TEMPLATE_EXPORT_SEEDS = (
    ".agents/memory/decisions.md",
    ".agents/memory/preferences.md",
    TEMPLATE_MANIFEST,
    "specs/.archive/.gitkeep",
    "specs/.gitkeep",
)


class CliError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def specs_dir() -> Path:
    return ROOT / "specs"


def spec_dirs() -> list[Path]:
    base = specs_dir()
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir() and SPEC_DIR_NAME.match(p.name))


def archived_spec_dirs() -> list[Path]:
    base = specs_dir() / ".archive"
    return sorted(p for p in base.iterdir() if p.is_dir() and SPEC_DIR_NAME.match(p.name)) \
        if base.is_dir() else []


def resolve_spec(name: str) -> Path:
    """Accept '001-login', '001' or 'specs/001-login'."""
    name = Path(name).name
    matches = [d for d in spec_dirs() if d.name == name or d.name.startswith(f"{name}-")]
    if len(matches) != 1:
        raise CliError(f"spec '{name}' not found" if not matches else f"spec '{name}' is ambiguous")
    return matches[0]


def load_state(spec_dir: Path) -> dict:
    return sv.load_json(spec_dir / "state.json")


def atomic_write_bytes(path: Path, content: bytes) -> None:
    """Flush content to a sibling temporary file and atomically replace path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            shutil.copymode(path, temporary)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def atomic_write_text(path: Path, content: str) -> None:
    atomic_write_bytes(path, content.encode("utf-8"))


def atomic_copy_file(source: Path, destination: Path) -> None:
    """Copy a regular file through an fsynced sibling and preserve its metadata."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=str(destination.parent))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as destination_handle, source.open("rb") as source_handle:
            shutil.copyfileobj(source_handle, destination_handle)
            destination_handle.flush()
            os.fsync(destination_handle.fileno())
        shutil.copystat(source, temporary)
        os.replace(temporary, destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def save_state(spec_dir: Path, state: dict) -> None:
    atomic_write_text(spec_dir / "state.json", json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def record_event(state: dict, event: str, *, task: str | None = None, actor: str | None = None,
                 reason: str | None = None, at: str | None = None) -> None:
    state.setdefault("events", []).append({
        "event": event,
        "at": at or now(),
        "task": task,
        "actor": actor,
        "reason": reason,
    })


def require_transition(action: str, state: dict) -> None:
    current = (state.get("status"), state.get("phase"))
    if current not in TRANSITIONS[action]:
        expected = ", ".join(f"{status}/{phase}" for status, phase in sorted(TRANSITIONS[action]))
        raise CliError(f"cannot {action.replace('_', ' ')} from {current[0]}/{current[1]} (expected: {expected})")


def migrated_state(state: dict, spec_dir: Path | None = None) -> tuple[dict, bool]:
    """Return a current-schema state without inventing approvals or evidence."""
    version = state.get("schema_version", 1)
    changed = False
    if version == 1:
        state = dict(state)
        state["schema_version"] = 2
        changed = True
        version = 2
    if version == 2:
        state = dict(state)
        state.update(schema_version=3, created_at=None, events=[])
        changed = True
    elif version != sv.SCHEMA_VERSION:
        raise CliError(f"unsupported schema_version={version!r}")
    approval = state.get("approval")
    if approval and not approval.get("design_hashes"):
        if spec_dir is None:
            raise CliError("approved legacy state needs its spec directory to migrate design hashes")
        approval["design_hashes"] = sv.design_hashes(state, spec_dir)
        changed = True
    return state, changed


def validate(spec_dir: Path) -> tuple[list[str], list[str]]:
    return sv.validate_state_file(spec_dir / "state.json", sv.load_json(sv.SCHEMA_PATH))


def transaction(spec_dir: Path, files: list[str], change) -> list[str]:
    """Apply change and restore every declared path after any exception or invalid result."""
    backup = {name: (spec_dir / name).read_bytes() if (spec_dir / name).is_file() else None
              for name in files}
    try:
        change()
        errors, warnings = validate(spec_dir)
        if errors:
            raise CliError("change rolled back, spec would be invalid:\n"
                           + "\n".join(f"  ✗ {error}" for error in errors))
        return warnings
    except BaseException as original:
        try:
            for name, content in backup.items():
                path = spec_dir / name
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write_bytes(path, content)
        except BaseException as rollback_error:
            raise original from rollback_error
        raise


def mark_existing_artifacts(spec_dir: Path, state: dict, keys: list[str]) -> None:
    for key in keys:
        path = spec_dir / sv.ARTIFACT_FILE_MAP[key]
        if path.is_file() and path.read_text(encoding="utf-8").strip():
            state["artifacts"][key] = True


def read_tasks(spec_dir: Path) -> list[tuple[str, str]]:
    path = spec_dir / "tasks.md"
    return sv.parse_tasks(path.read_text(encoding="utf-8")) if path.is_file() else []


def set_task_mark(spec_dir: Path, task_id: str, mark: str) -> None:
    path = spec_dir / "tasks.md"
    pattern = re.compile(rf"^(\s*[-*]\s*\[)[ /xX](\]\s*{re.escape(task_id)}\b)", re.MULTILINE)
    content, count = pattern.subn(rf"\g<1>{mark}\g<2>", path.read_text(encoding="utf-8"))
    if count != 1:
        raise CliError(f"{task_id} not found in tasks.md")
    atomic_write_text(path, content)


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def project_commands(include_e2e: bool = False) -> list[tuple[str, str]]:
    """Global project checks, reserved for the final close gate."""
    path = ROOT / ".agents" / "project.json"
    commands = sv.load_json(path).get("commands", {}) if path.is_file() else {}
    if not (commands.get("test") or "").strip():
        raise CliError("define commands.test in .agents/project.json (AGENTS.md §K) before running checks")
    names = ("test", "lint", "build", "e2e") if include_e2e else ("test", "lint", "build")
    return [(name, commands[name]) for name in names if (commands.get(name) or "").strip()]


def run_checks(include_e2e: bool = False) -> tuple[bool, str]:
    """Run global project checks; return (passed, markdown report)."""
    report: list[str] = []
    for name, command in project_commands(include_e2e):
        started = time.monotonic()
        result = subprocess.run(command, shell=True, cwd=ROOT, capture_output=True, text=True)
        duration = time.monotonic() - started
        tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-TAIL_LINES:])
        report.append(f"- {name}: `{command}` → exit {result.returncode} ({duration:.3f}s)"
                      f"\n\n```text\n{tail}\n```")
        if result.returncode != 0:
            return False, "\n".join(report)
    return True, "\n".join(report)


def workspace_fingerprint() -> dict[str, str]:
    commit = git("rev-parse", "HEAD") or "n/a"
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    if commit != "n/a" and not status:
        return {"commit": commit, "content": git("rev-parse", "HEAD^{tree}") or "n/a", "state": "clean"}
    digest = hashlib.sha256()
    diff = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=ROOT, capture_output=True).stdout
    digest.update(diff)
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT,
                               capture_output=True, check=False).stdout.split(b"\0")
    for raw_path in sorted(path for path in untracked if path):
        digest.update(b"\0path\0" + raw_path + b"\0")
        path = ROOT / raw_path.decode("utf-8", errors="surrogateescape")
        if path.is_file():
            digest.update(path.read_bytes())
    return {"commit": commit, "content": digest.hexdigest(), "state": "dirty"}


def _git_command(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True)


def resolve_change_base(explicit: str = "", head: str = "HEAD") -> str | None:
    """Resolve the nearest normal integration branch unless CI supplies an exact base."""
    requested = explicit.strip() or os.environ.get("SPECKIT_BASE_SHA", "").strip()
    if requested:
        result = _git_command("rev-parse", "--verify", f"{requested}^{{commit}}")
        if result.returncode != 0:
            raise CliError(f"unknown Git base: {requested}")
        return result.stdout.decode().strip()
    candidates = ("origin/main", "origin/develop", "main", "develop")
    choices = []
    for candidate in candidates:
        merge_base = _git_command("merge-base", head, candidate)
        if merge_base.returncode != 0:
            continue
        base = merge_base.stdout.decode().strip()
        distance = _git_command("rev-list", "--count", f"{base}..{head}")
        if distance.returncode == 0:
            choices.append((int(distance.stdout.decode().strip()), candidates.index(candidate), base))
    return min(choices)[2] if choices else None


def _changed_paths(base: str, head: str, include_worktree: bool) -> set[str]:
    result = _git_command("diff", "--name-only", "-z", "--no-renames", base, head, "--")
    if result.returncode != 0:
        raise CliError(result.stderr.decode(errors="replace").strip() or "cannot inspect Git diff")
    paths = {raw.decode("utf-8", errors="surrogateescape") for raw in result.stdout.split(b"\0") if raw}
    if include_worktree:
        dirty = _git_command("diff", "--name-only", "-z", "--no-renames", head, "--")
        if dirty.returncode != 0:
            raise CliError(dirty.stderr.decode(errors="replace").strip() or "cannot inspect working tree")
        paths.update(raw.decode("utf-8", errors="surrogateescape")
                     for raw in dirty.stdout.split(b"\0") if raw)
        untracked = _git_command("ls-files", "--others", "--exclude-standard", "-z")
        paths.update(raw.decode("utf-8", errors="surrogateescape")
                     for raw in untracked.stdout.split(b"\0") if raw)
    return paths


def _spec_artifact_path(path: str) -> tuple[str, str] | None:
    parts = Path(path).parts
    if len(parts) >= 3 and parts[0] == "specs" and parts[1] != ".archive" \
            and SPEC_DIR_NAME.match(parts[1]):
        return parts[1], "/".join(parts[2:])
    if len(parts) >= 4 and parts[:2] == ("specs", ".archive") and SPEC_DIR_NAME.match(parts[2]):
        return parts[2], "/".join(parts[3:])
    return None


def _final_file(path: str, head: str, include_worktree: bool) -> tuple[bytes, str] | None:
    if include_worktree:
        candidate = ROOT / path
        if candidate.is_symlink():
            return os.readlink(candidate).encode("utf-8", errors="surrogateescape"), "120000"
        if candidate.is_file():
            mode = "100755" if candidate.stat().st_mode & 0o111 else "100644"
            return candidate.read_bytes(), mode
        return None
    content = _git_command("show", f"{head}:{path}")
    if content.returncode != 0:
        return None
    tree = _git_command("ls-tree", head, "--", path)
    mode = tree.stdout.decode().split(None, 1)[0] if tree.returncode == 0 and tree.stdout else "100644"
    return content.stdout, mode


def _related_final_file(spec_name: str, relative: str, head: str,
                        include_worktree: bool) -> tuple[bytes, str] | None:
    for path in (f"specs/{spec_name}/{relative}", f"specs/.archive/{spec_name}/{relative}"):
        entry = _final_file(path, head, include_worktree)
        if entry is not None:
            return entry
    return None


def change_fingerprint(spec_name: str, base: str, head: str = "HEAD",
                       include_worktree: bool = False) -> str:
    """Hash final changed content, normalizing active/archive paths and mutable SDD bookkeeping."""
    entries: dict[str, tuple[bytes, str] | None] = {}
    for path in sorted(_changed_paths(base, head, include_worktree)):
        spec_path = _spec_artifact_path(path)
        if spec_path and spec_path[0] == spec_name:
            relative = spec_path[1]
            if relative in CI_MUTABLE_SPEC_FILES:
                continue
            entries[f"specs/<SPEC>/{relative}"] = _related_final_file(
                spec_name, relative, head, include_worktree
            )
        else:
            entries[path] = _final_file(path, head, include_worktree)
    digest = hashlib.sha256()
    for path, entry in sorted(entries.items()):
        digest.update(b"path\0" + path.encode("utf-8", errors="surrogateescape") + b"\0")
        if entry is None:
            digest.update(b"deleted\0")
        else:
            content, mode = entry
            digest.update(mode.encode() + b"\0" + hashlib.sha256(content).digest())
    return digest.hexdigest()


def resolve_ci_spec(spec_name: str) -> Path:
    candidates = [ROOT / "specs" / spec_name, ROOT / "specs" / ".archive" / spec_name]
    matches = [path for path in candidates if path.is_dir()]
    if len(matches) != 1:
        raise CliError(f"branch must resolve exactly one active or archived spec named {spec_name}")
    return matches[0]


def _history_relocation_exists(spec_name: str, relative: str, head: str,
                               include_worktree: bool) -> bool:
    return _final_file(f".agents/examples/history/{spec_name}/{relative}", head, include_worktree) is not None


def close_fingerprint(spec_dir: Path) -> str | None:
    evidence = spec_dir / "evidence.md"
    text = evidence.read_text(encoding="utf-8") if evidence.is_file() else ""
    entries = re.findall(r"^##\s+CLOSE\s+[-—]\s+PASS\b.*?(?=^##\s+|\Z)", text,
                         re.MULTILINE | re.DOTALL)
    match = CI_FINGERPRINT.search(entries[-1]) if entries else None
    return match.group(1) if match else None


def ci_guard(branch: str, base: str, head: str = "HEAD", include_worktree: bool = False) -> dict[str, str]:
    branch_match = FEATURE_BRANCH.fullmatch(branch)
    quick_match = QUICK_BRANCH.fullmatch(branch)
    if not branch_match and not quick_match:
        raise CliError("CI branch must match exactly feat/<NNN-slug> or quick/<slug>")
    resolved_base = resolve_change_base(base, head)
    if resolved_base is None:
        raise CliError("cannot resolve the integration base; pass --base <commit>")
    paths = _changed_paths(resolved_base, head, include_worktree)
    if quick_match:
        spec_paths = sorted(path for path in paths if _spec_artifact_path(path))
        if spec_paths:
            raise CliError(f"quick branch cannot change specs/: {spec_paths[0]}")
        fingerprint = change_fingerprint("", resolved_base, head, include_worktree)
        return {"branch": branch, "spec": f"quick:{quick_match.group(1)}", "base": resolved_base,
                "head": head, "fingerprint": fingerprint}
    spec_name = branch_match.group(1)
    spec_dir = resolve_ci_spec(spec_name)
    for path in sorted(paths):
        spec_path = _spec_artifact_path(path)
        if not spec_path or spec_path[0] == spec_name:
            continue
        other_spec, relative = spec_path
        # A pure distribution migration may remove legacy runtime specs into the matching history folder.
        if _final_file(path, head, include_worktree) is None \
                and _history_relocation_exists(other_spec, relative, head, include_worktree):
            continue
        raise CliError(f"diff changes artifact of unrelated spec {other_spec}: {path}")
    actual = change_fingerprint(spec_name, resolved_base, head, include_worktree)
    expected = close_fingerprint(spec_dir)
    if expected is None:
        raise CliError(f"{spec_name} has no CLOSE — PASS with a CI fingerprint")
    if actual != expected:
        raise CliError(f"CI fingerprint mismatch for {spec_name}: evidence={expected}, diff={actual}")
    return {"branch": branch, "spec": spec_name, "base": resolved_base, "head": head,
            "fingerprint": actual}


def test_cases_for_task(spec_dir: Path, task_id: str) -> list[sv.TestCaseRecord]:
    tasks_text = (spec_dir / "tasks.md").read_text(encoding="utf-8")
    task = next((record for record in sv.parse_task_records(tasks_text) if record.task_id == task_id), None)
    acs = set(task.acs) if task else set()
    test_plan = spec_dir / "test-plan.md"
    if not acs:
        return []
    if test_plan.is_file():
        content = test_plan.read_text(encoding="utf-8")
    else:
        spec_text = (spec_dir / "spec.md").read_text(encoding="utf-8")
        content = sv.section_body(spec_text, "Pruebas") or ""
    return [case for case in sv.parse_test_cases(content) if case.ac in acs]


def manual_cases_for_task(spec_dir: Path, task_id: str) -> list[sv.TestCaseRecord]:
    return [case for case in test_cases_for_task(spec_dir, task_id) if case.kind == "manual"]


def run_task_scenarios(cases: list[sv.TestCaseRecord], manual_evidence: str = "") -> tuple[bool, str]:
    """Run task-scoped scenarios once per exact command, with evidence per TC."""
    report: list[str] = []
    executions: dict[str, tuple[int, float, str]] = {}
    for case in cases:
        if case.kind == "manual":
            report.append(
                f"### {case.case_id} — PASS\n"
                f"- Type: `manual`\n- Steps: {case.command}\n"
                f"- Evidence: {manual_evidence.strip()}"
            )
            continue

        if case.command not in executions:
            started = time.monotonic()
            result = subprocess.run(case.command, shell=True, cwd=ROOT, capture_output=True, text=True)
            duration = time.monotonic() - started
            tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-TAIL_LINES:])
            executions[case.command] = (result.returncode, duration, tail)
        returncode, duration, tail = executions[case.command]
        outcome = "PASS" if returncode == 0 else "FAIL"
        report.append(
            f"### {case.case_id} — {outcome}\n"
            f"- Type: `{case.kind}`\n- Command: `{case.command}`\n"
            f"- Exit: {returncode} ({duration:.3f}s)\n\n```text\n{tail}\n```"
        )
        if returncode != 0:
            return False, "\n\n".join(report)
    return True, "\n\n".join(report)


def append_evidence(spec_dir: Path, heading: str, body: str) -> None:
    path = spec_dir / "evidence.md"
    previous = path.read_text(encoding="utf-8") if path.is_file() else "# Evidence\n"
    fingerprint = workspace_fingerprint()
    entry = (f"\n## {heading} — {now()}\n- Commit: {fingerprint['commit']}\n"
             f"- Tested content: {fingerprint['content']} ({fingerprint['state']})\n{body}\n")
    atomic_write_text(path, previous.rstrip("\n") + "\n" + entry)


def failed_attempts(spec_dir: Path, task_id: str) -> int:
    path = spec_dir / "evidence.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return len(re.findall(rf"^##\s+{re.escape(task_id)}\s+[-—]\s+FAIL\b", text, re.MULTILINE))


# ---------------------------------------------------------------- commands


def parse_issue_form(text: str) -> dict[str, str]:
    """'### Label' sections of a GitHub issue form body -> {label: value}, skipping empty answers."""
    parts = re.split(r"^###\s+(.+?)\s*$", text.replace("\r\n", "\n"), flags=re.MULTILINE)
    fields = {label.strip(): value.strip() for label, value in zip(parts[1::2], parts[2::2])}
    return {k: v for k, v in fields.items() if v and v != "_No response_"}


def fill_brief(brief: str, fields: dict[str, str]) -> str:
    """Replace the body of each '## N. <Title>' section whose title is a field label."""
    parts = re.split(r"^(## (?:\d+\.\s+)?(.+?)\s*)$", brief, flags=re.MULTILINE)
    out = [parts[0]]
    for heading, title, body in zip(parts[1::3], parts[2::3], parts[3::3]):
        out.append(heading + (f"\n{fields[title]}\n\n" if title in fields else body))
    return "".join(out).rstrip() + "\n"


def cmd_new(args) -> int:
    fields: dict[str, str] = {}
    if args.from_issue:
        fields = parse_issue_form(Path(args.from_issue).read_text(encoding="utf-8"))
        args.slug = args.slug or fields.pop("Slug", "").strip()
        args.size = fields.pop("Tamaño", args.size).strip()[:1].upper()
        if args.size not in ("S", "M"):
            raise CliError("size must be S or M (split size L into several specs)")
    if not SLUG.match(args.slug or ""):
        raise CliError("slug must be kebab-case: lowercase letters, digits and '-'")
    numbers = [int(SPEC_DIR_NAME.match(d.name).group(1)) for d in spec_dirs()]
    archive = specs_dir() / ".archive"
    if archive.is_dir():
        numbers += [int(m.group(1)) for d in archive.iterdir() if (m := SPEC_DIR_NAME.match(d.name))]
    requested = args.number
    if requested is not None and (requested < 1 or requested in numbers):
        raise CliError(f"spec number {requested:03d} is invalid or already exists")
    number = f"{requested if requested is not None else max(numbers, default=0) + 1:03d}"
    spec_dir = specs_dir() / f"{number}-{args.slug}"
    spec_dir.mkdir(parents=True)

    templates = ROOT / ".agents" / "templates"
    files = ["brief.md", "spec.md", "tasks.md"]
    if args.size == "M":
        files += ["implementation-plan.md", "test-plan.md"]
    for name in files:
        content = (templates / name).read_text(encoding="utf-8")
        content = content.replace("<NNN>", number).replace("<nombre de la idea>", args.slug).replace("<nombre>", args.slug)
        if name == "spec.md" and args.size == "M":
            content = content.split("## Notas técnicas (solo size S)")[0].rstrip() + "\n"
        if name == "brief.md" and fields:
            content = fill_brief(content, fields)
        atomic_write_text(spec_dir / name, content)

    state = sv.load_json(templates / "state.json")
    created_at = now()
    state.update(spec_name=spec_dir.name, size=args.size, created_at=created_at)
    record_event(state, "created", at=created_at)
    save_state(spec_dir, state)
    print(f"✓ {spec_dir.relative_to(ROOT)} (size {args.size})")
    print(f"  Next: fill brief.md, then ask the agent to write the spec ({', '.join(files[1:])}).")
    return 0


def summarize(spec_dir: Path) -> dict:
    state = load_state(spec_dir)
    tasks = read_tasks(spec_dir)
    errors, warnings = validate(spec_dir)
    return {
        "spec": spec_dir.name,
        "size": state.get("size", "?"),
        "status": state.get("status", "?"),
        "phase": state.get("phase", "?"),
        "tasks": f"{sum(m == 'x' for m, _ in tasks)}/{len(tasks)}",
        "current": state.get("current_task") or "-",
        "approved": "yes" if state.get("approval") else "no",
        "check": f"FAIL({len(errors)})" if errors else (f"WARN({len(warnings)})" if warnings else "OK"),
        "_state": state, "_tasks": tasks, "_errors": errors, "_warnings": warnings,
    }


def cmd_status(args) -> int:
    dirs = [resolve_spec(args.spec)] if args.spec else spec_dirs()
    if not dirs:
        print("No specs yet. Create one with: ./speckit new <slug>")
        return 0
    rows = [summarize(d) for d in dirs]
    print(f"Speckit template {sv.TEMPLATE_VERSION} · schema {sv.SCHEMA_VERSION}")
    columns = ["spec", "size", "status", "phase", "tasks", "current", "approved", "check"]
    widths = {c: max(len(c), *(len(r[c]) for r in rows)) for c in columns}
    print("  ".join(c.upper().ljust(widths[c]) for c in columns))
    for row in rows:
        print("  ".join(row[c].ljust(widths[c]) for c in columns))
    if args.spec:
        for e in rows[0]["_errors"]:
            print(f"  ✗ {e}")
        for w in rows[0]["_warnings"]:
            print(f"  ⚠ {w}")
    return 1 if any(r["_errors"] for r in rows) else 0


def cmd_design(args) -> int:
    spec_dir = resolve_spec(args.spec)
    state = load_state(spec_dir)
    if args.action == "revise":
        require_transition("design_revise", state)
        actor = (args.by or "").strip()
        reason = (args.reason or "").strip()
        if not actor or not reason:
            raise CliError("design revise requires non-empty --by and --reason")

        def revise():
            state["artifacts"]["tasks_md"] = False
            state["artifacts"]["test_plan_md"] = False
            state.update(status="planning", phase="plan", current_task=None,
                         blocked_reason=None, approval=None)
            record_event(state, "design_revised", actor=actor, reason=reason)
            save_state(spec_dir, state)

        warnings = transaction(spec_dir, ["state.json"], revise)
        print(f"✓ {spec_dir.name} design revision opened by {actor}. "
              "Update the design, run 'design ready', and request approval again.")
        for warning in warnings:
            print(f"  ⚠ {warning}")
        return 0

    require_transition("design_ready", state)

    def change():
        mark_existing_artifacts(spec_dir, state, sv.DESIGN_ARTIFACTS)
        state.update(status="awaiting_approval", phase="plan", current_task=None, blocked_reason=None)
        record_event(state, "design_ready")
        save_state(spec_dir, state)

    warnings = transaction(spec_dir, ["state.json"], change)
    print(f"✓ {spec_dir.name} design ready and awaiting explicit approval.")
    for warning in warnings:
        print(f"  ⚠ {warning}")
    return 0


def cmd_approve(args) -> int:
    spec_dir = resolve_spec(args.spec)
    state = load_state(spec_dir)
    if state.get("approval"):
        raise CliError(f"{spec_dir.name} is already approved")
    require_transition("approve", state)
    by = args.by or git("config", "user.name") or "user"

    def change():
        mark_existing_artifacts(spec_dir, state, sv.DESIGN_ARTIFACTS)
        state.update(approval={"by": by, "at": now(), "design_hashes": sv.design_hashes(state, spec_dir)},
                     status="planning", phase="tasks", current_task=None)
        record_event(state, "approved", actor=by)
        save_state(spec_dir, state)

    warnings = transaction(spec_dir, ["state.json"], change)
    print(f"✓ GATE 1: {spec_dir.name} approved by {by}. Next: tasks.md" +
          (" and test-plan.md" if state.get("size") == "M" else "") + ", then 'ready'.")
    for w in warnings:
        print(f"  ⚠ {w}")
    return 0


def cmd_ready(args) -> int:
    spec_dir = resolve_spec(args.spec)
    state = load_state(spec_dir)
    require_transition("ready", state)

    def change():
        mark_existing_artifacts(spec_dir, state, ["tasks_md", "test_plan_md"])
        state.update(status="ready", phase="ready", current_task=None, blocked_reason=None)
        record_event(state, "ready")
        save_state(spec_dir, state)

    warnings = transaction(spec_dir, ["state.json"], change)
    print(f"✓ GATE 2 passed: {spec_dir.name} is Ready. Next: 'task start'.")
    for warning in warnings:
        print(f"  ⚠ {warning}")
    return 0


def cmd_task(args) -> int:
    spec_dir = resolve_spec(args.spec)
    state = load_state(spec_dir)
    marks = dict((task_id, mark) for mark, task_id in read_tasks(spec_dir))
    if args.task_id not in marks:
        raise CliError(f"{args.task_id} not found in {spec_dir.name}/tasks.md")
    return task_start(spec_dir, state, args.task_id, marks) if args.action == "start" \
        else task_done(spec_dir, state, args.task_id, marks, args.manual_evidence)


def task_start(spec_dir: Path, state: dict, task_id: str, marks: dict) -> int:
    require_transition("task_start", state)
    current = state.get("current_task")
    if current and current != task_id:
        raise CliError(f"{current} is in progress: finish it first ('task done {current}')")
    if marks[task_id] == "x":
        raise CliError(f"{task_id} is already done")

    def change():
        state.update(status="in_progress", phase="implementation", current_task=task_id, blocked_reason=None)
        record_event(state, "task_started", task=task_id)
        save_state(spec_dir, state)
        set_task_mark(spec_dir, task_id, "/")

    warnings = transaction(spec_dir, ["state.json", "tasks.md"], change)
    print(f"✓ GATE 2 passed: {task_id} in progress.")
    for w in warnings:
        print(f"  ⚠ {w}")
    return 0


def task_done(spec_dir: Path, state: dict, task_id: str, marks: dict, manual_evidence: str = "") -> int:
    require_transition("task_done", state)
    if state.get("current_task") != task_id or marks[task_id] != "/":
        raise CliError(f"{task_id} is not in progress (run 'task start' first)")
    cases = test_cases_for_task(spec_dir, task_id)
    if not cases:
        raise CliError(f"{task_id} has no associated test scenarios")
    manual_cases = [case for case in cases if case.kind == "manual"]
    if manual_cases and not manual_evidence.strip():
        raise CliError(f"{task_id} has manual test cases; pass --manual-evidence '<observable result>'")
    passed, report = run_task_scenarios(cases, manual_evidence)
    if not passed:
        append_evidence(spec_dir, f"{task_id} — FAIL", report)
        attempts = failed_attempts(spec_dir, task_id)
        record_event(state, "task_failed", task=task_id, reason=f"attempt {attempts}/{MAX_ATTEMPTS}")
        if attempts >= MAX_ATTEMPTS:
            state.update(status="blocked", blocked_reason=f"{task_id} failed {attempts} times; see evidence.md")
            record_event(state, "blocked", task=task_id, reason=state["blocked_reason"])
            print(f"✗ {task_id} failed {attempts}/{MAX_ATTEMPTS}: spec blocked. Report to the user what was tried.")
        else:
            print(f"✗ {task_id} checks failed (attempt {attempts}/{MAX_ATTEMPTS}); task stays [/]. See evidence.md.")
        save_state(spec_dir, state)
        return 1

    def change():
        append_evidence(spec_dir, f"{task_id} — PASS", report)
        set_task_mark(spec_dir, task_id, "x")
        remaining = [t for t, m in marks.items() if m != "x" and t != task_id]
        state.update(current_task=None, phase="implementation" if remaining else "validation")
        record_event(state, "task_passed", task=task_id)
        save_state(spec_dir, state)

    warnings = transaction(spec_dir, ["state.json", "tasks.md", "evidence.md"], change)
    print(f"✓ GATE 3: {task_id} done, evidence recorded in {spec_dir.name}/evidence.md.")
    for w in warnings:
        print(f"  ⚠ {w}")
    return 0


def cmd_resume(args) -> int:
    spec_dir = resolve_spec(args.spec)
    state = load_state(spec_dir)
    require_transition("resume", state)
    task_id = state.get("current_task")
    if not task_id:
        raise CliError("blocked spec has no current_task")
    reason = args.reason.strip()
    actor = args.by.strip()
    if not reason or not actor:
        raise CliError("resume requires non-empty --by and --reason")

    def change():
        append_evidence(spec_dir, "RESUME", f"- Authorized by: {actor}\n- Task: {task_id}\n"
                        f"- Prior failures: {failed_attempts(spec_dir, task_id)}\n- Reason: {reason}")
        state.update(status="in_progress", blocked_reason=None)
        record_event(state, "resumed", task=task_id, actor=actor, reason=reason)
        save_state(spec_dir, state)

    transaction(spec_dir, ["state.json", "evidence.md"], change)
    print(f"✓ {spec_dir.name} resumed by {actor}; {task_id} may be attempted again.")
    return 0


def cmd_close(args) -> int:
    spec_dir = resolve_spec(args.spec)
    state = load_state(spec_dir)
    require_transition("close", state)
    tasks = read_tasks(spec_dir)
    open_tasks = [t for m, t in tasks if m != "x"]
    if open_tasks:
        raise CliError(f"open tasks: {', '.join(open_tasks)}")
    passed, report = run_checks(include_e2e=True)
    if not passed:
        append_evidence(spec_dir, "CLOSE — FAIL", report)
        raise CliError("final checks failed; see evidence.md")
    base = resolve_change_base(args.base)
    if base is None:
        ci_report = "- CI fingerprint: unavailable (no Git integration base)"
    else:
        fingerprint = change_fingerprint(spec_dir.name, base, include_worktree=True)
        ci_report = f"- CI base: {base}\n- CI fingerprint: {fingerprint}"
    closed_at = now()
    failures = {task_id: failed_attempts(spec_dir, task_id) for _, task_id in tasks}
    failure_summary = ", ".join(f"{task_id}: {count}" for task_id, count in failures.items() if count) \
        or "ninguno"
    retro = spec_dir / "retro.md"

    def change():
        append_evidence(spec_dir, "CLOSE — PASS", ci_report + "\n" + report)
        state.update(status="completed", phase="validation", current_task=None, blocked_reason=None)
        record_event(state, "closed", at=closed_at)
        save_state(spec_dir, state)
        if not retro.exists():
            template = (ROOT / ".agents" / "templates" / "retro.md").read_text(encoding="utf-8")
            content = template.format(
                spec=spec_dir.name,
                size=state.get("size"),
                approved=(state.get("approval") or {}).get("at", "n/a"),
                closed=closed_at,
                tasks=len(tasks),
                failures=failure_summary,
            )
        else:
            content = retro.read_text(encoding="utf-8")
            metadata = {
                r"(?m)^- Tamaño:.*$": (
                    f"- Tamaño: {state.get('size')} · "
                    f"Aprobado: {(state.get('approval') or {}).get('at', 'n/a')} · Cerrado: {closed_at}"
                ),
                r"(?m)^- Tareas:.*$": f"- Tareas: {len(tasks)} · Intentos fallidos: {failure_summary}",
            }
            for pattern, replacement in metadata.items():
                content, replacements = re.subn(pattern, replacement, content, count=1)
                if replacements != 1:
                    raise CliError(f"{retro}: generated metadata line is missing")
        atomic_write_text(retro, content)

    transaction(spec_dir, ["state.json", "evidence.md", "retro.md"], change)
    print(f"✓ {spec_dir.name} completed. Fill {retro.relative_to(ROOT)} and move new preferences "
          "to .agents/memory/preferences.md.")
    return 0


def cmd_ci_guard(args) -> int:
    result = ci_guard(args.branch, args.base, args.head, args.worktree)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"✓ CI traceability: {result['branch']} → {result['spec']} · {result['fingerprint']}")
    return 0


def next_step(row: dict) -> str:
    state, tasks = row["_state"], row["_tasks"]
    status, phase, current = state.get("status"), state.get("phase"), state.get("current_task")
    pending = [t for m, t in tasks if m != "x"]
    if status == "blocked":
        return (f"Resolver el bloqueo: {state.get('blocked_reason')}. Para autorizar otro intento: "
                f"`speckit resume {row['spec']} --by <nombre> --reason <motivo>`.")
    if status == "completed":
        return "Nada pendiente; completar retro.md si falta."
    if status == "awaiting_approval":
        return f"Esperar la aprobación explícita del usuario y ejecutar `speckit approve {row['spec']}`."
    if not state.get("approval"):
        return "Completar el diseño (spec + plan en M), resolver NEEDS CLARIFICATION y pedir aprobación."
    if current:
        return f"Terminar {current} y ejecutar `speckit task done {row['spec']} {current}`."
    if phase in ("tasks", "test_plan") or not tasks:
        return f"Escribir tasks.md{' y test-plan.md' if state.get('size') == 'M' else ''} y ejecutar `speckit ready {row['spec']}`."
    if status == "ready":
        return f"Ejecutar `speckit task start {row['spec']} {pending[0]}`."
    if pending:
        return f"Ejecutar `speckit task start {row['spec']} {pending[0]}`."
    return f"Ejecutar `speckit close {row['spec']}`."


def cmd_handoff(args) -> int:
    if args.spec:
        spec_dir = resolve_spec(args.spec)
    else:
        active = [d for d in spec_dirs() if load_state(d).get("status") != "completed"]
        if len(active) != 1:
            raise CliError("specify the spec: " + (", ".join(d.name for d in active) or "no active specs"))
        spec_dir = active[0]
    row = summarize(spec_dir)
    state = row["_state"]
    approval = state.get("approval")
    evidence = spec_dir / "evidence.md"
    last = [l for l in evidence.read_text(encoding="utf-8").splitlines() if l.startswith("## ")][-3:] \
        if evidence.is_file() else []
    lines = [
        f"# Handoff — {row['spec']}",
        "",
        f"Generado: {now()} · verificar contra el estado real antes de continuar.",
        "",
        f"- Tamaño · estado · fase: {row['size']} · {row['status']} · {row['phase']}",
        f"- Aprobación: {approval['by']} ({approval['at']})" if approval else "- Aprobación: pendiente",
        f"- Tarea actual: {row['current']}",
        f"- Bloqueo: {state.get('blocked_reason') or 'ninguno'}",
        f"- Validación: {row['check']}",
        *[f"  - ✗ {e}" for e in row["_errors"]],
        *[f"  - ⚠ {w}" for w in row["_warnings"]],
        "",
        "## Tareas",
        *([f"- [{m}] {t}" for m, t in row["_tasks"]] or ["- (sin tareas)"]),
        "",
        "## Última evidencia",
        *([f"- {l[3:]}" for l in last] or ["- (sin evidencia)"]),
        "",
        "## Siguiente paso",
        next_step(row),
    ]
    if args.note:
        lines += ["", "## Nota", args.note]
    lines += ["", "## Leer primero",
              f"`AGENTS.md`, `.agents/memory/preferences.md`, `specs/{row['spec']}/` (spec, tasks, evidence)."]
    text = "\n".join(lines) + "\n"
    out = ROOT / ".agents" / "SESSION_STATE.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(out, text)
    print(text)
    print("→ Saved to .agents/SESSION_STATE.md. Open a new chat to continue with a clean context.")
    return 0


def cmd_archive(args) -> int:
    spec_dir = resolve_spec(args.spec)
    require_transition("archive", load_state(spec_dir))
    errors, _ = validate(spec_dir)
    errors.extend(sv.validate_retro(spec_dir))
    if errors:
        raise CliError("cannot archive invalid spec:\n" + "\n".join(f"  ✗ {error}" for error in errors))
    target = specs_dir() / ".archive" / spec_dir.name
    if target.exists():
        raise CliError(f"{target.relative_to(ROOT)} already exists")
    target.parent.mkdir(exist_ok=True)
    shutil.move(str(spec_dir), str(target))
    errors, _ = validate(target)
    errors.extend(sv.validate_retro(target))
    if errors:
        shutil.move(str(target), str(spec_dir))
        raise CliError("archive rolled back after validation:\n" + "\n".join(f"  ✗ {error}" for error in errors))
    print(f"✓ {spec_dir.name} archived to {target.relative_to(ROOT)}")
    return 0


def parse_time(value: str | None) -> datetime | None:
    try:
        return datetime.strptime(value or "", "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _hours_between(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None or end < start:
        return None
    return round((end - start).total_seconds() / 3600, 3)


def lifecycle_metrics(state: dict) -> dict:
    """Calculate only durations supported by explicit v3 timestamps and events."""
    created = parse_time(state.get("created_at"))
    parsed_events = [(event.get("event"), parse_time(event.get("at")))
                     for event in state.get("events", []) if isinstance(event, dict)]

    def first(name: str) -> datetime | None:
        return next((at for event, at in parsed_events if event == name and at is not None), None)

    def last(name: str) -> datetime | None:
        return next((at for event, at in reversed(parsed_events) if event == name and at is not None), None)

    design_ready, approved, ready, closed = first("design_ready"), first("approved"), first("ready"), last("closed")
    if created is None:
        return {
            "created_at": None, "closed_at": None, "lead_time_hours": None,
            "gate_hours": {"design": None, "approval_wait": None, "ready": None,
                           "implementation": None},
            "block_events": None, "blocked_time_hours": None,
        }

    block_count = 0
    blocked_seconds = 0.0
    blocked_at: datetime | None = None
    incomplete_block = False
    for event, at in parsed_events:
        if at is None:
            continue
        if event == "blocked" and blocked_at is None:
            block_count += 1
            blocked_at = at
        elif event in ("resumed", "closed") and blocked_at is not None:
            if at < blocked_at:
                incomplete_block = True
            else:
                blocked_seconds += (at - blocked_at).total_seconds()
            blocked_at = None
    if blocked_at is not None:
        incomplete_block = True

    return {
        "created_at": state.get("created_at"),
        "closed_at": closed.strftime("%Y-%m-%dT%H:%M:%SZ") if closed else None,
        "lead_time_hours": _hours_between(created, closed),
        "gate_hours": {
            "design": _hours_between(created, design_ready),
            "approval_wait": _hours_between(design_ready, approved),
            "ready": _hours_between(approved, ready),
            "implementation": _hours_between(ready, closed),
        },
        "block_events": block_count,
        "blocked_time_hours": None if incomplete_block else round(blocked_seconds / 3600, 3),
    }


def spec_metrics(spec_dir: Path, archived: bool) -> dict:
    state = load_state(spec_dir)
    tasks = read_tasks(spec_dir)
    evidence = spec_dir / "evidence.md"
    entries = EVIDENCE_ENTRY.findall(evidence.read_text(encoding="utf-8")) if evidence.is_file() else []
    approved = parse_time((state.get("approval") or {}).get("at"))
    lifecycle = lifecycle_metrics(state)
    return {**lifecycle,
        "spec": spec_dir.name, "size": state.get("size", "?"), "status": state.get("status", "?"),
        "archived": archived, "approved_at": state["approval"]["at"] if approved else None,
        "tasks_done": sum(m == "x" for m, _ in tasks), "tasks_total": len(tasks),
        "fails": sum(kind != "CLOSE" and result == "FAIL" for kind, result, _ in entries),
        "blocked": state.get("status") == "blocked",
    }


def format_hours(hours: float | None) -> str:
    if hours is None:
        return "-"
    return f"{hours:.1f}h" if hours < 48 else f"{hours / 24:.1f}d"


def cmd_report(args) -> int:
    archive = specs_dir() / ".archive"
    archived = sorted(d for d in archive.iterdir() if d.is_dir() and SPEC_DIR_NAME.match(d.name)) if archive.is_dir() else []
    rows = [spec_metrics(d, True) for d in archived] + [spec_metrics(d, False) for d in spec_dirs()]
    leads = [r["lead_time_hours"] for r in rows if r["lead_time_hours"] is not None]
    block_counts = [r["block_events"] for r in rows if r["block_events"] is not None]
    totals = {
        "specs": len(rows), "completed": sum(r["status"] == "completed" for r in rows),
        "blocked": sum(r["blocked"] for r in rows), "tasks_done": sum(r["tasks_done"] for r in rows),
        "tasks_total": sum(r["tasks_total"] for r in rows), "fails": sum(r["fails"] for r in rows),
        "avg_lead_time_hours": round(sum(leads) / len(leads), 1) if leads else None,
        "block_events": sum(block_counts) if block_counts else (0 if rows and all(r["created_at"] for r in rows) else None),
        "avg_fails_per_task": round(sum(r["fails"] for r in rows) / max(1, sum(r["tasks_done"] for r in rows)), 2),
    }
    if args.json:
        print(json.dumps({"specs": rows, "totals": totals}, indent=2, ensure_ascii=False))
        return 0
    if not rows:
        print("No specs yet. Create one with: ./speckit new <slug>")
        return 0
    table = [{"spec": r["spec"] + (" (archived)" if r["archived"] else ""), "size": r["size"], "status": r["status"],
              "lead time": format_hours(r["lead_time_hours"]), "tasks": f"{r['tasks_done']}/{r['tasks_total']}",
              "fails": str(r["fails"]),
              "blocks": "-" if r["block_events"] is None else str(r["block_events"]),
              "blocked": "yes" if r["blocked"] else "no"} for r in rows]
    columns = list(table[0])
    widths = {c: max(len(c), *(len(r[c]) for r in table)) for c in columns}
    print("  ".join(c.upper().ljust(widths[c]) for c in columns))
    for row in table:
        print("  ".join(row[c].ljust(widths[c]) for c in columns))
    print(f"\n{totals['specs']} specs · {totals['completed']} completed · {totals['blocked']} blocked · "
          f"tasks {totals['tasks_done']}/{totals['tasks_total']} · {totals['fails']} FAIL · "
          f"{totals['block_events'] if totals['block_events'] is not None else '-'} block events "
          f"({totals['avg_fails_per_task']}/task) · avg lead time {format_hours(totals['avg_lead_time_hours'])}")
    return 0


def cmd_worktree(args) -> int:
    spec_dir = resolve_spec(args.spec)
    branch, path = f"feat/{spec_dir.name}", ROOT.parent / f"{ROOT.name}-{spec_dir.name}"
    if path.exists():
        raise CliError(f"{path} already exists")
    exists = bool(git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"))
    command = ["git", "worktree", "add", str(path), branch] if exists \
        else ["git", "worktree", "add", "-b", branch, str(path)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise CliError(result.stderr.strip() or "git worktree add failed")
    print(f"✓ worktree {path} on {branch}. Open your agent there; remove it with 'git worktree remove {path}'.")
    return 0


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_update_path(value: str) -> str:
    path = Path(value)
    if not value or "\\" in value or path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise CliError(f"unsafe template manifest path: {value!r}")
    return value


def contained_update_path(root: Path, rel_path: str) -> Path:
    root = root.resolve()
    candidate = root / safe_update_path(rel_path)
    current = candidate
    while current != root:
        if current.is_symlink():
            raise CliError(f"template path traverses a symlink: {rel_path}")
        current = current.parent
    try:
        candidate.resolve(strict=False).relative_to(root)
    except (OSError, RuntimeError, ValueError):
        raise CliError(f"template path escapes its root: {rel_path}")
    return candidate


def maintainer_only_path(rel_path: str) -> bool:
    return rel_path == ".github/workflows/publish-template.yml" \
        or rel_path == ".agents/docs" or rel_path.startswith(".agents/docs/") \
        or rel_path == ".agents/examples/node-cypress" \
        or rel_path.startswith(".agents/examples/node-cypress/") \
        or rel_path.startswith(".agents/examples/history/") \
        and rel_path != ".agents/examples/history/README.md"


def expected_manifest_owners(root: Path) -> dict[str, str]:
    """Discover distributed core files while excluding project runtime/state."""
    root = root.resolve()
    owners: dict[str, str] = {}
    for rel_path in sorted(MANIFEST_TEMPLATE_FILES):
        if (root / rel_path).is_file():
            owners[rel_path] = TEMPLATE_OWNER
    for rel_path in sorted(MANIFEST_PROJECT_FILES):
        if (root / rel_path).is_file():
            owners[rel_path] = PROJECT_OWNER
    for rel_root in MANIFEST_TEMPLATE_TREES:
        directory = root / rel_root
        if not directory.is_dir():
            continue
        for path in sorted(candidate for candidate in directory.rglob("*") if candidate.is_file()):
            if "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo"):
                continue
            rel_path = path.relative_to(root).as_posix()
            if rel_path.startswith(".agents/rules/stack-") or maintainer_only_path(rel_path):
                continue
            owners[rel_path] = TEMPLATE_OWNER
    return owners


def load_template_manifest(root: Path) -> dict:
    path = contained_update_path(root, TEMPLATE_MANIFEST)
    data = sv.load_json(path)
    format_version = data.get("format_version")
    if format_version not in (1, 2):
        raise CliError(f"{path}: unsupported format_version")
    if format_version == 2 and data.get("owner") != TEMPLATE_OWNER:
        raise CliError(f"{path}: owner must be {TEMPLATE_OWNER}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(data.get("template_version", ""))):
        raise CliError(f"{path}: invalid template_version")
    files = data.get("files")
    if not isinstance(files, list):
        raise CliError(f"{path}: files must be an array")
    normalized = []
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"path", "owner", "sha256"}:
            raise CliError(f"{path}: every file needs path, owner and sha256")
        rel_path = safe_update_path(entry["path"] if isinstance(entry.get("path"), str) else "")
        if rel_path == ".agents/backups" or rel_path.startswith(".agents/backups/"):
            raise CliError(f"{path}: backup paths cannot be template-managed")
        owner = entry.get("owner")
        if format_version == 1 and owner == "template":
            owner = TEMPLATE_OWNER
        if owner not in (TEMPLATE_OWNER, PROJECT_OWNER) \
                or not re.fullmatch(r"[a-f0-9]{64}", str(entry.get("sha256", ""))):
            raise CliError(f"{path}: invalid owner or sha256 for {rel_path}")
        normalized.append({**entry, "owner": owner})
    paths = [entry["path"] for entry in normalized]
    if paths != sorted(set(paths)):
        raise CliError(f"{path}: file paths must be sorted and unique")
    return {**data, "owner": TEMPLATE_OWNER, "files": normalized}


def template_export_paths(root: Path) -> list[str]:
    """Return a verified, complete projection without development specs."""
    root = root.resolve()
    manifest = load_template_manifest(root)
    declared = {entry["path"]: entry for entry in manifest["files"]}
    expected = expected_manifest_owners(root)
    declared_owners = {path: entry["owner"] for path, entry in declared.items()}
    if declared_owners != expected:
        missing = sorted(set(expected) - set(declared_owners))
        extra = sorted(set(declared_owners) - set(expected))
        wrong_owner = sorted(
            path for path in set(expected) & set(declared_owners)
            if expected[path] != declared_owners[path]
        )
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing[:3])}")
        if extra:
            details.append(f"extra: {', '.join(extra[:3])}")
        if wrong_owner:
            details.append(f"wrong owner: {', '.join(wrong_owner[:3])}")
        raise CliError("template manifest does not match the export inventory (" + "; ".join(details) + ")")

    for rel_path, entry in declared.items():
        source = contained_update_path(root, rel_path)
        if not source.is_file():
            raise CliError(f"template export source is missing: {rel_path}")
        if file_sha256(source) != entry["sha256"]:
            raise CliError(f"template export source hash mismatch: {rel_path}")

    paths = sorted(set(declared) | set(TEMPLATE_EXPORT_SEEDS))
    for rel_path in paths:
        source = contained_update_path(root, rel_path)
        if not source.is_file():
            raise CliError(f"template export seed is missing: {rel_path}")
    return paths


def export_template(destination: Path, root: Path = ROOT) -> list[str]:
    """Build the distribution in a sibling staging directory, then publish atomically."""
    root = root.resolve()
    destination = destination.expanduser().resolve(strict=False)
    if destination.exists() or destination.is_symlink():
        raise CliError(f"template export destination already exists: {destination}")
    try:
        destination.relative_to(root)
    except ValueError:
        pass
    else:
        raise CliError("template export destination must be outside the source checkout")

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=str(destination.parent)))
    try:
        paths = template_export_paths(root)
        for rel_path in paths:
            atomic_copy_file(contained_update_path(root, rel_path), staging / rel_path)
        os.replace(staging, destination)
        return paths
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def cmd_template(args: argparse.Namespace) -> int:
    paths = export_template(Path(args.destination))
    destination = Path(args.destination).expanduser().resolve(strict=False)
    print(f"✓ exported {len(paths)} files to {destination}")
    return 0


def update_preview(source: Path, target: Path = ROOT) -> dict:
    source, target = source.resolve(), target.resolve()
    source_manifest = load_template_manifest(source)
    local_manifest = load_template_manifest(target)
    new_inventory = {entry["path"]: entry for entry in source_manifest["files"]}
    old = {
        entry["path"]: entry for entry in local_manifest["files"]
        if entry["owner"] == TEMPLATE_OWNER
        and new_inventory.get(entry["path"], {}).get("owner") != PROJECT_OWNER
    }
    new = {entry["path"]: entry for entry in source_manifest["files"]
           if entry["owner"] == TEMPLATE_OWNER}
    actions = []
    for rel_path in sorted(set(old) | set(new)):
        destination = contained_update_path(target, rel_path)
        current_hash = file_sha256(destination) if destination.is_file() else None
        if rel_path in new:
            source_file = contained_update_path(source, rel_path)
            if not source_file.is_file() or file_sha256(source_file) != new[rel_path]["sha256"]:
                raise CliError(f"source package hash mismatch: {rel_path}")
            if current_hash == new[rel_path]["sha256"]:
                status = "unchanged"
            elif rel_path not in old and current_hash is None:
                status = "add"
            elif rel_path in old and current_hash == old[rel_path]["sha256"]:
                status = "update"
            else:
                status = "conflict"
        elif current_hash is None:
            status = "unchanged"
        elif current_hash == old[rel_path]["sha256"]:
            status = "remove"
        else:
            status = "conflict"
        actions.append({"path": rel_path, "status": status})
    return {
        "current_version": local_manifest["template_version"],
        "target_version": source_manifest["template_version"],
        "source": str(source),
        "actions": actions,
        "conflicts": [action["path"] for action in actions if action["status"] == "conflict"],
    }


def next_backup_dir(target: Path, version: str) -> Path:
    backups = contained_update_path(target, ".agents/backups")
    base = backups / f"{now().replace(':', '').replace('-', '')}-{version}"
    candidate, suffix = base, 1
    while candidate.exists():
        candidate = base.with_name(f"{base.name}-{suffix}")
        suffix += 1
    return candidate


def apply_update(source: Path, target: Path = ROOT, confirm_conflicts: bool = False) -> tuple[dict, Path | None]:
    plan = update_preview(source, target)
    if plan["conflicts"] and not confirm_conflicts:
        raise CliError("conflicts require explicit --yes: " + ", ".join(plan["conflicts"]))
    changes = [action for action in plan["actions"] if action["status"] != "unchanged"]
    if not changes:
        return plan, None

    source, target = source.resolve(), target.resolve()
    backup = next_backup_dir(target, plan["current_version"])
    (backup / "files").mkdir(parents=True)
    entries = []
    for action in changes:
        rel_path = safe_update_path(action["path"])
        destination = contained_update_path(target, rel_path)
        existed = destination.is_file()
        entries.append({"path": rel_path, "existed": existed})
        if existed:
            backup_file = backup / "files" / rel_path
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            atomic_copy_file(destination, backup_file)
    atomic_copy_file(target / TEMPLATE_MANIFEST, backup / "template-manifest.json")
    atomic_write_text(backup / "backup.json", json.dumps({
        "format_version": 1,
        "from_version": plan["current_version"],
        "to_version": plan["target_version"],
        "entries": entries,
    }, indent=2, ensure_ascii=False) + "\n")

    statuses = {action["path"]: action["status"] for action in changes}
    try:
        for rel_path, status in statuses.items():
            destination = contained_update_path(target, rel_path)
            source_file = contained_update_path(source, rel_path)
            if status == "remove" or status == "conflict" and not source_file.is_file():
                destination.unlink(missing_ok=True)
            else:
                atomic_copy_file(source_file, destination)
        atomic_copy_file(contained_update_path(source, TEMPLATE_MANIFEST),
                         contained_update_path(target, TEMPLATE_MANIFEST))
    except BaseException as original:
        try:
            restore_update(backup, target)
        except BaseException as rollback_error:
            raise original from rollback_error
        raise
    return plan, backup


def restore_update(backup: Path, target: Path = ROOT) -> None:
    backup, target = backup.resolve(), target.resolve()
    data = sv.load_json(backup / "backup.json")
    entries = data.get("entries")
    if data.get("format_version") != 1 or not isinstance(entries, list):
        raise CliError(f"{backup}: invalid backup metadata")
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("existed"), bool):
            raise CliError(f"{backup}: invalid backup entry")
        rel_path = safe_update_path(entry.get("path", ""))
        destination = contained_update_path(target, rel_path)
        if entry["existed"]:
            source = contained_update_path(backup, f"files/{rel_path}")
            if not source.is_file():
                raise CliError(f"{backup}: missing backup file {rel_path}")
            atomic_copy_file(source, destination)
        else:
            destination.unlink(missing_ok=True)
    atomic_copy_file(contained_update_path(backup, "template-manifest.json"),
                     contained_update_path(target, TEMPLATE_MANIFEST))


def cmd_update(args) -> int:
    if args.restore:
        if args.source or args.apply or args.yes:
            raise CliError("--restore cannot be combined with a source, --apply or --yes")
        restore_update(Path(args.restore), ROOT)
        print(f"✓ restored template backup {args.restore}")
        return 0
    if not args.source:
        raise CliError("update needs a source directory, or --restore <backup>")
    source = Path(args.source)
    if not source.is_dir():
        raise CliError(f"update source is not a directory: {source}")
    if args.yes and not args.apply:
        raise CliError("--yes requires --apply")
    plan = update_preview(source, ROOT)
    backup = None
    if args.apply:
        plan, backup = apply_update(source, ROOT, args.yes)
    if args.json:
        print(json.dumps({**plan, "applied": args.apply, "backup": str(backup) if backup else None},
                         indent=2, ensure_ascii=False))
    else:
        print(f"Template {plan['current_version']} → {plan['target_version']}"
              + (" (applied)" if args.apply else " (preview; no files written)"))
        for action in plan["actions"]:
            print(f"  {action['status']:<9} {action['path']}")
        if backup:
            print(f"  Backup: {backup}")
        elif plan["conflicts"] and not args.apply:
            print("  Conflicts require: --apply --yes")
    return 0 if not plan["conflicts"] or args.apply else 1


def doctor_report(root: Path = ROOT) -> dict:
    checks: list[dict[str, str]] = []

    def add(check_id: str, status: str, summary: str, remediation: str = "") -> None:
        item = {"id": check_id, "status": status, "summary": summary}
        if remediation and status != "pass":
            item["remediation"] = remediation
        checks.append(item)

    required = ["AGENTS.md", "CLAUDE.md", "speckit", "specs", ".agents/project.json",
                ".agents/version.json", TEMPLATE_MANIFEST, ".agents/schemas/spec-state.schema.json"]
    missing = [path for path in required if not (root / path).exists()]
    add("required_files", "pass" if not missing else "fail",
        "required files and directories are present" if not missing else f"missing: {', '.join(missing)}",
        "restore the missing paths from the matching template version")

    venv_candidates = [root / ".venv" / "bin" / "python", root / ".venv" / "Scripts" / "python.exe"]
    venv_python = next((path for path in venv_candidates if path.is_file()), None)
    add("venv", "pass" if venv_python is not None else "fail",
        f"virtual environment: {venv_python.relative_to(root)}" if venv_python else ".venv Python is missing",
        "run: python3 -m venv .venv && .venv/bin/python -m pip install -r .agents/requirements-dev.txt")

    project_path = root / ".agents" / "project.json"
    project: dict = {}
    try:
        project = sv.load_json(project_path)
        commands = project.get("commands")
        valid_commands = isinstance(commands, dict) and isinstance(commands.get("test"), str) \
            and bool(commands["test"].strip()) and all(isinstance(value, str) for value in commands.values())
        add("commands", "pass" if valid_commands else "fail", "project commands are configured" if valid_commands
            else "commands.test is missing or command values are invalid",
            "define commands.test and optional lint/build/e2e strings in .agents/project.json")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        add("commands", "fail", f"cannot read project commands: {error}", "repair .agents/project.json")

    try:
        metadata = sv.load_version_info(root / ".agents" / "version.json")
        schema = sv.load_json(root / ".agents" / "schemas" / "spec-state.schema.json")
        template = sv.load_json(root / ".agents" / "templates" / "state.json")
        schema_values = schema["properties"]["schema_version"].get("enum")
        update_manifest = load_template_manifest(root)
        versions_ok = schema_values == [metadata["schema_version"]] \
            and template.get("schema_version") == metadata["schema_version"] \
            and update_manifest["template_version"] == metadata["template_version"]
        add("version_schema", "pass" if versions_ok else "fail",
            f"template {metadata['template_version']} · schema {metadata['schema_version']}" if versions_ok
            else "version metadata, schema and state template disagree",
            "align schema and state template with .agents/version.json")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        schema = None
        add("version_schema", "fail", f"cannot validate version/schema: {error}",
            "repair .agents/version.json and spec-state.schema.json")

    try:
        manifest = load_template_manifest(root)
        declared = {entry["path"]: entry for entry in manifest["files"]}
        expected = expected_manifest_owners(root)
        uncovered = sorted(path for path, owner in expected.items()
                           if declared.get(path, {}).get("owner") != owner)
        forbidden = sorted(
            path for path in declared
            if path == "specs" or path.startswith("specs/")
            or path == ".agents/memory" or path.startswith(".agents/memory/")
            or path.startswith(".agents/rules/stack-")
            or maintainer_only_path(path)
        )
        maintainer_content = sorted(
            path.relative_to(root).as_posix()
            for base in (root / ".agents" / "docs", root / ".agents" / "examples")
            if base.is_dir()
            for path in base.rglob("*")
            if path.is_file() and maintainer_only_path(path.relative_to(root).as_posix())
        )
        missing_core = sorted(
            path for path, entry in declared.items()
            if entry["owner"] == TEMPLATE_OWNER and not (root / path).is_file()
        )
        drift = sorted(
            path for path, entry in declared.items()
            if entry["owner"] == TEMPLATE_OWNER and (root / path).is_file()
            and file_sha256(root / path) != entry["sha256"]
        )
        problems = []
        if uncovered:
            problems.append(f"uncovered ownership: {', '.join(uncovered[:3])}")
        if forbidden:
            problems.append(f"forbidden ownership entries: {', '.join(forbidden[:3])}")
        if maintainer_content:
            problems.append(f"maintainer-only content: {', '.join(maintainer_content[:3])}")
        if missing_core:
            problems.append(f"missing template-owned: {', '.join(missing_core[:3])}")
        if drift:
            problems.append(f"template drift: {', '.join(drift[:3])}")
        add("manifest", "fail" if problems else "pass",
            "; ".join(problems) if problems else
            f"ownership complete: {len(declared)} files ({sum(e['owner'] == TEMPLATE_OWNER for e in declared.values())} template-owned)",
            "restore template-owned files or regenerate .agents/template-manifest.json from the matching release")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, CliError) as error:
        add("manifest", "fail", f"cannot validate ownership manifest: {error}",
            "restore .agents/template-manifest.json from the matching release")

    spec_errors: list[str] = []
    if schema is not None:
        active = sorted((root / "specs").glob("[0-9]*-*/state.json"))
        archived = sorted((root / "specs" / ".archive").glob("[0-9]*-*/state.json"))
        for state_path in active + archived:
            errors, _ = sv.validate_state_file(state_path, schema)
            spec_errors.extend(f"{state_path.parent.name}: {error}" for error in errors)
    add("specs", "pass" if not spec_errors else "fail", "all spec states are valid" if not spec_errors
        else f"{len(spec_errors)} spec validation error(s): {spec_errors[0]}", "run: ./speckit validate --all")

    active_specs = []
    for state_path in sorted((root / "specs").glob("[0-9]*-*/state.json")):
        try:
            if sv.load_json(state_path).get("status") != "completed":
                active_specs.append(state_path.parent.name)
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    git_result = subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True)
    branch = git_result.stdout.strip() if git_result.returncode == 0 else ""
    git_warnings = []
    if not active_specs:
        git_warnings.append("no active spec")
    elif len(active_specs) > 1:
        git_warnings.append("multiple active specs: " + ", ".join(active_specs))
    elif branch != f"feat/{active_specs[0]}":
        git_warnings.append(f"branch {branch or '(detached/not Git)'} does not match feat/{active_specs[0]}")
    if git_result.returncode != 0:
        git_warnings.append("Git context unavailable")
    add("git_context", "warn" if git_warnings else "pass",
        "; ".join(git_warnings) if git_warnings else f"branch {branch} matches {active_specs[0]}",
        "create/select one spec and work on its exact feat/<spec> branch")

    return {
        "ok": all(check["status"] != "fail" for check in checks),
        "template_version": project.get("template_version", sv.TEMPLATE_VERSION),
        "schema_version": project.get("schema_version", sv.SCHEMA_VERSION),
        "checks": checks,
    }


def cmd_doctor(args) -> int:
    report = doctor_report(ROOT)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Speckit doctor · template {report['template_version']} · schema {report['schema_version']}")
        for check in report["checks"]:
            symbol = {"pass": "✓", "warn": "⚠", "fail": "✗"}[check["status"]]
            print(f"{symbol} {check['id']}: {check['summary']}")
            if "remediation" in check:
                print(f"  Fix: {check['remediation']}")
    return 0 if report["ok"] else 1


def cmd_migrate(args) -> int:
    dirs = [resolve_spec(args.spec)] if args.spec else spec_dirs() + archived_spec_dirs()
    pending: list[tuple[Path, dict]] = []
    for spec_dir in dirs:
        state, changed = migrated_state(load_state(spec_dir), spec_dir)
        if changed:
            pending.append((spec_dir, state))
    if args.check:
        if pending:
            print("✗ state migration required: " + ", ".join(path.name for path, _ in pending))
            return 1
        print(f"✓ {len(dirs)} state file(s) use schema_version={sv.SCHEMA_VERSION}")
        return 0
    for spec_dir, state in pending:
        save_state(spec_dir, state)
        errors, _ = validate(spec_dir)
        if errors:
            raise CliError(f"migrated {spec_dir.name} but validation fails:\n" + "\n".join(errors))
    print(f"✓ migrated {len(pending)} state file(s) to schema_version={sv.SCHEMA_VERSION}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="speckit", description=__doc__.strip().splitlines()[0])
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {sv.TEMPLATE_VERSION} (schema {sv.SCHEMA_VERSION})")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("new"); p.add_argument("slug", nargs="?"); p.add_argument("--from-issue")
    p.add_argument("--number", type=int, help=argparse.SUPPRESS)
    p.add_argument("--size", choices=["S", "M"], default="M")
    p.set_defaults(func=cmd_new)
    p = sub.add_parser("status"); p.add_argument("spec", nargs="?"); p.set_defaults(func=cmd_status)
    p = sub.add_parser("design"); p.add_argument("action", choices=["ready", "revise"]); p.add_argument("spec")
    p.add_argument("--by"); p.add_argument("--reason")
    p.set_defaults(func=cmd_design)
    p = sub.add_parser("approve"); p.add_argument("spec"); p.add_argument("--by"); p.set_defaults(func=cmd_approve)
    p = sub.add_parser("ready"); p.add_argument("spec"); p.set_defaults(func=cmd_ready)
    p = sub.add_parser("task"); p.add_argument("action", choices=["start", "done"])
    p.add_argument("spec"); p.add_argument("task_id"); p.add_argument("--manual-evidence", default="")
    p.set_defaults(func=cmd_task)
    p = sub.add_parser("resume"); p.add_argument("spec"); p.add_argument("--by", required=True)
    p.add_argument("--reason", required=True); p.set_defaults(func=cmd_resume)
    p = sub.add_parser("close"); p.add_argument("spec"); p.add_argument("--base", default="")
    p.set_defaults(func=cmd_close)
    p = sub.add_parser("ci-guard"); p.add_argument("--branch", required=True); p.add_argument("--base", default="")
    p.add_argument("--head", default="HEAD"); p.add_argument("--worktree", action="store_true")
    p.add_argument("--json", action="store_true"); p.set_defaults(func=cmd_ci_guard)
    p = sub.add_parser("handoff"); p.add_argument("spec", nargs="?"); p.add_argument("--note", default="")
    p.set_defaults(func=cmd_handoff)
    p = sub.add_parser("archive"); p.add_argument("spec"); p.set_defaults(func=cmd_archive)
    p = sub.add_parser("report"); p.add_argument("--json", action="store_true"); p.set_defaults(func=cmd_report)
    p = sub.add_parser("worktree"); p.add_argument("spec"); p.set_defaults(func=cmd_worktree)
    p = sub.add_parser("doctor"); p.add_argument("--json", action="store_true"); p.set_defaults(func=cmd_doctor)
    p = sub.add_parser("update"); p.add_argument("source", nargs="?"); p.add_argument("--apply", action="store_true")
    p.add_argument("--yes", action="store_true"); p.add_argument("--json", action="store_true")
    p.add_argument("--restore"); p.set_defaults(func=cmd_update)
    p = sub.add_parser("migrate"); p.add_argument("spec", nargs="?"); p.add_argument("--check", action="store_true")
    p.set_defaults(func=cmd_migrate)
    p = sub.add_parser("template"); p.add_argument("action", choices=["export"])
    p.add_argument("destination"); p.set_defaults(func=cmd_template)
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (CliError, ValueError, json.JSONDecodeError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
