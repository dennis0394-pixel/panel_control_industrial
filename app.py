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

# ===================== CARGA DE DATOS =====================
st.header("📂 Carga de Datos del Motor")

try:
    df = pd.read_csv("datos_motor.csv", encoding="utf-8", sep=",")
    st.success("✅ Datos cargados correctamente desde 'datos_motor.csv'")
except Exception as e:
    st.error(f"⚠️ Error al cargar 'datos_motor.csv': {e}")
    st.stop()

# Vista previa
st.write("👁️ Vista previa de los datos cargados:")
st.dataframe(df.head())

# =========================================================
# 📊 MODO 1: MONITOREO EN VIVO
# =========================================================
if modo == "📊 Monitoreo en Vivo":
    st.title("🧠 Monitoreo en Tiempo Real del Motor")

    df_numerico = df.select_dtypes(include=["float64", "int64"])
    if df_numerico.empty:
        st.error("⚠️ No hay columnas numéricas válidas en el archivo.")
        st.stop()

    # Modelo de detección de anomalías
    model = IsolationForest(contamination=0.3, random_state=42)
    df["riesgo_falla"] = model.fit_predict(df_numerico)
    df["riesgo_falla"] = df["riesgo_falla"].map({1: "Normal", -1: "Riesgo"})

    # Diagnóstico simple
    def diagnostico_falla(row):
        if row["riesgo_falla"] == "Normal":
            return "Sin anomalías detectadas"
        if row["Corriente_motor (A)"] > 18:
            return "Posible sobrecarga eléctrica"
        elif row["Presión_hidráulica (bar)"] < 80:
            return "Presión baja — posible fuga"
        elif row["Temperatura_aceite (°C)"] > 70:
            return "Temperatura alta — riesgo de sobrecalentamiento"
        elif row["Torque (Nm)"] > 160:
            return "Torque elevado — posible fricción"
        else:
            return "Anomalía no clasificada"

    df["causa_probable"] = df.apply(diagnostico_falla, axis=1)

    # Contadores
    conteo = df["riesgo_falla"].value_counts()
    col1, col2, col3 = st.columns(3)
    col1.metric("⚠️ Riesgos Detectados", conteo.get("Riesgo", 0))
    col2.metric("✅ Normales", conteo.get("Normal", 0))
    col3.metric("📊 Registros Totales", len(df))

    # Gráfico
    fig_barras = px.bar(conteo, x=conteo.index, y=conteo.values,
                        color=conteo.index,
                        color_discrete_map={"Normal": "#10B981", "Riesgo": "#EF4444"},
                        title="Distribución de Riesgos de Falla")
    st.plotly_chart(fig_barras, use_container_width=True)

    # === ESTILO DE TABLA: Colores según riesgo ===
    def color_filas(row):
        color = 'background-color: '
        if row["riesgo_falla"] == "Riesgo":
            return [color + '#FCA5A5'] * len(row)  # rojo claro
        else:
            return [color + '#BBF7D0'] * len(row)  # verde claro

    st.write("📋 Estado de Monitoreo con Colores de Riesgo:")
    st.dataframe(df.style.apply(color_filas, axis=1))

# =========================================================
# 📈 MODO 2: HISTÓRICO
# =========================================================
elif modo == "📈 Histórico":
    st.title("📈 Histórico de Variables")

    tiempo = np.arange(0, len(df))
    fig_line = px.line(df, x=tiempo, y=df.columns[:4],
                       title="Evolución de Variables del Motor",
                       labels={"value": "Medición", "variable": "Variable"})
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
        corriente = st.number_input("Corriente_motor (A)", min_value=0.0, format="%.2f")
        torque = st.number_input("Torque (Nm)", min_value=0.0, format="%.2f")
        presion = st.number_input("Presión_hidráulica (bar)", min_value=0.0, format="%.2f")
        temp = st.number_input("Temperatura_aceite (°C)", min_value=0.0, format="%.2f")
        enviar = st.form_submit_button("💾 Guardar registro")

    if enviar:
        nuevo = pd.DataFrame([{
            "Corriente_motor (A)": corriente,
            "Torque (Nm)": torque,
            "Presión_hidráulica (bar)": presion,
            "Temperatura_aceite (°C)": temp,
            "Fecha_Hora": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])

        # Validación básica
        if corriente == 0 or torque == 0 or presion == 0 or temp == 0:
            st.warning("⚠️ Por favor, ingresa valores mayores a 0 en todos los campos.")
        else:
            df = pd.concat([df, nuevo], ignore_index=True)
            df.to_csv("datos_motor.csv", index=False)
            st.success("✅ Nuevo dato guardado correctamente en 'datos_motor.csv'.")
