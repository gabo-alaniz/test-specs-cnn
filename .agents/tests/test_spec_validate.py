"""Tests for .agents/bin/spec_validate.py (stdlib only: python3 -m unittest discover -s .agents/tests)."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("spec_validate", ROOT / ".agents" / "bin" / "spec_validate.py")
sv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sv)

SCHEMA = sv.load_json(sv.SCHEMA_PATH)
APPROVED = {"by": "owner", "at": "2026-10-01T10:00:00Z"}
ALL_TRUE = {"spec_md": True, "implementation_plan_md": True, "tasks_md": True, "test_plan_md": True}
TEMPLATES = ROOT / ".agents" / "templates"


def make_state(**overrides) -> dict:
    state = {
        "schema_version": sv.SCHEMA_VERSION,
        "created_at": "2026-10-01T09:00:00Z",
        "events": [],
        "spec_name": "001-demo",
        "size": "M",
        "status": "in_progress",
        "phase": "implementation",
        "current_task": "TASK-001",
        "blocked_reason": None,
        "approval": dict(APPROVED),
        "artifacts": dict(ALL_TRUE),
    }
    state.update(overrides)
    return state


class SpecDirTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.spec_dir = Path(self._tmp.name) / "001-demo"
        self.spec_dir.mkdir()
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
## Pruebas
| ID | AC | Escenario | Tipo | Comando o pasos |
|----|----|-----------|------|-----------------|
| TC-001 | AC-001 | escenario observable | unit | true |
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
        self.write("tasks.md", "- [x] TASK-001: first (AC-001)\n- [ ] TASK-002: second (AC-001)\n")
        self.write("test-plan.md", "| TC-001 | AC-001 | scenario | unit | true |\n")
        self.write("evidence.md", "## TASK-001 — PASS — 2026-10-01T12:00:00Z\n")

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name: str, content: str) -> None:
        (self.spec_dir / name).write_text(content, encoding="utf-8")

    def check(self, state: dict) -> tuple[list[str], list[str]]:
        if state.get("approval") and not state["approval"].get("design_hashes"):
            try:
                state["approval"]["design_hashes"] = sv.design_hashes(state, self.spec_dir)
            except OSError:
                keys = [key for key in sv.DESIGN_ARTIFACTS if key in sv.required_artifacts(state)]
                state["approval"]["design_hashes"] = {key: "0" * 64 for key in keys}
        path = self.spec_dir / "state.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        return sv.validate_state_file(path, SCHEMA)

    def errors(self, state: dict) -> list[str]:
        return self.check(state)[0]

    def test_valid_spec_passes(self):
        self.assertEqual(self.check(make_state()), ([], []))

    def test_empty_artifact_fails(self):
        self.write("test-plan.md", "  \n")
        self.assertTrue(any("is empty" in e for e in self.errors(make_state())))

    def test_template_placeholders_and_empty_sections_fail(self):
        self.write("spec.md", """# Spec
