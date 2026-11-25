"""
04 - Exporta los datos limpios y los resultados al dashboard web
Proyecto final - Electiva III: Introducción a la Ciencia de Datos

Entrada : datos/limpio/escenario1_limpio.csv y archivos de salidas/
Salida  : dashboard/datos.js  (lo carga dashboard/index.html con <script src="datos.js">)

El dashboard es una página HTML + JavaScript sin dependencias externas: se abre con doble clic
(funciona sin internet) o se publica en cualquier hosting estático.
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDAS = RAIZ / "salidas"
d = pd.read_csv(RAIZ / "datos" / "limpio" / "escenario1_limpio.csv")
aud = pd.read_csv(SALIDAS / "auditoria.csv")
kpis = json.loads((SALIDAS / "kpis.json").read_text(encoding="utf-8"))
met = pd.read_csv(SALIDAS / "modelo_metricas.csv")
pred = pd.read_csv(SALIDAS / "modelo_predicciones_prueba.csv")
mres = json.loads((SALIDAS / "modelo_resumen.json").read_text(encoding="utf-8"))

ETAPAS = ["Parada", "Pretratamiento", "Ósmosis inversa", "Pretratamiento + ósmosis"]


def col(serie, dec):
    vals = serie.round(dec).tolist()
    return [int(v) if float(v).is_integer() else v for v in vals]


banderas = (d["soc_corregido"].astype(int) * 1 + d["atipico_ratio_original"].astype(int) * 2 +
            d["inconsistencia_neta"].astype(int) * 4)

datos = {
    "meta": {
        "generado": date.today().isoformat(),
        "fuente": "Resultados de simulación de una planta desalinizadora con energía solar, batería y respaldo "
                  "diésel. Escenario 1, 30 horas, registro por minuto (1.800 registros).",
        "etapas": ETAPAS,
        "capacidad_wh": float(d["energia_bateria_wh"].max()),
    },
    "serie": {
        "m": d["minuto"].tolist(),
        "e": d["etapa"].map({e: i for i, e in enumerate(ETAPAS)}).tolist(),
        "ps": col(d["potencia_solar_w"], 0), "co": col(d["consumo_planta_w"], 1),
        "pn": col(d["potencia_neta_w"], 0), "so": col(d["soc_pct"], 2),
        "ra": col(d["radiacion_w_m2"], 1), "te": col(d["temperatura_c"], 2), "vi": col(d["viento_m_s"], 2),
        "eb": col(d["energia_bateria_wh"], 2), "ag": col(d["agua_m3"], 4), "sa": col(d["salmuera_m3"], 4),
        "lg": col(d["lodos_gruesos_paq"], 0), "lf": col(d["lodos_finos_paq"], 0),
        "ex": col(d["excedente_wh"], 2), "di": col(d["diesel_wh"], 2), "cb": col(d["combustible_l"], 5),
        "fl": banderas.tolist(),
    },
    "auditoria": aud.fillna("").to_dict(orient="records"),
    "kpis": kpis,
    "modelo": {
        "metricas": met[["modelo", "version", "validacion", "MAE_W", "RMSE_W", "R2"]].round(4).to_dict("records"),
        "resumen": mres,
        "pred": {"real": col(pred["potencia_real_w"], 0), "a": col(pred["pred_A_w"], 0),
                 "b": col(pred["pred_B_w"], 0)},
    },
}

salida = RAIZ / "dashboard" / "datos.js"
salida.write_text("window.DATOS = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n",
                  encoding="utf-8")
print(f"dashboard/datos.js: {salida.stat().st_size / 1024:.0f} KB")
