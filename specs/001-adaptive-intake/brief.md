# Brief: intake adaptativo y vía rápida para ajustes leves

> Lo normaliza `business-analyst` mediante `sdd-intake`. El usuario elige el modo y confirma el
> resultado antes de `sdd-specify`. Si algo cambia reglas, fórmulas, permisos o datos y no se conoce,
> queda como decisión abierta; no lo inventes.

## 1. Intake
- Modo: proposal
- Estado: confirmed
- Confirmado por: usuario
- Confirmado el: 2026-10-13

## 2. Usuario
- Personas que solicitan cambios a un agente regido por este repositorio.
- Agentes que conducen el intake y deciden qué flujo corresponde a cada solicitud.
- Mantenedores del framework SDD, afectados por los cambios de gobernanza y validación.

## 3. Problema
El intake guiado presenta todas las preguntas a la vez, lo que aumenta la carga para el usuario e
impide adaptar cada pregunta a la respuesta anterior. Además, solicitudes muy pequeñas recorren una
entrevista y todo el ciclo SDD aunque su alcance y riesgo no lo justifiquen.

## 4. Proceso actual
Toda idea nueva exige elegir un modo de intake. En modo `guided`, el agente formula una ronda única
de preguntas consolidadas; después normaliza un brief y continúa por diseño, aprobación,
planificación, implementación y revisión. El mismo flujo se intenta aplicar a cambios operativos
pequeños, como crear un script local para iniciar y detener la aplicación.

## 5. Resultado esperado
- El intake `guided` se comporta como una conversación: muestra una sola pregunta, espera la
  respuesta y decide la siguiente con el contexto acumulado.
- La entrevista termina con un máximo de 20 preguntas. Si para entonces el alcance no es claro, el
  agente detiene el avance y pide redefinir o dividir la solicitud.
- Los ajustes pequeños, acotados y de bajo riesgo pueden ejecutarse mediante una vía rápida sin
  entrevista ni artefactos de spec.
- El agente explica de forma breve qué flujo aplicará y permite que el usuario corrija una
  clasificación equivocada.

Se considera exitoso cuando las pruebas del protocolo demuestran que nunca se presentan varias
preguntas de intake en un mismo turno, no existe una pregunta 21 y las solicitudes leves elegibles
no crean un directorio en `specs/`.

## 6. Reglas de negocio y fuentes
- En modo `guided`, cada turno del `business-analyst` contiene como máximo una pregunta de intake.
- Cada respuesta puede cambiar la siguiente pregunta; no se exige recorrer un cuestionario fijo si
  un tema ya quedó resuelto.
- El contador incluye toda pregunta destinada a aclarar la intención de negocio durante el intake
  guiado. La solicitud final de confirmar el brief normalizado no forma parte de la entrevista.
- Al responder la pregunta 20, el agente puede normalizar el brief si el alcance ya es suficiente.
  Si persiste una decisión que impide delimitar el resultado, detiene el intake y solicita redefinir
  o dividir la idea; no inicia diseño.
- La vía rápida se propone para un cambio que sea simultáneamente pequeño, localizado, reversible,
  de bajo riesgo y con resultado verificable mediante los checks existentes.
- Un cambio no es elegible para vía rápida si altera comportamiento funcional público, contratos o
  APIs, datos o esquemas, autenticación o permisos, seguridad, dependencias, arquitectura,
  infraestructura compartida, CI/CD o reglas de gobernanza del repositorio.
- La vía rápida conserva las reglas de seguridad, permisos de archivos, stack, Git y pruebas. Solo
  omite intake, brief, spec, plan, tasks, gates y cierre SDD.
- Antes de actuar, el agente anuncia `vía rápida` y su justificación concisa. El usuario puede pedir
  que se use el flujo SDD normal.
- Fuente: observaciones y ejemplo aportados por el usuario en esta solicitud.
- Responsable funcional propuesto: mantenedores del framework SDD.

## 7. Permisos y sensibilidad
- Cualquier usuario puede solicitar un cambio; el agente aplica la clasificación con las reglas
  anteriores y el usuario puede invalidarla.
