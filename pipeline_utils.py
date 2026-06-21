"""
Funciones auxiliares usadas dentro del pipeline guardado (modelo_concrete.pkl).

Este módulo debe existir y ser importable tanto al momento de ENTRENAR y
guardar el pipeline (joblib.dump) como al momento de CARGARLO en la app
Flask (joblib.load). Si esta función viviera solo dentro de un notebook o
script suelto, joblib no podría reconstruir el objeto FunctionTransformer
al cargarlo en otro proceso (error: "Can't get attribute ... on '__main__'").
"""

# Índices de las 5 columnas seleccionadas (age, cement, superplasticizer,
# water, blast_furnace_slag) dentro del orden que produce el ColumnTransformer
# de imputación: primero las columnas con nulos (cement, water, age), luego
# el resto en su orden original (blast_furnace_slag, fly_ash, superplasticizer,
# coarse_aggregate, fine_aggregate).
COLUMNAS_REORDENADAS = [
    "cement", "water", "age",
    "blast_furnace_slag", "fly_ash", "superplasticizer",
    "coarse_aggregate", "fine_aggregate",
]
CARACTERISTICAS_SELECCIONADAS = ["age", "cement", "superplasticizer", "water", "blast_furnace_slag"]
INDICES_SELECCION_ESCENARIO1 = [COLUMNAS_REORDENADAS.index(c) for c in CARACTERISTICAS_SELECCIONADAS]


def seleccionar_columnas(X_array, indices=INDICES_SELECCION_ESCENARIO1):
    """Selecciona, por índice posicional, las columnas del Escenario 1 tras el ColumnTransformer."""
    return X_array[:, indices]