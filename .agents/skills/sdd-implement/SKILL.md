---
name: sdd-implement
description: Implementa una a una las tareas de un spec SDD Ready, registrando evidencia de tests (GATE 3). Úsala cuando el usuario pida implementar o continuar un spec.
---

# SDD · Implement

Para cada tarea pendiente de `tasks.md`, en orden:

1. Ejecuta `./speckit task start <spec> TASK-NNN` (omítelo si la tarea ya está `[/]`).
2. Lee solo lo que la tarea necesita: sus AC en `spec.md`, la parte del plan que le afecta y el código que toca.
3. Implementa lo mínimo que cumple sus AC y añade o ajusta los tests del test plan. No salgas del alcance de la tarea.
4. Ejecuta `./speckit task done <spec> TASK-NNN`, que corre solo los escenarios asociados a los AC de la tarea y escribe evidencia por `TC-NNN`. Si hay escenarios manuales, añade `--manual-evidence "<resultado observable>"`. Los checks globales se ejecutan en `close`.
   - **Pasa:** la tarea queda en `[x]`. Haz commit `feat(TASK-NNN): …` y sigue con la siguiente.
   - **Falla:** lee el log en `evidence.md`, corrige la causa raíz y vuelve a ejecutar `task done`.
   - **Tercer fallo:** el CLI bloquea el spec. Detente y explica al usuario qué probaste y qué sospechas. Solo continúa tras `speckit resume <spec> --by <nombre> --reason <motivo>`.
5. Cuando no queden tareas pendientes, continúa con `sdd-review`.

Nunca marques `[x]` a mano. Si el contexto crece mucho, ejecuta `./speckit handoff <spec>` y sugiere abrir un chat nuevo.
