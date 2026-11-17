# Brief: clasificacion-flores

## 1. Intake
- Modo: proposal
- Estado: confirmed
- Confirmado por: gabo
- Confirmado el: 2026-11-17T19:58:00+00:00

## 2. Usuario
Solicita y usa el resultado una persona del equipo de ciencia de datos que prueba el flujo de specs y
organiza su trabajo de ciencia de datos. No hay usuarios finales ni terceros afectados.

## 3. Problema
No existe un ejemplo reproducible de clasificación de imágenes dentro de `data-science/`. Se necesita
uno que valide, con un caso real y rápido en CPU, que el entorno (PyTorch Lightning, Jupyter) y el
flujo de specs funcionan de punta a punta.

## 4. Proceso actual
No hay proceso previo: `data-science/` contiene solo el entorno (`.venv`, `requirements.txt`,
`setup-env.sh`). No hay notebooks, scripts ni datos.

## 5. Resultado esperado
Un notebook `data-science/clasificacion_flores.ipynb` que se ejecuta de principio a fin, descarga el
dataset, entrena unas pocas épocas en CPU, evalúa el modelo y muestra métricas y gráficas dentro del
mismo notebook.

## 6. Reglas de negocio y fuentes
- Fuente de datos: `flower_photos` (público, TensorFlow), 5 clases de flores.
- Sin reglas de negocio, fórmulas ni responsables de datos: es un ejercicio técnico.

## 7. Permisos y sensibilidad
- Datos: `público` (fotos de flores, sin PII).
- Sin control de acceso: el notebook y su salida son de uso local del equipo.
- No se versionan credenciales de Kaggle ni los datos descargados.

## 8. Criterios de aceptación
- AC-001: Dado un entorno limpio con `data-science/.venv`, cuando se ejecuta el notebook completo,
  entonces termina sin errores.
- AC-002: Dado que el dataset no está en local, cuando corre la celda de descarga, entonces queda en
  una carpeta dentro de `data-science/` y no se versiona.
- AC-003: Dado el dataset descargado, cuando se entrena el modelo con PyTorch Lightning unas pocas
  épocas en CPU, entonces el entrenamiento termina en un tiempo razonable y registra la pérdida.
- AC-004: Dado el modelo entrenado, cuando se evalúa sobre datos no usados en el entrenamiento,
  entonces el notebook muestra métricas y gráficas de resultados.

## 9. Fuera de alcance
- Entrenamiento prolongado o ajuste de hiperparámetros para máxima precisión.
- Uso de GPU, despliegue, API o servicio de inferencia.
- Transfer learning y pesos preentrenados.
- Dependencias nuevas sin tu aprobación previa.

## 10. Restricciones y riesgos
- Todo vive dentro de `data-science/`; ejecución en CPU con `data-science/.venv` (Python 3.13).
- Usar PyTorch Lightning, que ya está instalado (`lightning` 2.6.6).
- No hay credenciales de Kaggle en el entorno (sin `~/.kaggle` ni variables `KAGGLE_*`).
- Riesgo: la descarga del dataset requiere red. Con una CNN desde cero y pocas épocas, la exactitud
  será modesta; el objetivo es validar el flujo, no maximizar la precisión.

## 11. Referencias
- `alxmamaev/flowers-recognition` (Kaggle) y `flower_photos` de TensorFlow (público, sin credenciales). Kaggle `alxmamaev/flowers-recognition` queda
  descartado por no haber credenciales.

## 12. Hechos aportados
- El notebook va en `data-science/clasificacion_flores.ipynb`.
- Dataset: `flower_photos` (descarga pública, sin credenciales de Kaggle).
- Modelo: CNN pequeña desde cero con PyTorch Lightning, entrenada pocas épocas en CPU.
- Métricas: exactitud, matriz de confusión, reporte por clase, curvas de pérdida y exactitud, y una
  muestra de predicciones.
- El `.ipynb` se entrega ejecutado, con las salidas guardadas.
- Resultado: métricas y gráficas dentro del mismo notebook.
- Si hace falta una librería extra, se te consulta antes y se actualiza `data-science/requirements.txt`.
- Las librerías `lightning`, `pytorch-lightning`, `torchmetrics`, `torchvision`, `ipywidgets`,
  `kagglehub`, `matplotlib`, `scikit-learn`, `ipykernel`, `nbformat` y `nbconvert` ya están instaladas.

## 13. Supuestos
- El dataset se guarda en `data-science/data/` y se ignora en git.
- Se divide en entrenamiento y validación con semilla fija para que sea reproducible.
- Con las librerías ya instaladas no hace falta añadir ninguna dependencia.

## 14. Decisiones abiertas
- Ninguna.
