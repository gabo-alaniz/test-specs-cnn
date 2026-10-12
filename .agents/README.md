# 🚀 KM AI Speckit

Repositorio **template** para trabajar con agentes de IA bajo **Spec-Driven Development (SDD)**. Clonas, y cualquier agente (Claude Code, Codex, OpenCode, Cursor, Copilot…) ya trae las reglas, el contrato de estado y los gates: sin configurar reglas, condicionales ni contratos en cada proyecto.

## 📁 Estructura

En la raíz solo queda lo que las herramientas exigen ahí; todo lo del template vive en `.agents/`.

```
AGENTS.md                  Constitución: fuente única de instrucciones del agente
README.md                  README del proyecto (el repo hijo lo reemplaza)
CLAUDE.md                  Solo importa AGENTS.md y las reglas (Claude Code no lee AGENTS.md)
speckit                    CLI: ciclo SDD, doctor y actualización del template
specs/                     Una carpeta por Spec: specs/001-login/ (cerradas: specs/.archive/)
.github/                   CI, formulario «Nueva spec» y la Action que abre el PR con el brief
.env.example               Variables base (USE_MOCKS)

.agents/README.md          Este documento (guía del template)
.agents/AGENT_PROMPT.md    Plan B: bootstrap para pegar en herramientas que no cargan AGENTS.md
.agents/rules/             Reglas núcleo (siempre activas)
.agents/rules/optional/    Reglas por tipo de proyecto: UI/UX, cloud, MCP de memoria
.agents/templates/         Plantillas: brief, spec, plan, tasks, test-plan, state.json, retro
.agents/skills/            Skills por fase: sdd-intake, sdd-specify, sdd-plan, sdd-implement, sdd-review
.agents/memory/            preferences.md y decisions.md: lo aprendido entre specs
.agents/project.json       Comandos del proyecto: test, lint, build, e2e
.agents/template-manifest.json    Inventario `template-owned`/`project-owned` y hashes de integridad
.agents/version.json       Fuente única de versión del template y schema
.agents/requirements-dev.txt      Lock reproducible para Python 3.9–3.13
.agents/roles/             Roles: orchestrator, business-analyst, architect, implementer, reviewer
.agents/schemas/           JSON Schema de state.json
.agents/examples/          Estados, una spec de referencia y el índice histórico consolidado
.agents/bin/               Motor (stdlib): speckit_cli.py y spec_validate.py
.agents/tests/             Tests del validador, del CLI, de los contratos del repo y un smoke E2E de un repo hijo
```

### Sin configuración por herramienta

El template no versiona `.claude/`, `.codex/`, `.opencode/` ni ninguna otra carpeta de herramienta: reglas, skills y roles son Markdown en `.agents/` y valen para cualquier agente. Cada herramienta usa su propio sandbox y modo de aprobación por defecto; las prohibiciones viven como reglas en `AGENTS.md` §G. Las carpetas locales que cree una herramienta están en `.gitignore`.

```text
proyecto/
├── .agents/      # Fuente única: motor, reglas, roles, skills y plantillas
├── .github/      # Ruta fija de GitHub
├── specs/        # Artefactos SDD del proyecto
├── AGENTS.md     # Lo leen Codex, OpenCode, Cursor, Copilot, Gemini…
├── CLAUDE.md     # Solo importa AGENTS.md para Claude Code
└── speckit
```

## 🏗️ Iniciar un proyecto

1. **Use this template → Create a new repository** en GitHub, y clónalo.
2. Abre tu agente en la raíz del repo. Carga `AGENTS.md` automáticamente:

   | Herramienta | Archivo que lee |
   |-------------|-----------------|
   | Codex, OpenCode, Cursor, Copilot, Gemini | `AGENTS.md` |
   | Claude Code | `CLAUDE.md` → `@AGENTS.md` |
   | Otras | Pega `.agents/AGENT_PROMPT.md` como primer mensaje |

3. Adapta el template a tu stack (una sola vez, antes del primer spec):
   - Crea `.venv` con `python3 -m venv .venv`, instala el lock con `.venv/bin/python -m pip install -r .agents/requirements-dev.txt` y completa `.agents/project.json`: los escenarios dirigen `task done`; `close` ejecuta test/lint/build/e2e globales.
   - Indica en **§J** qué reglas de `.agents/rules/optional/` aplican.
   - Añade reglas propias como `.agents/rules/stack-<tecnologia>.md`.
   - `cp .env.example .env`.
   - Reemplaza `README.md` por el de tu proyecto; esta guía sigue en `.agents/README.md`.
   - Ejecuta `./speckit doctor`; corrige cualquier `✗` antes del primer spec. `⚠` informa contexto Git sin hacer fallar el diagnóstico.

## 🔄 Flujo SDD

```
Intake → Spec → Plan → Tasks → Test Plan → Implement → Validate → Document
```

El agente activo es el `orchestrator`, el único punto visible de coordinación. En una idea nueva te
pide elegir uno de estos modos:

