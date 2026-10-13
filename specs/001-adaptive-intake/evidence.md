# Evidence

## TASK-001 — PASS — 2026-10-13T22:25:56Z
- Commit: f06973d85a9800384d9b1bb6657331f3204ed4d3
- Tested content: eff61a8253b7e9111446c732cd0afb2f97795ecc33982d3cf0cfd17ca5ae2788 (dirty)
### TC-001 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.IntakeOrchestrationContractTestCase.test_guided_mode_is_sequential -v`
- Exit: 0 (0.044s)

```text
test_guided_mode_is_sequential (test_repo_contract.IntakeOrchestrationContractTestCase.test_guided_mode_is_sequential) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

### TC-002 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.IntakeOrchestrationContractTestCase.test_guided_mode_adapts_to_answers -v`
- Exit: 0 (0.045s)

```text
test_guided_mode_adapts_to_answers (test_repo_contract.IntakeOrchestrationContractTestCase.test_guided_mode_adapts_to_answers) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

### TC-003 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.IntakeOrchestrationContractTestCase.test_guided_mode_stops_at_twenty_when_unclear -v`
- Exit: 0 (0.044s)

```text
test_guided_mode_stops_at_twenty_when_unclear (test_repo_contract.IntakeOrchestrationContractTestCase.test_guided_mode_stops_at_twenty_when_unclear) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

### TC-004 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.IntakeOrchestrationContractTestCase.test_guided_mode_finishes_at_twenty_when_clear -v`
- Exit: 0 (0.043s)

```text
test_guided_mode_finishes_at_twenty_when_clear (test_repo_contract.IntakeOrchestrationContractTestCase.test_guided_mode_finishes_at_twenty_when_clear) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

### TC-005 — PASS
- Type: `manual`
- Steps: Revisar la secuencia `Pregunta 20/20` → detener entrevista → pedir redefinir o dividir → no hacer handoff a architect.
- Evidence: Revisión 2026-10-13: con alcance insuficiente, Pregunta 20/20 detiene el intake, solicita redefinir o dividir y no hace handoff; con alcance suficiente, normaliza y presenta el brief sin formular una pregunta 21.

### TC-006 — PASS
- Type: `manual`
- Steps: Revisar la secuencia `Pregunta 20/20` → normalizar brief → pedir confirmación sin formular otra pregunta de entrevista.
- Evidence: Revisión 2026-10-13: con alcance insuficiente, Pregunta 20/20 detiene el intake, solicita redefinir o dividir y no hace handoff; con alcance suficiente, normaliza y presenta el brief sin formular una pregunta 21.

### TC-007 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_speckit_cli.TemplateLifecycleTestCase.test_template_manifest_hashes_match_the_seed -v`
- Exit: 0 (0.078s)

```text
test_template_manifest_hashes_match_the_seed (test_speckit_cli.TemplateLifecycleTestCase.test_template_manifest_hashes_match_the_seed) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.004s

OK
```

## TASK-002 — PASS — 2026-10-13T22:33:26Z
- Commit: d446b95a283c348c4dce9afb9566d8f28a6a0682
- Tested content: b3c0e850a0bbf40d9dac1df002efd30a6a0f3047663fa496c8c139f2af505a58 (dirty)
### TC-008 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_precedes_spec_creation -v`
- Exit: 0 (0.047s)

```text
test_fast_path_precedes_spec_creation (test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_precedes_spec_creation) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

### TC-009 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_exclusions_require_sdd -v`
- Exit: 0 (0.045s)

```text
test_fast_path_exclusions_require_sdd (test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_exclusions_require_sdd) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

### TC-010 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_allows_user_override -v`
- Exit: 0 (0.051s)

```text
test_fast_path_allows_user_override (test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_allows_user_override) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

### TC-011 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_preserves_safeguards -v`
- Exit: 0 (0.056s)

```text
test_fast_path_preserves_safeguards (test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_preserves_safeguards) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
```

### TC-012 — PASS
- Type: `manual`
- Steps: Evaluar el ejemplo de un script local de inicio/parada: anunciar vía rápida antes de `speckit new` y comprobar que no se crea ni modifica `specs/`.
- Evidence: Revisión 2026-10-13: el ejemplo de script local elegible anuncia vía rápida antes de speckit new, usa quick/<slug> y no toca specs/; si el usuario exige SDD, se detiene antes de modificar archivos y solicita elegir guided o proposal.

### TC-013 — PASS
- Type: `manual`
- Steps: Tras anunciar vía rápida, simular que el usuario exige SDD y comprobar que el siguiente paso es elegir modo de intake sin modificar archivos.
- Evidence: Revisión 2026-10-13: el ejemplo de script local elegible anuncia vía rápida antes de speckit new, usa quick/<slug> y no toca specs/; si el usuario exige SDD, se detiene antes de modificar archivos y solicita elegir guided o proposal.

### TC-014 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_speckit_cli.TemplateLifecycleTestCase.test_template_manifest_hashes_match_the_seed test_speckit_cli.TemplateLifecycleTestCase.test_version_is_reported_from_canonical_metadata -v`
- Exit: 0 (0.128s)

```text
test_template_manifest_hashes_match_the_seed (test_speckit_cli.TemplateLifecycleTestCase.test_template_manifest_hashes_match_the_seed) ... ok
test_version_is_reported_from_canonical_metadata (test_speckit_cli.TemplateLifecycleTestCase.test_version_is_reported_from_canonical_metadata) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.063s

OK
```

### TC-015 — PASS
- Type: `integration`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_speckit_cli.CliFlowTestCase.test_ci_guard_accepts_quick_branch_without_spec -v`
- Exit: 0 (0.105s)

```text
test_ci_guard_accepts_quick_branch_without_spec (test_speckit_cli.CliFlowTestCase.test_ci_guard_accepts_quick_branch_without_spec) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.041s

OK
```
