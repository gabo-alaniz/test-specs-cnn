# Plan 001: intake adaptativo y vía rápida

> Solo size M. Se aprueba junto con `spec.md` (GATE 1).

## Módulos y componentes afectados
- `AGENTS.md`: entrada canónica del agente; clasifica la vía rápida antes del intake y delimita la
  excepción al flujo SDD.
- `.agents/rules/core-constitution.md`: integra la vía rápida en la precedencia y evita que contradiga
  el flujo canónico aplicable a cambios SDD.
- `.agents/rules/intake-orchestration.md`: define el clasificador previo, las exclusiones y la
  entrevista secuencial con máximo de 20 preguntas.
- `.agents/rules/speckit-methodology.md` y `.agents/rules/progress-continuity.md`: distinguen cambios
  SDD de la vía rápida y mantienen validación proporcional fuera de los gates.
- `.agents/skills/sdd-intake/SKILL.md`: reemplaza la ronda consolidada por preguntas adaptativas de
  una en una con contador `N/20` y condición de parada.
- `.agents/roles/orchestrator.md` y `.agents/roles/business-analyst.md`: asignan la clasificación y la
  entrevista a sus responsables sin mezclar permisos.
- `.agents/AGENT_PROMPT.md` y `.agents/README.md`: actualizan el bootstrap alternativo y la guía
  distribuida del template.
- `.agents/tests/test_repo_contract.py`: fija contratos contra regresiones del límite, el formato
  secuencial, la clasificación previa, las exclusiones y el override del usuario.
- `.agents/version.json` y `.agents/template-manifest.json`: publican el cambio como actualización
  patch del template y recalculan hashes de los archivos distribuidos modificados.

## Decisiones

| Decisión | Alternativa descartada | Motivo |
|----------|------------------------|--------|
| Clasificar antes de `speckit new` y antes de pedir `guided` o `proposal` | Crear primero un spec y borrarlo si resulta trivial | AC-005 exige que la vía rápida no cree ni modifique artefactos en `specs/`. |
| Exigir todos los criterios de elegibilidad y rechazar ante cualquier exclusión | Medir por líneas, archivos o duración estimada | El riesgo no guarda relación segura con el tamaño textual del cambio. |
| Mostrar `Pregunta N/20` y permitir una sola pregunta independiente por turno | Conservar preguntas agrupadas o esconder el contador | Hace observable el límite y evita eludirlo mediante preguntas compuestas. |
| No contar la confirmación del brief como entrevista | Consumir una de las 20 preguntas con la confirmación | La confirmación valida el documento resultante; no descubre alcance nuevo. |
| Mantener seguridad, permisos, stack, Git y testing en la vía rápida | Omitir toda gobernanza junto con los gates | La petición solo elimina burocracia SDD para cambios de bajo riesgo. |
| Verificar el protocolo con contratos estáticos y escenarios manuales | Añadir un motor o clasificador automático al CLI | El comportamiento reside en instrucciones para agentes; automatizar semántica excede el alcance. |
| Actualizar solo `.agents/AGENT_PROMPT.md` como bootstrap distribuido | Sincronizar también `AGENT_PROMPT.md` de la raíz | El archivo raíz no forma parte del inventario exportable ni de la fuente canónica del template. |

## Datos y migraciones
No hay cambios de datos, schemas ni migraciones. El contador vive en la conversación visible como
`Pregunta N/20`; no se persiste la transcripción ni se añaden campos a `state.json`.

## Dependencias nuevas
Ninguna.

## Riesgos y mitigación
- **Clasificación subjetiva:** el agente podría tratar como leve un cambio riesgoso. Se mitiga con
  criterios acumulativos, exclusiones explícitas, sesgo al flujo SDD ante duda y override del usuario.
- **Reglas contradictorias:** varias fuentes hoy declaran obligatorio el SDD. Se mitiga actualizando
  constitución, metodología, continuidad, orquestación, skill, roles y bootstrap en una misma tarea.
- **Límite eludido con preguntas compuestas:** se prohíbe agrupar preguntas independientes y se fija
  el formato observable `Pregunta N/20`.
- **Pérdida de evidencia en vía rápida:** se conserva la ejecución autónoma de checks aplicables y el
  reporte de resultados, aunque no exista `evidence.md`.
- **Comportamiento no ejecutable en tests:** las pruebas contractuales detectan drift normativo y los
  escenarios manuales revisan la interacción; no se afirma que un test estático simule un LLM.
- **Drift de distribución:** modificar archivos template-owned rompe `doctor` si no cambian sus
  hashes. Se mitiga recalculando el manifiesto, actualizando la versión patch y ejecutando tests,
  `doctor` y validación global al cierre.