- `guided`: `business-analyst` hace una entrevista consolidada en lenguaje de negocio.
- `proposal`: el facilitator propone un brief y separa hechos, supuestos y decisiones abiertas.

Ambos terminan en el mismo `brief.md`. Tú corriges o confirmas ese brief; solo después pasa a
`architect`. Confirmar el brief no aprueba el diseño: `spec.md` y el plan todavía requieren GATE 1.
Si la herramienta no ofrece subagentes, el mismo agente anuncia y asume cada rol secuencialmente.

Para empezar un spec:

```bash
./speckit new login --size M     # crea specs/001-login/
# pídele al agente: "sigue sdd-intake con 001-login; prefiero guided"
# tras confirmar el brief, el orchestrator continúa con sdd-specify
```

O abre un issue con el formulario **Nueva spec**: la Action `spec-from-issue` crea `specs/NNN-<slug>/` con el brief relleno y abre un PR en borrador (sin LLM). Actívala en *Settings → Actions → General → Allow GitHub Actions to create and approve pull requests*. Como los eventos de `GITHUB_TOKEN` no disparan workflows, la Action lanza la CI sobre la rama del PR con `gh workflow run ci.yml`. Si defines el secret opcional `SPEC_BOT_TOKEN` (PAT fine-grained o token de GitHub App con `contents` y `pull-requests: write`), el push y el PR los hace ese token y la CI se dispara de forma normal.

La spec completa `.agents/examples/001-archive-specs/` muestra cómo queda cada artefacto al cerrar un ciclo.

Cada fase tiene su skill: `sdd-intake` → `sdd-specify` → `sdd-plan` → `sdd-implement` → `sdd-review`, en `.agents/skills/<nombre>/SKILL.md`. Pídele al agente que siga la skill de la fase; las herramientas que detectan `.agents/skills/` (Codex, OpenCode) también la ofrecen como comando.

| Size | Artefactos | Tareas |
|------|-----------|--------|
| S | `spec.md` (con notas técnicas y pruebas) y `tasks.md` | ≤ 3 |
| M | `spec.md`, `implementation-plan.md`, `tasks.md` y `test-plan.md` | ≤ 8 |
| L | Se divide en specs S o M | — |

| Gate | Antes de | Evidencia |
|------|----------|-----------|
| GATE 1 — Diseño | Tasks | El usuario aprueba hashes concretos de spec y plan (`state.json.approval`) |
| GATE 2 — Ready | Código | `speckit ready` valida estructura y trazabilidad, sin iniciar una tarea |
| GATE 3 — Evidencia | Task `[x]` | `task done` pasa escenarios asociados y registra cada `TC-NNN` |

Formato de tareas: `- [ ] TASK-001: descripción (AC-001)` (`[/]` en progreso, `[x]` hecha). Tras 3 fallos el spec queda `blocked`; otro intento requiere `resume` con actor y motivo.

## 🛠️ Comandos

```bash
./speckit new <slug> [--size S|M]       # nuevo spec desde las plantillas
./speckit status [<spec>]               # tabla: size, status, fase, tareas, aprobación, check
./speckit validate specs/001-login/     # una Spec (o --all)
./speckit design ready 001              # diseño completo → awaiting_approval
./speckit design revise 001 --by x --reason y  # invalida aprobación/Ready antes de implementar
./speckit approve 001 --by "<nombre>"   # GATE 1, tras la aprobación del usuario
./speckit ready 001                     # GATE 2, sin iniciar implementación
./speckit task start 001 TASK-001       # marca una única tarea [/]
./speckit task done 001 TASK-001        # GATE 3: escenarios dirigidos + evidencia por TC
./speckit resume 001 --by x --reason y  # autoriza otro intento tras tres FAIL
./speckit close 001 [--base main]       # test/lint/build/e2e, fingerprint, completed y retro
./speckit ci-guard --branch feat/001-login --base main  # rama + diff + spec + CLOSE
./speckit handoff 001 --note "..."      # resumen de sesión → .agents/SESSION_STATE.md
./speckit archive 001                   # spec completed → specs/.archive/
./speckit migrate [001] [--check]       # migra estados al schema vigente
./speckit report [--json]               # métricas por spec (incluye specs/.archive/)
./speckit worktree 001                  # ../<repo>-001-login en la rama feat/001-login
./speckit --version                     # versión del template y schema
./speckit doctor [--json]               # integridad/drift, entorno, specs y warnings Git
./speckit update <template-dir>         # preview: no escribe
./speckit update <template-dir> --apply # aplica cambios sin conflicto y crea backup
./speckit template export <destino>     # mantenedores: genera la proyección limpia de main
.venv/bin/python -S -m unittest discover -s .agents/tests -v  # fallback sin paquetes
.venv/bin/python -m unittest discover -s .agents/tests   # tests del validador y del CLI
```

