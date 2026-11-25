"""
03 - Componente predictivo (valor agregado)
Proyecto final - Electiva III: Introducción a la Ciencia de Datos

Variable objetivo : potencia_solar_w (potencia entregada por los paneles)
Variables de entrada: radiación solar y temperatura
Modelo            : regresión lineal múltiple (scikit-learn)
Validación        : separación aleatoria 70 % entrenamiento / 30 % prueba (semilla 42)
                    + prueba temporal (entrena con la mañana, evalúa con la tarde)

Se comparan dos versiones:
  A) radiación del mismo minuto (datos tal como vienen)
  B) radiación del minuto anterior (corrige el desfase encontrado en la auditoría, A21)

Salidas: salidas/modelo_metricas.csv, salidas/modelo_predicciones_prueba.csv, figuras/f6_modelo.png
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

RAIZ = Path(__file__).resolve().parents[1]
SALIDAS = RAIZ / "salidas"
FIGURAS = RAIZ / "figuras"

d = pd.read_csv(RAIZ / "datos" / "limpio" / "escenario1_limpio.csv")
# Solo horas de sol: de noche la potencia es 0 por definición y aumentaría artificialmente el ajuste
sol = d[(d["radiacion_w_m2"] > 0) | (d["radiacion_alineada_w_m2"] > 0) | (d["potencia_solar_w"] > 0)].copy()
y = sol["potencia_solar_w"]

versiones = {
    "A) Radiación del mismo minuto": ["radiacion_w_m2", "temperatura_c"],
    "B) Radiación alineada (minuto anterior)": ["radiacion_alineada_w_m2", "temperatura_c"],
}


def metricas(y_real, y_pred):
    return {
        "MAE_W": mean_absolute_error(y_real, y_pred),
        "RMSE_W": float(np.sqrt(mean_squared_error(y_real, y_pred))),
        "R2": r2_score(y_real, y_pred),
    }


filas, predicciones, modelos = [], {}, {}
idx_ent, idx_pru = train_test_split(sol.index, test_size=0.30, random_state=42)
manana = sol["minuto"] <= 720   # hasta las 12:00

for nombre, X_cols in versiones.items():
    X = sol[X_cols]
    # Línea base: predecir siempre el promedio del entrenamiento
    base = np.full(len(idx_pru), y.loc[idx_ent].mean())
    filas.append({"modelo": "Línea base (promedio)", "version": "Sin variables", "validacion": "Aleatoria 70/30",
                  **metricas(y.loc[idx_pru], base)})

    m = LinearRegression().fit(X.loc[idx_ent], y.loc[idx_ent])
    pred = m.predict(X.loc[idx_pru])
    filas.append({"modelo": "Regresión lineal", "version": nombre, "validacion": "Aleatoria 70/30",
                  **metricas(y.loc[idx_pru], pred),
                  "coef_radiacion": m.coef_[0], "coef_temperatura": m.coef_[1], "intercepto": m.intercept_})
    predicciones[nombre] = pred
    modelos[nombre] = m

    mt = LinearRegression().fit(X[manana], y[manana])
    filas.append({"modelo": "Regresión lineal", "version": nombre, "validacion": "Temporal (mañana → tarde)",
                  **metricas(y[~manana], mt.predict(X[~manana]))})

res = pd.DataFrame(filas)
res = res.drop_duplicates(subset=["modelo", "version", "validacion"]).round(4)
res.to_csv(SALIDAS / "modelo_metricas.csv", index=False, encoding="utf-8")

pred_df = pd.DataFrame({
    "minuto": sol.loc[idx_pru, "minuto"].values,
    "potencia_real_w": y.loc[idx_pru].values,
    "pred_A_w": predicciones["A) Radiación del mismo minuto"],
    "pred_B_w": predicciones["B) Radiación alineada (minuto anterior)"],
}).sort_values("minuto").round(2)
pred_df.to_csv(SALIDAS / "modelo_predicciones_prueba.csv", index=False, encoding="utf-8")

mB = modelos["B) Radiación alineada (minuto anterior)"]
resumen = {
    "registros_sol": int(len(sol)), "entrenamiento": int(len(idx_ent)), "prueba": int(len(idx_pru)),
    "coef_radiacion_w_por_w_m2": round(float(mB.coef_[0]), 2),
    "coef_temperatura_w_por_c": round(float(mB.coef_[1]), 2),
    "intercepto_w": round(float(mB.intercept_), 1),
}
(SALIDAS / "modelo_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

# Figura: real vs predicho
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharex=True, sharey=True)
for ax, (nombre, col) in zip(axes, [("A) Radiación del mismo minuto", "pred_A_w"),
                                    ("B) Radiación alineada (minuto anterior)", "pred_B_w")]):
    fila = res[(res["version"] == nombre) & (res["modelo"] == "Regresión lineal") &
               (res["validacion"] == "Aleatoria 70/30")].iloc[0]
    ax.scatter(pred_df["potencia_real_w"] / 1000, pred_df[col] / 1000, s=9, alpha=0.6,
               color="#3B6EA8" if col == "pred_B_w" else "#E8A33D")
    ax.plot([0, 56], [0, 56], color="#555", lw=1, ls="--")
    ax.set(title=f"{nombre}\nMAE {fila.MAE_W / 1000:.2f} kW · RMSE {fila.RMSE_W / 1000:.2f} kW · R² {fila.R2:.3f}"
           .replace(".", ","), xlabel="Potencia real (kW)")
axes[0].set_ylabel("Potencia predicha (kW)")
fig.text(0.01, 0.01, "Fuente: resultados de simulación, escenario 1. Conjunto de prueba (30 %). Elaboración propia.",
         fontsize=7.5, color="#666")
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(FIGURAS / "f6_modelo.png", dpi=160)
plt.close(fig)

pd.set_option("display.width", 200)
print(res[["modelo", "version", "validacion", "MAE_W", "RMSE_W", "R2"]].to_string(index=False))
print(resumen)
