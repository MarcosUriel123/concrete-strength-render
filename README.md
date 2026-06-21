# Predicción de Resistencia a la Compresión del Concreto — Despliegue en Render

Aplicación Flask que carga el pipeline entrenado en el proyecto (`modelo_concrete.pkl`)
y predice la resistencia a la compresión del concreto (MPa) a partir de las 8 variables
originales del dataset (sin requerir que el usuario conozca escalado, selección de
características ni PCA).

## Archivos del proyecto

| Archivo | Función |
|---|---|
| `app.py` | Aplicación Flask: carga el pipeline, valida datos, genera la predicción |
| `pipeline_utils.py` | Función `seleccionar_columnas` usada dentro del pipeline; debe existir en un módulo propio (no en un notebook) para que `joblib` pueda cargarlo correctamente fuera del entorno de entrenamiento |
| `modelo_concrete.pkl` | Pipeline completo (imputación + escalado + selección de características + RandomForestRegressor), entrenado con el 100% de los datos tras la evaluación |
| `requirements.txt` | Dependencias con versiones fijas, compatibles con el entorno Linux de Render |
| `templates/index.html` | Formulario web: solicita las 8 variables originales (cemento, escoria, ceniza, agua, superplastificante, agregado grueso, agregado fino, edad), muestra el resultado en MPa y los mensajes de error |

## Cómo se construyó la aplicación

1. Se extrajo el pipeline final del notebook (`crear_pipeline_escenario1` + `RandomForestRegressor`, el experimento ganador).
2. La función de selección de columnas (`FunctionTransformer`) se movió a un módulo independiente (`pipeline_utils.py`), porque al guardar un pipeline con joblib que usa una función definida dentro de un notebook o script `__main__`, la carga falla en otro proceso (error `Can't get attribute ... on '__main__'`). Moverla a un módulo importable resuelve esto.
3. Se reentrenó el pipeline con el 100% de los datos y se guardó con `joblib.dump`.
4. `app.py` carga ese pipeline una sola vez al iniciar el servidor (`joblib.load`), define las 8 columnas esperadas, valida la entrada del usuario y llama a `pipeline.predict(...)`.
5. Toda predicción se recorta con `np.clip(..., a_min=0)` antes de mostrarse, ya que la resistencia del concreto no puede ser negativa.

## Cómo se guardó y cargó el pipeline

```python
import joblib
joblib.dump(pipeline_final, "modelo_concrete.pkl")   # al entrenar
pipeline = joblib.load("modelo_concrete.pkl")         # en app.py, al iniciar
```

## Ejecución local

```bash
pip install -r requirements.txt
python app.py
# o, para simular el entorno de producción de Render:
gunicorn app:app --bind 127.0.0.1:8000
```

Abrir `http://127.0.0.1:8000/` en el navegador.

## Configuración en Render

- **Tipo de servicio:** Web Service.
- **Runtime:** Python 3.
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Repositorio:** conectado a GitHub, rama `main`.

## Pruebas realizadas

- `GET /` → formulario carga correctamente (código 200).
- `POST /predecir` con datos válidos → predicción correcta (ej. 46.98 MPa para una mezcla de prueba).
- `POST /predecir` con campo faltante → mensaje de error "es obligatorio".
- `POST /predecir` con valor no numérico → mensaje de error "debe ser un número".
- `POST /predecir` con valor negativo → mensaje de error "no puede ser negativo".
- `POST /api/predecir` (JSON) → respuesta JSON con la predicción, útil para pruebas automatizadas.
- Ejecución con `gunicorn` (servidor de producción) en local, antes de subir a Render.

## Dificultades encontradas y solución

- **Error al cargar el pipeline en un proceso nuevo:** `joblib` no pudo reconstruir el `FunctionTransformer` porque la función `seleccionar_columnas` vivía en el script de entrenamiento (`__main__`). Se resolvió moviéndola a `pipeline_utils.py`, importable tanto al entrenar como en `app.py`.
- **Versiones de librerías:** se fijaron las versiones exactas en `requirements.txt` (las mismas usadas al entrenar) para evitar incompatibilidades entre el pipeline guardado y el entorno de Render.

## URL pública

Ver `URL_Render.txt` en la raíz del proyecto.