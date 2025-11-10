import pandas as pd
import numpy as np
import datetime
import os
from sklearn.ensemble import IsolationForest
import plotly.express as px
import streamlit as st

# ===================== CONFIGURACIÓN =====================
st.set_page_config(page_title="Panel de Monitoreo Industrial 4.0",
                   layout="wide",
                   page_icon="⚙️")

# ===================== ESTILOS =====================
st.markdown("""
<style>
    .main { background-color: #F4F7FA; }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1F2937, #374151);
        color: white;
    }
    h1, h2, h3 { color: #1F2937; }
    .stMetricLabel { color: #6B7280 !important; }
</style>
""", unsafe_allow_html=True)

# ===================== SIDEBAR =====================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2721/2721283.png", width=80)
st.sidebar.title("⚙️ Control de Motor - V4.0")
modo = st.sidebar.radio("Selecciona vista:",
                        ["📊 Monitoreo en Vivo", "📈 Histórico", "🚨 Alarmas y Mantenimiento", "➕ Ingreso Manual"])
st.sidebar.info("Sistema Industrial 4.0 — Cloud Edition (Streamlit Cloud)")

# ===================== DATOS BASE =====================

try:
    # Intenta leer con varios formatos de codificación y separadores
    try:
        df = pd.read_csv("datos_motor.csv", encoding='utf-8', sep=',')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv("datos_motor.csv", encoding='latin-1', sep=',')
        except Exception:
            df = pd.read_csv("datos_motor.csv", encoding='latin-1', sep=';')

    st.sidebar.success("✅ Datos cargados correctamente desde 'datos_motor.csv'")
except FileNotFoundError:
    st.sidebar.warning("⚠️ No se encontró 'datos_motor.csv', creando datos de ejemplo...")
    df = pd.DataFrame({
        "Corriente_motor (A)": [18.5, 17.9, 16.8, 19.2, 18.7, 17.4, 15.9, 10.8, 11.2, 10.4],
        "Torque (Nm)": [160.4, 158.7, 157.3, 162.8, 159.9, 155.6, 152.0, 138.5, 140.2, 139.8],
        "Presión_hidráulica (bar)": [90.2, 88.9, 87.3, 91.0, 89.5, 88.1, 85.7, 82.1, 80.4, 80.6],
        "Temperatura_aceite (°C)": [68.4, 70.1, 67.5, 72.3, 69.8, 71.2, 65.9, 42.0, 41.8, 43.5]
    })

# =========================================================
# 📊 MODO 1: MONITOREO EN VIVO
# =========================================================
if modo == "📊 Monitoreo en Vivo":
    st.title("🧠 Monitoreo en Tiempo Real del Motor")

    model = IsolationForest(contamination=0.5, random_state=42)
    df["riesgo_falla"] = model.fit_predict(df)
    df["riesgo_falla"] = df["riesgo_falla"].map({1: "Normal", -1: "Riesgo"})

    def diagnostico_falla(row):
        if row["riesgo_falla"] == "Normal":
            return "Sin anomalías detectadas"
        if row["Corriente_motor (A)"] > 16:
            return "Posible sobrecarga eléctrica"
        elif row["Presión_hidráulica (bar)"] < 80:
            return "Presión baja — posible fuga"
        elif row["Temperatura_aceite (°C)"] > 63:
            return "Temperatura alta — riesgo de sobrecalentamiento"
        elif row["Torque (Nm)"] > 150:
            return "Torque elevado — posible fricción"
        else:
            return "Anomalía no clasificada"

    df["causa_probable"] = df.apply(diagnostico_falla, axis=1)
    conteo = df["riesgo_falla"].value_counts()

    col1, col2, col3 = st.columns(3)
    col1.metric("⚠️ Riesgos Detectados", conteo.get("Riesgo", 0))
    col2.metric("✅ Normales", conteo.get("Normal", 0))
    col3.metric("📊 Registros Totales", len(df))

    # Guardar alarmas si hay riesgo
    if "Riesgo" in df["riesgo_falla"].values:
        riesgos = df[df["riesgo_falla"] == "Riesgo"]
        for _, fila in riesgos.iterrows():
            nueva_alarma = pd.DataFrame([{
                "Fecha_Hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Variable": "Temperatura_aceite (°C)" if fila["Temperatura_aceite (°C)"] > 63 else "General",
                "Nivel": "Alta",
                "Descripción": fila["causa_probable"],
                "Estado": "Pendiente"
            }])
            if os.path.exists("alarmas_log.csv"):
                log = pd.read_csv("alarmas_log.csv")
                log = pd.concat([log, nueva_alarma], ignore_index=True)
            else:
                log = nueva_alarma
            log.to_csv("alarmas_log.csv", index=False)

    fig_barras = px.bar(conteo, x=conteo.index, y=conteo.values,
                        color=conteo.index,
                        color_discrete_map={"Normal": "#10B981", "Riesgo": "#EF4444"},
                        title="Distribución de Riesgos de Falla")
    st.plotly_chart(fig_barras, use_container_width=True)
    st.dataframe(df)

# =========================================================
# 📈 MODO 2: HISTÓRICO
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
# 🚨 MODO 3: ALARMAS
# =========================================================
elif modo == "🚨 Alarmas y Mantenimiento":
    st.title("🚨 Historial de Alarmas")
    if os.path.exists("alarmas_log.csv"):
        log = pd.read_csv("alarmas_log.csv")
        st.success(f"📁 {len(log)} alarmas registradas históricamente.")
        st.dataframe(log)
    else:
        st.warning("⚠️ No se encontraron alarmas previas.")

# =========================================================
# ➕ MODO 4: INGRESO MANUAL
# =========================================================
else:
    st.title("➕ Ingreso Manual de Nuevos Datos")
    with st.form("nuevo_dato"):
        corriente = st.number_input("Corriente (A)", 0.0)
        torque = st.number_input("Torque (Nm)", 0.0)
        presion = st.number_input("Presión hidráulica (bar)", 0.0)
        temp = st.number_input("Temperatura aceite (°C)", 0.0)
        enviado = st.form_submit_button("Guardar registro")

    if enviado:
        nuevo = pd.DataFrame([{
            "Corriente_motor (A)": corriente,
            "Torque (Nm)": torque,
            "Presión_hidráulica (bar)": presion,
            "Temperatura_aceite (°C)": temp
        }])
        df = pd.concat([df, nuevo], ignore_index=True)
        df.to_csv("datos_motor.csv", index=False)
        st.success("✅ Nuevo dato guardado correctamente.")

