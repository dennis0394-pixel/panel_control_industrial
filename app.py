import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt

# ==============================================================
# ⚙️ SIMULACIÓN DE MONITOREO DE MOTOR ELÉCTRICO — FASE 2
# ==============================================================

# Datos simulados del motor
data = {
  "Corriente_motor (A)": [18.5, 17.9, 16.8, 19.2, 18.7, 17.4, 15.9, 10.8, 11.2, 10.4],
    "Torque (Nm)": [160.4, 158.7, 157.3, 162.8, 159.9, 155.6, 152.0, 138.5, 140.2, 139.8],
    "Presión_hidráulica (bar)": [90.2, 88.9, 87.3, 91.0, 89.5, 88.1, 85.7, 82.1, 80.4, 80.6],
    "Temperatura_aceite (°C)": [68.4, 70.1, 67.5, 72.3, 69.8, 71.2, 65.9, 42.0, 41.8, 43.5]
}

# Crear el DataFrame y guardar CSV
df = pd.DataFrame(data)
df.to_csv("datos_motor.csv", index=False)
print("✅ Archivo CSV 'datos_motor.csv' creado correctamente.\n")

# ==============================================================
# 1️⃣ CARGA Y PREPARACIÓN DE DATOS
# ==============================================================

df = pd.read_csv("datos_motor.csv")

features = [
    "Corriente_motor (A)", "Torque (Nm)",
    "Presión_hidráulica (bar)", "Temperatura_aceite (°C)"
]

X = df[features]

# ==============================================================
# 2️⃣ DETECCIÓN DE ANOMALÍAS (Isolation Forest)
# ==============================================================

model = IsolationForest(contamination=0.5, random_state=42)
df["riesgo_falla"] = model.fit_predict(X)
df["riesgo_falla"] = df["riesgo_falla"].map({1: "Normal", -1: "Riesgo"})

# ==============================================================
# 3️⃣ DIAGNÓSTICO AUTOMÁTICO DE FALLAS
# ==============================================================

def diagnostico_falla(row):
    if row["riesgo_falla"] == "Normal":
        return "Sin anomalías detectadas"
    if row["Corriente_motor (A)"] > 16:
        return "Posible sobrecarga eléctrica del motor"
    elif row["Presión_hidráulica (bar)"] < 80:
        return "Presión hidráulica baja — posible fuga o válvula defectuosa"
    elif row["Temperatura_aceite (°C)"] > 63:
        return "Temperatura alta — riesgo de sobrecalentamiento"
    elif row["Torque (Nm)"] > 150:
        return "Torque elevado — posible fricción o desalineación"
    else:
        return "Anomalía no clasificada"

df["causa_probable"] = df.apply(diagnostico_falla, axis=1)

# ==============================================================
# 4️⃣ VISUALIZACIÓN
# ==============================================================

# Conteo de estados
conteo = df["riesgo_falla"].value_counts()
plt.bar(conteo.index, conteo.values, color=["lightgreen", "red"])
plt.title("Distribución de Riesgos de Falla")
plt.ylabel("Número de muestras")
plt.show()

# Boxplots individuales
for var in features:
    plt.figure(figsize=(5, 4))
    plt.boxplot(df[var].dropna())
    plt.title(f"Boxplot de {var}")
    plt.ylabel(var)
    plt.grid(True)
    plt.show()

# ==============================================================
# 5️⃣ TABLA FINAL CON COLORES
# ==============================================================

def pintar_riesgo_color(val):
    if val == 'Riesgo':
        return 'background-color: red; color: white'
    else:
        return 'background-color: lightgreen; color: black'

df_styled = df.style.applymap(pintar_riesgo_color, subset=['riesgo_falla'])
df_styled

