# CORE CONSTITUTION
# Propósito: Mapa de precedencia e integración de todas las reglas.
# No duplica AGENTS.md — lo complementa con el sistema de precedencia y el flujo canónico.

## 1. PRECEDENCIA DE REGLAS

Las reglas se interpretan en este orden. Una regla de nivel superior siempre gana; una especificación funcional define el qué, pero no puede invalidar las restricciones obligatorias de la Constitución ni de seguridad.

```
1. Constitución Core                  (límites no negociables)
2. Reglas de seguridad               (precondición de toda implementación)
3. Especificación funcional aprobada  (qué debe hacer el sistema dentro de esos límites)
4. Reglas de arquitectura y stack    (cómo se construye)
5. Reglas UI/UX                      (cómo se presenta)
6. Estándares de testing             (cómo se valida)
7. Convenciones existentes del repo  (cómo se mantiene consistencia)
8. Guidelines y recomendaciones      (preferencias, no obligaciones)
```

Una guideline nunca puede invalidar una rule.

Si dos reglas del mismo nivel entran en conflicto → el agente señala el conflicto y espera decisión. No resuelve silenciosamente. Si una Spec contradice una restricción Core o de seguridad, se debe corregir la Spec o aprobar una excepción explícita documentada antes de implementar.

## 2. JERARQUÍA DE ARCHIVOS DE REGLAS

```
AGENTS.md                       ← Constitución Core (CLAUDE.md solo la importa)
.agents/rules/                  ← Núcleo: siempre activas
  core-constitution.md          ← Este archivo: precedencia y flujo
.agents/templates/              ← Plantillas: brief, spec, plan, tasks, test-plan, state.json
  speckit-methodology.md        ← Metodología Speckit detallada
  progress-continuity.md        ← Evidencia obligatoria y puertas de aceptación (fuente única de gates)
  testing-standards.md          ← Estándares de pruebas
  backend-security.md           ← Seguridad y datos
  framework-stack.md            ← Reglas de stack y arquitectura
.agents/rules/optional/         ← Se activan según el proyecto (AGENTS.md §J)
  ui-ux-design-rules.md         ← Mockup como ley y Design System
  backend-cloud-rules.md        ← Arquitectura stateless y cloud
  memory-context-rules.md       ← Protocolo MCP de memoria
```

Los repos hijo añaden sus propias reglas en `.agents/rules/` (ej. `stack-<tecnologia>.md`). No sobreescriben archivos Core — los extienden con nuevos archivos.

## 3. FLUJO CANÓNICO DE IMPLEMENTACIÓN

Antes de entrar al flujo, `orchestrator` clasifica la solicitud según
`intake-orchestration.md`. Una solicitud que cumple todos los criterios de vía rápida y ninguna
exclusión queda fuera del ciclo SDD: el agente anuncia la clasificación, permite que el usuario exija
SDD, implementa el cambio acotado y reporta archivos y validaciones reales. La vía rápida no elimina
seguridad, permisos, reglas de stack, Git ni testing.

Para cualquier solicitud no elegible, dudosa o dirigida por el usuario a SDD, el flujo canónico es:

```
① Verificar estado de sesión: leer state.json + tasks.md (progress-continuity.md §1)
② Descubrimiento dirigido: MCP si existe, si no búsqueda local (AGENTS.md §B)
③ Verificar que el estado reportado es consistente con el código real
④ Leer spec aprobada y criterios de aceptación (speckit-methodology.md)
⑤ Verificar stack y dependencias antes de implementar (framework-stack.md)
⑥ Implementar con seguridad como precondición (backend-security.md)
⑦ Respetar Design System si hay UI (optional/ui-ux-design-rules.md)
⑧ Ejecutar validación — GATE 3 con `./speckit task done`, nunca [x] a mano (testing-standards.md)
⑨ Registrar cambios estructurales (MCP, plan o ADR)
⑩ Actualizar state.json con evidencia real
⑪ Ejecutar `./speckit handoff` al cerrar (progress-continuity.md §5)
```

Una vez seleccionada la ruta SDD, ninguna fase puede omitirse ni darse por completada sin evidencia.
La evidencia es el único criterio válido para avanzar entre fases.

## 4. SEÑAL DE ALERTA: CONFLICTO DE REGLAS

Si el agente detecta que una decisión viola una regla de nivel superior:

```
→ DETENER implementación
→ Documentar el conflicto explícitamente
→ Proponer opciones si existen
→ Esperar decisión del usuario
→ Registrar la resolución (MCP, plan o ADR)
```

## REGLA FINAL

> Clasificar → vía rápida verificable o Spec → Plan → Tasks → Test Plan → Implement → Validate → Document.

En SDD ningún paso puede omitirse. En vía rápida la validación proporcional y su reporte siguen
siendo obligatorios.
