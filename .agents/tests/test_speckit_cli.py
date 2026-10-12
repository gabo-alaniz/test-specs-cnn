"""Tests for .agents/bin/speckit_cli.py (stdlib only: python3 -m unittest discover -s .agents/tests)."""

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agents" / "bin"))
spec = importlib.util.spec_from_file_location("speckit_cli", ROOT / ".agents" / "bin" / "speckit_cli.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class CliFlowTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        shutil.copytree(ROOT / ".agents" / "templates", self.root / ".agents" / "templates")
        self.set_test_command("true")
        self._root = cli.ROOT
        cli.ROOT = self.root

    def tearDown(self):
        cli.ROOT = self._root
        self._tmp.cleanup()

    def set_test_command(self, command: str) -> None:
        self.set_commands(test=command)

    def set_commands(self, **overrides: str) -> None:
        path = self.root / ".agents" / "project.json"
        commands = {"test": "true", "lint": "", "build": "", "e2e": ""}
        commands.update(overrides)
        path.write_text(json.dumps({"commands": commands}), encoding="utf-8")

    def run_cli(self, *argv: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return cli.main(list(argv))

    def state(self) -> dict:
        return json.loads((self.spec_dir / "state.json").read_text(encoding="utf-8"))

    def write(self, name: str, content: str) -> None:
        (self.spec_dir / name).write_text(content, encoding="utf-8")

    def ready_spec(self) -> None:
        """new → design → approve → tasks + test plan → ready."""
        self.assertEqual(self.run_cli("new", "login"), 0)
        self.spec_dir = self.root / "specs" / "001-login"
        self.assertEqual(self.state()["spec_name"], "001-login")
        self.write("spec.md", """# Spec
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
""")
        self.write("implementation-plan.md", """# Plan
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
""")
        self.assertEqual(self.run_cli("design", "ready", "001"), 0)
        self.assertEqual(self.run_cli("approve", "001", "--by", "owner"), 0)
        self.assertEqual(self.state()["approval"]["by"], "owner")
        self.write("tasks.md", "- [ ] TASK-001: implementar (AC-001)\n")
        self.write("test-plan.md", "| TC-001 | AC-001 | escenario | unit | true |\n")
        self.assertEqual(self.run_cli("ready", "001"), 0)
        self.assertEqual((self.state()["status"], self.state()["phase"]), ("ready", "ready"))

    def test_new_numbers_specs_and_trims_size_m_spec(self):
        self.assertEqual(self.run_cli("new", "uno", "--size", "S"), 0)
        self.assertEqual(self.run_cli("new", "dos"), 0)
        small, medium = self.root / "specs" / "001-uno", self.root / "specs" / "002-dos"
        self.assertFalse((small / "implementation-plan.md").exists())
        self.assertIn("Notas técnicas", (small / "spec.md").read_text(encoding="utf-8"))
        self.assertNotIn("Notas técnicas", (medium / "spec.md").read_text(encoding="utf-8"))
        self.assertTrue((medium / "test-plan.md").exists())
        medium_state = json.loads((medium / "state.json").read_text())
        self.assertEqual(medium_state["schema_version"], cli.sv.SCHEMA_VERSION)
        self.assertIsNotNone(medium_state["created_at"])
        self.assertEqual(medium_state["events"][0]["event"], "created")
        self.assertNotEqual(self.run_cli("new", "Bad_Slug"), 0)

    def test_design_ready_rejects_untouched_template(self):
        self.assertEqual(self.run_cli("new", "raw"), 0)
        self.spec_dir = self.root / "specs" / "001-raw"
        self.assertNotEqual(self.run_cli("design", "ready", "001"), 0)
        self.assertEqual(self.state()["status"], "planning")

    def test_migrate_v1_state_is_idempotent(self):
        self.assertEqual(self.run_cli("new", "legacy"), 0)
        self.spec_dir = self.root / "specs" / "001-legacy"
        state = self.state()
        del state["schema_version"]
        cli.save_state(self.spec_dir, state)
        self.assertNotEqual(self.run_cli("migrate", "--check"), 0)
        self.assertEqual(self.run_cli("migrate"), 0)
        self.assertEqual(self.state()["schema_version"], cli.sv.SCHEMA_VERSION)
        self.assertIsNone(self.state()["created_at"])
        self.assertEqual(self.state()["events"], [])
        self.assertEqual(self.run_cli("migrate"), 0)

    def test_ready_is_separate_from_task_start_and_records_events(self):
        self.ready_spec()
        state = self.state()
        self.assertIsNone(state["current_task"])
        self.assertEqual(state["events"][-1]["event"], "ready")
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        state = self.state()
        self.assertEqual(state["current_task"], "TASK-001")
        self.assertEqual(state["events"][-1]["event"], "task_started")

    def test_approval_records_design_hashes(self):
        self.ready_spec()
        approval = self.state()["approval"]
        self.assertEqual(set(approval["design_hashes"]), {"spec_md", "implementation_plan_md"})
        self.write("spec.md", (self.spec_dir / "spec.md").read_text() + "\nCambio posterior.\n")
        errors, _ = cli.validate(self.spec_dir)
        self.assertTrue(any("approved design changed" in error for error in errors), errors)

    def test_design_revise_clears_approval_audits_reason_and_allows_reapproval(self):
        self.ready_spec()
        before = self.state()["approval"]["design_hashes"]
        tasks = (self.spec_dir / "tasks.md").read_text(encoding="utf-8")
        tests = (self.spec_dir / "test-plan.md").read_text(encoding="utf-8")

        self.assertEqual(self.run_cli(
            "design", "revise", "001", "--by", "architect", "--reason", "changed contract"
        ), 0)
        state = self.state()
        self.assertEqual((state["status"], state["phase"]), ("planning", "plan"))
        self.assertIsNone(state["approval"])
        self.assertFalse(state["artifacts"]["tasks_md"])
        self.assertFalse(state["artifacts"]["test_plan_md"])
        self.assertEqual(state["events"][-1]["event"], "design_revised")
        self.assertEqual(state["events"][-1]["actor"], "architect")
        self.assertEqual(state["events"][-1]["reason"], "changed contract")
        self.assertEqual((self.spec_dir / "tasks.md").read_text(encoding="utf-8"), tasks)
        self.assertEqual((self.spec_dir / "test-plan.md").read_text(encoding="utf-8"), tests)

        self.write("spec.md", (self.spec_dir / "spec.md").read_text() + "\nContrato revisado.\n")
        self.assertEqual(self.run_cli("design", "ready", "001"), 0)
        self.assertEqual(self.run_cli("approve", "001", "--by", "owner-2"), 0)
        self.assertNotEqual(self.state()["approval"]["design_hashes"], before)
        self.assertEqual(self.run_cli("ready", "001"), 0)

    def test_design_revise_rejects_empty_audit_fields_and_started_implementation(self):
        self.ready_spec()
        self.assertNotEqual(self.run_cli(
            "design", "revise", "001", "--by", "", "--reason", "missing actor"
        ), 0)
        self.assertIsNotNone(self.state()["approval"])
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertNotEqual(self.run_cli(
            "design", "revise", "001", "--by", "architect", "--reason", "too late"
        ), 0)
        self.assertEqual(self.state()["current_task"], "TASK-001")

    def test_full_flow_records_evidence_and_closes(self):
        self.ready_spec()
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertEqual(self.state()["current_task"], "TASK-001")
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 0)
        evidence = (self.spec_dir / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("## TASK-001 — PASS", evidence)
        self.assertIn("- Tested content:", evidence)
        self.assertIn("### TC-001 — PASS", evidence)
        self.assertRegex(evidence, r"- Command: `true`\n- Exit: 0 \([0-9.]+s\)")
        self.assertIn("- [x] TASK-001", (self.spec_dir / "tasks.md").read_text(encoding="utf-8"))
        self.assertEqual(self.state()["phase"], "validation")
        self.assertEqual(self.run_cli("close", "001"), 0)
        self.assertEqual(self.state()["status"], "completed")
        closes = (self.spec_dir / "evidence.md").read_text(encoding="utf-8").count("## CLOSE — PASS")
        self.assertEqual(self.run_cli("close", "001"), 0)
        self.assertEqual((self.spec_dir / "evidence.md").read_text(encoding="utf-8").count("## CLOSE — PASS"),
                         closes + 1)
        self.assertIn("001-login", (self.spec_dir / "retro.md").read_text(encoding="utf-8"))
        self.assertEqual(self.run_cli("status", "001"), 0)
        self.assertEqual(self.run_cli("handoff", "001"), 0)
        self.assertTrue((self.root / ".agents" / "SESSION_STATE.md").is_file())

    def test_review_can_start_a_new_task_from_validation(self):
        self.ready_spec()
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 0)
        self.assertEqual(self.state()["phase"], "validation")
        self.write(
            "tasks.md",
            (self.spec_dir / "tasks.md").read_text(encoding="utf-8")
            + "- [ ] TASK-002: corregir hallazgo de revisión (AC-001)\n",
        )

        self.assertEqual(self.run_cli("task", "start", "001", "TASK-002"), 0)
        state = self.state()
        self.assertEqual((state["status"], state["phase"]), ("in_progress", "implementation"))
        self.assertEqual(state["current_task"], "TASK-002")
        self.assertIn("- [/] TASK-002", (self.spec_dir / "tasks.md").read_text(encoding="utf-8"))

    def test_review_can_reopen_a_closed_spec_and_requires_a_new_close(self):
        self.ready_spec()
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 0)
        self.assertEqual(self.run_cli("close", "001"), 0)
        self.write("retro.md", (self.spec_dir / "retro.md").read_text(encoding="utf-8") + "\nContenido humano.\n")
        self.write(
            "tasks.md",
            (self.spec_dir / "tasks.md").read_text(encoding="utf-8")
            + "- [ ] TASK-002: corregir hallazgo posterior al cierre (AC-001)\n",
        )

        self.assertEqual(self.run_cli("task", "start", "001", "TASK-002"), 0)
        state = self.state()
        self.assertEqual((state["status"], state["phase"]), ("in_progress", "implementation"))
        self.assertEqual(state["current_task"], "TASK-002")
        self.assertIn("- [/] TASK-002", (self.spec_dir / "tasks.md").read_text(encoding="utf-8"))
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-002"), 0)
        self.assertEqual(self.run_cli("close", "001"), 0)
        retro = (self.spec_dir / "retro.md").read_text(encoding="utf-8")
        self.assertIn("- Tareas: 2 · Intentos fallidos: ninguno", retro)
        self.assertIn("Contenido humano.", retro)
        self.assertEqual(sum(event["event"] == "closed" for event in self.state()["events"]), 2)

    def test_approve_rolls_back_with_open_questions(self):
        self.assertEqual(self.run_cli("new", "login"), 0)
        self.spec_dir = self.root / "specs" / "001-login"
        self.write("spec.md", """# Spec
## Problema y contexto
Problema.
## Usuarios y flujos
Usuario.
## Criterios de aceptación
- AC-001: Dado x, cuando y, entonces [NEEDS CLARIFICATION: quién].
## Alcance
Acotado.
## Restricciones y datos
Ninguna.
""")
        self.write("implementation-plan.md", """# Plan
## Módulos y componentes afectados
Módulo.
## Decisiones
Decisión.
## Datos y migraciones
Ninguna.
## Dependencias nuevas
Ninguna.
## Riesgos y mitigación
Controlados.
""")
        self.assertNotEqual(self.run_cli("design", "ready", "001"), 0)
        self.assertIsNone(self.state()["approval"])

    def test_start_requires_traceability(self):
        self.ready_spec()
        self.write("test-plan.md", "| TC-001 | — | escenario | unit | true |\n")
        self.assertNotEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertIsNone(self.state()["current_task"])
        self.assertIn("- [ ] TASK-001", (self.spec_dir / "tasks.md").read_text(encoding="utf-8"))

    def test_three_failures_block_the_spec(self):
        self.ready_spec()
        self.write("test-plan.md", "| TC-001 | AC-001 | escenario | unit | false |\n")
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        for _ in range(cli.MAX_ATTEMPTS):
            self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 1)
        state = self.state()
        self.assertEqual(state["status"], "blocked")
        self.assertIn("TASK-001", state["blocked_reason"])
        self.assertIn("- [/] TASK-001", (self.spec_dir / "tasks.md").read_text(encoding="utf-8"))
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 1)
        self.assertEqual(cli.failed_attempts(self.spec_dir, "TASK-001"), cli.MAX_ATTEMPTS)
        self.write("test-plan.md", "| TC-001 | AC-001 | escenario | unit | true |\n")
        self.assertEqual(self.run_cli("resume", "001", "--by", "owner", "--reason", "fix available"), 0)
        self.assertEqual(self.state()["status"], "in_progress")
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 0)
        evidence = (self.spec_dir / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("## RESUME", evidence)
        self.assertIn("- Authorized by: owner", evidence)
        self.assertEqual(cli.failed_attempts(self.spec_dir, "TASK-001"), cli.MAX_ATTEMPTS)

    def test_task_done_ignores_global_commands_but_close_requires_test(self):
        self.ready_spec()
        self.set_test_command("")
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 0)
        self.assertNotEqual(self.run_cli("close", "001"), 0)
        evidence = (self.spec_dir / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("## TASK-001 — PASS", evidence)
        self.assertNotIn("## CLOSE", evidence)

    def test_task_done_deduplicates_scenarios_and_close_runs_global_checks(self):
        self.ready_spec()
        scenario = "printf 'scenario\\n' >> calls.log"
        self.write("test-plan.md", f"| TC-001 | AC-001 | first | unit | {scenario} |\n"
                   f"| TC-002 | AC-001 | second | integration | {scenario} |\n")
        self.set_commands(
            test="printf 'test\\n' >> calls.log", lint="printf 'lint\\n' >> calls.log",
            build="printf 'build\\n' >> calls.log", e2e="printf 'e2e\\n' >> calls.log",
        )
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 0)
        calls = (self.root / "calls.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(calls, ["scenario"])
        evidence = (self.spec_dir / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("### TC-001 — PASS", evidence)
        self.assertIn("### TC-002 — PASS", evidence)

        self.assertEqual(self.run_cli("close", "001"), 0)
        calls = (self.root / "calls.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(calls, ["scenario", "test", "lint", "build", "e2e"])

    def test_task_scenarios_stop_after_first_failed_command(self):
        self.ready_spec()
        self.write("test-plan.md",
                   "| TC-001 | AC-001 | first | unit | printf 'first\\n' >> calls.log; false |\n"
                   "| TC-002 | AC-001 | second | unit | printf 'second\\n' >> calls.log |\n")
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 1)
        self.assertEqual((self.root / "calls.log").read_text(encoding="utf-8").splitlines(), ["first"])
        evidence = (self.spec_dir / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("### TC-001 — FAIL", evidence)
        self.assertNotIn("### TC-002", evidence)

    def test_manual_case_requires_explicit_evidence(self):
        self.ready_spec()
        self.write("test-plan.md", "| TC-001 | AC-001 | observar resultado | manual | pasos |\n")
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertNotEqual(self.run_cli("task", "done", "001", "TASK-001"), 0)
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001", "--manual-evidence", "resultado visible"), 0)
        evidence = (self.spec_dir / "evidence.md").read_text(encoding="utf-8")
        self.assertIn("### TC-001 — PASS", evidence)
        self.assertIn("- Evidence: resultado visible", evidence)

    def test_report_includes_archived_and_blocked_specs(self):
        self.test_archive_moves_only_completed_specs()
        self.spec_dir = self.root / "specs" / "003-tercero"
        state = self.state()
        state.update(status="blocked", blocked_reason="TASK-001 failed 3 times")
        cli.save_state(self.spec_dir, state)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["report", "--json"]), 0)
        report = json.loads(out.getvalue())
        rows = {r["spec"]: r for r in report["specs"]}
        self.assertTrue(rows["001-login"]["archived"])
        self.assertIsNotNone(rows["001-login"]["lead_time_hours"])
        self.assertEqual((rows["001-login"]["tasks_done"], rows["001-login"]["fails"]), (1, 0))
        self.assertTrue(rows["003-tercero"]["blocked"])
        self.assertIsNone(rows["003-tercero"]["lead_time_hours"])
        self.assertEqual((report["totals"]["specs"], report["totals"]["completed"], report["totals"]["blocked"]), (3, 1, 1))
        self.assertEqual(self.run_cli("report"), 0)

    def test_report_counts_task_failures(self):
        self.ready_spec()
        self.write("test-plan.md", "| TC-001 | AC-001 | escenario | unit | false |\n")
        self.assertEqual(self.run_cli("task", "start", "001", "TASK-001"), 0)
        self.assertEqual(self.run_cli("task", "done", "001", "TASK-001"), 1)
        self.assertEqual(cli.spec_metrics(self.spec_dir, False)["fails"], 1)

    def test_lifecycle_metrics_use_created_gates_and_historical_blocks(self):
        def event(name: str, hour: int) -> dict:
            return {"event": name, "at": f"2026-10-01T{hour:02d}:00:00Z", "task": None,
                    "actor": None, "reason": None}

        state = {
            "created_at": "2026-10-01T00:00:00Z",
            "events": [
                event("created", 0), event("design_ready", 1), event("approved", 3),
                event("ready", 4), event("blocked", 6), event("resumed", 7),
                event("blocked", 8), event("resumed", 10), event("closed", 12),
            ],
        }
        metrics = cli.lifecycle_metrics(state)
        self.assertEqual(metrics["lead_time_hours"], 12.0)
        self.assertEqual(metrics["gate_hours"], {
            "design": 1.0, "approval_wait": 2.0, "ready": 1.0, "implementation": 8.0,
        })
        self.assertEqual((metrics["block_events"], metrics["blocked_time_hours"]), (2, 3.0))

        legacy = cli.lifecycle_metrics({"created_at": None, "events": []})
        self.assertIsNone(legacy["lead_time_hours"])
        self.assertTrue(all(value is None for value in legacy["gate_hours"].values()))
        self.assertEqual((legacy["block_events"], legacy["blocked_time_hours"]), (None, None))

    def test_archive_moves_only_completed_specs(self):
        self.test_full_flow_records_evidence_and_closes()
        self.assertEqual(self.run_cli("new", "otro"), 0)
        self.assertNotEqual(self.run_cli("archive", "002"), 0)
        self.assertTrue((self.root / "specs" / "002-otro").is_dir())
        self.assertNotEqual(self.run_cli("archive", "001"), 0)  # generated retro is still incomplete
        self.write("retro.md", """# Retro
## Qué funcionó
Todo.
## Qué costó (vueltas, reintentos, ambigüedades del brief)
Nada.
## Preferencias nuevas
Ninguna.
## Reglas o plantillas a ajustar
Ninguna.
""")
        self.assertEqual(self.run_cli("archive", "001"), 0)
        self.assertTrue((self.root / "specs" / ".archive" / "001-login" / "evidence.md").is_file())
        self.assertFalse(self.spec_dir.exists())
        self.assertEqual(self.run_cli("new", "tercero"), 0)  # numbering counts archived specs
        self.assertTrue((self.root / "specs" / "003-tercero").is_dir())

    def test_new_from_issue_form(self):
        issue = self.root / "issue.md"
        issue.write_text("### Slug\n\nlogin-email\n\n### Tamaño\n\nS\n\n### Problema\n\nNo hay login.\n\n"
                         "### Usuario\n\n_No response_\n", encoding="utf-8")
        self.assertEqual(self.run_cli("new", "--from-issue", str(issue)), 0)
        self.spec_dir = self.root / "specs" / "001-login-email"
        brief = (self.spec_dir / "brief.md").read_text(encoding="utf-8")
        self.assertIn("# Brief: login-email", brief)
        self.assertIn("## 3. Problema\nNo hay login.\n", brief)
        self.assertIn("¿Quién lo usa?", brief)  # unanswered fields keep the template prompt
        self.assertEqual(self.state()["size"], "S")

    def test_new_accepts_a_reserved_unique_number(self):
        self.assertEqual(self.run_cli("new", "first", "--number", "7", "--size", "S"), 0)
        self.assertTrue((self.root / "specs" / "007-first").is_dir())
        self.assertNotEqual(self.run_cli("new", "duplicate", "--number", "7"), 0)
        self.assertNotEqual(self.run_cli("new", "invalid", "--number", "0"), 0)

    def test_worktree_creates_branch_per_spec(self):
        git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a],  # noqa: E731
                                        cwd=self.root, check=True, capture_output=True)
        self.assertEqual(self.run_cli("new", "login"), 0)
        git("init", "-q")
        git("add", ".")
        git("commit", "-qm", "init")
        self.assertEqual(self.run_cli("worktree", "001"), 0)
        path = self.root.parent / f"{self.root.name}-001-login"
        self.addCleanup(shutil.rmtree, path, True)
        self.assertTrue((path / "specs" / "001-login" / "state.json").is_file())
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=path, capture_output=True, text=True)
        self.assertEqual(branch.stdout.strip(), "feat/001-login")
        self.assertNotEqual(self.run_cli("worktree", "001"), 0)

    def test_ci_guard_links_branch_diff_spec_and_close_fingerprint(self):
        git = lambda *args: subprocess.run(  # noqa: E731
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=self.root,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        git("init", "-q", "-b", "main")
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "base")
        base = git("rev-parse", "HEAD")
        git("switch", "-qc", "feat/001-login")

        spec_dir = self.root / "specs" / "001-login"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("approved design\n", encoding="utf-8")
        (self.root / "src.txt").write_text("implemented\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "feature")
        fingerprint = cli.change_fingerprint("001-login", base)
        (spec_dir / "state.json").write_text("{}\n", encoding="utf-8")
        (spec_dir / "tasks.md").write_text("- [x] bookkeeping\n", encoding="utf-8")
        (spec_dir / "evidence.md").write_text(
            f"## CLOSE — PASS — 2026-10-01T00:00:00Z\n- CI fingerprint: {fingerprint}\n",
            encoding="utf-8",
        )
        git("add", ".")
        git("commit", "-qm", "close bookkeeping")

        result = cli.ci_guard("feat/001-login", base)
        self.assertEqual((result["spec"], result["fingerprint"]), ("001-login", fingerprint))
        with self.assertRaisesRegex(cli.CliError, "feat/<NNN-slug>"):
            cli.ci_guard("feature/001-login", base)

        (self.root / "src.txt").write_text("changed after close\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "untested change")
        with self.assertRaisesRegex(cli.CliError, "fingerprint mismatch"):
            cli.ci_guard("feat/001-login", base)

        other = self.root / "specs" / "002-other"
        other.mkdir()
        (other / "spec.md").write_text("unrelated\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-qm", "unrelated spec")
        with self.assertRaisesRegex(cli.CliError, "unrelated spec 002-other"):
            cli.ci_guard("feat/001-login", base)

    def test_change_fingerprint_matches_dirty_and_committed_git_modes(self):
        git = lambda *args: subprocess.run(  # noqa: E731
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=self.root,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        git("init", "-q", "-b", "main")
        git("add", ".")
        git("commit", "-qm", "base")
        base = git("rev-parse", "HEAD")
        git("switch", "-qc", "feat/001-login")

        (self.root / "regular.txt").write_text("regular\n", encoding="utf-8")
        executable = self.root / "run.sh"
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
        (self.root / "regular.link").symlink_to("regular.txt")

        dirty = cli.change_fingerprint("001-login", base, include_worktree=True)
        git("add", ".")
        git("commit", "-qm", "feature")
        committed = cli.change_fingerprint("001-login", base)
        self.assertEqual(dirty, committed)

    def test_transaction_restores_existing_and_new_files_after_change_exception(self):
        spec_dir = self.root / "transaction"
        spec_dir.mkdir()
        existing, created = spec_dir / "existing.txt", spec_dir / "created.txt"
        existing.write_text("before", encoding="utf-8")

        def failing_change():
            cli.atomic_write_text(existing, "after")
            cli.atomic_write_text(created, "temporary")
            raise RuntimeError("mutation exploded")

        with self.assertRaisesRegex(RuntimeError, "mutation exploded"):
            cli.transaction(spec_dir, ["existing.txt", "created.txt"], failing_change)
        self.assertEqual(existing.read_text(encoding="utf-8"), "before")
        self.assertFalse(created.exists())

    def test_atomic_write_keeps_original_when_replace_fails(self):
        path = self.root / "atomic.txt"
        path.write_text("before", encoding="utf-8")
        with mock.patch.object(cli.os, "replace", side_effect=OSError("replace failed")):
            with self.assertRaisesRegex(OSError, "replace failed"):
                cli.atomic_write_text(path, "after")
        self.assertEqual(path.read_text(encoding="utf-8"), "before")
        self.assertEqual(list(self.root.glob(".atomic.txt.*")), [])


class TemplateLifecycleTestCase(unittest.TestCase):
    @staticmethod
    def write_template_manifest(root: Path, version: str, paths: list[str],
                                project_owned: tuple[str, ...] = ()) -> None:
        files = []
        for rel_path in sorted(paths):
            owner = cli.PROJECT_OWNER if rel_path in project_owned else cli.TEMPLATE_OWNER
            files.append({"path": rel_path, "owner": owner, "sha256": cli.file_sha256(root / rel_path)})
        path = root / ".agents" / "template-manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"format_version": 2, "template_version": version,
                                    "owner": cli.TEMPLATE_OWNER, "files": files},
                                   indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def copy_manifest_installation(target: Path) -> None:
        manifest = cli.load_template_manifest(ROOT)
        for entry in manifest["files"]:
            source = ROOT / entry["path"]
            destination = target / entry["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        destination = target / cli.TEMPLATE_MANIFEST
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / cli.TEMPLATE_MANIFEST, destination)
        (target / "specs" / ".archive").mkdir(parents=True)
        python = target / ".venv" / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.write_text("", encoding="utf-8")

    def test_update_previews_conflicts_backs_up_and_restores(self):
        with tempfile.TemporaryDirectory() as target_tmp, tempfile.TemporaryDirectory() as source_tmp:
            target, source = Path(target_tmp), Path(source_tmp)
            paths = [".agents/bin/core.py", "AGENTS.md"]
            for root, core, agents in ((target, "old-core", "base-rules"),
                                       (source, "new-core", "new-rules")):
                (root / ".agents" / "bin").mkdir(parents=True)
                (root / ".agents" / "bin" / "core.py").write_text(core, encoding="utf-8")
                (root / "AGENTS.md").write_text(agents, encoding="utf-8")
            self.write_template_manifest(target, "0.1.0", paths)
            (source / ".agents" / "version.json").write_text("new-file", encoding="utf-8")
            self.write_template_manifest(source, "0.2.0", paths + [".agents/version.json"])
            (target / "AGENTS.md").write_text("child-rules", encoding="utf-8")
            (target / "local.txt").write_text("keep", encoding="utf-8")

            before = (target / ".agents" / "bin" / "core.py").read_text()
            preview = cli.update_preview(source, target)
            self.assertEqual({item["path"]: item["status"] for item in preview["actions"]}, {
                ".agents/bin/core.py": "update", ".agents/version.json": "add", "AGENTS.md": "conflict"})
            self.assertEqual((target / ".agents" / "bin" / "core.py").read_text(), before)
            with self.assertRaises(cli.CliError):
                cli.apply_update(source, target)

            _, backup = cli.apply_update(source, target, confirm_conflicts=True)
            self.assertIsNotNone(backup)
            self.assertEqual((target / ".agents" / "bin" / "core.py").read_text(), "new-core")
            self.assertEqual((target / "AGENTS.md").read_text(), "new-rules")
            self.assertEqual((target / "local.txt").read_text(), "keep")
            self.assertTrue((backup / "backup.json").is_file())

            cli.restore_update(backup, target)
            self.assertEqual((target / ".agents" / "bin" / "core.py").read_text(), "old-core")
            self.assertEqual((target / "AGENTS.md").read_text(), "child-rules")
            self.assertFalse((target / ".agents" / "version.json").exists())
            self.assertEqual(cli.load_template_manifest(target)["template_version"], "0.1.0")

    def test_update_rolls_back_all_paths_and_propagates_original_exception(self):
        with tempfile.TemporaryDirectory() as target_tmp, tempfile.TemporaryDirectory() as source_tmp:
            target, source = Path(target_tmp), Path(source_tmp)
            (target / "a.txt").write_text("old-a", encoding="utf-8")
            (source / "a.txt").write_text("new-a", encoding="utf-8")
            (source / "b.txt").write_text("new-b", encoding="utf-8")
            self.write_template_manifest(target, "0.1.0", ["a.txt"])
            self.write_template_manifest(source, "0.2.0", ["a.txt", "b.txt"])

            original_copy = cli.atomic_copy_file

            def fail_on_new_file(copy_source: Path, destination: Path) -> None:
                if destination == target / "b.txt":
                    raise RuntimeError("copy exploded")
                original_copy(copy_source, destination)

            with mock.patch.object(cli, "atomic_copy_file", side_effect=fail_on_new_file):
                with self.assertRaisesRegex(RuntimeError, "copy exploded"):
                    cli.apply_update(source, target)

            self.assertEqual((target / "a.txt").read_text(encoding="utf-8"), "old-a")
            self.assertFalse((target / "b.txt").exists())
            self.assertEqual(cli.load_template_manifest(target)["template_version"], "0.1.0")

    def test_update_never_modifies_project_owned_paths(self):
        with tempfile.TemporaryDirectory() as target_tmp, tempfile.TemporaryDirectory() as source_tmp:
            target, source = Path(target_tmp), Path(source_tmp)
            for root, core, project in ((target, "old-core", "child-config"),
                                        (source, "new-core", "template-default")):
                (root / "core.txt").write_text(core, encoding="utf-8")
                (root / "project.txt").write_text(project, encoding="utf-8")
            paths = ["core.txt", "project.txt"]
            self.write_template_manifest(target, "0.1.0", paths, project_owned=("project.txt",))
            self.write_template_manifest(source, "0.2.0", paths, project_owned=("project.txt",))

            plan = cli.update_preview(source, target)
            self.assertEqual([action["path"] for action in plan["actions"]], ["core.txt"])
            cli.apply_update(source, target)
            self.assertEqual((target / "core.txt").read_text(encoding="utf-8"), "new-core")
            self.assertEqual((target / "project.txt").read_text(encoding="utf-8"), "child-config")

    def test_update_removes_retired_template_content_and_preserves_memory(self):
        with tempfile.TemporaryDirectory() as target_tmp, tempfile.TemporaryDirectory() as source_tmp:
            target, source = Path(target_tmp), Path(source_tmp)
            retired = ".agents/examples/node-cypress/README.md"
            for root, core in ((target, "old-core"), (source, "new-core")):
                (root / "core.txt").write_text(core, encoding="utf-8")
            retired_path = target / retired
            retired_path.parent.mkdir(parents=True)
            retired_path.write_text("legacy example", encoding="utf-8")
            memory = target / ".agents" / "memory" / "preferences.md"
            memory.parent.mkdir(parents=True)
            memory.write_text("project preference", encoding="utf-8")
            self.write_template_manifest(target, "0.1.0", ["core.txt", retired])
            self.write_template_manifest(source, "0.2.0", ["core.txt"])

            plan = cli.update_preview(source, target)
            self.assertEqual({item["path"]: item["status"] for item in plan["actions"]}, {
                retired: "remove", "core.txt": "update",
            })
            cli.apply_update(source, target)
            self.assertFalse(retired_path.exists())
            self.assertEqual(memory.read_text(encoding="utf-8"), "project preference")

    def test_update_manifest_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".agents").mkdir()
            (root / ".agents" / "template-manifest.json").write_text(json.dumps({
                "format_version": 1, "template_version": "1.0.0",
                "files": [{"path": "../outside", "owner": "template", "sha256": "0" * 64}],
            }), encoding="utf-8")
            with self.assertRaises(cli.CliError):
                cli.load_template_manifest(root)

    def test_update_rejects_symlink_escapes(self):
        with tempfile.TemporaryDirectory() as target_tmp, tempfile.TemporaryDirectory() as source_tmp, \
                tempfile.TemporaryDirectory() as outside_tmp:
            target, source, outside = Path(target_tmp), Path(source_tmp), Path(outside_tmp)
            (outside / "core.py").write_text("old", encoding="utf-8")
            (target / "managed").symlink_to(outside, target_is_directory=True)
            (source / "managed").mkdir()
            (source / "managed" / "core.py").write_text("new", encoding="utf-8")
            self.write_template_manifest(source, "0.2.0", ["managed/core.py"])
            (target / ".agents").mkdir()
            (target / ".agents" / "template-manifest.json").write_text(json.dumps({
                "format_version": 1, "template_version": "0.1.0", "files": [{
                    "path": "managed/core.py", "owner": "template",
                    "sha256": cli.file_sha256(outside / "core.py"),
                }],
            }), encoding="utf-8")
            with self.assertRaises(cli.CliError):
                cli.update_preview(source, target)
            self.assertEqual((outside / "core.py").read_text(), "old")

    def test_template_manifest_hashes_match_the_seed(self):
        manifest = cli.load_template_manifest(ROOT)
        self.assertEqual(manifest["owner"], cli.TEMPLATE_OWNER)
        self.assertEqual({entry["path"]: entry["owner"] for entry in manifest["files"]},
                         cli.expected_manifest_owners(ROOT))
        self.assertEqual(manifest["template_version"], cli.sv.TEMPLATE_VERSION)
        for entry in manifest["files"]:
            self.assertEqual(cli.file_sha256(ROOT / entry["path"]), entry["sha256"], entry["path"])

    def test_version_is_reported_from_canonical_metadata(self):
        result = subprocess.run([str(ROOT / "speckit"), "--version"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(),
                         f"speckit {cli.sv.TEMPLATE_VERSION} (schema {cli.sv.SCHEMA_VERSION})")

    def test_doctor_reports_actionable_human_and_json_results(self):
        result = subprocess.run([str(ROOT / "speckit"), "doctor", "--json"], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual({check["id"] for check in report["checks"]},
                         {"required_files", "venv", "commands", "version_schema", "manifest", "specs",
                          "git_context"})
        self.assertTrue(all(check["status"] in ("pass", "warn") for check in report["checks"]))

        human = subprocess.run([str(ROOT / "speckit"), "doctor"], cwd=ROOT,
                               capture_output=True, text=True)
        self.assertEqual(human.returncode, 0)
        self.assertIn("✓ venv:", human.stdout)

    def test_doctor_detects_missing_files_broken_commands_and_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / ".agents", root / ".agents", ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copy2(ROOT / "AGENTS.md", root / "AGENTS.md")
            shutil.copy2(ROOT / "speckit", root / "speckit")
            (root / "specs").mkdir()
            venv_python = root / ".venv" / "bin" / "python"
            venv_python.parent.mkdir(parents=True)
            venv_python.write_text("", encoding="utf-8")

            project = json.loads((root / ".agents" / "project.json").read_text())
            project["commands"]["test"] = ""
            (root / ".agents" / "project.json").write_text(json.dumps(project), encoding="utf-8")
            schema = json.loads((root / ".agents" / "schemas" / "spec-state.schema.json").read_text())
            schema["properties"]["schema_version"]["enum"] = [999]
            (root / ".agents" / "schemas" / "spec-state.schema.json").write_text(json.dumps(schema), encoding="utf-8")

            report = cli.doctor_report(root)
            failed = {check["id"] for check in report["checks"] if check["status"] == "fail"}
            self.assertTrue({"required_files", "commands", "version_schema", "manifest"} <= failed)
            self.assertTrue(all("remediation" in check for check in report["checks"] if check["status"] == "fail"))

    def test_doctor_detects_manifest_coverage_missing_core_and_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.copy_manifest_installation(root)
            baseline = cli.doctor_report(root)
            self.assertTrue(baseline["ok"], baseline)
            self.assertEqual(next(check for check in baseline["checks"] if check["id"] == "git_context")["status"],
                             "warn")

            unlisted = root / ".agents" / "templates" / "unlisted.md"
            unlisted.write_text("new core", encoding="utf-8")
            coverage = cli.doctor_report(root)
            self.assertIn("uncovered ownership", next(check for check in coverage["checks"]
                                                       if check["id"] == "manifest")["summary"])
            unlisted.unlink()

            core = root / ".agents" / "bin" / "spec_validate.py"
            original = core.read_bytes()
            core.unlink()
            missing = cli.doctor_report(root)
            self.assertIn("missing template-owned", next(check for check in missing["checks"]
                                                          if check["id"] == "manifest")["summary"])
            core.write_bytes(original)

            core.write_bytes(original + b"\n# drift\n")
            drift = cli.doctor_report(root)
            self.assertIn("template drift", next(check for check in drift["checks"]
                                                  if check["id"] == "manifest")["summary"])

            core.write_bytes(original)
            retired = root / ".agents" / "examples" / "node-cypress" / "README.md"
            retired.parent.mkdir(parents=True)
            retired.write_text("legacy", encoding="utf-8")
            maintainer = cli.doctor_report(root)
            self.assertIn("maintainer-only content", next(check for check in maintainer["checks"]
                                                           if check["id"] == "manifest")["summary"])

    def test_reference_spec_is_valid(self):
        schema = cli.sv.load_json(cli.sv.SCHEMA_PATH)
        errors, _ = cli.sv.validate_state_file(ROOT / ".agents" / "examples" / "001-archive-specs" / "state.json", schema)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
