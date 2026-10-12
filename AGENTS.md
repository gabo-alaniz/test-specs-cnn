# AGENTS.md — Constitución del agente

Esta es la fuente única de instrucciones para cualquier agente (Claude Code, Codex, OpenCode, Cursor, Copilot, Gemini…). No hay configuración por herramienta: el `CLAUDE.md` de la raíz solo la importa, porque Claude Code no lee `AGENTS.md`. Los repos hijo la extienden con archivos en `.agents/rules/`, sin contradecirla.

**Antes de actuar, lee y obedece estas reglas siempre activas:** `.agents/rules/backend-security.md`, `.agents/rules/core-constitution.md`, `.agents/rules/framework-stack.md`, `.agents/rules/intake-orchestration.md`, `.agents/rules/progress-continuity.md`, `.agents/rules/speckit-methodology.md` y `.agents/rules/testing-standards.md`.

## A. Integridad
- Si un requerimiento es ambiguo o está incompleto, pregunta antes de escribir código. No inventes requisitos, flujos ni "mejoras" no pedidas.
- Trabaja solo dentro del alcance del spec activo.
- Si dos reglas entran en conflicto, aplica la precedencia de `.agents/rules/core-constitution.md`. Si son del mismo nivel, señálalo y espera una decisión.

## B. Contexto
- Si hay un MCP de memoria, úsalo (`.agents/rules/optional/memory-context-rules.md`). Si no, haz búsquedas dirigidas y lee solo lo necesario; no escanees el repo completo.
- Al empezar, lee `.agents/memory/preferences.md` y `decisions.md`, y aplícalos.
- Al cerrar una tarea, registra los componentes compartidos nuevos, los cambios de esquema y las decisiones (en el MCP, en `implementation-plan.md`, en un ADR o en `.agents/memory/decisions.md`). Cuando el usuario corrija tu forma de trabajar, añádelo a `preferences.md`.

## C. Comunicación
- Responde de forma técnica y directa, sin relleno.
- Cuando modifiques un archivo, muestra el diff o el fragmento afectado, no el archivo completo.

## D. Flujo SDD
`Intake → Spec → Plan → Tasks → Test Plan → Implement → Validate → Document`

0. El agente activo es `orchestrator`. Ante una idea nueva, el usuario elige `guided` o `proposal` y `business-analyst` sigue `sdd-intake` para normalizar `brief.md`. Solo tras la confirmación explícita del brief hace handoff a `architect`; esta confirmación no es GATE 1. Véase `.agents/rules/intake-orchestration.md`.
1. Cada spec vive en `specs/<NNN>-<nombre>/` y se crea con `./speckit new <nombre> --size S|M` (o desde un issue con el formulario «Nueva spec»). `architect` convierte el brief confirmado en diseño; no repite el intake y agrupa en una sola ronda solo las aclaraciones técnicas bloqueantes.
2. Elige el tamaño en `state.json.size`:

| Size | Artefactos | Tareas |
|------|-----------|--------|
| S | `spec.md` (incluye notas técnicas y pruebas) y `tasks.md` | ≤ 3 |
| M | `spec.md`, `implementation-plan.md`, `tasks.md` y `test-plan.md` | ≤ 8 |
| L | No se implementa: divídelo en specs S o M | — |

3. `state.json` sigue el schema `.agents/schemas/spec-state.schema.json` y refleja el estado real, no el deseado.

| Gate | Antes de | Evidencia |
|------|----------|-----------|
| GATE 1 — Diseño aprobado | Escribir las tasks | El usuario aprueba spec y plan juntos; `state.json.approval` guarda actor, fecha y hashes del diseño |
| GATE 2 — Ready | Escribir código | `speckit ready` deja `status=ready`, sin tarea activa; cada AC está trazado a una tarea y escenario estructurado |
| GATE 3 — Evidencia | Marcar `[x]` | `task done` ejecuta los escenarios asociados a los AC de la tarea y registra evidencia individual por `TC-NNN` |

4. Los cambios de estado los hace el CLI (`./speckit <cmd>`), que valida y revierte si el resultado es inválido:

| Paso | Comando |
|------|---------|
| Diseño listo | `design ready <spec>` → `awaiting_approval` (nunca edites el estado a mano) |
| Revisar diseño | `design revise <spec> --by <nombre> --reason <motivo>` invalida aprobación y Ready solo antes de implementar; después repite `design ready` |
| GATE 1 | `approve <spec> --by <nombre>`, **solo tras la aprobación explícita del usuario** |
| GATE 2 | `ready <spec>` valida planificación sin iniciar implementación |
| Implementar | `task start <spec> TASK-NNN` es la única vía que marca `[/]` |
| GATE 3 | `task done <spec> TASK-NNN`. Nunca marques `[x]` a mano |
| Reanudar bloqueo | `resume <spec> --by <nombre> --reason <motivo>`; conserva todos los `FAIL` |
| Cierre | `close <spec> [--base <ref>]` ejecuta checks globales, graba el fingerprint, completa `retro.md` y lleva lo aprendido a `.agents/memory/` |
| Fin de sesión | `handoff <spec>` → `.agents/SESSION_STATE.md` |
| Después del cierre | Completa `retro.md`; `archive <spec>` valida cierre y retro antes de mover a `specs/.archive/` |
| Migrar estados | `migrate [<spec>] [--check]` actualiza `state.json` al schema vigente |
| Métricas | `report [--json]`: creación→cierre, duración por gate, tareas, `FAIL` y bloqueos históricos |
| CI | `ci-guard --branch feat/<spec> [--base <ref>]` vincula rama, diff, spec y fingerprint de CLOSE |

