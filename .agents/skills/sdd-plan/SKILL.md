---
name: sdd-plan
description: Descompone un spec SDD aprobado en tareas atómicas y test plan hasta dejarlo Ready (GATE 2). Úsala después de que el usuario aprobó el spec con speckit approve.
---

# SDD · Plan de tareas

1. Comprueba con `./speckit status <spec>` que aparece `approved=yes`. Si no, vuelve a `sdd-specify`.
2. Escribe `tasks.md`:
   - Formato de cada línea: `- [ ] TASK-001: <verbo + resultado> (AC-001, AC-002)`.
   - Tareas pequeñas y verificables por separado, que dejen los tests en verde.
   - Como máximo 3 tareas en S y 8 en M.
   - Cada AC del `spec.md` aparece en al menos una tarea.
3. En size M, escribe `test-plan.md` con ≥ 1 escenario por AC: `| TC-001 | AC-001 | escenario | unit | comando |`. Elige la prueba más barata que demuestre el AC (unit antes que e2e). En size S, la tabla de pruebas vive en `spec.md`.
4. Comprueba que cada escenario automático tiene un comando ejecutable y que `.agents/project.json` define `commands.test` para el cierre global.
5. Ejecuta `./speckit validate specs/<spec>/` y corrige hasta que pase.
6. Ejecuta `./speckit ready <spec>`, que aplica el GATE 2 sin iniciar ninguna tarea. El implementador ejecutará después `task start`.
