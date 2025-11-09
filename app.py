import pandas as pd
from sklearn.ensemble import IsolationForest
import plotly.express as px
import streamlit as st

# ============================================================== #
# 🧠 PANEL INDUSTRIAL 4.0 — MONITOREO + HISTÓRICO + LOG DE ALARMAS
# ============================================================== #

with open("app.py", "w") as f:
    f.write('''
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
                        ["📊 Monitoreo en Vivo", "Histórico", "🚨 Alarmas y Mantenimiento"])
st.sidebar.info("Sistema Industrial 4.0 — con almacenamiento CSV persistente")


# ==================== DATOS BASE ====================
st.subheader("📂 Carga de Datos del Motor")

try:
    # 🔗 Leer directamente desde GitHub RAW
    url = "https://raw.githubusercontent.com/dennis0394-pixel/panel_control_industrial/main/datos_motor.csv"
    df = pd.read_csv(url, encoding='latin-1')
    st.success("✅ Datos cargados correctamente desde GitHub (datos_motor.csv)")
except Exception as e:
    st.error("⚠️ No se encontró o no se pudo leer 'datos_motor.csv'. Se usarán datos de respaldo.")
    st.write(e)
    df = pd.DataFrame({
        "Corriente_motor (A)": [18.5, 17.9, 16.8, 19.2],
        "Torque (Nm)": [160.4, 158.7, 157.3, 162.8],
        "Presión_hidráulica (bar)": [90.2, 88.9, 87.3, 91.0],
        "Temperatura_aceite (°C)": [68.4, 70.1, 67.5, 72.3]
    })


# ==============================================================
# 📊 MODO 1: MONITOREO EN VIVO
# ============================================================== #

if modo == "Monitoreo en Vivo":
    st.title("🧠 Monitoreo en Tiempo Real del Motor")

    # Asegurar que solo se usen columnas numéricas
    df_numerico = df.select_dtypes(include=["float64", "int64"]).dropna()
    if df_numerico.empty or df_numerico.shape[1] == 0:
        st.error("⚠️ No se encontraron columnas numéricas válidas en el CSV. Verifica tu archivo 'datos_motor.csv'.")
        st.stop()

    # Mostrar columnas utilizadas
    st.info(f"📈 Columnas utilizadas para el análisis: {', '.join(df_numerico.columns)}")

    # Modelo de detección de anomalías
    from sklearn.ensemble import IsolationForest
    model = IsolationForest(contamination=0.3, random_state=42)
    df["riesgo_falla"] = model.fit_predict(df_numerico)
    df["riesgo_falla"] = df["riesgo_falla"].map({1: "Normal", -1: "Riesgo"})

    # Contar resultados
    conteo = df["riesgo_falla"].value_counts()
    col1, col2, col3 = st.columns(3)
    col1.metric("⚠️ Riesgos Detectados", conteo.get("Riesgo", 0))
    col2.metric("✅ Normales", conteo.get("Normal", 0))
    col3.metric("📊 Registros Totales", len(df))

    # Mostrar tabla de datos
    st.markdown("---")
    st.dataframe(df)

    # Gráfico resumen
    import plotly.express as px
    fig_barras = px.bar(conteo, x=conteo.index, y=conteo.values,
                        color=conteo.index,
                        color_discrete_map={"Normal": "#10B981", "Riesgo": "#EF4444"},
                        title="Distribución de Riesgos de Falla")
    st.plotly_chart(fig_barras, use_container_width=True)

# ==============================================================
# 📈 MODO 2: HISTÓRICO DE VARIABLES
# ==============================================================
elif modo == "Histórico":
    st.title("📈 Histórico de Variables")

    import numpy as np
    import plotly.express as px

    # Generar datos simulados (si no hay históricos)
    tiempo = np.arange(0, 100)
    torque = 150 + 5 * np.sin(tiempo / 5) + np.random.normal(0, 1, 100)
    temperatura = 60 + 8 * np.sin(tiempo / 8) + np.random.normal(0, 1, 100)
    hist = pd.DataFrame({
        "Tiempo (min)": tiempo,
        "Torque (Nm)": torque,
        "Temperatura_aceite (°C)": temperatura
    })

    # Gráfico de evolución
    fig_line = px.line(hist, x="Tiempo (min)",
                       y=["Torque (Nm)", "Temperatura_aceite (°C)"],
                       title="Evolución del Torque y Temperatura del Motor",
                       labels={"value": "Medición", "variable": "Variable"})
    st.plotly_chart(fig_line, use_container_width=True)

# ==============================================================
# 🚨 MODO 3: ALARMAS Y MANTENIMIENTO
# ==============================================================
else:
    st.title("🚨 Gestión de Alarmas y Mantenimiento Histórico")

    import os

    # Si existe el archivo de alarmas, cargarlo
    if os.path.exists("alarmas_log.csv"):
        log = pd.read_csv("alarmas_log.csv")
        st.success(f"📁 {len(log)} alarmas registradas históricamente.")
    else:
        log = pd.DataFrame(columns=["Fecha_Hora", "Variable", "Nivel", "Descripción", "Estado"])
        st.warning("⚠️ No se han registrado alarmas aún.")

    # Mostrar tabla de alarmas
    st.dataframe(log)

    # Gráfico resumen de alarmas
    if not log.empty:
        import plotly.express as px
        fig_pie = px.pie(log, names="Nivel",
                         title="Distribución de Niveles de Alarma",
                         color_discrete_map={"Alta": "#DC2626", "Media": "#F59E0B", "Baja": "#10B981"})
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.info("💡 Consejo: Usa este historial para planificar mantenimientos preventivos y evaluar patrones de falla.")

