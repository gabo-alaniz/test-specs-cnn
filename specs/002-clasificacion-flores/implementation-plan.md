# Plan 002: clasificacion-flores

> Solo size M. Se aprueba junto con `spec.md` (GATE 1).

## Módulos y componentes afectados

| Componente | Ubicación | Responsabilidad |
|------------|-----------|-----------------|
| Notebook | `data-science/clasificacion_flores.ipynb` | Flujo completo: configuración, descarga, datos, modelo, entrenamiento, evaluación. Las celdas llevan `metadata.tags` (`config`, `descarga`, `datos`, `modelo`, `entrenamiento`, `evaluacion`) para poder ejecutarlas por separado en las pruebas. |
| Pruebas | `data-science/tests/test_clasificacion_flores.py` | Pruebas `unittest` sobre el notebook: estructura, ejecución de celdas etiquetadas y comprobación de salidas. |
| Ignorados de git | `.gitignore` | Añade `data-science/data/` (única edición fuera de `data-science/` y `specs/`). |

Dentro del notebook:
- `FloresDataModule(LightningDataModule)`: `prepare_data` descarga, `setup` lista y divide, `*_dataloader` devuelve los loaders.
- `CnnFlores(LightningModule)`: 3 bloques `Conv2d → BatchNorm2d → ReLU → MaxPool2d` y una cabeza lineal; `torchmetrics.Accuracy` y `self.log` de pérdida y exactitud por época.
- Evaluación con `scikit-learn` (`confusion_matrix`, `classification_report`) y `matplotlib`.

## Decisiones

| Decisión | Alternativa descartada | Motivo |
|----------|------------------------|--------|
| Dataset `flower_photos` por URL pública con `urllib` + `tarfile` (filtro `data`) | Kaggle `alxmamaev/flowers-recognition` con `kagglehub` | No hay credenciales de Kaggle; la descarga pública no necesita dependencias ni secretos. El filtro `data` evita rutas peligrosas al extraer. |
| CNN pequeña desde cero | Transfer learning (ResNet18) | Decisión del usuario: sin descarga de pesos; el objetivo es validar el flujo. |
| Imágenes a 96×96, 3 épocas, batch 32, `num_workers=0` | Resolución mayor, más épocas | Ejecución rápida y estable en CPU; sin procesos hijo en el notebook. |
| División 80/20 con `torch.Generator` sembrado y `lightning.seed_everything` | División aleatoria sin semilla | Reproducibilidad (AC-005). |
| Pruebas con `unittest` y `nbclient`/`nbformat` ya instalados | `pytest` u otro framework | `.agents/rules/testing-standards.md`: usar el framework del proyecto. |
| Pruebas en `data-science/tests/` | `tests/` en la raíz | El usuario pidió que todo viva en `data-science/`. |
| Notebook entregado con salidas ejecutadas | Notebook limpio | Decisión del usuario: sirve como evidencia. |

## Datos y migraciones
Sin base de datos ni migraciones. El dataset (~220 MB) se descarga a `data-science/data/flower_photos/`
y no se versiona. Datos públicos, sin PII.

## Dependencias nuevas
Ninguna. Se usan `lightning`, `torch`, `torchvision`, `torchmetrics`, `matplotlib`, `scikit-learn`,
`nbformat`, `nbclient` y `ipykernel`, todas ya instaladas y fijadas en `data-science/requirements.txt`.

## Riesgos y mitigación
- **Sin red o URL caída:** la descarga falla. Mitigación: la celda informa el error con claridad y se reutiliza el dataset si ya existe; las pruebas de descarga son `integration` y se reportan como no ejecutadas si no hay red, sin marcar la tarea como completa.
- **Entrenamiento lento en CPU:** mitigación con 96×96, 3 épocas y una CNN pequeña; el tiempo se mide en la evidencia.
- **Exactitud baja de una CNN desde cero:** esperado y fuera de criterio; ningún AC fija un umbral de exactitud.
- **Salidas pesadas en el `.ipynb`:** se limitan las imágenes y se comprueba el tamaño del archivo.
- **Fugas en el notebook:** AC-006 comprueba que no haya rutas absolutas del equipo ni credenciales en el JSON.
- **Edición fuera de la lista de permitidas de `AGENTS.md` §G (`data-science/**`):** es el alcance que el usuario pidió explícitamente; no se toca `.agents/**`.
