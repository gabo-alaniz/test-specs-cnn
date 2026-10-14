# Spec 001: intake adaptativo y vía rápida

> Fuente: `brief.md`. Tamaño: M (`AGENTS.md` §D).

## Problema y contexto
El intake guiado actual presenta una ronda completa de preguntas y obliga a que cualquier idea
recorra el ciclo SDD. Esto genera una conversación pesada y un coste desproporcionado para ajustes
locales, reversibles y de bajo riesgo. El proceso necesita adaptar cada pregunta a la respuesta
anterior, limitar la entrevista a 20 preguntas y reconocer una vía rápida segura antes de crear un
spec.

## Usuarios y flujos
- **Solicitante de un cambio:** describe una necesidad y puede aceptar la vía rápida propuesta o
  exigir el flujo SDD normal.
- **Orchestrator:** clasifica primero la solicitud. Solo crea o recupera un spec y pide elegir
  `guided` o `proposal` cuando la solicitud no cumple la vía rápida.
- **Business analyst:** en `guided`, formula una única pregunta por turno, identificada como
  `Pregunta N/20`, y usa las respuestas acumuladas para omitir temas resueltos y elegir la siguiente.
- **Mantenedor del template:** conserva coherentes la constitución, reglas, roles, skills,
  documentación y pruebas contractuales.

Flujo de vía rápida:

1. Antes de ejecutar `speckit new`, el orchestrator evalúa alcance y riesgo.
2. Si el cambio es pequeño, localizado, reversible, de bajo riesgo, verificable con checks
   existentes y no toca ninguna exclusión, anuncia `vía rápida` y explica brevemente por qué.
3. El usuario puede exigir el flujo SDD normal antes de que se modifiquen archivos.
4. Si se mantiene la vía rápida, el agente implementa el cambio sin crear artefactos en `specs/`,
   ejecuta la validación proporcional y entrega la evidencia disponible.

Flujo de intake guiado:

1. El business analyst formula `Pregunta 1/20` y espera la respuesta.
2. Tras cada respuesta, determina si el brief ya puede normalizarse; si no, formula una sola
   pregunta nueva sin repetir información ya resuelta.
3. Después de la respuesta 20 no formula otra pregunta de entrevista. Si el alcance ya es claro,
   presenta el brief; si no, detiene el intake y solicita redefinir o dividir la idea.
4. La solicitud de confirmar el brief sucede después de la entrevista y no incrementa el contador.

## Criterios de aceptación
- AC-001: Dado un intake en modo `guided`, cuando el agente necesita información del usuario,
  entonces presenta exactamente una pregunta de intake con el indicador `Pregunta N/20` y espera la
  respuesta antes de formular la siguiente.
- AC-002: Dado un intake guiado con menos de 20 respuestas, cuando una respuesta resuelve o cambia
  una incertidumbre, entonces la siguiente pregunta se adapta al contexto acumulado y no repite
  información ya contestada ni agrupa preguntas independientes.
- AC-003: Dado que el usuario respondió `Pregunta 20/20`, cuando todavía no puede delimitarse el
  alcance, entonces el agente detiene el intake, no inicia el diseño y solicita redefinir o dividir
  la idea.
- AC-004: Dado que el usuario respondió `Pregunta 20/20`, cuando el alcance ya es suficiente,
  entonces el agente presenta el brief para confirmación sin formular más preguntas de entrevista.
- AC-005: Dada una solicitud pequeña, localizada, reversible, de bajo riesgo, verificable con checks
  existentes y sin exclusiones, cuando el orchestrator la clasifica, entonces anuncia la vía rápida
  y puede implementarla sin crear ni modificar un directorio en `specs/`.
- AC-006: Dada una solicitud que incumple algún criterio de vía rápida o que altera comportamiento
  funcional público, APIs o contratos, datos o esquemas, autenticación o permisos, seguridad,
  dependencias, arquitectura, infraestructura compartida, CI/CD o gobernanza, cuando se clasifica,
  entonces el orchestrator aplica el flujo SDD normal sin omitir gates.
- AC-007: Dada una clasificación de vía rápida, cuando el usuario solicita el flujo SDD normal antes
  de modificar archivos, entonces el agente respeta esa elección y comienza por el intake.
- AC-008: Dado un cambio realizado por vía rápida, cuando el agente lo entrega, entonces reporta los
  archivos modificados y la evidencia de validación aplicable, sin relajar seguridad, permisos,
  stack, Git ni estándares de pruebas.

## Alcance
**Incluye:**
- Clasificación de la vía rápida antes de crear un spec o preguntar por el modo de intake.
- Criterios acumulativos de elegibilidad, exclusiones por riesgo y capacidad de override del usuario.
- Entrevista `guided` secuencial, adaptativa, con contador visible y máximo de 20 preguntas.
- Armonización de las fuentes normativas, roles, skills, bootstrap alternativo y guía del template.
- Pruebas contractuales del contenido distribuido y actualización de versión y manifiesto.

**Excluye:**
- Un comando nuevo del CLI para ejecutar o registrar cambios por vía rápida.
- Clasificación automática basada únicamente en líneas o cantidad de archivos.
- Cambios en gates, estados o evidencia de los specs que sí siguen SDD.
- Relajar seguridad, permisos, reglas de stack, Git o testing.
- Cambiar el comportamiento del modo `proposal` después de entrar al intake.
- Modificar el duplicado no distribuido `AGENT_PROMPT.md` de la raíz.

## Restricciones y datos
- Las reglas de la vía rápida deben resolver la contradicción actual entre el flujo obligatorio y la
  mención existente de cambios triviales fuera de Speckit.
- La vía rápida solo omite artefactos y gates SDD; no amplía permisos de escritura ni autoriza
  instalaciones, operaciones Git o cambios protegidos.
- El agente no conserva transcripciones de la entrevista, secretos ni PII. Solo normaliza la
  intención en `brief.md` cuando corresponde usar SDD.
- La solución no introduce dependencias ni cambia el schema de `state.json`.
- Los archivos template-owned modificados deben conservar hashes coherentes en el manifiesto y una
  versión de template alineada.
