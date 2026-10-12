"""End-to-end smoke test for the deterministic GitHub Template projection (stdlib only)."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_DIRS = (".claude", ".codex", ".opencode", ".cursor")
GIT_ENV = {"GIT_AUTHOR_NAME": "smoke", "GIT_AUTHOR_EMAIL": "smoke@example.com",
           "GIT_COMMITTER_NAME": "smoke", "GIT_COMMITTER_EMAIL": "smoke@example.com"}

SPEC = """# Spec
## Problema y contexto
Problema real.
## Usuarios y flujos
Un flujo.
## Criterios de aceptación
- AC-001: Dado x, cuando y, entonces z.
## Alcance
Incluye x; excluye w.
## Restricciones y datos
Sin datos sensibles.
"""
SPEC_S = """# Spec
## Problema y contexto
Problema pequeño y verificable.
## Usuarios y flujos
Un usuario ejecuta el flujo corto.
## Criterios de aceptación
- AC-001: Dado un proyecto nuevo, cuando se implementa el flujo corto, entonces el archivo existe.
## Alcance
Incluye el flujo corto; excluye integraciones externas.
## Restricciones y datos
Sin datos sensibles.
## Notas técnicas (solo size S)
Crear un módulo Python sin dependencias.
## Pruebas
| ID | AC | Escenario | Tipo | Comando o pasos |
|----|----|-----------|------|-----------------|
| TC-001 | AC-001 | El módulo pequeño existe | integration | test -f src/small.py |
"""
PLAN = """# Plan
## Módulos y componentes afectados
Un módulo.
## Decisiones
Una decisión.
## Datos y migraciones
Ninguna.
## Dependencias nuevas
Ninguna.
## Riesgos y mitigación
Riesgo controlado.
"""
RETRO = """# Retro
## Qué funcionó
Todo.
## Qué costó (vueltas, reintentos, ambigüedades del brief)
Nada.
## Preferencias nuevas
Ninguna.
## Reglas o plantillas a ajustar
Ninguna.
"""


class TemplateSmokeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.child = Path(cls._tmp.name) / "child"
        export = subprocess.run(
            [str(ROOT / "speckit"), "template", "export", str(cls.child)],
            cwd=ROOT, capture_output=True, text=True,
        )
        if export.returncode != 0:
            raise RuntimeError(f"template export failed\n{export.stdout}{export.stderr}")
        cls.files = sorted(
            path.relative_to(cls.child).as_posix()
            for path in cls.child.rglob("*") if path.is_file()
        )
        # Interpreter of this run stands in for the child's .venv (doctor requires it; no pip needed).
        venv_python = cls.child / ".venv" / "bin" / "python"
        venv_python.parent.mkdir(parents=True)
        venv_python.symlink_to(sys.executable)
        # The child's own project check: the "implemented" code must exist.
        project_path = cls.child / ".agents" / "project.json"
        project = json.loads(project_path.read_text(encoding="utf-8"))
        project["commands"] = {"test": "test -f src/app.py", "lint": "", "build": "", "e2e": ""}
        project_path.write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")
        cls.git("init", "-q", "-b", "main")
        cls.git("add", "-A")
        cls.git("commit", "-q", "-m", "chore: create from template")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    @classmethod
    def git(cls, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=cls.child, capture_output=True, text=True, check=True,
                              env={**os.environ, **GIT_ENV}).stdout

    def speckit(self, *args: str, ok: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run([str(self.child / "speckit"), *args], cwd=self.child,
                                capture_output=True, text=True, timeout=120, env={**os.environ, **GIT_ENV})
        if ok:
            self.assertEqual(result.returncode, 0, f"speckit {' '.join(args)}\n{result.stdout}{result.stderr}")
        return result

    def test_1_layout_has_no_tool_specific_config(self):
        manifest = json.loads((self.child / ".agents" / "template-manifest.json").read_text(encoding="utf-8"))
        expected = {entry["path"] for entry in manifest["files"]} | {
            ".agents/memory/decisions.md", ".agents/memory/preferences.md",
            ".agents/template-manifest.json", "specs/.archive/.gitkeep", "specs/.gitkeep",
        }
        self.assertEqual(set(self.files), expected)
        offending = [path for path in self.files if path.split("/", 1)[0] in TOOL_DIRS]
        self.assertEqual(offending, [])
        for path in (".agents/bin/sync_agents.py", ".agents/bin/agent_guard.py",
                     ".agents/permissions.json", ".agents/generated-manifest.json"):
            self.assertNotIn(path, self.files)
        self.assertIn("AGENTS.md", self.files)
        self.assertIn("CLAUDE.md", self.files)
        history = self.child / ".agents" / "examples" / "history"
        self.assertEqual([path.name for path in history.iterdir()], ["README.md"])
        self.assertEqual(list((self.child / "specs").glob("[0-9]*-*")), [])
        self.assertEqual(list((self.child / "specs" / ".archive").glob("[0-9]*-*")), [])
        for folder in TOOL_DIRS:  # a local tool folder must never end up in a commit
            self.assertEqual(subprocess.run(["git", "check-ignore", "-q", "--no-index", f"{folder}/x"],
                                            cwd=self.child).returncode, 0, folder)

    def test_2_every_instruction_reference_resolves(self):
        agents = (self.child / "AGENTS.md").read_text(encoding="utf-8")
        claude = (self.child / "CLAUDE.md").read_text(encoding="utf-8")
        imports = [line[1:] for line in claude.splitlines() if line.startswith("@")]
        self.assertIn("AGENTS.md", imports)
        for rel_path in imports:
            self.assertTrue((self.child / rel_path).is_file(), f"CLAUDE.md imports missing {rel_path}")
        active = sorted(path.relative_to(self.child).as_posix()
                        for path in (self.child / ".agents" / "rules").glob("*.md"))
        self.assertEqual(sorted(path for path in imports if path.startswith(".agents/rules/")), active)
        for rel_path in set(re.findall(r"`(\.agents/[^`*<>\s]+\.(?:md|json))`", agents)):
            if subprocess.run(["git", "check-ignore", "-q", rel_path], cwd=self.child).returncode == 0:
                continue  # generated at runtime (e.g. SESSION_STATE.md)
            self.assertTrue((self.child / rel_path).exists(), f"AGENTS.md references missing {rel_path}")
        for name in ("sdd-intake", "sdd-specify", "sdd-plan", "sdd-implement", "sdd-review"):
            self.assertTrue((self.child / ".agents" / "skills" / name / "SKILL.md").is_file(), name)
        for name in ("orchestrator", "business-analyst", "architect", "implementer", "reviewer"):
            self.assertTrue((self.child / ".agents" / "roles" / f"{name}.md").is_file(), name)
        brief = (self.child / ".agents" / "templates" / "brief.md").read_text(encoding="utf-8")
        self.assertIn("## 1. Intake", brief)
        self.assertIn("`guided` o `proposal`", brief)
        self.assertTrue((self.child / ".agents" / "rules" / "intake-orchestration.md").is_file())
        for removed in ("speckit sync", "init --tools", "permissions.json", "agent_guard"):
            self.assertNotIn(removed, agents)

    def test_3_cli_and_doctor_are_green(self):
        version = json.loads((self.child / ".agents" / "version.json").read_text(encoding="utf-8"))
        self.assertIn(version["template_version"], self.speckit("--version").stdout)
        usage = self.speckit("help", ok=False)
        self.assertNotEqual(usage.returncode, 0)
        self.assertNotIn("sync", usage.stdout)
        self.assertNotIn("init", usage.stdout)
        self.assertNotEqual(self.speckit("sync", ok=False).returncode, 0)
        report = json.loads(self.speckit("doctor", "--json").stdout)
        self.assertTrue(report["ok"], report)
        self.assertEqual(next(check for check in report["checks"] if check["id"] == "git_context")["status"],
                         "warn")
        self.speckit("validate", "--all")

    def test_4_full_sdd_cycle_through_the_launcher(self):
        created = re.search(r"specs/((\d{3,})-login)", self.speckit("new", "login", "--size", "M").stdout)
        self.assertIsNotNone(created)
        name, number = created.groups()
        self.assertEqual((name, number), ("001-login", "001"))
        spec_dir = self.child / "specs" / name
        brief_path = spec_dir / "brief.md"
        brief = brief_path.read_text(encoding="utf-8")
        self.assertIn("Modo: pendiente (elegir `guided` o `proposal`)", brief)
        brief = brief.replace("Modo: pendiente (elegir `guided` o `proposal`)", "Modo: guided")
        brief = brief.replace("Estado: draft", "Estado: confirmed")
        brief = brief.replace("Confirmado por: pendiente", "Confirmado por: course-user")
        brief = brief.replace("Confirmado el: pendiente", "Confirmado el: 2026-10-12")
        brief_path.write_text(brief, encoding="utf-8")
        self.assertIn("Estado: confirmed", brief_path.read_text(encoding="utf-8"))
        (spec_dir / "spec.md").write_text(SPEC, encoding="utf-8")
        (spec_dir / "implementation-plan.md").write_text(PLAN, encoding="utf-8")
        self.speckit("design", "ready", number)
        self.speckit("approve", number, "--by", "owner")
        (spec_dir / "tasks.md").write_text("- [ ] TASK-001: implementar (AC-001)\n", encoding="utf-8")
        (spec_dir / "test-plan.md").write_text("| TC-001 | AC-001 | escenario | unit | test -f src/app.py |\n",
                                               encoding="utf-8")
        self.speckit("validate", f"specs/{name}/")
        self.speckit("ready", number)
        self.speckit("task", "start", number, "TASK-001")

        # GATE 3 rejects a task whose project check fails, and records the attempt.
        self.assertNotEqual(self.speckit("task", "done", number, "TASK-001", ok=False).returncode, 0)
        evidence = (spec_dir / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("## TASK-001 — FAIL", evidence)
        self.assertIn("- [/] TASK-001", (spec_dir / "tasks.md").read_text(encoding="utf-8"))  # stays in progress

        (self.child / "src").mkdir(exist_ok=True)
        (self.child / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.speckit("task", "done", number, "TASK-001")
        self.assertIn("## TASK-001 — PASS", (spec_dir / "evidence.md").read_text(encoding="utf-8"))
        self.assertIn("- [x] TASK-001", (spec_dir / "tasks.md").read_text(encoding="utf-8"))

        self.speckit("close", number)
        self.assertEqual(json.loads((spec_dir / "state.json").read_text())["status"], "completed")
        self.assertRegex((spec_dir / "evidence.md").read_text(encoding="utf-8"),
                         r"- CI fingerprint: [a-f0-9]{64}")
        self.speckit("handoff", number)
        self.assertTrue((self.child / ".agents" / "SESSION_STATE.md").is_file())
        (spec_dir / "retro.md").write_text(RETRO, encoding="utf-8")
        self.speckit("archive", number)
        self.assertTrue((self.child / "specs" / ".archive" / name / "evidence.md").is_file())

        metrics = json.loads(self.speckit("report", "--json").stdout)
        self.assertEqual(metrics["totals"]["specs"], 1)
        self.assertEqual([row["spec"] for row in metrics["specs"]], [name])
        self.speckit("validate", "--all")
        self.assertTrue(json.loads(self.speckit("doctor", "--json").stdout)["ok"])

    def test_5_size_s_cycle_uses_embedded_tests_through_the_launcher(self):
        created = re.search(r"specs/((\d{3,})-small)", self.speckit("new", "small", "--size", "S").stdout)
        self.assertIsNotNone(created)
        name, number = created.groups()
        self.assertEqual((name, number), ("002-small", "002"))
        spec_dir = self.child / "specs" / name
        self.assertFalse((spec_dir / "implementation-plan.md").exists())
        self.assertFalse((spec_dir / "test-plan.md").exists())
        (spec_dir / "spec.md").write_text(SPEC_S, encoding="utf-8")
        self.speckit("design", "ready", number)
        self.speckit("approve", number, "--by", "owner")
        (spec_dir / "tasks.md").write_text("- [ ] TASK-001: implementar flujo corto (AC-001)\n",
                                                encoding="utf-8")
        self.speckit("validate", f"specs/{name}/")
        self.speckit("ready", number)
        self.speckit("task", "start", number, "TASK-001")
        (self.child / "src" / "small.py").write_text("VALUE = 2\n", encoding="utf-8")
        self.speckit("task", "done", number, "TASK-001")
        evidence = (spec_dir / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("## TASK-001 — PASS", evidence)
        self.assertIn("### TC-001 — PASS", evidence)
        self.speckit("close", number)
        (spec_dir / "retro.md").write_text(RETRO, encoding="utf-8")
        self.speckit("archive", number)
        self.speckit("validate", "--all")

    @unittest.skipUnless(shutil.which("codex"), "codex CLI not installed")
    def test_6_codex_sandbox_can_run_shell_in_the_child(self):
        # Regression: a generated .codex/config.toml (":minimal" profile) hid Codex's own binary from
        # bwrap, so every command failed with "bwrap: execvp .../codex: No such file or directory".
        # ":workspace" is the built-in profile Codex applies to a project without its own config.
        result = subprocess.run(["codex", "sandbox", "-P", ":workspace", "-C", str(self.child), "--",
                                 "sh", "-c", "test -f AGENTS.md && echo SANDBOX_SHELL_OK"],
                                cwd=self.child, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        self.assertNotIn("execvp", output)
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("SANDBOX_SHELL_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