- Solo los mantenedores autorizados pueden integrar cambios a las reglas compartidas del framework.
- La información tratada es interna y no requiere PII, credenciales ni secretos.

## 8. Criterios de aceptación
- AC-001: Dado un intake en modo `guided`, cuando el agente necesita información del usuario,
  entonces presenta exactamente una pregunta de intake y espera su respuesta antes de formular la
  siguiente.
- AC-002: Dado un intake guiado con menos de 20 respuestas, cuando una respuesta resuelve o cambia
  una incertidumbre, entonces la siguiente pregunta se adapta al contexto acumulado y no repite
  información ya contestada.
- AC-003: Dado que el usuario respondió la pregunta 20, cuando todavía no puede delimitarse el
  alcance, entonces el agente detiene el intake, no inicia el diseño y solicita redefinir o dividir
  la idea.
- AC-004: Dado que el usuario respondió la pregunta 20, cuando el alcance ya es suficiente, entonces
  el agente presenta el brief para confirmación sin formular más preguntas de entrevista.
- AC-005: Dada una solicitud que cumple todos los criterios de vía rápida y ninguna exclusión, cuando
  el agente la clasifica, entonces anuncia la vía rápida y puede implementarla sin crear artefactos
  en `specs/`.
- AC-006: Dada una solicitud que incumple un criterio de vía rápida o toca una exclusión, cuando el
  agente la clasifica, entonces aplica el flujo SDD normal y no omite sus gates.
- AC-007: Dada una clasificación de vía rápida, cuando el usuario solicita el flujo SDD normal,
  entonces el agente respeta esa elección antes de modificar archivos.
- AC-008: Dado un cambio realizado por vía rápida, cuando se entrega, entonces se reportan el cambio
  y la evidencia de validación aplicable sin afirmar pruebas que no fueron ejecutadas.

## 9. Fuera de alcance
- Cambiar los gates o la evidencia requerida para solicitudes que sí usan el flujo SDD.
- Relajar seguridad, permisos de edición, estándares de pruebas o restricciones de Git.
- Definir excepciones para cambios de alto riesgo aunque tengan pocas líneas.
- Modificar el modo `proposal` más allá de la clasificación previa de la solicitud.
- Diseñar en este brief la implementación técnica concreta de las reglas y validaciones.

## 10. Restricciones y riesgos
- La vía rápida introduce una excepción a la regla vigente que exige artefactos SDD antes de todo
  cambio; la excepción deberá quedar explícita y consistente en las fuentes de gobernanza.
- “Pequeño” no puede medirse solo por líneas de código: un cambio corto puede afectar seguridad,
  datos o producción.
- El límite de 20 preguntas no debe incentivar preguntas compuestas que vuelvan a presentar un
  cuestionario completo en un solo turno.
- La entrevista debe conservar la cobertura necesaria del brief, pero omitir temas que no aplican o
  que ya se resolvieron con respuestas anteriores.
- Implementar esta mejora requerirá autorización explícita antes de editar `AGENTS.md` o
  `.agents/**`.

## 11. Referencias
- Solicitud del usuario del 2026-10-13.
- Ejemplo aportado: script para iniciar y detener la aplicación.
- `.agents/rules/intake-orchestration.md`.
- `.agents/rules/speckit-methodology.md`.
- `.agents/skills/sdd-intake/SKILL.md`.

## 12. Hechos aportados
- Actualmente el agente entrega todas las preguntas de la entrevista de una sola vez.
- Se desea una entrevista secuencial, con una pregunta por vez.
- Una entrevista no debe superar 20 preguntas; superar ese umbral indica que el alcance necesita
  redefinirse.
- Los ajustes muy pequeños no deberían exigir entrevista ni la construcción de un spec completo.
- Crear un script para iniciar y detener la aplicación es el ejemplo aportado de ajuste leve.

## 13. Supuestos
- Ninguno pendiente. Los supuestos de la propuesta fueron confirmados por el usuario y quedaron
  incorporados como reglas en la sección 6.

## 14. Decisiones abiertas
- Ninguna.
