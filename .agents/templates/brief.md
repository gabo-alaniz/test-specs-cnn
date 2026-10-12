# Brief: <nombre de la idea>

> Lo normaliza `business-analyst` mediante `sdd-intake`. El usuario elige el modo y confirma el
> resultado antes de `sdd-specify`. Si algo cambia reglas, fórmulas, permisos o datos y no se conoce,
> queda como decisión abierta; no lo inventes.

## 1. Intake
- Modo: pendiente (elegir `guided` o `proposal`)
- Estado: draft
- Confirmado por: pendiente
- Confirmado el: pendiente

## 2. Usuario
¿Quién lo usa? Indica también quién solicita la solución y quién resulta afectado. Usa roles, no PII.

## 3. Problema
¿Qué falla hoy y por qué importa? (1-3 frases)

## 4. Proceso actual
¿Cómo se realiza hoy, con qué frecuencia, volumen, entradas, salidas y excepciones?

## 5. Resultado esperado
¿Qué cambia cuando esto existe? ¿Qué métrica u observable demuestra que funcionó?

## 6. Reglas de negocio y fuentes
Reglas, fórmulas, excepciones, origen de datos y responsable. Lo no confirmado queda abierto.

## 7. Permisos y sensibilidad
¿Quién puede ver o modificar el resultado? Clasifica los datos: público, interno, confidencial o PII.

## 8. Criterios de aceptación
Uno por comportamiento observable, en formato Dado / Cuando / Entonces.
- AC-001: Dado <contexto>, cuando <acción>, entonces <resultado observable>.

## 9. Fuera de alcance
- <lo que explícitamente NO se hace>

## 10. Restricciones y riesgos
Restricciones de stack, plazo, rendimiento, seguridad, legales o de adopción.

## 11. Referencias
Mockups, enlaces, ejemplos y specs relacionados.

## 12. Hechos aportados
- Información confirmada por el usuario o por una fuente identificada.

## 13. Supuestos
- Interpretaciones provisionales que requieren confirmación.

## 14. Decisiones abiertas
- [NEEDS CLARIFICATION: pregunta que cambia resultado, fórmula, permiso o uso de datos]
