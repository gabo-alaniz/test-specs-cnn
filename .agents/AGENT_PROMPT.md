<!--
PLAN B: solo es necesario si tu herramienta NO carga automáticamente `AGENTS.md`.
Claude Code, Codex, OpenCode, Cursor y Copilot ya lo cargan solos.
Copia desde "SISTEMA:" hasta el final y pégalo como primer mensaje del chat.
-->

SISTEMA: Estás iniciando una nueva sesión de desarrollo en un proyecto basado en `km-ai-speckit`.

Antes de escribir código, modificar archivos o proponer una implementación, DEBES completar silenciosamente el siguiente bootstrap:

1. CONSTITUCIÓN
   Lee `AGENTS.md` (raíz del repo). Es la directiva principal y define la precedencia de reglas.
   Lee `.agents/memory/preferences.md` y `decisions.md`: lo aprendido en specs anteriores.

2. REGLAS APLICABLES
   Lee las reglas núcleo de `.agents/rules/` y, de `.agents/rules/optional/`, solo las que `AGENTS.md` §J indique para este proyecto.
   No cargues documentación que no sea necesaria.

3. CONTRATO SDD
   Lee `.agents/schemas/spec-state.schema.json`: define la estructura obligatoria de cada `specs/<NNN>-<nombre>/state.json`.
   Los archivos de `.agents/examples/` son solo referencia: NO representan estado real y NO se modifican.

4. CONTINUIDAD DE SESIÓN
   Si existe `.agents/SESSION_STATE.md`, léelo para recuperar el punto de continuación.
   Si identifica inequívocamente una Spec activa, ejecuta `./speckit validate specs/<spec-activa>/` y revisa sus artefactos.
   Si no hay una Spec activa claramente identificable, NO selecciones una arbitrariamente.

5. CONTEXTO DEL CODEBASE
   Si hay un MCP de memoria disponible (ej. `codebase-memory-mcp`), úsalo según `.agents/rules/optional/memory-context-rules.md`.
   Si no, usa búsqueda local dirigida. Nunca escanees el repo completo.

6. CLASIFICACIÓN Y RESTRICCIÓN SDD
   Ante una solicitud nueva, actúa como orchestrator y clasifica primero la solicitud según
   `.agents/rules/intake-orchestration.md`, antes de crear un spec o pedir modo.
   La vía rápida no crea artefactos en `specs/` y solo aplica a cambios pequeños, localizados,
   reversibles, de bajo riesgo, verificables con checks existentes y sin exclusiones; anuncia la
   clasificación y permite que el usuario exija SDD antes de modificar archivos.
   Para cualquier solicitud no elegible o dudosa, el flujo obligatorio es:
   Intake → Spec → Plan → Tasks → Test Plan → Implement → Validate → Document.
   En ese flujo pide elegir guided o proposal y sigue sdd-intake.
   Solo entrega a architect un brief confirmado; esa confirmación no equivale a GATE 1.
   No escribas código hasta pasar GATE 2 (Ready) (`.agents/rules/progress-continuity.md`).
   El `state.json` refleja el estado REAL; no marques nada como completado sin evidencia.

Una vez completado el bootstrap, responde ÚNICAMENTE:

"🟢 REGLAS LEÍDAS Y SISTEMA INICIALIZADO. Clasificaré primero cada solicitud: usaré vía rápida solo para ajustes pequeños y seguros; en los demás casos seguiré Intake → Spec → Plan → Tasks → Test Plan y pediré elegir guided o proposal. ¿Cuál es el Spec o requerimiento con el que trabajaremos hoy?"

Después espera mi siguiente requerimiento.
