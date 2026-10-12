"""Repository contracts: layout, ownership, .gitignore and GitHub workflows (stdlib only)."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agents" / "bin"))
import speckit_cli as cli  # noqa: E402


class DistributionLayoutTestCase(unittest.TestCase):
    def tracked_files(self) -> list[str]:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            self.skipTest("not a git checkout")
        return [path for path in result.stdout.split("\0") if path and (ROOT / path).is_file()]

    def test_root_allowlist(self):
        allowed = {
            ".agents", ".env.example", ".github", ".gitignore", "AGENTS.md", "CLAUDE.md",
            "README.md", "speckit", "specs",
        }
        roots = {Path(path).parts[0] for path in self.tracked_files()}
        self.assertEqual(roots, allowed)

    def test_project_memory_is_neutral(self):
        preferences = (ROOT / ".agents" / "memory" / "preferences.md").read_text(encoding="utf-8")
        decisions = (ROOT / ".agents" / "memory" / "decisions.md").read_text(encoding="utf-8")
        self.assertNotRegex(preferences, r"(?m)^- ")
        self.assertNotRegex(decisions, r"(?m)^## \d{4}-\d{2}-\d{2}")
        self.assertNotRegex(preferences + decisions, r"specs? 00[1-9]")

    def test_default_examples_are_minimal(self):
        examples = ROOT / ".agents" / "examples"
        prefix = Path(".agents/examples")
        example_files = [Path(path) for path in self.tracked_files() if Path(path).is_relative_to(prefix)]
        directories = {path.parts[2] for path in example_files if len(path.parts) > 3}
        self.assertEqual(directories, {"001-archive-specs", "history"})
        self.assertEqual(
            [path.name for path in (examples / "history").iterdir() if path.is_file()],
            ["README.md"],
        )

    def test_history_index_covers_seed_specs(self):
        history = (ROOT / ".agents" / "examples" / "history" / "README.md").read_text(
            encoding="utf-8",
        )
        entries = re.findall(
            r"^## (00[1-8]-[^\n]+).*?/commit/([0-9a-f]{40})\)\.$", history,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertEqual([name[:3] for name, _commit in entries], [f"{number:03d}" for number in range(1, 9)])
        self.assertEqual(len({commit for _name, commit in entries}), 8)


class TemplateOwnershipTestCase(unittest.TestCase):
    def test_manifest_covers_core_and_excludes_project_runtime(self):
        manifest = json.loads((ROOT / ".agents" / "template-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual((manifest["format_version"], manifest["owner"]), (2, "template-owned"))
        declared = {entry["path"]: entry["owner"] for entry in manifest["files"]}
        self.assertEqual(list(declared), sorted(declared))
        self.assertEqual(
            {path for path, owner in declared.items() if owner == "project-owned"},
            {".agents/project.json", ".env.example", ".gitignore", "README.md"},
        )
        for directory in ("bin", "examples", "roles", "schemas", "skills", "templates", "tests"):
            for path in (ROOT / ".agents" / directory).rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix not in (".pyc", ".pyo"):
                    self.assertEqual(declared.get(path.relative_to(ROOT).as_posix()), "template-owned", path)
        for path in (ROOT / ".agents" / "rules").rglob("*.md"):
            rel_path = path.relative_to(ROOT).as_posix()
            if not rel_path.startswith(".agents/rules/stack-"):
                self.assertEqual(declared.get(rel_path), "template-owned", path)
        self.assertFalse(any(path.startswith("specs/") or path.startswith(".agents/memory/")
                             or path.startswith(".agents/rules/stack-") for path in declared))
        self.assertFalse(any(cli.maintainer_only_path(path) for path in declared))


class AgnosticLayoutTestCase(unittest.TestCase):
    def test_no_tool_specific_config_is_versioned(self):
        # Local tool state may exist on a machine; the template itself ships none of it.
        folders = (".claude", ".codex", ".opencode", ".cursor")
        result = subprocess.run(["git", "ls-files", "--", *folders], cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            self.skipTest("not a git checkout")
        self.assertEqual(result.stdout.strip(), "")

    def test_entry_points_load_the_same_rules(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("@AGENTS.md", claude.splitlines())
        for rule in sorted((ROOT / ".agents" / "rules").glob("*.md")):
            rel_path = rule.relative_to(ROOT).as_posix()
            self.assertIn(rel_path, agents, rel_path)
            self.assertIn(f"@{rel_path}", claude.splitlines(), rel_path)

    def test_skills_and_roles_are_plain_markdown(self):
        for path in sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md")):
            head = path.read_text(encoding="utf-8").split("---")[1]
            self.assertIn(f"name: {path.parent.name}\n", head, path)
            self.assertIn("description: ", head, path)
        for path in sorted((ROOT / ".agents" / "roles").glob("*.md")):
            head = path.read_text(encoding="utf-8").split("---")[1]
            self.assertIn(f"name: {path.stem}\n", head, path)
            self.assertNotIn("edit:", head, path)  # path scopes are instructions, not tool config


class IntakeOrchestrationContractTestCase(unittest.TestCase):
    @staticmethod
    def read(path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_intake_requires_explicit_mode(self):
        rule = self.read(".agents/rules/intake-orchestration.md")
        skill = self.read(".agents/skills/sdd-intake/SKILL.md")
        self.assertIn("`guided`", rule)
        self.assertIn("`proposal`", rule)
        self.assertIn("No se inicia `sdd-specify`", rule)
        self.assertIn("No elijas por el usuario", skill)

    def test_guided_mode_contract(self):
        rule = self.read(".agents/rules/intake-orchestration.md")
        skill = self.read(".agents/skills/sdd-intake/SKILL.md")
        brief = self.read(".agents/templates/brief.md")
        self.assertIn("una sola ronda consolidada", rule)
        for section in ("Proceso actual", "Resultado esperado", "Reglas de negocio y fuentes",
                        "Permisos y sensibilidad"):
            self.assertIn(section, brief)
        self.assertIn("Propón opciones o ejemplos", skill)

    def test_proposal_mode_contract(self):
        rule = self.read(".agents/rules/intake-orchestration.md")
        brief = self.read(".agents/templates/brief.md")
        for label in ("Hechos aportados", "Supuestos", "Decisiones abiertas"):
            self.assertIn(label, rule)
            self.assertIn(label, brief)
        self.assertIn("Un supuesto nunca se presenta como hecho", rule)

    def test_intake_minimizes_sensitive_data(self):
        rule = self.read(".agents/rules/intake-orchestration.md")
        role = self.read(".agents/roles/business-analyst.md")
        self.assertIn("nunca la transcripción cruda", rule)
        self.assertIn("secretos", rule)
        self.assertIn("PII", rule)
        self.assertIn("datos sintéticos", rule)
        self.assertIn("No conservas transcripciones crudas", role)

    def test_brief_confirmation_precedes_architect(self):
        rule = self.read(".agents/rules/intake-orchestration.md")
        skill = self.read(".agents/skills/sdd-intake/SKILL.md")
        orchestrator = self.read(".agents/roles/orchestrator.md")
        for value in ("Estado: confirmed", "Confirmado por", "Confirmado el"):
            self.assertIn(value, rule)
        self.assertIn("Confirmar el brief no es GATE 1", rule)
        self.assertIn("no hace handoff", skill)
        self.assertIn("No haces handoff", orchestrator)

    def test_architect_does_not_repeat_confirmed_intake(self):
        role = self.read(".agents/roles/architect.md")
        skill = self.read(".agents/skills/sdd-specify/SKILL.md")
        self.assertIn("No repitas preguntas de negocio", role)
        self.assertIn("No repitas la entrevista de negocio", skill)
        self.assertIn("una sola ronda consolidada", skill)
        self.assertIn("brief legacy", skill)

    def test_role_ownership_and_single_agent_fallback(self):
        rule = self.read(".agents/rules/intake-orchestration.md")
        agents = self.read("AGENTS.md")
        for role in ("orchestrator", "business-analyst", "architect", "implementer", "reviewer"):
            self.assertIn(f"`{role}`", rule)
            self.assertTrue((ROOT / ".agents" / "roles" / f"{role}.md").is_file(), role)
        self.assertIn("Sin subagentes", rule)
        self.assertIn("Actuando como <rol>", rule)
        self.assertIn("sin mezclar permisos", agents)

    def test_business_analyst_is_the_only_intake_role_name(self):
        old_role = "business" + "-facilitator"
        manifest = cli.load_template_manifest(ROOT)
        declared = {entry["path"] for entry in manifest["files"]}
        self.assertIn(".agents/roles/business-analyst.md", declared)
        self.assertNotIn(f".agents/roles/{old_role}.md", declared)
        self.assertFalse((ROOT / ".agents" / "roles" / f"{old_role}.md").exists())
        for rel_path in sorted(declared):
            path = ROOT / rel_path
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            self.assertNotIn(old_role, content, rel_path)


class GitIgnoreTestCase(unittest.TestCase):
    def test_legitimate_bin_directories_are_not_ignored(self):
        for path in (".agents/bin/new.py", "src/bin/tool", "bin/tool"):
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", path], cwd=ROOT,
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1, path)
        for path in ("dist/tool", ".env"):
            result = subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", path], cwd=ROOT,
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, path)


class WorkflowContractTestCase(unittest.TestCase):
    def test_launcher_exposes_ci_guard(self):
        result = subprocess.run([str(ROOT / "speckit"), "ci-guard", "--help"], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--branch", result.stdout)

    def test_template_publish_projects_develop_without_merge(self):
        workflow_path = ROOT / ".github" / "workflows" / "publish-template.yml"
        manifest_paths = {entry["path"] for entry in cli.load_template_manifest(ROOT)["files"]}
        self.assertNotIn(".github/workflows/publish-template.yml", manifest_paths)
        if not workflow_path.exists():
            return  # The maintainer workflow is intentionally absent from exported projects.
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn("push:\n    branches: [develop]", workflow)
        self.assertNotIn("workflow_dispatch", workflow)
        self.assertIn("github.ref_name == 'develop'", workflow)
        self.assertIn("./speckit template export", workflow)
        self.assertIn("git read-tree --empty", workflow)
        self.assertIn("git commit-tree", workflow)
        self.assertIn("refs/heads/main", workflow)
        self.assertNotIn("git merge", workflow)
        self.assertNotIn("git push --force", workflow)
        self.assertTrue(cli.maintainer_only_path(".github/workflows/publish-template.yml"))

    def test_actions_are_sha_pinned_with_versions_and_least_privilege(self):
        workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        uses = []
        for path in workflows:
            for line in path.read_text(encoding="utf-8").splitlines():
                if "uses:" in line:
                    uses.append((path.name, line.strip()))
        self.assertTrue(uses)
        for name, line in uses:
            self.assertRegex(line, r"^- uses: [^@\s]+@[0-9a-f]{40} # v\d+(?:\.\d+)*$", name)

        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("\npermissions:\n  contents: read\n", ci)
        self.assertIn(
            "  secrets:\n"
            "    permissions:\n"
            "      contents: read\n"
            "      pull-requests: read\n",
            ci,
        )
        self.assertNotRegex(ci, r"(?m)^\s+[A-Za-z-]+:\s*write\s*$")
        issue = (ROOT / ".github" / "workflows" / "spec-from-issue.yml").read_text(encoding="utf-8")
        self.assertIn("\npermissions: {}\n", issue)
        self.assertIn("    permissions:\n      contents: write\n      pull-requests: write\n      actions: write\n", issue)

    def test_issue_spec_ids_are_globally_serialized_and_retried(self):
        workflow = (ROOT / ".github" / "workflows" / "spec-from-issue.yml").read_text(encoding="utf-8")
        self.assertIn("group: spec-from-issue-id-allocation", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("git ls-remote --heads origin 'refs/heads/feat/[0-9]*-*'", workflow)
        self.assertIn("for attempt in 1 2 3 4 5", workflow)
        self.assertIn("--number \"$next\"", workflow)
        self.assertNotIn("git push --force", workflow)

    def test_ci_uses_locked_dependencies_in_venv_and_python_extremes(self):
        requirements = (ROOT / ".agents" / "requirements-dev.txt").read_text(encoding="utf-8")
        pins = [line for line in requirements.splitlines() if line and not line.startswith("#")]
        self.assertTrue(pins)
        self.assertTrue(all(re.fullmatch(r"[a-z0-9-]+==[^=\s]+", pin) for pin in pins))

        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn('python-version: ["3.9", "3.13"]', ci)
        self.assertIn("python -m venv .venv", ci)
        self.assertIn(".venv/bin/python -m pip install", ci)
        self.assertIn(".venv/bin/python -S -m unittest", ci)
        self.assertNotRegex(ci, r"(?m)^\s*run: (?:pip|python) (?:install|-m unittest)")

        issue = (ROOT / ".github" / "workflows" / "spec-from-issue.yml").read_text(encoding="utf-8")
        self.assertIn("python3 -m venv .venv", issue)
        self.assertIn(".venv/bin/python .agents/bin/speckit_cli.py", issue)

    def test_ci_links_feature_branch_diff_spec_and_close_fingerprint(self):
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("  traceability:\n", ci)
        self.assertIn("fetch-depth: 0", ci)
        self.assertIn("BRANCH_NAME: ${{ github.head_ref || github.ref_name }}", ci)
        self.assertIn("BASE_SHA: ${{ github.event.pull_request.base.sha || '' }}", ci)
        self.assertIn("HEAD_SHA: ${{ github.event.pull_request.head.sha || github.sha }}", ci)
        self.assertIn('./speckit ci-guard "${args[@]}"', ci)


if __name__ == "__main__":
    unittest.main()
