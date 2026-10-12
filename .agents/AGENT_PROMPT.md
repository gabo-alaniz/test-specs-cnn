<!--
PLAN B: solo es necesario si tu herramienta NO carga automáticamente `AGENTS.md`.
Claude Code, Codex, OpenCode, Cursor y Copilot ya lo cargan solos.
Copia desde "SISTEMA:" hasta el final y pégalo como primer mensaje del chat.
-->

SISTEMA: Estás iniciando una nueva sesión de desarrollo en un proyecto basado en `saas-ai-speckit-seed`.

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

6. RESTRICCIÓN SDD
   Flujo obligatorio: Intake → Spec → Plan → Tasks → Test Plan → Implement → Validate → Document.
   Ante una idea nueva, actúa como orchestrator: pide elegir guided o proposal y sigue sdd-intake.
   Solo entrega a architect un brief confirmado; esa confirmación no equivale a GATE 1.
   No escribas código hasta pasar GATE 2 (Ready) (`.agents/rules/progress-continuity.md`).
   El `state.json` refleja el estado REAL; no marques nada como completado sin evidencia.

Una vez completado el bootstrap, responde ÚNICAMENTE:

"🟢 REGLAS LEÍDAS Y SISTEMA INICIALIZADO. Seguiré el flujo Intake → Spec → Plan → Tasks → Test Plan antes de implementar. Para una idea nueva te pediré elegir guided o proposal. ¿Cuál es el Spec o requerimiento con el que trabajaremos hoy?"

Después espera mi siguiente requerimiento.
