import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# ============================
# CONFIGURACIÓN DE LA PÁGINA
# ============================
st.set_page_config(
    page_title="Simulador de EBIT - Arauco",
    layout="wide"
)

# ============================
# ESTILO CAFÉ CORPORATIVO
# ============================
CAFE_OSCURO = "#6B3E26"
CAFE_CLARO = "#C9A27C"
BANDA_CAFE = "#EBD3B1"
AXIS_CAFE = "#4B2E20"
TICKS_SUAVE = "#7A7067"
GRID_SUAVE = "#E6DED4"
FONDO_CLARO = "#FBF7F2"

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif"]
plt.rcParams.update({
    "axes.edgecolor": AXIS_CAFE,
    "axes.labelcolor": AXIS_CAFE,
    "text.color": AXIS_CAFE,
    "xtick.color": TICKS_SUAVE,
    "ytick.color": TICKS_SUAVE,
    "grid.color": GRID_SUAVE,
    "font.size": 11,
})

def fmt_millones(x, pos):
    return f"{x/1e6:,.0f} M"

# ============================
# PARÁMETROS ECONÓMICOS
# ============================

EBIT_base = 380_266_000
horiz_meses = 12
meses = np.arange(horiz_meses + 1)

# -----------------------------
# PRECIOS SPOT Y BE
# -----------------------------
P_urea_spot  = 494.98
P_met_spot   = 664.69
P_mad_spot   = 445.10

P_urea_BE    = 650.00
P_met_BE     = 800.00
P_mad_BE     = 495.54

# EXPOSICIONES ANUALES
VS_urea_anual    = 946_856.35 * 12
VS_metanol_anual = 774_925.06 * 12
VS_madera_anual  = 858_115_026.19

# R² MODELOS
R2_urea = 0.7007
R2_metanol = 0.5487
R2_madera  = 0.62

base_commodities = {
    "UREA": {
        "P0": P_urea_spot,
        "VS": VS_urea_anual,
        "R2": R2_urea,
    },
    "METANOL": {
        "P0": P_met_spot,
        "VS": VS_metanol_anual,
        "R2": R2_metanol,
    },
    "MADERA": {
        "P0": P_mad_spot,
        "VS": VS_madera_anual,
        "R2": R2_madera,
    },
}

# ============================
# FUNCIÓN DE ESCENARIO
# ============================

def construye_escenario_targets(target_prices):
    precios = {}
    ebit_sin = np.full(horiz_meses + 1, EBIT_base, float)
    ebit_con = np.full(horiz_meses + 1, EBIT_base, float)
    ahorro   = np.zeros(horiz_meses + 1, float)

    for name, base in base_commodities.items():
        P0 = base["P0"]
        VS = base["VS"]
        R2 = base["R2"]
        P_T = target_prices[name]

        path = np.linspace(P0, P_T, horiz_meses + 1)
        precios[name] = path

        rel = path / P0
        delta_costo = VS * (rel - 1.0)

        ebit_sin -= delta_costo
        ebit_con -= (1 - R2) * delta_costo
        ahorro   += R2 * delta_costo

    precios_df = pd.DataFrame(precios, index=meses)
    precios_df.index.name = "Mes"

    return precios_df, ebit_sin, ebit_con, ahorro

# ============================
# INTERFAZ STREAMLIT
# ============================

st.title("📊 Simulador Interactivo del EBIT de Arauco")
st.markdown(
    "Ajusta los precios finales (M12) y observa cómo cambian el EBIT **con** y **sin** coberturas."
)

col1, col2, col3 = st.columns(3)

with col1:
    P_urea_M12 = st.slider(
        "Precio UREA en M12 (USD/ton)",
        min_value=float(P_urea_spot * 0.5),
        max_value=float(P_urea_spot * 2.0),
        value=float(P_urea_BE),
        step=1.0,
    )

with col2:
    P_met_M12 = st.slider(
        "Precio METANOL en M12 (USD/ton)",
        min_value=float(P_met_spot * 0.5),
        max_value=float(P_met_spot * 2.0),
        value=float(P_met_BE),
        step=1.0,
    )

with col3:
    P_mad_M12 = st.slider(
        "Precio MADERA en M12 (USD/m3)",
        min_value=float(P_mad_spot * 0.7),
        max_value=float(P_mad_spot * 2.0),
        value=float(P_mad_BE),
        step=1.0,
    )

targets = {
    "UREA": P_urea_M12,
    "METANOL": P_met_M12,
    "MADERA": P_mad_M12,
}

precios_df, ebit_sin, ebit_con, ahorro = construye_escenario_targets(targets)

# ============================
# GRÁFICA
# ============================

fig, ax = plt.subplots(figsize=(10, 5))
ax.set_facecolor(FONDO_CLARO)

ax.fill_between(
    meses,
    ebit_sin,
    ebit_con,
    where=ebit_sin > ebit_con,
    color=BANDA_CAFE,
    alpha=0.5,
    label="EBIT protegido por coberturas",
)

ax.plot(
    meses,
    ebit_sin,
    marker="o",
    color=CAFE_OSCURO,
    label="Sin coberturas",
    linewidth=1.5,
)
ax.plot(
    meses,
    ebit_con,
    marker="o",
    color=CAFE_CLARO,
    label="Con coberturas",
    linewidth=2.0,
)

ax.set_xticks(meses)
ax.set_xticklabels([f"M{m}" for m in meses])

ax.set_ylabel("EBIT (millones USD)")
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x/1e6:,.0f} M"))
ax.grid(alpha=0.3)

ax.set_title("Evolución del EBIT con precios finales seleccionados", fontsize=14)
ax.legend()

# 👇 ESTA LÍNEA ES CLAVE PARA QUE NO SE “CONGELE” LA FIGURA
st.pyplot(fig, clear_figure=True)

# ============================
# RESUMEN NUMÉRICO
# ============================

gap_final = ebit_con[-1] - ebit_sin[-1]

st.subheader("📌 Resumen del escenario")
st.write(f"**EBIT base:** {EBIT_base/1e6:,.1f} M USD")
st.write(f"**EBIT M12 sin coberturas:** {ebit_sin[-1]/1e6:,.1f} M USD")
st.write(f"**EBIT M12 con coberturas:** {ebit_con[-1]/1e6:,.1f} M USD")
st.write(f"**Ahorro (protección) en M12:** +{gap_final/1e6:,.1f} M USD")

# ============================
# TABLA DE PRECIOS
# ============================

st.subheader("📄 Precios utilizados")
tabla = pd.DataFrame(
    {
        "Spot (P0)": [P_urea_spot, P_met_spot, P_mad_spot],
        "Precio M12": [P_urea_M12, P_met_M12, P_mad_M12],
        "Variación %": [
            (P_urea_M12 / P_urea_spot - 1) * 100,
            (P_met_M12 / P_met_spot - 1) * 100,
            (P_mad_M12 / P_mad_spot - 1) * 100,
        ],
    },
    index=["UREA", "METANOL", "MADERA"],
)

st.dataframe(
    tabla.style.format(
        {
            "Spot (P0)": "{:,.2f}",
            "Precio M12": "{:,.2f}",
            "Variación %": "{:,.2f} %",
        }
    )
)