## Problema y contexto
## Usuarios y flujos
Usuario.
## Criterios de aceptación
- AC-001: Dado <contexto>, cuando <acción>, entonces <resultado observable>.
## Alcance
Algo.
## Restricciones y datos
Ninguna.
""")
        errors = self.errors(make_state())
        self.assertTrue(any("template placeholders" in e for e in errors), errors)
        self.assertTrue(any("empty required section" in e for e in errors), errors)

    def test_status_phase_machine_rejects_incoherent_state(self):
        errors = self.errors(make_state(status="planning", phase="validation", current_task=None))
        self.assertTrue(any("incompatible" in e for e in errors), errors)

    def test_approved_design_hash_detects_drift(self):
        state = make_state()
        state["approval"]["design_hashes"] = sv.design_hashes(state, self.spec_dir)
        self.write("implementation-plan.md", (self.spec_dir / "implementation-plan.md").read_text() + "\nCambio.\n")
        errors = self.errors(state)
        self.assertTrue(any("approved design changed" in e for e in errors), errors)

    def test_completed_with_open_tasks_fails(self):
        errors = self.errors(make_state(status="completed", phase="validation", current_task=None))
        self.assertTrue(any("tasks not done" in e for e in errors))

    def test_completed_requires_close_evidence(self):
        self.write("tasks.md", "- [x] TASK-001: first (AC-001)\n")
        self.write("evidence.md", "## TASK-001 — PASS — 2026-10-01T12:00:00Z\n")
        errors = self.errors(make_state(status="completed", phase="validation", current_task=None))
        self.assertTrue(any("CLOSE — PASS" in e for e in errors), errors)

    def test_current_task_requires_exact_id(self):
        self.assertTrue(self.errors(make_state(current_task="TASK-00")))
        errors = self.errors(make_state(current_task="TASK-009"))
        self.assertTrue(any("not found in tasks.md" in e for e in errors))

    def test_implementation_requires_test_plan(self):
        errors = self.errors(make_state(artifacts=dict(ALL_TRUE, test_plan_md=False)))
        self.assertTrue(any("test_plan_md" in e for e in errors))

    def test_tasks_phase_requires_approval(self):
        errors = self.errors(make_state(phase="tasks", current_task=None, approval=None))
        self.assertTrue(any("GATE 1" in e for e in errors))

    def test_spec_name_must_match_directory(self):
        errors = self.errors(make_state(spec_name="002-other"))
        self.assertTrue(any("must match directory" in e for e in errors))

    def test_done_task_requires_evidence(self):
        self.write("evidence.md", "## TASK-001 — FAIL — 2026-10-01T12:00:00Z\n")
        self.assertTrue(any("without PASS entry" in e for e in self.errors(make_state())))

    def test_size_s_needs_only_spec_and_tasks(self):
        for name in ("implementation-plan.md", "test-plan.md"):
            (self.spec_dir / name).unlink()
        artifacts = dict(ALL_TRUE, implementation_plan_md=False, test_plan_md=False)
        self.assertEqual(self.errors(make_state(size="S", artifacts=artifacts)), [])
        self.assertTrue(self.errors(make_state(size="M", artifacts=artifacts)))

    def test_size_l_must_be_split(self):
        self.assertTrue(any("split" in e for e in self.errors(make_state(size="L"))))

    def test_open_clarification_blocks_approval(self):
        original = (self.spec_dir / "spec.md").read_text(encoding="utf-8")
        self.write("spec.md", original + "\n[NEEDS CLARIFICATION: who?]\n")
        errors = self.errors(make_state(status="awaiting_approval", phase="plan", current_task=None, approval=None))
        self.assertTrue(any("NEEDS CLARIFICATION" in e for e in errors))

    def test_spec_without_acceptance_criteria_fails(self):
        original = (self.spec_dir / "spec.md").read_text(encoding="utf-8")
        self.write("spec.md", original.replace("- AC-001: Dado x, cuando y, entonces z.\n", "Sin criterios.\n"))
        self.assertTrue(any("acceptance criteria" in e for e in self.errors(make_state())))

    def test_untraced_acceptance_criterion_fails(self):
        original = (self.spec_dir / "spec.md").read_text(encoding="utf-8")
        self.write("spec.md", original.replace("- AC-001: Dado x, cuando y, entonces z.\n",
                                               "- AC-001: Dado x, cuando y, entonces z.\n"
                                               "- AC-002: Dado a, cuando b, entonces c.\n"))
        errors = self.errors(make_state())
        self.assertTrue(any("tasks.md does not trace AC-002" in e for e in errors))
        self.assertTrue(any("test-plan.md does not trace AC-002" in e for e in errors))

    def test_task_declarations_require_description_separator_and_known_ac(self):
        self.write("tasks.md", "- [ ] TASK-001 missing separator (AC-001)\n"
                   "- [ ] TASK-002: valid task (AC-999)\n")
        errors = self.errors(make_state(current_task="TASK-002"))
        self.assertTrue(any("line 1 must match" in error for error in errors), errors)
        self.assertTrue(any("AC-999" in error and "not in spec.md" in error for error in errors), errors)

    def test_test_plan_requires_complete_unique_canonical_rows(self):
        self.write("test-plan.md", "| ID | AC | Escenario | Tipo | Comando |\n"
                   "|----|----|-----------|------|---------|\n"
                   "| TC-001 | AC-001 | | unit | true |\n"
                   "| TC-001 | AC-999 | scenario | unknown | |\n")
        errors = self.errors(make_state())
        self.assertTrue(any("duplicated test IDs" in error for error in errors), errors)
        self.assertTrue(any("non-empty scenario" in error for error in errors), errors)
        self.assertTrue(any("unknown AC" in error for error in errors), errors)
        self.assertTrue(any("invalid type" in error for error in errors), errors)
        self.assertTrue(any("command or manual steps" in error for error in errors), errors)

    def test_size_s_requires_structured_embedded_test_table(self):
        for name in ("implementation-plan.md", "test-plan.md"):
            (self.spec_dir / name).unlink()
        artifacts = dict(ALL_TRUE, implementation_plan_md=False, test_plan_md=False)
        self.write("spec.md", (self.spec_dir / "spec.md").read_text().replace("| TC-001 |", "| BAD |"))
        errors = self.errors(make_state(size="S", artifacts=artifacts))
        self.assertTrue(any("spec.md ## Pruebas" in error for error in errors), errors)

    def test_size_s_accepts_only_the_exact_legacy_tests_heading_alias(self):
        for name in ("implementation-plan.md", "test-plan.md"):
            (self.spec_dir / name).unlink()
        artifacts = dict(ALL_TRUE, implementation_plan_md=False, test_plan_md=False)
        legacy = (self.spec_dir / "spec.md").read_text().replace(
            "## Pruebas\n", "## Pruebas (solo size S)\n"
        )
        self.write("spec.md", legacy)
        self.assertEqual(self.errors(make_state(size="S", artifacts=artifacts)), [])

        self.write("spec.md", legacy.replace("## Pruebas (solo size S)", "## Pruebas heredadas"))
        errors = self.errors(make_state(size="S", artifacts=artifacts))
        self.assertTrue(any("completed '## Pruebas'" in error for error in errors), errors)

    def test_approved_planning_validates_edited_candidates_with_false_flags(self):
        artifacts = dict(ALL_TRUE, tasks_md=False, test_plan_md=False)
        self.write("tasks.md", "- [ ] TASK-001 missing separator (AC-001)\n")
        self.write("test-plan.md", "| TC-001 | AC-001 | | unknown | |\n")
        state = make_state(status="planning", phase="tasks", current_task=None, artifacts=artifacts)
        errors = self.errors(state)
        self.assertTrue(any("tasks.md line 1 must match" in error for error in errors), errors)
        self.assertTrue(any("non-empty scenario" in error for error in errors), errors)
        self.assertTrue(any("invalid type" in error for error in errors), errors)
        self.assertTrue(any("command or manual steps" in error for error in errors), errors)

    def test_approved_planning_allows_untouched_future_artifact_scaffolds(self):
        number, name = self.spec_dir.name.split("-", 1)
        for filename in ("tasks.md", "test-plan.md"):
            content = (TEMPLATES / filename).read_text(encoding="utf-8")
            content = content.replace("<NNN>", number).replace("<nombre>", name)
            self.write(filename, content)
        artifacts = dict(ALL_TRUE, tasks_md=False, test_plan_md=False)
        state = make_state(status="planning", phase="tasks", current_task=None, artifacts=artifacts)
        self.assertEqual(self.errors(state), [])

    def test_completed_legacy_structure_is_grandfathered_until_a_ready_event_exists(self):
        self.write("tasks.md", "- [x] TASK-001: first (AC-001)\n")
        self.write("test-plan.md", "| TC-001 | AC-001 | legacy scenario | contract | true |\n")
        self.write("evidence.md", "## TASK-001 — PASS — 2026-10-01T12:00:00Z\n"
                   "## CLOSE — PASS — 2026-10-01T13:00:00Z\n")
        legacy = make_state(status="completed", phase="validation", current_task=None, events=[])
        self.assertEqual(self.errors(legacy), [])

        ready_event = {
            "event": "ready", "at": "2026-10-01T11:00:00Z", "task": None,
            "actor": None, "reason": None,
        }
        errors = self.errors(make_state(status="completed", phase="validation", current_task=None,
                                        events=[ready_event]))
        self.assertTrue(any("invalid type: contract" in error for error in errors), errors)

    def test_too_many_tasks_warns(self):
        self.write("tasks.md", "".join(f"- [ ] TASK-{i:03d}: t (AC-001)\n" for i in range(1, 10)))
        errors, warnings = self.check(make_state())
        self.assertEqual(errors, [])
        self.assertTrue(any("consider splitting" in w for w in warnings))


class SchemaFallbackTestCase(unittest.TestCase):
    def test_examples_and_template_pass_both_validators(self):
        files = sorted((ROOT / ".agents" / "examples").glob("*.json")) + [TEMPLATES / "state.json"]
        for path in files:
            state = sv.load_json(path)
            self.assertEqual(sv.mini_validate(state, SCHEMA, SCHEMA), [], path.name)
            self.assertEqual(sv.validate_semantic_rules(state), [], path.name)

    def test_fallback_reports_all_errors(self):
        state = make_state(status="done", extra=1)
        del state["approval"]
        errors = sv.mini_validate(state, SCHEMA, SCHEMA)
        self.assertEqual(len(errors), 3, errors)

    def test_validate_all_collects_active_and_archived_specs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "specs"
            (root / "001-active").mkdir(parents=True)
            (root / ".archive" / "002-old").mkdir(parents=True)
            for path in (root / "001-active" / "state.json", root / ".archive" / "002-old" / "state.json"):
                path.write_text("{}", encoding="utf-8")
            previous, sv.SPECS_DIR = sv.SPECS_DIR, root
            try:
                targets, problems = sv.collect_targets(["--all"])
            finally:
                sv.SPECS_DIR = previous
            self.assertEqual(problems, [])
            self.assertEqual({path.parent.name for path in targets}, {"001-active", "002-old"})


class VersionContractTestCase(unittest.TestCase):
    def test_version_metadata_matches_schema_and_template(self):
        metadata = sv.load_version_info()
        schema = sv.load_json(sv.SCHEMA_PATH)
        template = sv.load_json(ROOT / ".agents" / "templates" / "state.json")
        self.assertEqual(metadata["template_version"], sv.TEMPLATE_VERSION)
        self.assertEqual(metadata["schema_version"], sv.SCHEMA_VERSION)
        self.assertEqual(schema["properties"]["schema_version"]["enum"], [sv.SCHEMA_VERSION])
        self.assertEqual(template["schema_version"], sv.SCHEMA_VERSION)

    def test_size_s_template_uses_canonical_tests_heading(self):
        template = (TEMPLATES / "spec.md").read_text(encoding="utf-8")
        self.assertIn("## Pruebas\n", template)
        self.assertNotIn("## Pruebas (solo size S)", template)


if __name__ == "__main__":
    unittest.main()
