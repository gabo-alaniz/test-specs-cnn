# Spec 002: clasificacion-flores

> Fuente: `brief.md`. Tamaño: M (`AGENTS.md` §D).

## Problema y contexto
No existe un ejemplo reproducible de clasificación de imágenes dentro de `data-science/`. Se necesita
un notebook que valide, con un caso real y rápido en CPU, que el entorno (`data-science/.venv`,
PyTorch Lightning, Jupyter) y el flujo de specs funcionan de punta a punta. El objetivo es validar el
flujo, no maximizar la exactitud del modelo.

## Usuarios y flujos
- **Persona de ciencia de datos del equipo:** ejecuta el notebook `data-science/clasificacion_flores.ipynb`
  con `data-science/.venv` y revisa las métricas y gráficas. No hay usuarios finales.

Flujo del notebook, en orden:

1. Configuración: semilla fija, rutas dentro de `data-science/` y dispositivo CPU.
2. Descarga de `flower_photos` (público, sin credenciales) a `data-science/data/`, solo si no existe.
3. `LightningDataModule`: lista las imágenes, divide entrenamiento/validación con semilla fija y
   construye los `DataLoader`.
4. `LightningModule`: CNN pequeña desde cero; entrenamiento de pocas épocas con `Trainer` en CPU.
5. Evaluación sobre la partición de validación: métricas y gráficas dentro del notebook.

## Criterios de aceptación
- AC-001: Dado `data-science/.venv` y acceso a red, cuando se ejecuta el notebook completo de principio a fin, entonces termina sin errores y sin celdas con salida de tipo `error`.
- AC-002: Dado que el dataset no está en local, cuando corre la celda de descarga, entonces `flower_photos` queda en `data-science/data/` con sus 5 carpetas de clase, sin credenciales de Kaggle, y git ignora esa carpeta.
- AC-003: Dado el dataset descargado, cuando se entrena la CNN con PyTorch Lightning unas pocas épocas en CPU, entonces el entrenamiento termina y registra la pérdida de entrenamiento y de validación de cada época.
- AC-004: Dado el modelo entrenado, cuando se evalúa sobre la partición de validación, entonces el notebook muestra la exactitud, la matriz de confusión, el reporte por clase, las curvas de pérdida y exactitud, y una muestra de predicciones.
- AC-005: Dada una semilla fija, cuando se construye la división entrenamiento/validación dos veces, entonces ambas divisiones son idénticas y no comparten ninguna imagen.
- AC-006: Dado el notebook entregado, cuando se abre sin ejecutarlo, entonces contiene las salidas guardadas de métricas y gráficas, y no contiene credenciales, rutas absolutas del equipo ni datos de usuario.

## Alcance
**Incluye:**
- El notebook `data-science/clasificacion_flores.ipynb`, ejecutado y con las salidas guardadas.
- La descarga pública de `flower_photos` a `data-science/data/` y su exclusión de git.
- Una CNN pequeña desde cero con PyTorch Lightning, pocas épocas en CPU.
- Pruebas automáticas en `data-science/tests/` con el framework del proyecto (`unittest`).

**Excluye:**
- Transfer learning, pesos preentrenados, GPU, ajuste de hiperparámetros y despliegue.
- El dataset de Kaggle `alxmamaev/flowers-recognition` (no hay credenciales).
- Dependencias nuevas: todas las librerías necesarias ya están instaladas.
- Cambios en `.agents/**`, incluido `project.json`.

## Restricciones y datos
- Todo vive en `data-science/`, salvo la línea de `.gitignore` que excluye `data-science/data/`.
- Ejecución en CPU con Python 3.13 y las versiones fijadas en `data-science/requirements.txt`.
- Datos: `público`, sin PII. No se versionan los datos descargados ni credenciales.
- La descarga necesita red. La CNN desde cero con pocas épocas dará una exactitud modesta.
