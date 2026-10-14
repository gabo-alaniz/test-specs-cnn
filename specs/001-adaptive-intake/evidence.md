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

## TASK-003 — PASS — 2026-10-14T16:51:53Z
- Commit: b073f17fdefba80f4c8134b31fda47f43df3d120
- Tested content: 198bbcdabc07f28057be0dc5739e8380531b982cb1c5b1e5f296b931e102035d (dirty)
### TC-011 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_preserves_safeguards -v`
- Exit: 0 (0.052s)

```text
test_fast_path_preserves_safeguards (test_repo_contract.IntakeOrchestrationContractTestCase.test_fast_path_preserves_safeguards) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.001s

OK
```

### TC-014 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_speckit_cli.TemplateLifecycleTestCase.test_template_manifest_hashes_match_the_seed test_speckit_cli.TemplateLifecycleTestCase.test_version_is_reported_from_canonical_metadata -v`
- Exit: 0 (0.143s)

```text
test_template_manifest_hashes_match_the_seed (test_speckit_cli.TemplateLifecycleTestCase.test_template_manifest_hashes_match_the_seed) ... ok
test_version_is_reported_from_canonical_metadata (test_speckit_cli.TemplateLifecycleTestCase.test_version_is_reported_from_canonical_metadata) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.067s

OK
```

### TC-015 — PASS
- Type: `integration`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_speckit_cli.CliFlowTestCase.test_ci_guard_accepts_quick_branch_without_spec -v`
- Exit: 0 (0.103s)

```text
test_ci_guard_accepts_quick_branch_without_spec (test_speckit_cli.CliFlowTestCase.test_ci_guard_accepts_quick_branch_without_spec) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.047s

OK
```

### TC-016 — PASS
- Type: `unit`
- Command: `PYTHONPATH=.agents/tests .venv/bin/python -S -m unittest test_repo_contract.DistributionLayoutTestCase.test_root_allowlist -v`
- Exit: 0 (0.044s)

```text
test_root_allowlist (test_repo_contract.DistributionLayoutTestCase.test_root_allowlist) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
```

## CLOSE — PASS — 2026-10-14T16:52:12Z
- Commit: c204199e95a5fff6c5ba56e542aefc2b8db61484
- Tested content: a738b026bd7d8025286672eb8d003cfc675dbb60 (clean)
- CI base: f06973d85a9800384d9b1bb6657331f3204ed4d3
- CI fingerprint: 1854d7f38fbc49edd1a961c883b72c5355b71740ad6bda54660c6c6dade3f7aa
- test: `.venv/bin/python -m unittest discover -s .agents/tests -v` → exit 0 (4.746s)

```text
test_reference_spec_is_valid (test_speckit_cli.TemplateLifecycleTestCase.test_reference_spec_is_valid) ... ok
test_template_manifest_hashes_match_the_seed (test_speckit_cli.TemplateLifecycleTestCase.test_template_manifest_hashes_match_the_seed) ... ok
test_update_manifest_rejects_traversal (test_speckit_cli.TemplateLifecycleTestCase.test_update_manifest_rejects_traversal) ... ok
test_update_never_modifies_project_owned_paths (test_speckit_cli.TemplateLifecycleTestCase.test_update_never_modifies_project_owned_paths) ... ok
test_update_previews_conflicts_backs_up_and_restores (test_speckit_cli.TemplateLifecycleTestCase.test_update_previews_conflicts_backs_up_and_restores) ... ok
test_update_rejects_symlink_escapes (test_speckit_cli.TemplateLifecycleTestCase.test_update_rejects_symlink_escapes) ... ok
test_update_removes_retired_template_content_and_preserves_memory (test_speckit_cli.TemplateLifecycleTestCase.test_update_removes_retired_template_content_and_preserves_memory) ... ok
test_update_rolls_back_all_paths_and_propagates_original_exception (test_speckit_cli.TemplateLifecycleTestCase.test_update_rolls_back_all_paths_and_propagates_original_exception) ... ok
test_version_is_reported_from_canonical_metadata (test_speckit_cli.TemplateLifecycleTestCase.test_version_is_reported_from_canonical_metadata) ... ok
test_1_layout_has_no_tool_specific_config (test_template_smoke.TemplateSmokeTestCase.test_1_layout_has_no_tool_specific_config) ... ok
test_2_every_instruction_reference_resolves (test_template_smoke.TemplateSmokeTestCase.test_2_every_instruction_reference_resolves) ... ok
test_3_cli_and_doctor_are_green (test_template_smoke.TemplateSmokeTestCase.test_3_cli_and_doctor_are_green) ... ok
test_4_full_sdd_cycle_through_the_launcher (test_template_smoke.TemplateSmokeTestCase.test_4_full_sdd_cycle_through_the_launcher) ... ok
test_5_size_s_cycle_uses_embedded_tests_through_the_launcher (test_template_smoke.TemplateSmokeTestCase.test_5_size_s_cycle_uses_embedded_tests_through_the_launcher) ... ok
test_6_codex_sandbox_can_run_shell_in_the_child (test_template_smoke.TemplateSmokeTestCase.test_6_codex_sandbox_can_run_shell_in_the_child) ... ok

----------------------------------------------------------------------
Ran 107 tests in 4.670s

OK
```