- `status` muestra el estado de todos los specs y `validate` el detalle. Si falla, corrige el spec antes de seguir.
- Skills con cada fase: `sdd-intake`, `sdd-specify`, `sdd-plan`, `sdd-implement`, `sdd-review`. Son Markdown en `.agents/skills/<nombre>/SKILL.md`: cuando el usuario pida una fase, lee y sigue el `SKILL.md` correspondiente (las herramientas que detectan `.agents/skills/` las ofrecen además como comando).
- Los checklists de cada gate están en `.agents/rules/progress-continuity.md`. Ejemplo completo de un ciclo: `.agents/examples/001-archive-specs/`.
- Roles (`.agents/roles/*.md`): `orchestrator` coordina y aplica handoffs; `business-analyst` entrevista y solo normaliza `brief.md`; `architect` diseña y solo edita `specs/**`; `implementer` ejecuta las tareas; `reviewer` revisa y solo edita `specs/**`. Si delegas en un subagente, pásale el contenido del rol como instrucciones. Sin subagentes, el agente activo anuncia y ejecuta cada rol secuencialmente sin mezclar permisos.
- Para trabajar varios specs en paralelo: `worktree <spec>` crea `../<repo>-<spec>` en la rama `feat/<spec>`.

## E. Datos
- Los esquemas de DB solo cambian mediante una migración explícita y documentada.
- El acceso a datos va detrás de repositorios o inyección de dependencias. El cambio entre mocks y producción depende solo de `USE_MOCKS=true|false`.

## F. QA y límites
- Ejecuta tú las pruebas con el comando de §K; no se las pidas al usuario.
- Si fallan, lee el log y corrige la causa raíz: el código, no el test, salvo que el test esté mal.
- **Presupuesto: 3 intentos por fallo.** `task done` cuenta los `FAIL` de `evidence.md` y al tercero pone `status: "blocked"`. No hay cuarto intento sin `resume` explícito; detente y explica qué probaste.
- Usa el framework de pruebas que ya tiene el proyecto; no añadas otro (`.agents/rules/testing-standards.md`).

## G. Permisos, dependencias y Git
- Los permisos son estas reglas; el sandbox y los modos de aprobación son los de cada herramienta, sin configuración del template.
  - **Prohibido:** leer o editar `.env` y `.env.*` (salvo `.env.example`); `git push --force`/`-f`, `git reset --hard`, `git clean`, `rm -rf` y `sudo`.
  - **Pregunta antes:** editar `AGENTS.md`, `.agents/**` o `.github/**`; `git push`, `git merge`, `git rebase`; instalar dependencias (`npm install`, `pnpm add`, `yarn add`, `pip install`, `uv add`) y `docker`.
  - **Permitido:** leer el repo; editar `src/**`, `tests/**` y `specs/**`; `./speckit *`, los comandos de §K y `git status|diff|log|add|commit|switch`.
- No termines una sesión con `./speckit validate --all` en rojo.
- No crees configuración propia de una herramienta (`.claude/`, `.codex/`, `.opencode/`, `.cursor/`…) en el repo; las preferencias locales de cada persona no se versionan.
- No instales ni declares dependencias sin la aprobación del usuario.
- Trabaja en la rama `feat/<NNN>-<nombre>` y usa Conventional Commits con el Task ID (`feat(TASK-014): ...`). No hagas commits directos a `main`.

## H. Código
- Tipado end-to-end: nada de `any`, `@ts-ignore` ni `# type: ignore` sin justificar.
- Usa las APIs oficiales y no deprecadas de la versión instalada, y no recrees lo que el framework ya ofrece (`.agents/rules/framework-stack.md`).

## I. Seguridad y revisión
- No dejes logs de depuración en producción y nunca registres PII ni secretos (`.agents/rules/backend-security.md`).
- Antes de entregar, revisa que no haya vulnerabilidades ni duplicación, que se respete el spec o el mockup y que el tipado sea correcto.

## J. Reglas por stack
Las reglas de `.agents/rules/*.md` están siempre activas. Las opcionales están en `.agents/rules/optional/`; el repo hijo marca las que aplican:

| Regla | Activar cuando | Activa |
|-------|----------------|--------|
| `ui-ux-design-rules.md` | El proyecto tiene UI (el mockup manda y el Design System es la única fuente) | no |
| `backend-cloud-rules.md` | Hay un backend desplegado en cloud | no |
| `memory-context-rules.md` | Se usa un MCP de memoria | no |

Las reglas propias del stack van en `.agents/rules/stack-<tecnologia>.md`.

## K. Comandos del proyecto
Cada escenario automático declara su comando en `test-plan.md` (o `spec.md ## Pruebas` en size S); `task done` ejecuta solo los escenarios de la tarea, deduplica comandos idénticos y registra cada `TC-NNN`. Los escenarios manuales requieren `--manual-evidence`. Los checks globales de `.agents/project.json` (`test`, `lint`, `build`, `e2e`) se ejecutan todos en `close`; `commands.test` es obligatorio. Python se ejecuta dentro de `.venv`. Ejemplo de E2E en `.agents/examples/node-cypress/`.
