# ============================================================
# ⚙️ PANEL INDUSTRIAL 4.0 — Monitoreo + Histórico + Alarmas + Simulación
# ============================================================

import pandas as pd
import numpy as np
import datetime
import time
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
    .main { background-color: #0e1117; color: white; }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1F2937, #374151);
        color: white;
    }
    h1, h2, h3 { color: #e5e7eb; }
    .stMetricLabel { color: #9ca3af !important; }
    .dataframe tbody tr:nth-child(even) { background-color: #1f2937; }
</style>
""", unsafe_allow_html=True)

# ===================== SIDEBAR =====================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2721/2721283.png", width=80)
st.sidebar.title("⚙️ Control de Motor - V4.0")

modo = st.sidebar.radio("Selecciona vista:",
                        ["📊 Monitoreo en Vivo",
                         "📈 Histórico",
                         "🚨 Alarmas y Mantenimiento",
                         "➕ Ingreso Manual",
                         "🧪 Simulación Automática"])
st.sidebar.info("Sistema Industrial 4.0 — Cloud Edition (Streamlit Cloud)")

# =========================================================
# FUNCIONES
# =========================================================
def detectar_riesgos(df):
    """Entrena un IsolationForest y clasifica normal/riesgo"""
    df_numerico = df.select_dtypes(include=["float64", "int64"]).dropna()
    if df_numerico.empty:
        st.warning("⚠️ No hay columnas numéricas válidas.")
        return df
    model = IsolationForest(contamination=0.3, random_state=42)
    df["riesgo_falla"] = model.fit_predict(df_numerico)
    df["riesgo_falla"] = df["riesgo_falla"].map({1: "Normal", -1: "Riesgo"})
    return df

def diagnostico_falla(row):
    """Clasifica la causa probable del riesgo"""
    if row["riesgo_falla"] == "Normal":
        return "Sin anomalías"
    if row["Corriente_motor (A)"] > 16:
        return "Posible sobrecarga eléctrica"
    elif row["Presión_hidráulica (bar)"] < 80:
        return "Presión baja — posible fuga"
    elif row["Temperatura_aceite (°C)"] > 70:
        return "Temperatura alta — sobrecalentamiento"
    elif row["Torque (Nm)"] > 160:
        return "Torque elevado — fricción"
    else:
        return "Anomalía no clasificada"

def guardar_alarmas(df):
    """Registra nuevas alarmas en el archivo"""
    if "Riesgo" in df["riesgo_falla"].values:
        alarmas = df[df["riesgo_falla"] == "Riesgo"].copy()
        alarmas["Fecha_Hora"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alarmas["Variable"] = "General"
        alarmas["Nivel"] = "Alta"
        alarmas["Descripción"] = alarmas["causa_probable"]
        alarmas["Estado"] = "Pendiente"

        if os.path.exists("alarmas_log.csv"):
            log = pd.read_csv("alarmas_log.csv")
            alarmas = pd.concat([log, alarmas], ignore_index=True)

        alarmas.to_csv("alarmas_log.csv", index=False)


# =========================================================
# 📊 MODO 1: MONITOREO EN VIVO (con velocímetros)
# =========================================================
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

if modo == "📊 Monitoreo en Vivo":
    st.title("🧠 Monitoreo en Tiempo Real del Motor")

    # --- Control de refresco automático ---
    refresh_rate = st.sidebar.slider("⏱️ Actualizar cada (segundos)", 5, 60, 15)
    st_autorefresh(interval=refresh_rate * 1000, key="refresh_datos")

    # --- Carga de datos ---
    try:
        df = pd.read_csv("datos_motor.csv", encoding="utf-8", sep=",")
        st.sidebar.success("✅ Datos cargados desde 'datos_motor.csv'")
    except:
        st.sidebar.warning("⚠️ No se encontró 'datos_motor.csv', se crearán datos de ejemplo...")
        df = pd.DataFrame({
            "Corriente_motor (A)": np.random.uniform(10, 20, 10),
            "Torque (Nm)": np.random.uniform(130, 170, 10),
            "Presión_hidráulica (bar)": np.random.uniform(80, 95, 10),
            "Temperatura_aceite (°C)": np.random.uniform(40, 75, 10)
        })

    # --- Procesamiento y detección de anomalías ---
    df = detectar_riesgos(df)
    df["causa_probable"] = df.apply(diagnostico_falla, axis=1)

    # --- Guardar alarmas ---
    guardar_alarmas(df)

    # --- Métricas ---
    conteo = df["riesgo_falla"].value_counts()
    col1, col2, col3 = st.columns(3)
    col1.metric("⚠️ Riesgos Detectados", conteo.get("Riesgo", 0))
    col2.metric("✅ Normales", conteo.get("Normal", 0))
    col3.metric("📊 Registros Totales", len(df))

    # --- Velocímetros en tiempo real ---
    col_g1, col_g2 = st.columns(2)

    # Último valor de cada variable
    corriente_actual = float(df["Corriente_motor (A)"].iloc[-1])
    temp_actual = float(df["Temperatura_aceite (°C)"].iloc[-1])

    # ⚡ Velocímetro de Corriente
    fig_corriente = go.Figure(go.Indicator(
        mode="gauge+number",
        value=corriente_actual,
        title={"text": "⚡ Corriente del Motor (A)"},
        gauge={
            "axis": {"range": [0, 25]},
            "bar": {"color": "#10B981"},
            "steps": [
                {"range": [0, 15], "color": "#22c55e"},
                {"range": [15, 20], "color": "#facc15"},
                {"range": [20, 25], "color": "#ef4444"},
            ],
        },
        number={"suffix": " A"},
    ))
    col_g1.plotly_chart(fig_corriente, use_container_width=True)

    # 🌡️ Velocímetro de Temperatura
    fig_temp = go.Figure(go.Indicator(
        mode="gauge+number",
        value=temp_actual,
        title={"text": "🌡️ Temperatura Aceite (°C)"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#3B82F6"},
            "steps": [
                {"range": [0, 60], "color": "#22c55e"},
                {"range": [60, 75], "color": "#facc15"},
                {"range": [75, 100], "color": "#ef4444"},
            ],
        },
        number={"suffix": " °C"},
    ))
    col_g2.plotly_chart(fig_temp, use_container_width=True)

    # --- Tabla principal con colores de riesgo ---
    def resaltar_riesgos(row):
        color = "background-color: #dc2626; color: white;" if row["riesgo_falla"] == "Riesgo" else ""
        return [color] * len(row)

    st.dataframe(df.style.apply(resaltar_riesgos, axis=1))

    # --- Gráfico resumen ---
    fig = px.bar(
        conteo,
        x=conteo.index,
        y=conteo.values,
        color=conteo.index,
        color_discrete_map={"Normal": "#10B981", "Riesgo": "#EF4444"},
        title="Distribución de Riesgos de Falla"
    )
    st.plotly_chart(fig, use_container_width=True)


# =========================================================
# 📈 MODO 2: HISTÓRICO
# =========================================================
elif modo == "📈 Histórico":
    st.title("📈 Histórico de Variables")
    if os.path.exists("datos_motor.csv"):
        df = pd.read_csv("datos_motor.csv")
        fig = px.line(df, y=["Torque (Nm)", "Temperatura_aceite (°C)"],
                      title="Evolución del Torque y la Temperatura")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ No se encontraron datos históricos.")

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
elif modo == "➕ Ingreso Manual":
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
        if os.path.exists("datos_motor.csv"):
            df = pd.read_csv("datos_motor.csv")
            df = pd.concat([df, nuevo], ignore_index=True)
        else:
            df = nuevo
        df.to_csv("datos_motor.csv", index=False)
        st.success("✅ Nuevo dato guardado correctamente.")

# =========================================================
# 🧪 MODO 5: SIMULACIÓN AUTOMÁTICA
# =========================================================
elif modo == "🧪 Simulación Automática":
    st.title("🧪 Generación Automática de Datos")
    cantidad = st.number_input("Cantidad de lecturas a generar", 1, 1000, 50)
    intervalo = st.slider("Intervalo entre lecturas (segundos)", 1, 10, 2)

    if st.button("▶️ Iniciar Simulación"):
        for i in range(int(cantidad)):
            nuevo = pd.DataFrame([{
                "Corriente_motor (A)": np.random.uniform(10, 22),
                "Torque (Nm)": np.random.uniform(130, 170),
                "Presión_hidráulica (bar)": np.random.uniform(75, 95),
                "Temperatura_aceite (°C)": np.random.uniform(40, 85),
                "Fecha_Hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])

            if os.path.exists("datos_motor.csv"):
                df = pd.read_csv("datos_motor.csv")
                df = pd.concat([df, nuevo], ignore_index=True)
            else:
                df = nuevo

            df.to_csv("datos_motor.csv", index=False)
            time.sleep(intervalo)

        st.success("✅ Simulación completada y datos guardados.")
