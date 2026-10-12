# Proyecto

> Creado desde el template **KM AI Speckit**. Reemplaza este README por el de tu proyecto; la guía del template está en [`.agents/README.md`](.agents/README.md).

Desarrollo guiado por specs (SDD) con cualquier agente: Claude Code, Codex, OpenCode, Cursor o Copilot. Las instrucciones del agente están en [`AGENTS.md`](AGENTS.md).

## Estructura

No hay configuración por herramienta: cualquier agente lee las mismas reglas.

```text
proyecto/
├── .agents/      # Fuente única: reglas, skills, roles, plantillas y motor de speckit
├── .github/      # Workflows e integración con GitHub
├── specs/        # Diseños, tareas y evidencia del proyecto
├── AGENTS.md     # Instrucciones del agente (Codex, OpenCode, Cursor, Copilot, Gemini…)
├── CLAUDE.md     # Solo importa AGENTS.md: Claude Code no lee AGENTS.md
└── speckit       # CLI del ciclo SDD
```

Las skills (`.agents/skills/*/SKILL.md`) y los roles (`.agents/roles/*.md`) son Markdown: pídele al agente que siga la skill de cada fase. Los permisos son reglas de texto en `AGENTS.md` §G; cada herramienta usa su propio sandbox y modo de aprobación, y sus carpetas locales (`.claude/`, `.codex/`, `.opencode/`…) no se versionan.

## Preparación

Completa la preparación antes de crear el primer spec:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r .agents/requirements-dev.txt
./speckit doctor
```

Completa los checks globales de test, lint, build y E2E en `.agents/project.json`; los comandos dirigidos viven en el plan de pruebas. Nada se instala en el Python global. `doctor` puede mostrar warnings Git, pero no errores.

## Primer spec

```bash
./speckit new login --size M     # crea specs/001-login/
# describe la idea en specs/001-login/brief.md y pídele al agente: "sigue la skill sdd-specify con 001-login"
./speckit status                 # estado de todos los specs
./speckit report                 # creación→cierre, gates, tareas, FAIL y bloqueos históricos
```

La guía técnica y de actualización segura del template está en [`.agents/README.md`](.agents/README.md).
