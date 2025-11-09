
import pandas as pd
import numpy as np
import datetime
from sklearn.ensemble import IsolationForest
import plotly.express as px
import streamlit as st
import os

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
                        ["📊 Monitoreo en Vivo", "📈 Histórico", "🚨 Alarmas y Mantenimiento"])
st.sidebar.info("Sistema Industrial 4.0 — con almacenamiento CSV persistente")


# ===================== DATOS BASE =====================
# 📂 Cargar datos desde archivo CSV externo
try:
    df = pd.read_csv("/content/datos_motor.csv")
    st.success("✅ Datos cargados correctamente desde datos_motor.csv")
except FileNotFoundError:
    st.error("⚠️ No se encontró el archivo 'datos_motor.csv'. Verifica que esté en la carpeta del proyecto.")
    df = pd.DataFrame(columns=[
        "Corriente_motor (A)",
        "Torque (Nm)",
        "Presión_hidráulica (bar)",
        "Temperatura_aceite (°C)"
    ])


# ==============================================================
# 📊 MODO 1: MONITOREO EN VIVO
# ==============================================================
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

    st.markdown("---")

    # 📍 Registrar alarmas si hay riesgo
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

    # 🔹 Gráficos
    fig_barras = px.bar(conteo, x=conteo.index, y=conteo.values,
                        color=conteo.index,
                        color_discrete_map={"Normal": "#10B981", "Riesgo": "#EF4444"},
                        title="Distribución de Riesgos de Falla")
    st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Datos en Tiempo Real")
    st.dataframe(df)

# ==============================================================
# 📈 MODO 2: HISTÓRICO DE VARIABLES
# ==============================================================
elif modo == "📈 Histórico":
    st.title("📈 Histórico de Variables")

    tiempo = np.arange(0, 100)
    torque = 150 + 5 * np.sin(tiempo / 5) + np.random.normal(0, 1, 100)
    temperatura = 60 + 8 * np.sin(tiempo / 8) + np.random.normal(0, 1, 100)
    hist = pd.DataFrame({"Tiempo (min)": tiempo, "Torque (Nm)": torque, "Temperatura_aceite (°C)": temperatura})

    fig_line = px.line(hist, x="Tiempo (min)", y=["Torque (Nm)", "Temperatura_aceite (°C)"],
                       title="Evolución del Torque y Temperatura",
                       labels={"value": "Medición", "variable": "Variable"},
                       color_discrete_map={"Torque (Nm)": "#2563EB", "Temperatura_aceite (°C)": "#F59E0B"})
    st.plotly_chart(fig_line, use_container_width=True)

# ==============================================================
# 🚨 MODO 3: ALARMAS Y MANTENIMIENTO
# ==============================================================
else:
    st.title("🚨 Gestión de Alarmas y Mantenimiento Histórico")

    # Si existe el archivo CSV, cargarlo
    if os.path.exists("alarmas_log.csv"):
        log = pd.read_csv("alarmas_log.csv")
        st.success(f"📁 {len(log)} alarmas registradas históricamente.")
    else:
        log = pd.DataFrame(columns=["Fecha_Hora", "Variable", "Nivel", "Descripción", "Estado"])
        st.warning("⚠️ No se han registrado alarmas aún.")

    # Mostrar tabla
    st.dataframe(log)

    # Gráfico resumen
    if not log.empty:
        fig_pie = px.pie(log, names="Nivel", title="Distribución de Niveles de Alarma",
                         color_discrete_map={"Alta": "#DC2626", "Media": "#F59E0B", "Baja": "#10B981"})
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.info("💡 Consejo: Usa este historial para planificar mantenimientos preventivos y evaluar patrones de falla.")
