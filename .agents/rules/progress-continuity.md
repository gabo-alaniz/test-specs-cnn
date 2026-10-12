# PROGRESS CONTINUITY & ACCEPTANCE GATES
# Propósito: Garantizar que el progreso reportado es real y verificable.
# Impedir que el agente avance entre fases sin evidencia de cumplimiento.
# Aplicable a cualquier sesión, nueva o de continuación.

## PRINCIPIO FUNDAMENTAL

> El agente no avanza a la siguiente fase sin evidencia demostrable de que la fase actual fue completada.
> Una afirmación de "completado" sin evidencia es equivalente a no completado.

---

## 1. INICIO DE SESIÓN — PROTOCOLO DE RECUPERACIÓN

**ANTES de escribir cualquier código en una sesión nueva**, el agente ejecuta este protocolo:

```
① Leer state.json del Spec activo
② Leer tasks.md y ubicar la última tarea marcada como [x] o [/]
③ Descubrimiento dirigido: MCP si existe, si no búsqueda local (arquitectura, componentes, decisiones)
④ Verificar que el estado reportado es consistente con el código real
⑤ Solo entonces continuar desde el punto correcto
```

**Prohibido** asumir que el estado reportado en `state.json` o `tasks.md` es correcto sin verificación.
Si hay inconsistencia → reportarla al usuario antes de continuar.

### Señales de inconsistencia a detectar:
- `tasks.md` marca `[x]` pero el código no existe o no compila
- `state.json` reporta un artefacto como `true` pero el archivo está vacío o incompleto
- La última tarea "completada" no tiene evidencia asociada (tests pasando, build limpio, etc.)
- El MCP (si se usa) no tiene registrado un componente que `tasks.md` dice haber creado

---

## 2. PUERTAS DE ACEPTACIÓN (ACCEPTANCE GATES)

Cada transición entre fases del Speckit requiere pasar una puerta de aceptación explícita.
**El agente no puede abrir la siguiente puerta sin cerrar la anterior.**

```
┌─────────────────────────────────────────────────────────┐
│  SPEC + PLAN   →  GATE 1  →  TASKS + TEST PLAN          │
│  TASKS         →  GATE 2  →  IMPLEMENTACIÓN             │
│  TASK          →  GATE 3  →  [x] COMPLETADA             │
└─────────────────────────────────────────────────────────┘
```

### GATE 1 — Diseño aprobado (antes de generar Tasks)
Una sola aprobación para spec y plan juntos (en size S, solo `spec.md`). Evidencia requerida:
- [ ] `spec.md` contiene criterios `AC-NNN` verificables (Dado / Cuando / Entonces) y el alcance, con lo que incluye y lo que excluye
- [ ] En size M, `implementation-plan.md` documenta componentes, decisiones y riesgos con su mitigación
- [ ] No queda ningún `[NEEDS CLARIFICATION]` (lo comprueba el validador)
- [ ] El usuario aprobó de forma explícita y quedó registrado en `state.json.approval` (`{"by", "at"}`)

Si el diseño cambia antes de iniciar implementación, `design revise --by --reason` invalida esta
evidencia de forma auditada; se repiten `design ready` y la aprobación con hashes nuevos.

### GATE 2 — Ready (antes de escribir código)
Evidencia requerida:
- [ ] `tasks.md` tiene Task IDs estables y, en size M, existe `test-plan.md`
- [ ] Cada `AC-NNN` está en al menos una tarea y, en size M, en un escenario de `test-plan.md`
- [ ] `./speckit validate specs/<id>-<nombre>/` termina en verde (comprueba todo lo anterior)
- [ ] `./speckit ready <spec>` deja `status=ready`, `phase=ready` y `current_task=null`; solo después `task start` inicia implementación

### GATE 3 — Task completada (antes de marcar `[x]`)
**Este es el gate más crítico.** Evidencia requerida:

- [ ] El código implementado existe y compila/transpila sin errores
- [ ] Los tests definidos en `test-plan.md` para esta Task fueron ejecutados
- [ ] Todos los escenarios asociados pasan (exit code = 0) y cada `TC-NNN` tiene resultado y output propio
- [ ] Los criterios de aceptación del Spec cubiertos por esta Task son verificables en el output
- [ ] `state.json` fue actualizado reflejando el progreso real
- [ ] `./speckit task done <spec> TASK-NNN` pasó y dejó `## TASK-NNN — PASS` en `evidence.md` (el validador rechaza un `[x]` sin esa entrada)
- [ ] La evidencia identifica el commit y el árbol o hash del diff probado; los escenarios manuales incluyen `--manual-evidence`

Los checks globales `test`, `lint`, `build` y `e2e` de `.agents/project.json` se reservan para `close`, que además graba el fingerprint canónico que CI compara con rama y diff.

**Si alguno de estos puntos no se puede verificar → la Task permanece en `[/]` (en progreso).**

