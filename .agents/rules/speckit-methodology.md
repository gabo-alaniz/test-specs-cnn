# SPECKIT METHODOLOGY
# Propósito: Protocolo obligatorio de diseño antes de programar una solicitud clasificada como SDD.
# La vía rápida válida queda fuera de Speckit, pero no de seguridad, permisos ni validación.

## PRINCIPIO

Speckit impone una cascada de diseño que separa el *qué* del *cómo* del *cuándo* para toda solicitud
clasificada como SDD. Solo una vía rápida válida según `intake-orchestration.md` queda fuera de esta
cascada; no crea artefactos Speckit, pero conserva seguridad, permisos, stack, Git y testing.

## 0. INTAKE, BRIEF Y TAMAÑO

- El agente activo actúa como `orchestrator` y clasifica la solicitud antes de crear un spec. Solo si
  no aplica la vía rápida, el usuario elige `guided` o `proposal` según
  `.agents/rules/intake-orchestration.md`.
- `business-analyst` sigue `sdd-intake`, normaliza la idea en
  `specs/<id>-<nombre>/brief.md` y solicita confirmación explícita.
- Un brief con sección `Intake` solo llega a `architect` cuando registra `Estado: confirmed`, actor
  humano y fecha. La confirmación del brief no equivale a GATE 1.
- `architect` no repite un intake confirmado; solo agrupa en una ronda los bloqueos técnicos reales.
  Los briefs legacy sin sección `Intake` mantienen la ronda única del flujo anterior.
- Tamaño (`state.json.size`):
  - **S**: `spec.md` con notas técnicas y pruebas, más `tasks.md`; como máximo 3 tareas.
  - **M**: los 4 artefactos; como máximo 8 tareas.
  - **L**: se divide en varios specs.
- Plantillas de todos los artefactos: `.agents/templates/`.

## 1. SPEC — REQUERIMIENTOS (el *Qué* y el *Por Qué*)

**Ubicación:** `specs/<id>-<nombre>/spec.md`

Contenido obligatorio:
- Descripción del problema y contexto
- Casos de uso y flujos de negocio
- Criterios de aceptación verificables con ID estable: `AC-001: Dado …, cuando …, entonces …`
- Alcance: qué incluye y qué excluye explícitamente

El usuario aprueba el Spec y el Plan juntos (GATE 1).

## 2. PLAN — DISEÑO TÉCNICO (el *Cómo*, solo size M)

**Ubicación:** `specs/<id>-<nombre>/implementation-plan.md`

Contenido obligatorio:
- Módulos y componentes afectados
- Decisiones de arquitectura y justificación
- Migraciones de BD necesarias
- Dependencias nuevas (si aplica) con justificación
- Riesgos identificados

Sin la aprobación del usuario (GATE 1) no se generan Tasks.

## 3. TASKS — EJECUCIÓN ATÓMICA (el *Cuándo*)

**Ubicación:** `specs/<id>-<nombre>/tasks.md`

- Lista de tareas atómicas e independientes
- Cada tarea tiene un identificador estable: `TASK-001`, `TASK-002`, ...
- Estado de cada tarea: `[ ]` pendiente, `[/]` en progreso, `[x]` completada
- Los Task IDs no se reutilizan dentro de un mismo Spec
- `state.json.current_task` refleja el Task ID actualmente en ejecución
- Formato obligatorio de cada línea (lo verifica el validador): `- [ ] TASK-001: descripción (AC-001)`

## 4. TEST PLAN — VALIDACIÓN (la *Evidencia*, solo size M; en S va en `spec.md`)

**Ubicación:** `specs/<id>-<nombre>/test-plan.md`

- Escenarios de prueba para cada criterio de aceptación del Spec
- Puede ser manual, automatizado o combinado, según el proyecto
- Formato canónico: `| TC-001 | AC-001 | escenario | unit|integration|e2e|manual | comando o pasos |`
- `task done` ejecuta los escenarios de los AC de la tarea; `close` ejecuta los checks globales

## 5. STATE — REGISTRO DE PROGRESO

**Ubicación:** `specs/<id>-<nombre>/state.json`

**Schema:** `.agents/schemas/spec-state.schema.json`
**Ejemplos:** `.agents/examples/spec-state.*.example.json` (solo referencia, no editar)

Reglas del `state.json`:
- Cada Spec tiene exactamente un `state.json` en su propio directorio.
- Un artefacto solo se marca como `true` cuando el archivo existe y está completo.
- `completed: true` requiere que todos los artefactos y validaciones estén terminados.
- No crear un `state.json` global para todo el proyecto.
- No almacenar estados de múltiples Specs en un mismo archivo.
- Todo `state.json` debe validar contra el schema oficial.
- `spec_name` es igual al nombre del directorio (`001-login`).
- `speckit design ready <spec>` deja el diseño en `awaiting_approval`; no se edita `state.json` a mano.
- `speckit design revise <spec> --by <nombre> --reason <motivo>` abre una revisión solo antes de
  implementar: conserva archivos e historial, limpia aprobación y flags de Ready y exige repetir
  `design ready` y `approve`.
- `speckit ready <spec>` demuestra GATE 2 y deja `status=ready`, `phase=ready`, `current_task=null`.
- Solo `task start` inicia implementación y marca una tarea `[/]`.
- La aprobación del usuario (GATE 1) registra actor, fecha y hashes SHA-256 normalizados del diseño; cualquier cambio posterior exige nueva aprobación.
- `phase` indica la fase en curso; estar en una fase exige los artefactos y aprobaciones de las anteriores (ver gates en `progress-continuity.md`).

## 6. TASK IDENTIFIERS

Toda tarea en `tasks.md` lleva un identificador estable:

```
- [ ] TASK-001: <descripción concisa>
- [ ] TASK-002: <descripción concisa>
```

El Task ID se usa en:
- commits: `feat(TASK-014): add shared data table filtering`
- resultados de validación
- `state.json.current_task`

No crear Task IDs para cambios triviales fuera del flujo Speckit.

## 7. VALIDACIÓN DEL SPEC

En cada cambio de fase y antes de iniciar implementación:

```bash
./speckit validate specs/<id>-<nombre>/
```

El validador comprueba el schema, el tamaño, los gates, artefactos no vacíos, formato canónico y unicidad de tasks/escenarios, tipos de prueba, cobertura de AC y coherencia del estado. Avisa cuando hay demasiadas tareas.
Si falla → corregir antes de proceder. No omitir esta validación.

## 8. SESSION REBOOT

Al cerrar una sesión de trabajo → `./speckit handoff <spec>` (`progress-continuity.md` §5).
Al cerrar un spec → `./speckit close <spec>` y completar `retro.md`; las preferencias y decisiones nuevas van a `.agents/memory/`.

## REGLA FINAL

> Tras clasificar como SDD: Spec → Plan → Tasks → Test Plan → Implement → Validate → Document.

En SDD no se escribe código sin los artefactos que exige su tamaño. El `state.json` refleja siempre
la realidad, no las intenciones. La vía rápida no crea `state.json` ni artefactos en `specs/`.
