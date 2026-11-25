"""
02 - Análisis descriptivo
Proyecto final - Electiva III: Introducción a la Ciencia de Datos

Entrada : datos/limpio/escenario1_limpio.csv
Salidas : salidas/kpis.json, salidas/resumen_etapas.csv, salidas/resumen_horario.csv,
          salidas/eventos_diesel.csv, salidas/estadisticas_descriptivas.csv, figuras/*.png

Preguntas de análisis
  P1. ¿Qué tan confiables son los datos de la simulación?            (ver 01_auditoria_limpieza.py)
  P2. ¿Qué proporción de la energía solar generada se aprovecha?
  P3. ¿Cuándo y por qué interviene el generador diésel?
  P4. ¿Cuánta agua y cuántos residuos produce la planta, y con cuánta energía?
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SALIDAS = RAIZ / "salidas"
FIGURAS = RAIZ / "figuras"
FIGURAS.mkdir(exist_ok=True)
FUENTE = "Fuente: resultados de simulación, escenario 1 (30 h, registro por minuto). Elaboración propia."

d = pd.read_csv(RAIZ / "datos" / "limpio" / "escenario1_limpio.csv")
aud = pd.read_csv(SALIDAS / "auditoria.csv")
CAPACIDAD_WH = d["energia_bateria_wh"].max()
ultimo = d.iloc[-1]

# ---------------------------------------------------------------------------
# Estadísticas descriptivas de las variables continuas
# ---------------------------------------------------------------------------
continuas = ["radiacion_w_m2", "temperatura_c", "viento_m_s", "potencia_solar_w", "consumo_planta_w",
             "potencia_neta_w", "energia_bateria_wh", "soc_pct"]
desc = d[continuas].describe().T
desc["mediana"] = d[continuas].median()
desc = desc[["count", "mean", "mediana", "std", "min", "max"]].round(2)
desc.columns = ["registros", "promedio", "mediana", "desv_estandar", "minimo", "maximo"]
desc.to_csv(SALIDAS / "estadisticas_descriptivas.csv", encoding="utf-8")
dia_mask = d["radiacion_w_m2"] > 0
desc_dia = d.loc[dia_mask, ["radiacion_w_m2", "potencia_solar_w"]].describe().T.round(2)

# ---------------------------------------------------------------------------
# P2. Aprovechamiento de la energía solar
# ---------------------------------------------------------------------------
solar_kwh = d["energia_solar_wh"].sum() / 1000
consumo_kwh = d["energia_consumo_wh"].sum() / 1000
excedente_kwh = ultimo["excedente_acum_wh"] / 1000
diesel_kwh = ultimo["diesel_acum_wh"] / 1000
solar_directa_kwh = np.minimum(d["potencia_solar_w"], d["consumo_planta_w"]).sum() / 60 / 1000
delta_bat = d["energia_bateria_wh"].diff()
pasos = delta_bat[delta_bat != 0].dropna()
carga_bat_kwh = pasos[pasos > 0].sum() / 1000
descarga_bat_kwh = -pasos[pasos < 0].sum() / 1000
carga_max_w = pasos.max() * 30          # los cambios ocurren cada 2 min -> Wh/2min * 30 = W
descarga_max_w = -pasos.min() * 30

# ---------------------------------------------------------------------------
# P3. Diésel
# ---------------------------------------------------------------------------
eventos = d.loc[d["diesel_activo"], ["minuto", "hora_reloj", "etapa", "potencia_solar_w", "consumo_planta_w",
                                      "potencia_neta_w", "soc_pct", "diesel_wh", "combustible_l"]].copy()
eventos["deficit_sobre_limite_w"] = (-eventos["potencia_neta_w"] - descarga_max_w).round(1)
eventos["diesel_esperado_wh"] = (eventos["deficit_sobre_limite_w"] * 2 / 60).round(2)
eventos.to_csv(SALIDAS / "eventos_diesel.csv", index=False, encoding="utf-8")
litros = ultimo["combustible_acum_l"]

# ---------------------------------------------------------------------------
# P4. Agua, residuos y energía específica
# ---------------------------------------------------------------------------
agua = ultimo["agua_acum_m3"]
salmuera = ultimo["salmuera_acum_m3"]
lodos_g = int(ultimo["lodos_gruesos_acum_paq"])
lodos_f = int(ultimo["lodos_finos_acum_paq"])
minutos_preta = int((d["etapa"] == "Pretratamiento").sum())  # las 2 min de transición se excluyen (ver A17)
captado = d["caudal_m3_h"].iloc[0] * minutos_preta / 60
energia_osmosis_kwh = d.loc[d["etapa"].str.contains("smosis"), "energia_consumo_wh"].sum() / 1000

# ---------------------------------------------------------------------------
# Resúmenes por etapa y por hora
# ---------------------------------------------------------------------------
etapas = d.groupby("etapa").agg(
    minutos=("minuto", "size"),
    consumo_kwh=("energia_consumo_wh", lambda s: s.sum() / 1000),
    solar_kwh=("energia_solar_wh", lambda s: s.sum() / 1000),
    excedente_kwh=("excedente_wh", lambda s: s.sum() / 1000),
    diesel_wh=("diesel_wh", "sum"),
    agua_m3=("agua_m3", "sum"),
).round(3)
etapas["horas"] = (etapas["minutos"] / 60).round(2)
etapas.to_csv(SALIDAS / "resumen_etapas.csv", encoding="utf-8")

d["hora_sim"] = (d["minuto"] - 1) // 60 + 1
horario = d.groupby("hora_sim").agg(
    hora_reloj=("hora_reloj", "first"),
    radiacion_prom_w_m2=("radiacion_w_m2", "mean"),
    temperatura_prom_c=("temperatura_c", "mean"),
    solar_kwh=("energia_solar_wh", lambda s: s.sum() / 1000),
    consumo_kwh=("energia_consumo_wh", lambda s: s.sum() / 1000),
    excedente_kwh=("excedente_wh", lambda s: s.sum() / 1000),
    diesel_wh=("diesel_wh", "sum"),
    soc_min_pct=("soc_pct", "min"),
    agua_m3=("agua_m3", "sum"),
).round(3)
horario.to_csv(SALIDAS / "resumen_horario.csv", encoding="utf-8")

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
i_soc = d["soc_pct"].idxmin()
i_rad = d["radiacion_w_m2"].idxmax()
i_tmp = d["temperatura_c"].idxmax()
horas_operacion = (d["consumo_planta_w"] > 0).sum() / 60
kpis = {
    "horizonte_h": 30,
    "registros": int(len(d)),
    "agua_m3": round(agua, 2),
    "salmuera_m3": round(salmuera, 2),
    "recuperacion_pct": round(agua / (agua + salmuera) * 100, 1),
    "agua_captada_m3": round(captado, 1),
    "rendimiento_global_pct": round(agua / captado * 100, 1),
    "lodos_gruesos_paq": lodos_g, "lodos_finos_paq": lodos_f,
    "lodos_total_kg": (lodos_g + lodos_f) * 10,
    "lodos_kg_por_m3_captado": round((lodos_g + lodos_f) * 10 / captado, 1),
    "solar_kwh": round(solar_kwh, 1),
    "consumo_kwh": round(consumo_kwh, 1),
    "solar_directa_kwh": round(solar_directa_kwh, 1),
    "excedente_kwh": round(excedente_kwh, 1),
    "excedente_pct": round(excedente_kwh / solar_kwh * 100, 1),
    "aprovechamiento_solar_pct": round(100 - excedente_kwh / solar_kwh * 100, 1),
    "diesel_kwh": round(diesel_kwh, 3),
    "diesel_eventos": int(len(eventos)),
    "combustible_l": round(litros, 4),
    "consumo_especifico_l_kwh": round(litros / diesel_kwh, 3),
    "fraccion_renovable_pct": round((consumo_kwh - diesel_kwh) / consumo_kwh * 100, 2),
    "demanda_no_cubierta_wh": float(ultimo["demanda_no_cubierta_acum_wh"]),
    "kwh_por_m3": round(consumo_kwh / agua, 2),
    "kwh_por_m3_osmosis": round(energia_osmosis_kwh / agua, 2),
    "capacidad_bateria_kwh": round(CAPACIDAD_WH / 1000, 1),
    "soc_min_pct": round(d.loc[i_soc, "soc_pct"], 1),
    "soc_min_hora": d.loc[i_soc, "hora_reloj"],
    "bateria_carga_max_kw": round(carga_max_w / 1000, 1),
    "bateria_descarga_max_kw": round(descarga_max_w / 1000, 1),
    "bateria_ciclada_kwh": round(descarga_bat_kwh, 2),
    "horas_operacion": round(horas_operacion, 1),
    "utilizacion_pct": round(horas_operacion / 30 * 100, 1),
    "potencia_solar_max_kw": round(d["potencia_solar_w"].max() / 1000, 1),
    "radiacion_max_w_m2": round(d.loc[i_rad, "radiacion_w_m2"], 0),
    "radiacion_max_hora": d.loc[i_rad, "hora_reloj"],
    "temperatura_max_c": round(d.loc[i_tmp, "temperatura_c"], 1),
    "temperatura_max_hora": d.loc[i_tmp, "hora_reloj"],
    "auditoria_total": int(len(aud)),
    "auditoria_ok": int((aud["resultado"] == "OK").sum()),
    "auditoria_advertencia": int((aud["resultado"] == "Advertencia").sum()),
    "auditoria_corregido": int((aud["resultado"] == "Corregido").sum()),
}
(SALIDAS / "kpis.json").write_text(json.dumps(kpis, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------------------------------------------------------------------
# Figuras de respaldo (para informe y capturas)
# ---------------------------------------------------------------------------
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25})
C_SOLAR, C_CONS, C_EXC, C_DIE, C_AGUA, C_BAT = "#E8A33D", "#3B6EA8", "#B9C4D0", "#C2452D", "#2A9D8F", "#6A5ACD"
COLORES_ETAPA = {"Pretratamiento": "#F3E3C3", "Ósmosis inversa": "#CFE3F1", "Pretratamiento + ósmosis": "#E5D4EF"}
t = d["tiempo_h"]


def sombrear_etapas(ax):
    bloque = (d["etapa"] != d["etapa"].shift()).cumsum()
    for _, g in d.groupby(bloque):
        e = g["etapa"].iloc[0]
        if e in COLORES_ETAPA:
            ax.axvspan(g["tiempo_h"].iloc[0], g["tiempo_h"].iloc[-1], color=COLORES_ETAPA[e], alpha=0.6, lw=0)


def pie_fuente(fig):
    fig.text(0.01, 0.01, FUENTE, fontsize=7.5, color="#666")


# F1. Potencia solar vs consumo
fig, ax = plt.subplots(figsize=(10, 4.2))
sombrear_etapas(ax)
ax.plot(t, d["potencia_solar_w"] / 1000, color=C_SOLAR, lw=1.6, label="Potencia solar")
ax.plot(t, d["consumo_planta_w"] / 1000, color=C_CONS, lw=1.6, label="Consumo de la planta")
ax.scatter(eventos["minuto"] / 60, eventos["consumo_planta_w"] / 1000, color=C_DIE, zorder=5, s=25,
           label="Aporte diésel")
ax.set(title="Potencia solar frente a consumo de la planta", xlabel="Tiempo de simulación (h)", ylabel="kW",
       xlim=(0, 30))
from matplotlib.patches import Patch

handles, labels = ax.get_legend_handles_labels()
handles += [Patch(color=c, alpha=0.6) for c in COLORES_ETAPA.values()][:2]
labels += ["Pretratamiento", "Ósmosis inversa"]
ax.legend(handles, labels, loc="upper right", fontsize=8, frameon=False)
pie_fuente(fig)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIGURAS / "f1_potencia_vs_consumo.png", dpi=160)
plt.close(fig)

# F2. Destino de la energía solar
fig, ax = plt.subplots(figsize=(8, 2.6))
partes = [("Uso directo en la planta", solar_directa_kwh, C_CONS), ("Carga de batería", carga_bat_kwh, C_BAT),
          ("Excedente no aprovechado", excedente_kwh, C_EXC)]
izq = 0
for nombre, val, col in partes:
    ax.barh(0, val, left=izq, color=col)
    texto = f"{nombre}\n{val:,.1f} kWh ({val / solar_kwh * 100:.0f} %)".replace(".", ",")
    if val / solar_kwh < 0.08:   # segmento angosto: etiqueta fuera de la barra
        ax.annotate(texto, xy=(izq + val / 2, 0.4), xytext=(izq + val / 2 + 25, 0.62), fontsize=8.5,
                    ha="left", va="center", arrowprops={"arrowstyle": "-", "color": "#555"})
    else:
        ax.text(izq + val / 2, 0, texto, ha="center", va="center", fontsize=8.5,
                color="white" if col != C_EXC else "#222")
    izq += val
ax.set(title=f"Destino de la energía solar generada ({solar_kwh:,.1f} kWh)".replace(".", ","), yticks=[], ylim=(-0.6, 0.85),
       xlabel="kWh")
ax.grid(False)
pie_fuente(fig)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(FIGURAS / "f2_destino_energia_solar.png", dpi=160)
plt.close(fig)

# F3. Estado de carga y diésel
fig, ax = plt.subplots(figsize=(10, 3.8))
sombrear_etapas(ax)
ax.plot(t, d["soc_pct"], color=C_BAT, lw=1.6, label="Estado de carga")
ax.scatter(eventos["minuto"] / 60, eventos["soc_pct"], color=C_DIE, zorder=5, s=30, label="Aporte diésel")
ax.set(title="Estado de carga de la batería y momentos con aporte diésel", xlabel="Tiempo de simulación (h)",
       ylabel="%", xlim=(0, 30), ylim=(90, 100.8))
ax.legend(loc="lower right", fontsize=8, frameon=False)
pie_fuente(fig)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIGURAS / "f3_estado_carga_diesel.png", dpi=160)
plt.close(fig)

# F4. Producción acumulada
fig, ax = plt.subplots(figsize=(10, 3.8))
ax.plot(t, d["agua_acum_m3"], color=C_AGUA, lw=2, label="Agua desalinizada")
ax.plot(t, d["salmuera_acum_m3"], color="#8D6E63", lw=2, label="Salmuera")
ax.set(title="Producción acumulada de agua y salmuera", xlabel="Tiempo de simulación (h)", ylabel="m³",
       xlim=(0, 30))
ax.legend(loc="upper left", fontsize=8, frameon=False)
pie_fuente(fig)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIGURAS / "f4_produccion_acumulada.png", dpi=160)
plt.close(fig)

# F5. Resultado de la auditoría
fig, ax = plt.subplots(figsize=(6, 3))
cuenta = aud["resultado"].value_counts().reindex(["OK", "Corregido", "Advertencia"]).fillna(0)
ax.bar(cuenta.index, cuenta.values, color=["#2A9D8F", "#3B6EA8", "#E8A33D"])
for i, v in enumerate(cuenta.values):
    ax.text(i, v + 0.3, int(v), ha="center")
ax.set(title=f"Resultado de las {len(aud)} verificaciones de calidad", ylabel="Verificaciones")
pie_fuente(fig)
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(FIGURAS / "f5_auditoria.png", dpi=160)
plt.close(fig)

# ---------------------------------------------------------------------------
# Resumen en consola (hallazgos)
# ---------------------------------------------------------------------------
print("KPIs principales")
for k, v in kpis.items():
    print(f"  {k:28s} {v}")
print("\nResumen por etapa\n", etapas)
print("\nEventos diésel\n", eventos[["hora_reloj", "soc_pct", "deficit_sobre_limite_w", "diesel_wh",
                                     "diesel_esperado_wh"]])
print("\nRadiación y potencia en horas de sol\n", desc_dia)

# F7. Excedente por hora (horas de sol)
sol_h = horario[horario["solar_kwh"] > 0.5].copy()
usada = sol_h["solar_kwh"] - sol_h["excedente_kwh"]
etiquetas = [h[:2] + ":00" for h in sol_h["hora_reloj"]]
foco = sol_h["hora_reloj"].str[:2].isin(["11", "12", "13"])
fig, ax = plt.subplots(figsize=(10, 4.6))
ax.bar(etiquetas, usada, color="#B9C4D0", label="Usada por la planta o la batería")
ax.bar(etiquetas, sol_h["excedente_kwh"], bottom=usada, color=np.where(foco, C_CONS, "#8FB0CF"),
       label="Excedente no aprovechado")
exc_foco = sol_h.loc[foco, "excedente_kwh"].sum()
ax.set(title=f"Entre 11:00 y 14:00 se pierde el {exc_foco / excedente_kwh * 100:.0f} % del excedente solar",
       ylabel="kWh por hora")
ax.annotate(f"{exc_foco:,.1f} kWh".replace(".", ","), xy=(6, sol_h["solar_kwh"].max() + 1), ha="center",
            fontsize=11, fontweight="bold")
ax.grid(axis="x", visible=False)
ax.legend(loc="upper left", fontsize=8.5, frameon=False)
pie_fuente(fig)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIGURAS / "f7_excedente_por_hora.png", dpi=160)
plt.close(fig)
