# Test Plan 002: clasificacion-flores

> Solo size M. Necesita al menos un escenario por cada criterio AC-NNN del spec.

Las pruebas viven en `data-science/tests/test_clasificacion_flores.py` (`unittest`). Un asistente del
módulo ejecuta en un kernel solo las celdas del notebook cuyo `metadata.tags` se indica, para que cada
tarea pueda probarse sin que existan las posteriores. Todos los comandos se lanzan desde la raíz.

| ID | AC | Escenario | Tipo (unit / integration / e2e / manual) | Comando o pasos |
|----|----|-----------|------------------------------------------|-----------------|
| TC-001 | AC-002 | `data-science/data/` queda ignorado por git y el notebook es un `.ipynb` válido con las celdas etiquetadas | unit | `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.EstructuraTestCase -v` |
| TC-002 | AC-002 | Ejecutar las celdas `config` y `descarga` deja `flower_photos` con 5 carpetas de clase con imágenes y sin usar credenciales de Kaggle | integration | `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.DescargaTestCase -v` |
| TC-003 | AC-005 | Ejecutar `config`, `descarga` y `datos` dos veces con la misma semilla da divisiones idénticas y disjuntas | integration | `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.DivisionTestCase -v` |
| TC-004 | AC-003 | Ejecutar hasta `entrenamiento` termina en CPU y registra la pérdida de entrenamiento y de validación de cada época | integration | `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.EntrenamientoTestCase -v` |
| TC-005 | AC-004 | Ejecutar hasta `evaluacion` produce exactitud, matriz de confusión, reporte por clase, curvas y muestra de predicciones | integration | `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.EvaluacionTestCase -v` |
| TC-006 | AC-001 | Ejecutar el notebook completo con `nbclient` termina sin errores | e2e | `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.NotebookCompletoTestCase -v` |
| TC-007 | AC-006 | El `.ipynb` entregado tiene salidas guardadas de métricas y gráficas, y no contiene credenciales ni rutas absolutas del equipo | unit | `PYTHONPATH=data-science/tests .venv/bin/python -m unittest test_clasificacion_flores.EntregaTestCase -v` |
| TC-008 | AC-006 | Revisión visual del notebook abierto sin ejecutar: se leen las gráficas y las métricas | manual | Abrir `data-science/clasificacion_flores.ipynb` sin ejecutarlo y comprobar que se ven la matriz de confusión, las curvas y la muestra de predicciones. |
