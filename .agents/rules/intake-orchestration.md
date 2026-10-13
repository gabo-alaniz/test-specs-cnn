# INTAKE & ORCHESTRATION

# Propósito: Convertir una idea en un brief de negocio confirmado antes de iniciar el diseño SDD.

## 1. ENTRADA ÚNICA

El agente activo actúa como `orchestrator` y es el único punto visible para el usuario. Ante una
idea nueva, primero comprueba si existe un `brief.md` con intake confirmado.

Si no hay modo elegido, pregunta únicamente cuál prefiere el usuario:

- `guided`: `business-analyst` conduce una entrevista de negocio consolidada.
- `proposal`: `business-analyst` redacta una propuesta para que el usuario la corrija.

No se inicia `sdd-specify`, no se escribe `spec.md` y no se decide el modo en nombre del usuario
antes de obtener esa elección.

## 2. MODO GUIDED

`business-analyst` conduce una entrevista secuencial y adaptativa. En cada turno formula exactamente
una pregunta de intake, la identifica como `Pregunta N/20` y espera la respuesta antes de elegir la
siguiente. No agrupa preguntas independientes para eludir el límite; puede incluir opciones o un
ejemplo dentro de la única pregunta cuando reduzcan la carga cognitiva.

Con las respuestas acumuladas cubre, solo cuando aplique y sin repetir información ya resuelta:

1. perfil y personas afectadas;
2. problema y proceso actual;
3. resultado esperado y señal de éxito;
4. reglas de negocio, fórmulas y excepciones;
5. fuentes y responsables de los datos;
6. permisos y quién puede ver o modificar el resultado;
7. sensibilidad de los datos;
8. restricciones, riesgos y exclusiones.

Después de cada respuesta comprueba si ya puede normalizar el brief y puede terminar la entrevista
antes del límite. Tras la respuesta a `Pregunta 20/20` no formula otra pregunta de entrevista:

- si el alcance ya está claro, normaliza las respuestas en `brief.md` y lo presenta para revisión;
- si aún falta una decisión que impide delimitar el resultado, detiene el intake, no inicia diseño y
  pide redefinir o dividir la idea.

La solicitud final de confirmar el brief no cuenta como pregunta de entrevista. El agente no
conserva la conversación como transcripción.

## 3. MODO PROPOSAL

`business-analyst` redacta un brief inicial usando solo la solicitud y las referencias recibidas.
La propuesta separa de forma visible:

- **Hechos aportados:** información expresada por el usuario o una fuente identificada.
- **Supuestos:** interpretaciones provisionales que requieren confirmación.
- **Decisiones abiertas:** reglas, fórmulas, permisos, fuentes o límites todavía desconocidos.

Un supuesto nunca se presenta como hecho ni se convierte silenciosamente en requisito.

## 4. CONTRATO DEL BRIEF

Los dos modos producen el mismo `brief.md` normalizado. La sección `Intake` registra el modo,
estado `draft | confirmed`, actor y fecha de confirmación. El resto describe perfil, problema,
proceso actual, resultado, reglas y fuentes, permisos y sensibilidad, criterios, exclusiones,
restricciones, referencias, hechos, supuestos y decisiones abiertas.

Mientras existan decisiones que cambien el resultado, una fórmula, un permiso o el uso de datos, el
brief permanece `draft`. El agente presenta el brief completo para revisión y solicita confirmación
explícita; nunca se autoconfirma.

## 5. MINIMIZACIÓN Y SEGURIDAD

- Persiste solo el brief normalizado, nunca la transcripción cruda de la entrevista.
- No copia secretos, credenciales ni datos personales reales. Describe la sensibilidad mediante
  categorías como `público`, `interno`, `confidencial` o `PII`.
- No inventa reglas, fórmulas, permisos, fuentes ni responsables. Lo desconocido queda como decisión
  abierta.
- Usa ejemplos y datos sintéticos cuando sea necesario ilustrar un caso.
- Una confirmación valida la intención documentada; no autoriza acceso a sistemas o datos.

## 6. CONFIRMACIÓN Y HANDOFF

Solo una confirmación explícita del usuario permite cambiar la sección `Intake` a:

```text
- Estado: confirmed
- Confirmado por: <actor humano>
- Confirmado el: <fecha ISO-8601>
```

Antes de esos tres campos, el `orchestrator` no entrega el trabajo a `architect`. Si una corrección
posterior cambia intención, alcance, reglas, fórmulas, permisos o uso de datos, vuelve a `draft` y
requiere otra confirmación.

Confirmar el brief no es GATE 1: solo acepta que la intención está correctamente capturada. Después,
`architect` crea `spec.md` y el plan aplicable; el usuario los revisa por separado antes de que
`speckit approve` registre la aprobación del diseño.

Los briefs legacy que no contienen una sección `Intake` conservan el flujo anterior y no se migran
automáticamente. Cuando la sección existe, `sdd-specify` exige `Estado: confirmed`, actor y fecha.

## 7. RESPONSABILIDADES Y TRANSICIONES

| Rol | Recibe | Produce | No puede |
|-----|--------|---------|-----------|
| `orchestrator` | solicitud y estado real | selección de rol, orden y handoffs | inventar decisiones, confirmar o aprobar por el usuario, saltar gates |
| `business-analyst` | solicitud y modo | `brief.md` normalizado | diseñar arquitectura, escribir código o ejecutar gates |
| `architect` | brief confirmado | spec, plan, tasks y test plan | repetir el intake, implementar o autoaprobar |
| `implementer` | spec Ready y una tarea | código y evidencia GATE 3 | cambiar el contrato aprobado o revisar su propio cierre |
| `reviewer` | implementación y evidencia | hallazgos o cierre verificable | modificar código o dar por cumplido un AC sin evidencia |

Secuencia canónica:

```text
usuario → orchestrator → business-analyst → confirmación del brief
        → architect → aprobación GATE 1 → Ready GATE 2
        → implementer → evidencia GATE 3 → reviewer → cierre
```

El `orchestrator` sigue siendo el punto visible y verifica la precondición de cada handoff. No asume
la autoridad del rol que coordina ni sustituye las decisiones humanas.

## 8. HERRAMIENTAS CON Y SIN SUBAGENTES

- Con subagentes, el `orchestrator` les entrega el contenido de `.agents/roles/<rol>.md` y solo el
  contexto necesario. Revisa el resultado antes del siguiente handoff.
- Sin subagentes, el mismo agente activo ejecuta los roles secuencialmente. Antes de cada fase
  anuncia `Actuando como <rol>` y aplica sus límites de edición y decisión.
- Cambiar de rol no permite mezclar fases, conservar permisos del rol anterior ni omitir una
  confirmación, aprobación o gate.

## REGLA FINAL

> Elegir modo → facilitar intake → confirmar brief → diseñar → aprobar → planificar → implementar → revisar.
