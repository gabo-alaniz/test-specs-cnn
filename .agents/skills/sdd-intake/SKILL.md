---
name: sdd-intake
description: Convierte una idea en un brief de negocio confirmado mediante entrevista guiada o propuesta revisable, antes de sdd-specify.
---

# SDD · Intake

Sigue `.agents/rules/intake-orchestration.md`. En esta fase solo se edita el `brief.md` del spec;
no se escribe diseño, tareas ni código.

1. Si el spec no existe, el `orchestrator` ejecuta `./speckit new <slug> --size S|M` usando el tamaño
   mínimo razonable según el alcance conocido. Size L se divide después del intake.
2. Lee la solicitud inicial, el `brief.md` y las preferencias del proyecto. No hagas descubrimiento
   técnico amplio: esta fase captura intención de negocio.
3. Si `Modo` está pendiente, pregunta al usuario si prefiere:
   - `guided`: responder una entrevista consolidada;
   - `proposal`: revisar una propuesta redactada por el agente.
   No elijas por el usuario ni inicies `sdd-specify` antes de su respuesta.
4. En `guided`, formula exactamente una pregunta de intake por turno, identificada como
   `Pregunta N/20`, y espera la respuesta antes de elegir la siguiente. Adáptala al contexto
   acumulado, omite lo ya resuelto y no agrupes preguntas independientes. Cubre cuando aplique
   perfil, problema, proceso, resultado, éxito, reglas, fórmulas, excepciones, fuentes, permisos,
   sensibilidad, restricciones, riesgos y exclusiones. Propón opciones o ejemplos dentro de la
   pregunta cuando reduzcan carga cognitiva.
   - Después de cada respuesta, termina la entrevista si el brief ya puede normalizarse.
   - Después de `Pregunta 20/20`, no hagas una pregunta 21: si el alcance es claro, presenta el
     brief; si no, detén el intake y pide redefinir o dividir la idea sin iniciar diseño.
   - La confirmación final del brief no incrementa el contador de la entrevista.
5. En `proposal`, completa el brief con lo ya aportado y separa `Hechos aportados`, `Supuestos` y
   `Decisiones abiertas`. Nunca rellenes como hecho una fórmula, fuente, permiso o regla inferida.
6. Normaliza el resultado en `brief.md`, deja `Estado: draft` y elimina de ese archivo cualquier
   transcripción, secreto o PII innecesaria. Describe sensibilidad por categoría y usa ejemplos
   sintéticos.
7. Presenta un resumen legible del brief, destaca supuestos y decisiones abiertas, y pide al usuario
   que lo corrija o lo confirme explícitamente. El agente nunca se autoconfirma.
8. Solo tras esa confirmación cambia `Estado` a `confirmed` y registra el actor humano y la fecha
   ISO-8601. Si quedan decisiones que cambian resultado, fórmulas, permisos o datos, conserva
   `Estado: draft` y no hace handoff.
9. Devuelve el brief confirmado al `orchestrator`, que anuncia el cambio a `architect` y ejecuta
   `sdd-specify`. Esta confirmación no equivale a la aprobación del diseño de GATE 1.

Si una corrección posterior cambia la intención de negocio, vuelve el brief a `draft` y repite su
confirmación antes de entregarlo otra vez al architect.
