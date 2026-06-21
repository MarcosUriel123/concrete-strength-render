"""
Aplicación Flask para predecir la resistencia a la compresión del concreto
(Concrete Compressive Strength) a partir de las proporciones de sus
componentes y la edad de curado, usando el pipeline entrenado en el
proyecto de fin de mes 2 (CRISP-DM).
"""

from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np

from pipeline_utils import seleccionar_columnas  # noqa: F401 (necesario para joblib.load)

app = Flask(__name__)

# Se carga el pipeline una sola vez, al iniciar el servidor
pipeline = joblib.load("modelo_concrete.pkl")

# Las 8 variables originales que el formulario debe solicitar, con su
# etiqueta, unidad y rango razonable (derivado del dataset de entrenamiento)
CAMPOS = [
    {"nombre": "cement", "etiqueta": "Cemento", "unidad": "kg/m³", "min": 0, "max": 600},
    {"nombre": "blast_furnace_slag", "etiqueta": "Escoria de alto horno", "unidad": "kg/m³", "min": 0, "max": 400},
    {"nombre": "fly_ash", "etiqueta": "Ceniza volante", "unidad": "kg/m³", "min": 0, "max": 250},
    {"nombre": "water", "etiqueta": "Agua", "unidad": "kg/m³", "min": 100, "max": 250},
    {"nombre": "superplasticizer", "etiqueta": "Superplastificante", "unidad": "kg/m³", "min": 0, "max": 35},
    {"nombre": "coarse_aggregate", "etiqueta": "Agregado grueso", "unidad": "kg/m³", "min": 750, "max": 1200},
    {"nombre": "fine_aggregate", "etiqueta": "Agregado fino", "unidad": "kg/m³", "min": 550, "max": 1000},
    {"nombre": "age", "etiqueta": "Edad de curado", "unidad": "días", "min": 1, "max": 400},
]


def validar_datos(form):
    """Valida que los 8 campos existan, sean numéricos y no sean negativos.
    Devuelve (datos_dict, lista_de_errores)."""
    datos = {}
    errores = []
    for campo in CAMPOS:
        nombre = campo["nombre"]
        valor_str = str(form.get(nombre, "")).strip()

        if valor_str == "":
            errores.append(f"El campo '{campo['etiqueta']}' es obligatorio.")
            continue

        try:
            valor = float(valor_str)
        except ValueError:
            errores.append(f"El campo '{campo['etiqueta']}' debe ser un número.")
            continue

        if valor < 0:
            errores.append(f"El campo '{campo['etiqueta']}' no puede ser negativo.")
            continue

        datos[nombre] = valor

    return datos, errores


@app.route("/", methods=["GET"])
def inicio():
    return render_template("index.html", campos=CAMPOS, resultado=None, errores=None)


@app.route("/predecir", methods=["POST"])
def predecir():
    datos, errores = validar_datos(request.form)

    if errores:
        return render_template("index.html", campos=CAMPOS, resultado=None, errores=errores)

    entrada = pd.DataFrame([datos])[[c["nombre"] for c in CAMPOS]]

    try:
        prediccion = pipeline.predict(entrada)[0]
        # La resistencia a la compresión no puede ser negativa; se recorta por seguridad
        prediccion = float(np.clip(prediccion, a_min=0, a_max=None))
    except Exception as e:
        return render_template(
            "index.html", campos=CAMPOS, resultado=None,
            errores=[f"Ocurrió un error al generar la predicción: {e}"]
        )

    return render_template(
        "index.html", campos=CAMPOS,
        resultado=round(prediccion, 2), errores=None, valores_previos=datos
    )


@app.route("/api/predecir", methods=["POST"])
def predecir_json():
    """Endpoint JSON, útil para pruebas o integraciones externas."""
    data = request.get_json(silent=True) or {}
    datos, errores = validar_datos(data)

    if errores:
        return jsonify({"error": errores}), 400

    entrada = pd.DataFrame([datos])[[c["nombre"] for c in CAMPOS]]
    prediccion = pipeline.predict(entrada)[0]
    prediccion = float(np.clip(prediccion, a_min=0, a_max=None))

    return jsonify({
        "prediccion_mpa": round(prediccion, 2),
        "entrada": datos
    })


if __name__ == "__main__":
    app.run(debug=True)