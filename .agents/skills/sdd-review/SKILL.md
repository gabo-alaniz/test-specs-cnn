---
name: sdd-review
description: Revisa un spec SDD terminado contra sus criterios de aceptación, lo cierra y hace la retrospectiva. Úsala cuando todas las tareas estén hechas o el usuario pida una revisión.
---

# SDD · Review y cierre

1. Comprueba con `./speckit status <spec>` que todas las tareas están hechas y que aparece `check=OK`.
2. Revisa el diff del spec (`git diff <base>...HEAD`) como revisor senior:
   - ¿Se cumple cada AC? Cita la evidencia (test o comando) de cada uno.
   - Seguridad: sin inyección, XSS ni secretos, y sin PII en los logs.
   - Sin componentes ni lógica duplicados y sin alcance no pedido.
   - Tipado correcto de punta a punta, y mockup respetado si hay UI.
3. Cada hallazgo se convierte en una tarea nueva en `tasks.md` (`TASK-NNN … (AC-NNN)`) y vuelve a `sdd-implement`. No corrijas nada en silencio.
4. Sin hallazgos, ejecuta `./speckit close <spec> [--base <rama-destino>]`: corre test/lint/build/e2e, graba el fingerprint que verificará CI, marca `completed` y crea `retro.md`.
5. Completa `retro.md` con el usuario (≤ 5 preguntas). Lleva las preferencias nuevas a `.agents/memory/preferences.md` y las decisiones transversales a `.agents/memory/decisions.md`. `archive` rechazará una retro incompleta.