`report` mide cada spec activo o archivado desde `created_at` hasta el evento `closed`, con duraciones de diseño, espera de aprobación, preparación Ready e implementación. También cuenta `FAIL`, eventos históricos de bloqueo y su duración. Estados legacy sin timestamps explícitos devuelven `null`; nunca se reconstruyen fechas desde Git o evidencia.

Si cambia contenido relevante después del cierre, vuelve a ejecutar `close` sobre el spec `completed`: repite los checks globales y añade un `CLOSE — PASS` con la huella vigente. CI siempre compara contra la última entrada.

Los comandos que cambian el estado lo validan después y, si el resultado no es válido, revierten el cambio.
Si el diseño aprobado cambia antes de iniciar una tarea, `design revise` conserva los artefactos,
registra actor y motivo, limpia la aprobación y obliga a repetir `design ready` y `approve`.

Soporta Python 3.9–3.13. Las dependencias de desarrollo están fijadas en `.agents/requirements-dev.txt` y se instalan solo dentro de `.venv`; en ejecución, `jsonschema` sigue siendo opcional y sin él se usa el validador mínimo de la stdlib.

## 🔄 Actualizar el template

Obtén una copia local de la nueva versión del template y previsualiza primero:

```bash
./speckit update ../km-ai-speckit-nuevo
./speckit update ../km-ai-speckit-nuevo --apply
```

`.agents/template-manifest.json` enumera todos los archivos núcleo. El updater solo toca entradas `template-owned`; `project-owned` (`project.json`, README, `.gitignore`, `.env.example`) se conserva. Un archivo del template que cambió respecto a su hash aparece como `conflict`; revísalo y confirma explícitamente con `--apply --yes`. Antes de escribir se crea un backup local en `.agents/backups/`, que no se borra automáticamente. Para revertir:

```bash
./speckit update --restore .agents/backups/<fecha>-<version>
./speckit doctor
```

Memoria, specs y reglas `stack-*.md` quedan fuera del manifiesto y nunca los toca el updater. `doctor` falla por cobertura incompleta, ausencia o drift de `template-owned`, pero solo avisa por rama/spec activo.

Si usas un proyecto como fuente de otro GitHub Template, genera su distribución en un destino que aún no
exista:

```bash
release_root="$(mktemp -d)"
./speckit template export "$release_root/main"
find "$release_root/main" -maxdepth 2 -type f | sort
```

La exportación falla si el manifiesto tiene drift, el destino ya existe o está dentro del checkout fuente.
Incluye memoria neutra y `specs/` vacío; nunca incluye specs de desarrollo.

El validador rechaza:
- artefactos marcados `true` que están vacíos o no existen;
- placeholders o secciones obligatorias sin completar;
- combinaciones incoherentes de status y phase;
- diseños que cambiaron después de su aprobación;
- fases que no tienen la aprobación previa;
- `[NEEDS CLARIFICATION]` sin resolver al aprobar;
- AC sin trazar a tasks o al test-plan;
- `size=L`;
- `tasks.md` sin tareas `TASK-NNN`;
- `completed` con tareas abiertas;
- `spec_name` distinto del directorio;
- tareas `[x]` sin su entrada `PASS` en `evidence.md`.
- specs `completed` sin `CLOSE — PASS`; `validate --all` también revisa `.archive/`.

Avisa cuando hay más tareas de las que admite el tamaño.

## 🤖 Roles y permisos

Roles: `orchestrator` coordina los handoffs; `business-analyst` conduce el intake y solo edita el
brief; `architect` diseña; `implementer` ejecuta tareas; y `reviewer` valida evidencia y cierre. Sus
contratos viven en `.agents/roles/*.md` y la secuencia normativa en
`.agents/rules/intake-orchestration.md`. Para delegar, pasa al subagente el contenido del rol; sin
subagentes, el agente activo los ejecuta uno a uno sin mezclar permisos.

Los permisos son reglas de texto en `AGENTS.md` §G (prohibido, preguntar antes, permitido). El template no instala hooks, sandbox ni perfiles de permisos: cada persona usa el modo de aprobación de su herramienta. La CI (`validate --all`, tests y Gitleaks) es la red de seguridad común a todos los agentes.

### Migrar desde 0.1.x

La 0.1.x generaba configuración por herramienta. Tras `./speckit update <seed> --apply`, retira lo que ya no se usa:

```bash
git rm -r --ignore-unmatch .claude .codex .opencode .agents/permissions.json .agents/generated-manifest.json
```

y elimina `"tools"` de `.agents/project.json`.

## ✅ CI

`.github/workflows/ci.yml` usa `.venv`, prueba Python 3.9 y 3.13 con dependencias y con fallback stdlib, valida sintaxis, contratos, ejemplos y specs, y escanea secretos. Todas las Actions externas están fijadas a SHA completo. El workflow principal solo tiene `contents: read`; el job aislado de Issue→spec conserva los permisos de escritura mínimos y serializa globalmente la asignación de IDs con reintentos sin force-push.
