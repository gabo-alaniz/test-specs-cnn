---
name: sdd-specify
description: Convierte un brief en un diseño SDD listo para aprobar (spec.md y, en size M, implementation-plan.md). Úsala cuando el usuario quiera empezar o especificar una feature o spec nueva.
---

# SDD · Specify

1. Si el spec no existe, vuelve a `sdd-intake`: el `orchestrator` crea el spec y obtiene un brief
   confirmado antes del diseño.
   - Usa S si caben ≤ 3 tareas sin decisiones de diseño; en otro caso, M.
   - Si salen más de 8 tareas, propón dividirlo en varios specs.
2. Lee `brief.md` y comprueba el intake:
   - Si contiene la sección `Intake`, exige `Estado: confirmed`, `Confirmado por` y `Confirmado el`
     con valores reales. En otro caso detente y devuelve el flujo a `sdd-intake`.
   - Si es un brief legacy sin esa sección, conserva el flujo anterior; no lo migres como efecto
     secundario.
3. Lee `.agents/memory/preferences.md` y haz una búsqueda dirigida del código afectado (si dudas del
   nivel de detalle, mira `.agents/examples/001-archive-specs/`).
4. No repitas la entrevista de negocio de un intake confirmado. Haz **una sola ronda consolidada**
   solo para bloqueos técnicos reales, numerados y con una respuesta por defecto. Si una pregunta
   cambia intención, reglas, fórmulas, permisos o datos, vuelve a `sdd-intake` en vez de resolverla.
   En un brief legacy, esta ronda también cubre sus `[NEEDS CLARIFICATION]` y huecos reales.
5. Escribe `spec.md` (y `implementation-plan.md` en M) con:
   - Problema, usuarios y alcance (qué incluye y qué excluye).
   - Criterios `AC-001: Dado …, cuando …, entonces …`, observables y testeables.
   - Ningún `[NEEDS CLARIFICATION]`.
6. Ejecuta `./speckit design ready <spec>`: marca los artefactos existentes, valida placeholders y secciones obligatorias y deja el estado en `awaiting_approval`. Nunca edites `state.json` a mano.
7. Presenta al usuario un resumen de ≤ 15 líneas (AC, alcance, decisiones y riesgos) y pide su aprobación explícita. Confirmar el brief no cuenta como esta aprobación.
8. Solo cuando el usuario apruebe el diseño, ejecuta `./speckit approve <spec> --by "<nombre>"` y continúa con `sdd-plan`.

En esta skill no se escribe código de producción.
