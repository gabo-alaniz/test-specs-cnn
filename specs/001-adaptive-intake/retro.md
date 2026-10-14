# Retro 001-adaptive-intake

> Lo genera `speckit close`. El agente lo completa con el usuario en 5 minutos antes de ejecutar `speckit archive`.
> Lo que deba repetirse va a `.agents/memory/preferences.md` y las decisiones transversales a `decisions.md`.

- Tamaño: M · Aprobado: 2026-10-13T22:23:12Z · Cerrado: 2026-10-14T16:52:12Z
- Tareas: 3 · Intentos fallidos: ninguno

## Qué funcionó

- La entrevista guiada quedó expresada como una secuencia adaptativa de una pregunta por turno, con
  límite verificable de 20 preguntas.
- La vía rápida quedó delimitada por criterios acumulativos, exclusiones explícitas, override del
  usuario y trazabilidad para ramas `quick/<slug>`.
- Los escenarios dirigidos de cada tarea y el cierre global dejaron evidencia reproducible sin
  intentos fallidos.

## Qué costó (vueltas, reintentos, ambigüedades del brief)

- El contrato del allowlist raíz no reflejaba que `AGENT_PROMPT.md` debía conservarse. El hallazgo
  apareció en la revisión global y requirió `TASK-003` y `TC-016` antes del cierre.
- La distinción entre `.agents/AGENT_PROMPT.md` como fuente canónica y `AGENT_PROMPT.md` como
  bootstrap raíz debía quedar explícita para evitar interpretar el duplicado como archivo sobrante.

## Preferencias nuevas

- Conservar `AGENT_PROMPT.md` en la raíz sin modificarlo — el usuario confirmó que forma parte del
  modo de uso esperado del repositorio; el allowlist de distribución debe aceptarlo.

## Reglas o plantillas a ajustar

- Ejecutar el contrato completo de distribución antes de concluir la primera revisión, además de
  los escenarios dirigidos de las tareas, para detectar antes inconsistencias del layout raíz.
- Mantener `TC-016` como regresión de que el bootstrap raíz está permitido.
