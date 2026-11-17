# Evidence

## TASK-001 — PASS — 2026-11-17T20:00:06Z
- Commit: e9fd25e4b5b06886e614c63e980212301fcadf32
- Tested content: 01825330c60f6d0622fdd2ea90b0f8bcdfd3dca9d51aeae5642c4351b79e411c (dirty)
### TC-001 — PASS
- Type: `unit`
- Command: `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.EstructuraTestCase -v`
- Exit: 0 (0.993s)

```text
test_datos_ignorados_por_git (test_clasificacion_flores.EstructuraTestCase.test_datos_ignorados_por_git) ... ok
test_notebook_valido_con_celdas_etiquetadas (test_clasificacion_flores.EstructuraTestCase.test_notebook_valido_con_celdas_etiquetadas) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.023s

OK
```

### TC-002 — PASS
- Type: `integration`
- Command: `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.DescargaTestCase -v`
- Exit: 0 (5.770s)

```text
test_descarga_deja_cinco_clases_con_imagenes (test_clasificacion_flores.DescargaTestCase.test_descarga_deja_cinco_clases_con_imagenes) ... [IPKernelApp] WARNING | Kernel is running over TCP without encryption. All communication (including code and outputs) is sent in plain text and is susceptible to eavesdropping. Use IPC transport or launch with kernel manager-provisioned CurveZMQ keys to enable transport encryption.
ok
test_sin_credenciales_de_kaggle (test_clasificacion_flores.DescargaTestCase.test_sin_credenciales_de_kaggle) ... ok

----------------------------------------------------------------------
Ran 2 tests in 4.821s

OK
```

## TASK-002 — PASS — 2026-11-17T20:01:06Z
- Commit: e9fd25e4b5b06886e614c63e980212301fcadf32
- Tested content: ad99014e5abf6247f9db8086bd80105dd9e71b0fb497baa343be9e9e8a38a3e5 (dirty)
### TC-003 — PASS
- Type: `integration`
- Command: `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.DivisionTestCase -v`
- Exit: 0 (10.651s)

```text
[IPKernelApp] WARNING | Kernel is running over TCP without encryption. All communication (including code and outputs) is sent in plain text and is susceptible to eavesdropping. Use IPC transport or launch with kernel manager-provisioned CurveZMQ keys to enable transport encryption.
test_division_reproducible_y_disjunta (test_clasificacion_flores.DivisionTestCase.test_division_reproducible_y_disjunta) ... [IPKernelApp] WARNING | Kernel is running over TCP without encryption. All communication (including code and outputs) is sent in plain text and is susceptible to eavesdropping. Use IPC transport or launch with kernel manager-provisioned CurveZMQ keys to enable transport encryption.
ok
test_la_celda_de_datos_construye_lotes (test_clasificacion_flores.DivisionTestCase.test_la_celda_de_datos_construye_lotes) ... ok

----------------------------------------------------------------------
Ran 2 tests in 9.717s

OK
```

## TASK-003 — PASS — 2026-11-17T20:03:05Z
- Commit: e9fd25e4b5b06886e614c63e980212301fcadf32
- Tested content: 2b51a67cedf77dc260883e896bf31b3ad9b659bbcd872f6bf50aa979b3195ef4 (dirty)
### TC-004 — PASS
- Type: `integration`
- Command: `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.EntrenamientoTestCase -v`
- Exit: 0 (54.198s)

```text
[IPKernelApp] WARNING | Kernel is running over TCP without encryption. All communication (including code and outputs) is sent in plain text and is susceptible to eavesdropping. Use IPC transport or launch with kernel manager-provisioned CurveZMQ keys to enable transport encryption.
test_el_modelo_se_construye (test_clasificacion_flores.EntrenamientoTestCase.test_el_modelo_se_construye) ... ok
test_entrena_en_cpu_y_termina (test_clasificacion_flores.EntrenamientoTestCase.test_entrena_en_cpu_y_termina) ... ok
test_registra_perdida_y_exactitud_por_epoca (test_clasificacion_flores.EntrenamientoTestCase.test_registra_perdida_y_exactitud_por_epoca) ... ok

----------------------------------------------------------------------
Ran 3 tests in 53.240s

OK
```

## TASK-004 — PASS — 2026-11-17T20:05:08Z
- Commit: e9fd25e4b5b06886e614c63e980212301fcadf32
- Tested content: a81bb44cfbe47c8bd9a15c810291c0eec4f35c3ea7ba7a509c60a1dbd6fe0aee (dirty)
### TC-005 — PASS
- Type: `integration`
- Command: `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.EvaluacionTestCase -v`
- Exit: 0 (53.774s)

```text
[IPKernelApp] WARNING | Kernel is running over TCP without encryption. All communication (including code and outputs) is sent in plain text and is susceptible to eavesdropping. Use IPC transport or launch with kernel manager-provisioned CurveZMQ keys to enable transport encryption.
test_exactitud_y_reporte_por_clase (test_clasificacion_flores.EvaluacionTestCase.test_exactitud_y_reporte_por_clase) ... ok
test_genera_tres_figuras (test_clasificacion_flores.EvaluacionTestCase.test_genera_tres_figuras) ... ok
test_sin_errores_en_la_celda (test_clasificacion_flores.EvaluacionTestCase.test_sin_errores_en_la_celda) ... ok

----------------------------------------------------------------------
Ran 3 tests in 52.813s

OK
```
