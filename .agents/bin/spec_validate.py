"""
Spec state.json validator for the SDD methodology.

Validates state.json against the JSON Schema and performs semantic checks:
size (S/M/L), gates (approval), phase prerequisites, non-empty artifacts,
tasks.md format, evidence.md PASS entry for every [x] task, Definition of Ready (no [NEEDS CLARIFICATION], AC-NNN traced
to tasks and test plan) and status coherence. Too many tasks is a warning. Uses `jsonschema` when installed; otherwise falls back
to a minimal stdlib validator that covers the keywords used by the schema.

Usage:
    python3 .agents/bin/spec_validate.py specs/001-login            # spec dir or state.json
    python3 .agents/bin/spec_validate.py --all                      # every specs/*/state.json
    python3 .agents/bin/spec_validate.py --no-files .agents/examples/*.json   # schema + rules, no file checks
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import jsonschema
except ImportError:  # stdlib fallback below
    jsonschema = None

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / ".agents" / "schemas" / "spec-state.schema.json"
VERSION_PATH = ROOT / ".agents" / "version.json"
SPECS_DIR = ROOT / "specs"


def load_version_info(path: Path = VERSION_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    version, schema = data.get("template_version"), data.get("schema_version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError(f"{path}: template_version must use semantic X.Y.Z format")
    if not isinstance(schema, int) or isinstance(schema, bool) or schema < 1:
        raise ValueError(f"{path}: schema_version must be a positive integer")
    return data


VERSION_INFO = load_version_info()
TEMPLATE_VERSION = VERSION_INFO["template_version"]
SCHEMA_VERSION = VERSION_INFO["schema_version"]

ARTIFACT_FILE_MAP = {
    "spec_md": "spec.md",
    "implementation_plan_md": "implementation-plan.md",
    "tasks_md": "tasks.md",
    "test_plan_md": "test-plan.md",
}

# Artifacts each size needs; S keeps technical notes and tests inside spec.md
REQUIRED_ARTIFACTS = {
    "S": {"spec_md", "tasks_md"},
    "M": set(ARTIFACT_FILE_MAP),
}
DESIGN_ARTIFACTS = ["spec_md", "implementation_plan_md"]  # what GATE 1 approves
MAX_TASKS = {"S": 3, "M": 8}

PHASE_ORDER = ["spec", "plan", "tasks", "test_plan", "ready", "implementation", "validation"]

# Cumulative prerequisites to *be* in a phase: (artifacts, needs approval)
PHASE_PREREQUISITES = {
    "plan": (["spec_md"], False),
    "tasks": (["implementation_plan_md"], True),           # GATE 1: spec + plan approved
    "test_plan": (["tasks_md"], False),
    "ready": (["test_plan_md"], False),                    # GATE 2: ready (see validate_files)
    "implementation": ([], False),
    "validation": ([], False),
}

TASK_LINE = re.compile(
    r"^\s*[-*]\s*\[([ /xX])\]\s*(TASK-\d{3,}):\s*(\S.*?)\s+"
    r"\((AC-\d{3,}(?:\s*,\s*AC-\d{3,})*)\)\s*$",
    re.MULTILINE,
)
TASK_CANDIDATE = re.compile(r"^\s*[-*]\s*\[[^\]]*\]\s*TASK-", re.IGNORECASE)
AC_ID = re.compile(r"\bAC-\d{3,}\b")
TC_ID = re.compile(r"^TC-\d{3,}$")
TEST_TYPES = {"unit", "integration", "e2e", "manual"}
EVIDENCE_PASS = re.compile(r"^##\s+(TASK-\d{3,})\s+[-—]\s+PASS\b", re.MULTILINE)
CLOSE_PASS = re.compile(r"^##\s+CLOSE\s+[-—]\s+PASS\b", re.MULTILINE)
CLARIFICATION = "[NEEDS CLARIFICATION"
PLACEHOLDER_RE = re.compile(
    r"<(?:NNN|nombre(?: de la idea)?|contexto|acción|resultado observable|descripción|"
    r"escenario observable|comando|lo que explícitamente NO se hace|paquete|"
    r"comando de tests de AGENTS\.md §K)>"
)
REQUIRED_SECTIONS = {
    "spec_md": ["Problema y contexto", "Usuarios y flujos", "Criterios de aceptación", "Alcance",
                "Restricciones y datos"],
    "implementation_plan_md": ["Módulos y componentes afectados", "Decisiones", "Datos y migraciones",
                               "Dependencias nuevas", "Riesgos y mitigación"],
}
STATUS_PHASES = {
    "planning": {"spec", "plan", "tasks", "test_plan"},
    "awaiting_approval": {"plan"},
    "ready": {"ready"},
    "in_progress": {"implementation", "validation"},
    "blocked": {"implementation"},
    "completed": {"validation"},
}
TYPE_MAP = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "null": type(None), "integer": int, "number": (int, float),
}


class TaskRecord(NamedTuple):
    mark: str
    task_id: str
    description: str
    acs: tuple[str, ...]
    line: int


class TestCaseRecord(NamedTuple):
    case_id: str
    ac: str
    scenario: str
    kind: str
    command: str
    line: int


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def _matches_type(value, expected) -> bool:
    types = expected if isinstance(expected, list) else [expected]
    for t in types:
        if t in ("integer", "number") and isinstance(value, bool):
            continue
        if isinstance(value, TYPE_MAP[t]):
            return True
    return False


def mini_validate(instance, schema: dict, root: dict, path: str = "$") -> list[str]:
    """Minimal draft-07 subset: $ref, type, enum, pattern, minLength, required,
    properties, additionalProperties=false."""
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return mini_validate(instance, node, root, path)

    errors: list[str] = []
    if "type" in schema and not _matches_type(instance, schema["type"]):
        return [f"{path}: expected type {schema['type']}, got {type(instance).__name__}"]
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']}")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: {instance!r} does not match {schema['pattern']}")
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required property '{key}'")
        for key, value in instance.items():
            if key in props:
                errors.extend(mini_validate(value, props[key], root, f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: additional property '{key}' is not allowed")
    if isinstance(instance, list) and "items" in schema:
        for index, value in enumerate(instance):
            errors.extend(mini_validate(value, schema["items"], root, f"{path}[{index}]"))
    return errors


def validate_schema(state: dict, schema: dict) -> list[str]:
    if jsonschema is None:
        return [f"Schema: {e}" for e in mini_validate(state, schema, schema)]
    validator = jsonschema.Draft7Validator(schema)
    return [
        f"Schema: $.{'.'.join(str(p) for p in e.absolute_path)}: {e.message}".replace("$.:", "$:")
        for e in sorted(validator.iter_errors(state), key=lambda e: list(e.absolute_path))
    ]


def parse_task_records(content: str) -> list[TaskRecord]:
    """Parse canonical task declarations without accepting partial prefixes."""
    records = []
    for line_number, line in enumerate(content.splitlines(), 1):
        match = TASK_LINE.fullmatch(line)
        if not match:
            continue
        acs = tuple(part.strip() for part in match.group(4).split(","))
        records.append(TaskRecord(match.group(1).lower(), match.group(2), match.group(3).strip(), acs,
                                  line_number))
    return records


def parse_tasks(content: str) -> list[tuple[str, str]]:
    """Compatibility view used by lifecycle code: [(mark, task_id)]."""
    return [(record.mark, record.task_id) for record in parse_task_records(content)]


def validate_task_structure(content: str, spec_acs: set[str]) -> list[str]:
    errors = []
    records = parse_task_records(content)
    valid_lines = {record.line for record in records}
    for line_number, line in enumerate(content.splitlines(), 1):
        if TASK_CANDIDATE.match(line) and line_number not in valid_lines:
            errors.append(
                f"tasks.md line {line_number} must match '- [ ] TASK-001: description (AC-001)'"
            )
    ids = [record.task_id for record in records]
    duplicates = sorted({task_id for task_id in ids if ids.count(task_id) > 1})
    if duplicates:
        errors.append(f"tasks.md has duplicated task IDs: {', '.join(duplicates)}")
    for record in records:
        repeated = sorted({ac for ac in record.acs if record.acs.count(ac) > 1})
        if repeated:
            errors.append(f"tasks.md line {record.line} repeats ACs: {', '.join(repeated)}")
        unknown = sorted(set(record.acs) - spec_acs)
        if unknown:
            errors.append(f"tasks.md line {record.line} references ACs not in spec.md: {', '.join(unknown)}")
    return errors


def _markdown_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def parse_test_cases(content: str) -> list[TestCaseRecord]:
    records = []
    for line_number, line in enumerate(content.splitlines(), 1):
        cells = _markdown_cells(line)
        if not cells or len(cells) != 5 or not TC_ID.fullmatch(cells[0]):
            continue
        command = cells[4]
        if len(command) >= 2 and command[0] == command[-1] == "`":
            command = command[1:-1].strip()
        records.append(TestCaseRecord(cells[0], cells[1], cells[2], cells[3].lower(), command, line_number))
    return records


def validate_test_structure(content: str, spec_acs: set[str], filename: str) -> list[str]:
    errors = []
    records = parse_test_cases(content)
    valid_lines = {record.line for record in records}
    for line_number, line in enumerate(content.splitlines(), 1):
        cells = _markdown_cells(line)
        if not cells:
            continue
        if cells and cells[0].lower() == "id":
            continue
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if line_number not in valid_lines:
            errors.append(f"{filename} line {line_number} must contain 5 cells and a canonical TC-NNN ID")
    ids = [record.case_id for record in records]
    duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicates:
        errors.append(f"{filename} has duplicated test IDs: {', '.join(duplicates)}")
    for record in records:
        if record.ac not in spec_acs:
            errors.append(f"{filename} line {record.line} references unknown AC: {record.ac or '(empty)'}")
        if not record.scenario:
            errors.append(f"{filename} line {record.line} requires a non-empty scenario")
        if record.kind not in TEST_TYPES:
            errors.append(f"{filename} line {record.line} has invalid type: {record.kind or '(empty)'}")
        if not record.command:
            errors.append(f"{filename} line {record.line} requires a command or manual steps")
    covered = {record.ac for record in records if record.ac in spec_acs}
    if spec_acs - covered:
        errors.append(f"{filename} does not trace {', '.join(sorted(spec_acs - covered))}")
    return errors


def section_body(content: str, heading: str) -> str | None:
    """Return a level-2 markdown section body, or None when the heading is absent."""
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)", content,
                      re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def size_s_tests_body(content: str) -> str | None:
    """Read the canonical size-S tests section or its one supported legacy alias."""
    canonical = section_body(content, "Pruebas")
    return canonical if canonical is not None else section_body(content, "Pruebas (solo size S)")


def acceptance_criteria(content: str) -> set[str]:
    body = section_body(content, "Criterios de aceptación")
    return set(AC_ID.findall(body or ""))


def requires_strict_ready_structure(state: dict) -> bool:
    """Grandfather completed specs that predate the explicit Ready gate."""
    phase = state.get("phase")
    crossed_ready = any(
        isinstance(event, dict) and event.get("event") == "ready"
        for event in state.get("events", [])
    )
    return crossed_ready or (
        state.get("status") != "completed"
        and phase in ("ready", "implementation", "validation")
    )


def artifact_completeness_errors(key: str, content: str) -> list[str]:
    """Detect untouched template tokens and empty required design sections."""
    filename = ARTIFACT_FILE_MAP[key]
    errors = []
    placeholders = sorted(set(PLACEHOLDER_RE.findall(content)))
    if placeholders:
        errors.append(f"{filename} contains template placeholders: {', '.join(placeholders)}")
    for heading in REQUIRED_SECTIONS.get(key, []):
        body = section_body(content, heading)
        if body is None:
            errors.append(f"{filename} is missing required section '## {heading}'")
        elif not re.sub(r"[|:\-\s]", "", body):
            errors.append(f"{filename} has empty required section '## {heading}'")
    return errors


def validate_retro(spec_dir: Path) -> list[str]:
    path = spec_dir / "retro.md"
    if not path.is_file():
        return ["archive requires retro.md"]
    content = path.read_text(encoding="utf-8").strip()
    errors = []
    if re.search(r"<[^>\n]+>", content):
        errors.append("retro.md still contains template placeholders")
    for heading in ("Qué funcionó", "Qué costó (vueltas, reintentos, ambigüedades del brief)",
                    "Preferencias nuevas", "Reglas o plantillas a ajustar"):
        body = section_body(content, heading)
        if body is None or not re.sub(r"[-*\s]", "", body):
            errors.append(f"retro.md requires a completed '## {heading}' section")
    return errors


def normalized_content(content: str) -> str:
    """Canonical text used by design approvals across OS/editor line endings."""
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).rstrip("\n") + "\n"


def design_hashes(state: dict, spec_dir: Path) -> dict[str, str]:
    keys = [key for key in DESIGN_ARTIFACTS if key in required_artifacts(state)]
    hashes = {}
    for key in keys:
        path = spec_dir / ARTIFACT_FILE_MAP[key]
        if not path.is_file():
            raise OSError(f"missing design artifact: {path}")
        canonical = normalized_content(path.read_text(encoding="utf-8"))
        hashes[key] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return hashes


def required_artifacts(state: dict) -> set[str]:
    return REQUIRED_ARTIFACTS.get(state.get("size"), REQUIRED_ARTIFACTS["M"])


def read_artifact(state: dict, spec_dir: Path, key: str) -> str | None:
    """Content of an artifact marked true that exists and is not empty."""
    path = spec_dir / ARTIFACT_FILE_MAP[key]
    if state.get("artifacts", {}).get(key) is not True or not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def is_untouched_scaffold(spec_dir: Path, key: str, content: str) -> bool:
    """Keep future planning templates neutral until a user actually edits them."""
    template_path = ROOT / ".agents" / "templates" / ARTIFACT_FILE_MAP[key]
    if not template_path.is_file():
        return False
    number, separator, name = spec_dir.name.partition("-")
    if not separator:
        return False
    template = template_path.read_text(encoding="utf-8")
    rendered = template.replace("<NNN>", number).replace("<nombre>", name)
    return normalized_content(content) == normalized_content(rendered)


def read_planning_candidate(state: dict, spec_dir: Path, key: str) -> str | None:
    """Read edited planning artifacts even before Ready marks their flags true."""
    marked = read_artifact(state, spec_dir, key)
    if marked is not None:
        return marked
    if not state.get("approval") or key not in {"tasks_md", "test_plan_md"}:
        return None
    path = spec_dir / ARTIFACT_FILE_MAP[key]
    if not path.is_file():
        return None
    content = path.read_text(encoding="utf-8").strip()
    if not content or is_untouched_scaffold(spec_dir, key, content):
        return None
    return content


def validate_files(state: dict, spec_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    artifacts = state.get("artifacts", {})
    status = state.get("status")
    phase = state.get("phase")

    if state.get("spec_name") != spec_dir.name:
        errors.append(f"spec_name='{state.get('spec_name')}' must match directory '{spec_dir.name}'")

    for key, filename in ARTIFACT_FILE_MAP.items():
        if artifacts.get(key) is not True:
            continue
        artifact_path = spec_dir / filename
        if not artifact_path.is_file():
            errors.append(f"Artifact '{key}' is true but '{filename}' does not exist")
        elif not artifact_path.read_text(encoding="utf-8").strip():
            errors.append(f"Artifact '{key}' is true but '{filename}' is empty")

    # From design review onwards, marked artifacts must contain real content, not template scaffolding.
    if state.get("approval") or status == "awaiting_approval" or phase in ("implementation", "validation"):
        for key in required_artifacts(state):
            text = read_planning_candidate(state, spec_dir, key)
            if text is not None:
                errors.extend(artifact_completeness_errors(key, text))

    approval = state.get("approval")
    if approval:
        expected = approval.get("design_hashes") or {}
        required_keys = {key for key in DESIGN_ARTIFACTS if key in required_artifacts(state)}
        if set(expected) != required_keys:
            errors.append("approval.design_hashes must contain exactly: " + ", ".join(sorted(required_keys)))
        else:
            try:
                current = design_hashes(state, spec_dir)
            except OSError as exc:
                errors.append(str(exc))
            else:
                changed = [ARTIFACT_FILE_MAP[key] for key in sorted(required_keys) if current[key] != expected[key]]
                if changed:
                    errors.append("approved design changed: " + ", ".join(changed) + " (request a new approval)")

    spec_text = read_artifact(state, spec_dir, "spec_md")
    tasks_text = read_planning_candidate(state, spec_dir, "tasks_md")
    if tasks_text is not None:
        tasks = parse_tasks(tasks_text)
        ids = [task_id for _, task_id in tasks]
        if not tasks:
            errors.append("tasks.md has no tasks in format '- [ ] TASK-001: description (AC-001)'")
        limit = MAX_TASKS.get(state.get("size"))
        if limit and len(set(ids)) > limit:
            warnings.append(f"{len(set(ids))} tasks for size={state.get('size')} (max {limit}): consider splitting the spec")
        current_task = state.get("current_task")
        if current_task is not None and current_task not in ids:
            errors.append(f"current_task='{current_task}' not found in tasks.md")
        evidence_file = spec_dir / "evidence.md"
        evidence = evidence_file.read_text(encoding="utf-8") if evidence_file.is_file() else ""
        passed = set(EVIDENCE_PASS.findall(evidence))
        unproven = [task_id for mark, task_id in tasks if mark == "x" and task_id not in passed]
        if unproven:
            errors.append(f"tasks marked [x] without PASS entry in evidence.md: {', '.join(unproven)} (use 'speckit task done')")
        if status == "completed":
            open_tasks = [task_id for mark, task_id in tasks if mark != "x"]
            if open_tasks:
                errors.append(f"status=completed but tasks not done: {', '.join(open_tasks)}")
            if not CLOSE_PASS.search(evidence):
                errors.append("status=completed requires a '## CLOSE — PASS' entry in evidence.md")
    elif state.get("current_task") is not None:
        errors.append(f"current_task='{state.get('current_task')}' set but tasks.md is not available")

    # Definition of Ready: nothing is approved (or sent for approval) with open questions
    if state.get("approval") or status == "awaiting_approval":
        for key in DESIGN_ARTIFACTS:
            text = read_artifact(state, spec_dir, key)
            if text and CLARIFICATION in text:
                errors.append(f"{ARTIFACT_FILE_MAP[key]} still has [NEEDS CLARIFICATION] markers")
        if spec_text is not None and not acceptance_criteria(spec_text):
            errors.append("spec.md defines no acceptance criteria (AC-001: Dado/Cuando/Entonces)")

    # Definition of Ready: canonical tasks and structured scenarios for both sizes.
    planning_with_approval = bool(state.get("approval")) and status == "planning" \
        and phase in ("tasks", "test_plan")
    if requires_strict_ready_structure(state) or planning_with_approval:
        acs = acceptance_criteria(spec_text or "")
        if tasks_text is not None:
            errors.extend(validate_task_structure(tasks_text, acs))
        if state.get("size") == "S":
            tests_text = size_s_tests_body(spec_text or "")
            if tests_text is None:
                errors.append("spec.md requires a completed '## Pruebas' section for size S")
            else:
                errors.extend(validate_test_structure(tests_text, acs, "spec.md ## Pruebas"))
        else:
            tests_text = read_planning_candidate(state, spec_dir, "test_plan_md")
            if tests_text is not None:
                errors.extend(validate_test_structure(tests_text, acs, "test-plan.md"))

    # Traceability: every AC reaches a task (and a test scenario in size M) before coding.
    if phase in PHASE_ORDER and PHASE_ORDER.index(phase) >= PHASE_ORDER.index("ready"):
        acs = acceptance_criteria(spec_text or "")
        trace_keys = ["tasks_md"] + (["test_plan_md"] if "test_plan_md" in required_artifacts(state) else [])
        for key in trace_keys:
            text = read_artifact(state, spec_dir, key)
            if text is None:
                continue
            found = set(AC_ID.findall(text))
            filename = ARTIFACT_FILE_MAP[key]
            if acs - found:
                errors.append(f"{filename} does not trace {', '.join(sorted(acs - found))}")
            if found - acs:
                errors.append(f"{filename} references ACs not in spec.md: {', '.join(sorted(found - acs))}")

    return errors, warnings


def validate_semantic_rules(state: dict) -> list[str]:
    errors: list[str] = []
    status = state.get("status")
    phase = state.get("phase")
    blocked_reason = state.get("blocked_reason")
    artifacts = state.get("artifacts") or {}
    required = required_artifacts(state)

    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION} (run 'speckit migrate')")

    allowed_phases = STATUS_PHASES.get(status, set())
    if phase not in allowed_phases:
        errors.append(f"status={status} is incompatible with phase={phase}")

    if state.get("size") == "L":
        errors.append("size=L is too big to implement: split it into specs of size S or M")

    if status == "blocked" and not (blocked_reason or "").strip():
        errors.append("status=blocked requires a non-empty 'blocked_reason'")
    if status != "blocked" and blocked_reason is not None:
        errors.append(f"status={status} requires blocked_reason=null")

    if phase in PHASE_ORDER:
        for prior in PHASE_ORDER[1:PHASE_ORDER.index(phase) + 1]:
            prior_artifacts, needs_approval = PHASE_PREREQUISITES[prior]
            for key in prior_artifacts:
                if key in required and artifacts.get(key) is not True:
                    errors.append(f"phase={phase} requires artifact '{key}' to be true")
            if needs_approval and not state.get("approval"):
                errors.append(f"phase={phase} requires approval (GATE 1: user approves spec + plan)")

    if status == "awaiting_approval":
        if state.get("approval"):
            errors.append("status=awaiting_approval requires approval=null")
        for key in DESIGN_ARTIFACTS:
            if key in required and artifacts.get(key) is not True:
                errors.append(f"status=awaiting_approval requires '{key}' to be true")

    if phase in ("spec", "plan", "tasks", "test_plan", "ready") and state.get("current_task") is not None:
        errors.append(f"phase={phase} requires current_task=null")

    if state.get("approval") and phase in ("spec", "plan"):
        errors.append(f"phase={phase} requires approval=null")
    if not state.get("approval") and phase in ("tasks", "test_plan", "ready", "implementation", "validation"):
        errors.append(f"phase={phase} requires approval")

    if status == "blocked" and state.get("current_task") is None:
        errors.append("status=blocked requires current_task")

    if status == "completed":
        if phase != "validation":
            errors.append("status=completed requires phase=validation")
        if state.get("current_task") is not None:
            errors.append("status=completed requires current_task=null")

    return errors


def validate_state_file(state_path: Path, schema: dict, check_files: bool = True) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    try:
        state = load_json(state_path)
    except (OSError, json.JSONDecodeError) as e:
        return [f"Cannot read JSON: {e}"], []
    if not isinstance(state, dict):
        return ["state.json must contain a JSON object"], []

    errors = validate_schema(state, schema)
    errors.extend(validate_semantic_rules(state))
    warnings: list[str] = []
    if check_files:
        file_errors, warnings = validate_files(state, state_path.parent)
        errors.extend(file_errors)
    return errors, warnings


def collect_targets(args: list[str]) -> tuple[list[Path], list[str]]:
    targets: list[Path] = []
    problems: list[str] = []
    if "--all" in args:
        if SPECS_DIR.is_dir():
            for spec_dir in sorted(p for p in SPECS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")):
                state_file = spec_dir / "state.json"
                if state_file.is_file():
                    targets.append(state_file)
                else:
                    problems.append(f"{spec_dir.relative_to(ROOT)}: missing state.json")
            archive = SPECS_DIR / ".archive"
            if archive.is_dir():
                for spec_dir in sorted(p for p in archive.iterdir() if p.is_dir()):
                    state_file = spec_dir / "state.json"
                    if state_file.is_file():
                        targets.append(state_file)
                    else:
                        problems.append(f"{spec_dir.relative_to(ROOT)}: missing state.json")
    for arg in (a for a in args if not a.startswith("--")):
        path = Path(arg).resolve()
        path = path / "state.json" if path.is_dir() else path
        if path.is_file():
            targets.append(path)
        else:
            problems.append(f"{arg}: not found")
    return targets, problems


def main(argv: list[str]) -> int:
    if not argv or argv == ["--no-files"]:
        print(__doc__.strip())
        return 1
    if not SCHEMA_PATH.is_file():
        print(f"ERROR: Schema not found: {SCHEMA_PATH}")
        return 1

    schema = load_json(SCHEMA_PATH)
    targets, problems = collect_targets(argv)
    failed = bool(problems)
    for problem in problems:
        print(f"FAILED — {problem}")

    for state_path in targets:
        errors, warnings = validate_state_file(state_path, schema, check_files="--no-files" not in argv)
        label = state_path.relative_to(ROOT) if state_path.is_relative_to(ROOT) else state_path
        if errors:
            failed = True
            print(f"FAILED — {len(errors)} error(s) in {label}:")
            for err in errors:
                print(f"  ✗ {err}")
        else:
            print(f"OK — {label}")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    if not targets and not problems:
        print("OK — no specs to validate")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
