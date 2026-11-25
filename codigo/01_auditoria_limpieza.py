"""
01 - Auditoría de calidad y limpieza de datos
Proyecto final - Electiva III: Introducción a la Ciencia de Datos

Entrada : datos/original/resultados_escenario_1.xlsx (4 hojas: Minutos, Cada5min, Cada10min, Horas)
Salidas : datos/limpio/escenario1_limpio.csv
          datos/limpio/escenario1_limpio.xlsx (datos limpios + auditoría + diccionario)
          salidas/auditoria.csv

Ejecutar desde la carpeta raíz del proyecto:  python codigo/01_auditoria_limpieza.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ORIGINAL = RAIZ / "datos" / "original" / "resultados_escenario_1.xlsx"
LIMPIO_DIR = RAIZ / "datos" / "limpio"
SALIDAS = RAIZ / "salidas"
LIMPIO_DIR.mkdir(parents=True, exist_ok=True)
SALIDAS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Carga e inspección de estructura
# ---------------------------------------------------------------------------
libro = pd.ExcelFile(ORIGINAL)
hojas = {nombre: pd.read_excel(libro, nombre) for nombre in libro.sheet_names}
crudo = hojas["Minutos"].copy()

print("Hojas y tamaño:")
for nombre, df in hojas.items():
    print(f"  {nombre:10s} {df.shape[0]:5d} filas x {df.shape[1]} columnas")

# Diccionario de nombres: original -> limpio (snake_case con unidad)
RENOMBRAR = {
    "Minuto": "minuto",
    "Caudal (m3/h)": "caudal_m3_h",
    "Radiación solar (W/m2)": "radiacion_w_m2",
    "Temperatura (°C)": "temperatura_c",
    "Velocidad del viento (m/s) ": "viento_m_s",
    "Potencia solar (W)": "potencia_solar_w",
    "Potencia neta (W)": "potencia_neta_w",
    "Energía almacenada (W)": "energia_bateria_wh",
    "Consumo planta (W)": "consumo_planta_w",
    "Agua desalinizada (m3)": "agua_acum_m3",
    "Salmuera (m3)": "salmuera_acum_m3",
    "Lodos gruesos (N.º paquetes de 10 kg)": "lodos_gruesos_acum_paq",
    "Lodos finos (N.º paquetes de 10 kg)": "lodos_finos_acum_paq",
    "% estado de carga": "soc_pct",
    "Wh acum. excedente no aprovechado": "excedente_acum_wh",
    "Wh acum. entregados por el diesel": "diesel_acum_wh",
    "L acum. de combustible": "combustible_acum_l",
    "Wh acum. de demanda no cubierta": "demanda_no_cubierta_acum_wh",
}
DESCRIPCION = {
    "minuto": ("min", "Minuto transcurrido de simulación (1 a 1.800)"),
    "caudal_m3_h": ("m³/h", "Caudal de captación de agua"),
    "radiacion_w_m2": ("W/m²", "Radiación solar sobre los paneles"),
    "temperatura_c": ("°C", "Temperatura ambiente"),
    "viento_m_s": ("m/s", "Velocidad del viento (no se usa para generar en este escenario)"),
    "potencia_solar_w": ("W", "Potencia entregada por los paneles"),
    "potencia_neta_w": ("W", "Potencia solar menos consumo de la planta"),
    "energia_bateria_wh": ("Wh", "Energía almacenada en la batería (el original dice W)"),
    "consumo_planta_w": ("W", "Potencia demandada por la planta"),
    "agua_acum_m3": ("m³", "Agua desalinizada acumulada"),
    "salmuera_acum_m3": ("m³", "Salmuera acumulada"),
    "lodos_gruesos_acum_paq": ("paquetes de 10 kg", "Lodos gruesos acumulados"),
    "lodos_finos_acum_paq": ("paquetes de 10 kg", "Lodos finos acumulados"),
    "soc_pct": ("%", "Estado de carga de la batería"),
    "excedente_acum_wh": ("Wh", "Energía solar excedente no aprovechada, acumulada"),
    "diesel_acum_wh": ("Wh", "Energía entregada por el generador diésel, acumulada"),
    "combustible_acum_l": ("L", "Combustible diésel consumido, acumulado"),
    "demanda_no_cubierta_acum_wh": ("Wh", "Demanda de la planta que no se pudo cubrir, acumulada"),
}

auditoria = []  # cada fila: id, categoría, verificación, resultado, afectados, decisión


def es(valor, decimales=1):
    """Formato numérico en español: 1.234,5"""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def registrar(categoria, verificacion, resultado, afectados, decision):
    auditoria.append({
        "id": f"A{len(auditoria) + 1:02d}",
        "categoria": categoria,
        "verificacion": verificacion,
        "resultado": resultado,          # OK | Advertencia | Corregido
        "registros_afectados": int(afectados),
        "decision": decision,
    })


# ---------------------------------------------------------------------------
# 2. Verificaciones de estructura y completitud
# ---------------------------------------------------------------------------
desconocidas = [c for c in crudo.columns if c not in RENOMBRAR]
registrar("Estructura", "Columnas esperadas (18) presentes en la hoja Minutos",
          "OK" if not desconocidas else "Advertencia", len(desconocidas),
          "Se renombran a formato snake_case con la unidad en el nombre.")

espacios = [c for c in crudo.columns if c != c.strip()]
registrar("Formato", "Encabezados con espacios sobrantes",
          "Corregido" if espacios else "OK", len(espacios),
          f"Se eliminó el espacio final en: {', '.join(repr(c) for c in espacios)}." if espacios else "Sin cambios.")

df = crudo.rename(columns=RENOMBRAR)

nulos = int(df.isna().sum().sum())
registrar("Completitud", "Valores nulos en todas las columnas", "OK" if nulos == 0 else "Advertencia", nulos,
          "No hay nulos; no se requiere imputación.")

tipos_no_numericos = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
registrar("Tipos", "Todas las columnas son numéricas", "OK" if not tipos_no_numericos else "Advertencia",
          len(tipos_no_numericos), "Tipos correctos (entero y decimal).")

# Continuidad temporal
esperado = np.arange(1, 1801)
saltos = int((df["minuto"].values != esperado).sum())
registrar("Continuidad", "Minutos consecutivos de 1 a 1.800 sin saltos", "OK" if saltos == 0 else "Advertencia",
          saltos, "Serie temporal completa (30 horas).")

dup_clave = int(df["minuto"].duplicated().sum())
registrar("Duplicados", "Minutos repetidos (clave duplicada)", "OK" if dup_clave == 0 else "Advertencia", dup_clave,
          "No hay claves duplicadas.")

cuerpo = df.drop(columns="minuto")
repetidas = int(cuerpo.duplicated().sum())
registrar("Duplicados", "Filas con valores idénticos a otra fila (sin contar el minuto)", "Advertencia", repetidas,
          "Se conservan: son estados reales repetidos (planta detenida de noche) en minutos distintos, "
          "no registros duplicados.")

# ---------------------------------------------------------------------------
# 3. Consistencia entre hojas (5, 10 y 60 min frente a la hoja de minutos)
# ---------------------------------------------------------------------------
base_idx = crudo.set_index("Minuto")
for nombre, factor in [("Cada5min", 1), ("Cada10min", 1), ("Horas", 60)]:
    otra = hojas[nombre]
    tiempos = otra.iloc[:, 0] * factor
    sub = base_idx.loc[tiempos.values].reset_index(drop=True)
    diferencias = int((np.abs(sub.values - otra.iloc[:, 1:].values) > 1e-6).sum())
    registrar("Consistencia entre hojas",
              f"La hoja {nombre} coincide con la hoja Minutos en los mismos instantes",
              "OK" if diferencias == 0 else "Advertencia", diferencias,
              "Es una muestra del último minuto de cada intervalo (no un promedio). "
              "Se usa la hoja Minutos como base única; las otras resoluciones se recalculan agregando.")

# ---------------------------------------------------------------------------
# 4. Unidades y rangos
# ---------------------------------------------------------------------------
registrar("Unidades", "Unidad de 'Energía almacenada' declarada como W", "Corregido", len(df),
          "Es energía, no potencia: se renombra a energia_bateria_wh (Wh).")

CAPACIDAD_WH = float(df["energia_bateria_wh"].max())
registrar("Rangos", f"Capacidad de batería inferida = {es(CAPACIDAD_WH, 0)} Wh (máximo observado)", "OK", 0,
          "Se usa para validar el estado de carga.")

no_negativas = ["caudal_m3_h", "radiacion_w_m2", "viento_m_s", "potencia_solar_w", "energia_bateria_wh",
                "consumo_planta_w"]
negativos = int((df[no_negativas] < 0).sum().sum())
registrar("Rangos", "Variables físicas no negativas (caudal, radiación, viento, potencias, energía)",
          "OK" if negativos == 0 else "Advertencia", negativos,
          "Sin negativos. La potencia neta sí puede ser negativa (la planta consume más de lo que genera).")

fuera_soc = int(((df["soc_pct"] < 0) | (df["soc_pct"] > 100)).sum())
registrar("Rangos", "Estado de carga entre 0 % y 100 %", "OK" if fuera_soc == 0 else "Advertencia", fuera_soc,
          "Dentro de rango.")

constante = df.columns[(df.nunique() == 1)].tolist()
registrar("Variabilidad", "Columnas sin variación", "Advertencia" if constante else "OK", len(constante),
          f"Constantes: {', '.join(constante)}. El caudal (11,67 m³/h) es un parámetro de la simulación y la "
          "demanda no cubierta vale 0 en todo el periodo (resultado relevante). Se conservan, pero no aportan "
          "en correlaciones ni en el modelo." if constante else "Sin columnas constantes.")

# ---------------------------------------------------------------------------
# 5. Inconsistencias lógicas
# ---------------------------------------------------------------------------
soc_calculado = df["energia_bateria_wh"] / CAPACIDAD_WH * 100
desvio_soc = (df["soc_pct"] - soc_calculado).abs()
mal_soc = desvio_soc > 0.01
registrar("Inconsistencia", "Estado de carga coherente con la energía almacenada (SOC = energía / capacidad)",
          "Corregido", int(mal_soc.sum()),
          f"Minutos {', '.join(map(str, df.loc[mal_soc, 'minuto']))}: SOC = 0 % con la batería llena "
          "(error de arranque de la simulación). Se recalcula SOC = energía / capacidad × 100.")
df["soc_corregido"] = mal_soc
df.loc[mal_soc, "soc_pct"] = soc_calculado[mal_soc]

neta_calc = df["potencia_solar_w"] - df["consumo_planta_w"]
mal_neta = (df["potencia_neta_w"] - neta_calc).abs() > 0.5
df["inconsistencia_neta"] = mal_neta
registrar("Inconsistencia", "Potencia neta = potencia solar − consumo", "OK" if not mal_neta.any() else "Advertencia",
          int(mal_neta.sum()),
          f"Falla en los minutos {', '.join(map(str, df.loc[mal_neta, 'minuto']))}, justo en cambios de etapa: "
          "el consumo cambia 2 minutos antes que la potencia neta. El pico de 31,6 kW (ambas etapas a la vez) "
          "aparece solo en el consumo, por lo que se trata como posible efecto de transición. No se puede saber "
          "qué columna es la correcta: se conservan los valores y se marcan (columna inconsistencia_neta).")

acumuladas = ["agua_acum_m3", "salmuera_acum_m3", "lodos_gruesos_acum_paq", "lodos_finos_acum_paq",
              "excedente_acum_wh", "diesel_acum_wh", "combustible_acum_l", "demanda_no_cubierta_acum_wh"]
decrecientes = int((df[acumuladas].diff().iloc[1:] < -1e-9).sum().sum())
registrar("Inconsistencia", "Columnas acumuladas nunca disminuyen", "OK" if decrecientes == 0 else "Advertencia",
          decrecientes, "Todas las acumuladas son no decrecientes.")

# Ruido de punto flotante (p. ej. 3160.4999999 frente a 3160.5)
valores_consumo_antes = df["consumo_planta_w"].nunique()
redondeo = {"potencia_solar_w": 2, "potencia_neta_w": 2, "consumo_planta_w": 1, "energia_bateria_wh": 2,
            "agua_acum_m3": 4, "salmuera_acum_m3": 4, "excedente_acum_wh": 2, "diesel_acum_wh": 2,
            "combustible_acum_l": 5, "soc_pct": 3, "temperatura_c": 2, "viento_m_s": 2, "radiacion_w_m2": 2}
df = df.round(redondeo)
valores_consumo_despues = df["consumo_planta_w"].nunique()
registrar("Formato", "Ruido de punto flotante (mismo valor escrito distinto, p. ej. 3160,4999 y 3160,5)",
          "Corregido", valores_consumo_antes - valores_consumo_despues,
          f"Consumo pasó de {valores_consumo_antes} a {valores_consumo_despues} niveles distintos tras redondear "
          "a precisión física razonable (0,1 W; 0,0001 m³).")

# Actualización cada 2 minutos (escalonamiento)
cambios_rad = df.loc[df["radiacion_w_m2"].diff() != 0, "minuto"]
cambios_pot = df.loc[df["potencia_solar_w"].diff() != 0, "minuto"]
registrar("Resolución", "Frecuencia real de actualización de las variables",
          "Advertencia", int((df["temperatura_c"].diff() == 0).sum()),
          "Clima y energía cambian cada 2 minutos y se repiten en el minuto siguiente. "
          "La resolución efectiva es de 2 minutos; se documenta y no se modifica.")

# Desfase temporal radiación -> potencia solar
dia = (df["radiacion_w_m2"] > 0) | (df["potencia_solar_w"] > 0)
rad_prev = df["radiacion_w_m2"].shift(1)
corr_sin = np.corrcoef(df.loc[dia, "radiacion_w_m2"], df.loc[dia, "potencia_solar_w"])[0, 1]
mask = dia & rad_prev.notna()
corr_con = np.corrcoef(rad_prev[mask], df.loc[mask, "potencia_solar_w"])[0, 1]
registrar("Desfase temporal",
          "La potencia solar responde a la radiación del minuto anterior",
          "Corregido", int(dia.sum()),
          f"Radiación cambia en minutos impares y potencia en pares. Correlación sin alinear r = {es(corr_sin, 4)}; "
          f"alineando 1 minuto r = {es(corr_con, 4)}. Se agrega la columna radiacion_alineada_w_m2 "
          "y se conserva la original.")
df["radiacion_alineada_w_m2"] = rad_prev.fillna(0.0).round(2)

# Valores atípicos: relación potencia/radiación (rendimiento aparente)
ratio = df.loc[df["radiacion_w_m2"] > 0, "potencia_solar_w"] / df.loc[df["radiacion_w_m2"] > 0, "radiacion_w_m2"]
q1, q3 = ratio.quantile([0.25, 0.75])
iqr = q3 - q1
atipicos = ratio[(ratio < q1 - 1.5 * iqr) | (ratio > q3 + 1.5 * iqr)]
ok_al = df["radiacion_alineada_w_m2"] > 0
ratio_al = df.loc[ok_al, "potencia_solar_w"] / df.loc[ok_al, "radiacion_alineada_w_m2"]
q1a, q3a = ratio_al.quantile([0.25, 0.75])
iqra = q3a - q1a
atip_al = ratio_al[(ratio_al < q1a - 1.5 * iqra) | (ratio_al > q3a + 1.5 * iqra)]
df["atipico_ratio_original"] = False
df.loc[atipicos.index, "atipico_ratio_original"] = True
registrar("Atípicos", "Relación potencia solar / radiación (regla IQR × 1,5)",
          "Advertencia", len(atipicos),
          f"{len(atipicos)} atípicos con los datos originales; {len(atip_al)} tras alinear el desfase. "
          "Se marcan (columna atipico_ratio_original) y no se eliminan: su causa es el desfase, no un error "
          "de medición.")

for col in ["temperatura_c", "viento_m_s"]:
    s = df[col]
    a, b = s.quantile([0.25, 0.75])
    n = int(((s < a - 1.5 * (b - a)) | (s > b + 1.5 * (b - a))).sum())
    registrar("Atípicos", f"Valores extremos en {col} (regla IQR × 1,5)", "OK" if n == 0 else "Advertencia", n,
              f"Rango {es(s.min(), 2)} a {es(s.max(), 2)}: sin valores físicamente imposibles; se conservan.")

# Balance de energía: solar − consumo − Δbatería + diésel ≈ excedente
solar_wh = df["potencia_solar_w"].sum() / 60
consumo_wh = df["consumo_planta_w"].sum() / 60
delta_bat = df["energia_bateria_wh"].iloc[-1] - df["energia_bateria_wh"].iloc[0]
diesel_wh = df["diesel_acum_wh"].iloc[-1]
balance = solar_wh - consumo_wh - delta_bat + diesel_wh
excedente_wh = df["excedente_acum_wh"].iloc[-1]
dif_pct = (excedente_wh - balance) / excedente_wh * 100
registrar("Balance energético",
          "Excedente reportado frente a balance (solar − consumo − Δbatería + diésel)",
          "Advertencia" if abs(dif_pct) > 0.1 else "OK", 0,
          f"Reportado {es(excedente_wh / 1000)} kWh; balance {es(balance / 1000)} kWh; diferencia "
          f"{es(dif_pct, 2)} %. Diferencia menor, atribuible al paso de 2 minutos del modelo; se documenta.")

# ---------------------------------------------------------------------------
# 6. Variables derivadas
# ---------------------------------------------------------------------------
df["tiempo_h"] = (df["minuto"] / 60).round(4)
df["dia"] = np.where(df["minuto"] <= 1440, 1, 2)
minuto_reloj = df["minuto"] % 1440
df["hora_reloj"] = [f"{m // 60:02d}:{m % 60:02d}" for m in minuto_reloj]


def etapa(consumo):
    if consumo == 0:
        return "Parada"
    if abs(consumo - 3160.5) < 1:
        return "Pretratamiento"
    if abs(consumo - 28444.5) < 1:
        return "Ósmosis inversa"
    return "Pretratamiento + ósmosis"


df["etapa"] = df["consumo_planta_w"].apply(etapa)
df["energia_solar_wh"] = (df["potencia_solar_w"] / 60).round(3)
df["energia_consumo_wh"] = (df["consumo_planta_w"] / 60).round(3)
for col, nuevo in [("agua_acum_m3", "agua_m3"), ("salmuera_acum_m3", "salmuera_m3"),
                   ("excedente_acum_wh", "excedente_wh"), ("diesel_acum_wh", "diesel_wh"),
                   ("combustible_acum_l", "combustible_l"), ("lodos_gruesos_acum_paq", "lodos_gruesos_paq"),
                   ("lodos_finos_acum_paq", "lodos_finos_paq")]:
    df[nuevo] = df[col].diff().fillna(df[col].iloc[0]).clip(lower=0).round(6)
df["diesel_activo"] = df["diesel_wh"] > 0

etapas_cuenta = df["etapa"].value_counts()
registrar("Variables derivadas", "Etapa de la planta según el nivel de consumo", "OK", len(df),
          "; ".join(f"{k}: {v} min" for k, v in etapas_cuenta.items()) +
          ". Supuesto: el minuto 0 corresponde a las 00:00 (el sol sale 06:03 y se pone 18:00).")

# ---------------------------------------------------------------------------
# 7. Guardado
# ---------------------------------------------------------------------------
orden = (["minuto", "tiempo_h", "dia", "hora_reloj", "etapa"] + list(RENOMBRAR.values())[1:] +
         ["radiacion_alineada_w_m2", "energia_solar_wh", "energia_consumo_wh", "agua_m3", "salmuera_m3",
          "lodos_gruesos_paq", "lodos_finos_paq", "excedente_wh", "diesel_wh", "combustible_l",
          "diesel_activo", "soc_corregido", "atipico_ratio_original", "inconsistencia_neta"])
limpio = df[orden]
aud = pd.DataFrame(auditoria)

derivadas = {
    "tiempo_h": ("h", "Tiempo transcurrido en horas"),
    "dia": ("-", "Día de simulación (1 o 2)"),
    "hora_reloj": ("HH:MM", "Hora del día (supuesto: inicio a las 00:00)"),
    "etapa": ("-", "Parada, Pretratamiento, Ósmosis inversa o ambas"),
    "radiacion_alineada_w_m2": ("W/m²", "Radiación del minuto anterior (corrige el desfase)"),
    "energia_solar_wh": ("Wh", "Energía solar generada en el minuto"),
    "energia_consumo_wh": ("Wh", "Energía consumida por la planta en el minuto"),
    "agua_m3": ("m³", "Agua producida en el minuto"),
    "salmuera_m3": ("m³", "Salmuera producida en el minuto"),
    "lodos_gruesos_paq": ("paquetes", "Lodos gruesos generados en el minuto"),
    "lodos_finos_paq": ("paquetes", "Lodos finos generados en el minuto"),
    "excedente_wh": ("Wh", "Excedente solar no aprovechado en el minuto"),
    "diesel_wh": ("Wh", "Energía diésel en el minuto"),
    "combustible_l": ("L", "Combustible consumido en el minuto"),
    "diesel_activo": ("bool", "Hubo aporte diésel en el minuto"),
    "soc_corregido": ("bool", "El estado de carga fue recalculado"),
    "atipico_ratio_original": ("bool", "Atípico en potencia/radiación con datos sin alinear"),
    "inconsistencia_neta": ("bool", "Potencia neta distinta de solar − consumo (cambio de etapa)"),
}
inverso = {v: k for k, v in RENOMBRAR.items()}
dicc = pd.DataFrame([
    {"columna": c, "columna_original": inverso.get(c, "(derivada)"),
     "unidad": {**DESCRIPCION, **derivadas}[c][0], "descripcion": {**DESCRIPCION, **derivadas}[c][1]}
    for c in orden
])

limpio.to_csv(LIMPIO_DIR / "escenario1_limpio.csv", index=False, encoding="utf-8")
aud.to_csv(SALIDAS / "auditoria.csv", index=False, encoding="utf-8")
with pd.ExcelWriter(LIMPIO_DIR / "escenario1_limpio.xlsx") as w:
    limpio.to_excel(w, sheet_name="datos_limpios", index=False)
    aud.to_excel(w, sheet_name="auditoria", index=False)
    dicc.to_excel(w, sheet_name="diccionario", index=False)

print(f"\nBase limpia: {limpio.shape[0]} filas x {limpio.shape[1]} columnas")
print(f"Verificaciones: {len(aud)} | " + ", ".join(f"{k}: {v}" for k, v in aud['resultado'].value_counts().items()))
print(aud[["id", "categoria", "resultado", "registros_afectados"]].to_string(index=False))
