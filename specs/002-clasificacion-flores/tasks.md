# Tasks 002: clasificacion-flores

> Formato: una línea por tarea, `- [ ] TASK-NNN: descripción (AC-NNN)`. No cambies las marcas a mano: `speckit task start` pone `[/]` y `speckit task done` pone `[x]` tras registrar la evidencia.
> Cada criterio del spec debe aparecer en al menos una tarea. Máximo 3 tareas en size S y 8 en size M.

- [x] TASK-001: Ignorar `data-science/data/` en git, crear el esqueleto del notebook con celdas etiquetadas y la celda de descarga de `flower_photos` (AC-002)
- [x] TASK-002: Implementar `FloresDataModule` con división entrenamiento/validación reproducible por semilla (AC-005)
- [x] TASK-003: Implementar la CNN `CnnFlores` con Lightning y entrenar pocas épocas en CPU registrando pérdida y exactitud (AC-003)
- [x] TASK-004: Implementar la evaluación: exactitud, matriz de confusión, reporte por clase, curvas y muestra de predicciones (AC-004)
- [/] TASK-005: Ejecutar el notebook completo, guardar las salidas y verificar que no hay errores, credenciales ni rutas absolutas (AC-001, AC-006)
