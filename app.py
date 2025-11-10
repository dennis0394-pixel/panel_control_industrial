import pandas as pd
import numpy as np
import os
from sklearn.ensemble import IsolationForest
import plotly.express as px
import streamlit as st

# ===================== CONFIGURACIÓN =====================
st.set_page_config(page_title="Panel de Monitoreo Industrial 4.0",
                   layout="wide",
                   page_icon="⚙️")

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2721/2721283.png", width=80)
st.sidebar.title("⚙️ Control de Motor - V4.0")
modo = st.sidebar.radio("Selecciona vista:",
                        ["📊 Monitoreo en Vivo", "📈 Histórico", "🚨 Alarmas y Mantenimiento"])
st.sidebar.info("Sistema Industrial 4.0 — Cloud Edition")

# =========================================================
# 📂 CARGA DE DATOS
# =========================================================
st.subheader("📂 Carga de Datos del Motor")

try:
    df = pd.read_csv("datos_motor.csv", encoding="utf-8", sep=",")
    st.success("✅ Datos cargados correctamente desde 'datos_motor.csv'")
except Exception as e:
    st.error(f"⚠️ No se pudo leer 'datos_motor.csv'. Se usarán datos simulados. ({e})")
    df = pd.DataFrame({
        "Corriente_motor (A)": [18.5, 17.9, 16.8, 19.2, 18.7, 17.4, 15.9, 10.8, 11.2, 10.4],
        "Torque (Nm)": [160.4, 158.7, 157.3, 162.8, 159.9, 155.6, 152.0, 138.5, 140.2, 139.8],
        "Presión_hidráulica (bar)": [90.2, 88.9, 87.3, 91.0, 89.5, 88.1, 85.7, 82.1, 80.4, 80.6],
        "Temperatura_aceite (°C)": [68.4, 70.1, 67.5, 72.3, 69.8, 71.2, 65.9, 42.0, 41.8, 43.5]
    })

# Limpieza: reemplazar comas por puntos y convertir a número
for col in df.columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace('"', "", regex=False)
        .str.replace("'", "", regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Mostrar vista previa
st.write("🔍 Vista previa de los datos cargados:")
st.dataframe(df.head())

# Seleccionar solo columnas numéricas
df_numerico = df.select_dtypes(include=["float64", "int64"]).dropna()

# Mostrar diagnóstico
st.info(f"🔢 Columnas numéricas detectadas: {list(df_numerico.columns)}")
st.info(f"📏 Filas válidas encontradas: {len(df_numerico)}")

if df_numerico.empty:
    st.error("""
    ⚠️ No hay datos válidos en el archivo `datos_motor.csv`.
    Revisa que:
    - Los números usen punto (.) como separador decimal.
    - El separador de columnas sea coma (,).
    - No haya celdas vacías ni texto.
    """)
    st.stop()

# =========================================================
# 📊 MONITOREO EN VIVO
# =========================================================
if modo == "📊 Monitoreo en Vivo":
    st.title("🧠 Monitoreo en Tiempo Real del Motor")

    model = IsolationForest(contamination=0.3, random_state=42)
    df["riesgo_falla"] = model.fit_predict(df_numerico)
    df["riesgo_falla"] = df["riesgo_falla"].map({1: "Normal", -1: "Riesgo"})

    conteo = df["riesgo_falla"].value_counts()
    col1, col2, col3 = st.columns(3)
    col1.metric("⚠️ Riesgos Detectados", conteo.get("Riesgo", 0))
    col2.metric("✅ Normales", conteo.get("Normal", 0))
    col3.metric("📊 Registros Totales", len(df))

    st.markdown("---")
    st.dataframe(df)

    fig = px.bar(conteo, x=conteo.index, y=conteo.values,
                 color=conteo.index,
                 color_discrete_map={"Normal": "#10B981", "Riesgo": "#EF4444"},
                 title="Distribución de Riesgos de Falla")
    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# 📈 HISTÓRICO
# =========================================================
elif modo == "📈 Histórico":
    st.title("📈 Histórico de Variables")
    tiempo = np.arange(0, 100)
    torque = 150 + 5 * np.sin(tiempo / 5) + np.random.normal(0, 1, 100)
    temperatura = 60 + 8 * np.sin(tiempo / 8) + np.random.normal(0, 1, 100)
    hist = pd.DataFrame({"Tiempo (min)": tiempo, "Torque (Nm)": torque, "Temperatura_aceite (°C)": temperatura})

    fig_line = px.line(hist, x="Tiempo (min)", y=["Torque (Nm)", "Temperatura_aceite (°C)"],
                       title="Evolución del Torque y Temperatura")
    st.plotly_chart(fig_line, use_container_width=True)

# =========================================================
# 🚨 ALARMAS Y MANTENIMIENTO
# =========================================================
else:
    st.title("🚨 Historial de Alarmas")
    if os.path.exists("alarmas_log.csv"):
        log = pd.read_csv("alarmas_log.csv")
        st.success(f"📁 {len(log)} alarmas registradas históricamente.")
        st.dataframe(log)
    else:
        st.warning("⚠️ No se encontraron alarmas previas.")