---

## 3. PROHIBICIÓN DEL "DONE FALSO"

Las siguientes acciones son **fallos críticos que requieren autocorrección inmediata**:

- Marcar `[x]` en `tasks.md` sin haber ejecutado los tests correspondientes
- Reportar "implementación completada" sin evidencia de que el código funciona
- Actualizar `state.json` con `true` en un artefacto cuyo archivo no existe o está vacío
- Afirmar que un criterio de aceptación fue cumplido sin demostrarlo
- Avanzar al siguiente Task mientras el actual tiene tests fallando
- Asumir que algo que funcionaba antes sigue funcionando sin re-verificarlo

**Si el agente no puede ejecutar la validación en la sesión actual** (sin acceso al entorno, sin servidor, etc.):
```
→ Documentar explícitamente qué validación no pudo ejecutarse y por qué
→ Mantener la Task en [/] (en progreso)
→ No marcar como [x]
→ Indicar al usuario qué debe verificarse antes de continuar
```

---

## 4. EVIDENCIA REQUERIDA POR TIPO DE TAREA

| Tipo de Task | Evidencia mínima requerida |
|---|---|
| Creación de componente UI | Render sin errores + checklist de fidelidad al mockup completado |
| Endpoint de API | Tests de integración pasando + respuesta observable |
| Migración de BD | Migración ejecutada + schema verificado en DB |
| Refactor | Tests existentes pasando + sin regresiones |
| Configuración | Aplicación arranca + feature funciona end-to-end |
| Feature completa | Todos los criterios de aceptación del Spec verificados |

---

## 5. CONTINUIDAD ENTRE SESIONES

### Al CERRAR una sesión
Antes de terminar cualquier sesión de trabajo:

```bash
./speckit handoff <spec> --note "<deuda técnica, decisiones o contexto no obvio>"
```

El resumen se genera a partir del estado real: tareas, última evidencia, bloqueo, validación y siguiente paso. En `--note` va solo lo que no está en los archivos.

### Al INICIAR una sesión de continuación
El agente **DEBE** leer `AGENTS.md` (la mayoría de herramientas lo cargan solas; si no, pegar `AGENT_PROMPT.md`) y `.agents/SESSION_STATE.md` si existe.
No continuar desde memoria de la sesión anterior — verificar siempre el estado real.

### Formato del SESSION_STATE.md
Generado por `speckit handoff` (ignorado por git). Contiene tamaño, estado, fase, aprobación, tarea actual, bloqueo, resultado del validador, lista de tareas, últimas entradas de `evidence.md`, siguiente paso y la nota opcional.

---

## 6. MULTI-SPEC: CUÁNDO PAUSAR UN SPEC

Si durante la implementación de un Spec se descubre que se requiere trabajo en otro Spec:

```
→ NO comenzar el nuevo Spec silenciosamente
→ Documentar el bloqueo en state.json (status: "blocked", blocked_reason: "<descripción>")
→ Notificar al usuario con opciones: pausar, priorizar, o descartarlo
→ Esperar decisión antes de cambiar de Spec activo
```

No trabajar en dos Specs simultáneamente sin que el usuario lo haya decidido explícitamente.

---

## 7. CRITERIOS DE ACEPTACIÓN — CONTRATO IROMPIBLE

Los criterios de aceptación del `spec.md` son el contrato final:

- Se definen **antes** de implementar
- No se modifican durante la implementación para que sean más fáciles de cumplir
- Si la implementación revela que un criterio es técnicamente inviable → reportar al usuario, documentar la decisión, y actualizar el Spec con aprobación explícita
- **Prohibido** silenciosamente omitir criterios de aceptación porque son difíciles de implementar

### Trazabilidad Spec → Task → Evidencia

Cada criterio de aceptación del Spec debe poder trazarse a:
1. Una o más Tasks en `tasks.md`
2. Un escenario en `test-plan.md`
3. Evidencia de ejecución (log, screenshot, salida de comando)

Si un criterio de aceptación no tiene Task ni escenario de test, el Spec está incompleto y hay que corregirlo antes de implementar. El validador rechaza la fase `implementation` cuando falta la trazabilidad de los puntos 1 y 2.

---

## PROHIBICIONES

- Marcar `[x]` sin evidencia verificable
- Avanzar a la siguiente Gate sin cerrar la anterior
- Modificar criterios de aceptación para hacerlos más fáciles de cumplir
- Iniciar una sesión asumiendo que el estado reportado es correcto sin verificar
- Trabajar en múltiples Specs simultáneamente sin decisión explícita del usuario
- Afirmar que los tests pasan sin haberlos ejecutado en esta sesión
- Actualizar `state.json` con información que no corresponde al estado real del código

## REGLA FINAL

> Todo avance requiere evidencia. Sin evidencia, no hay avance.
> El estado reportado debe ser idéntico al estado real del código en el repositorio.
