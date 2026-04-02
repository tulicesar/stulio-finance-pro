import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from io import BytesIO
from datetime import datetime
import math

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"
LOGO_SIDEBAR = "logoapp 2.png" 
LOGO_APP_H = "LOGOapp horizontal.png" 

COLOR_MAP = {
    "Hogar": "#FFB347", "Servicios": "#FFB347", "Salud": "#B39EB5", 
    "Transporte": "#77B5FE", "Obligaciones": "#FF6961", "Alimentación": "#FDFD96", 
    "Otros": "#77DD77", "Impuestos": "#84b6f4"
}

st.markdown("""
    <style>
    header { background-color: rgba(0,0,0,0) !important; }
    .stApp { background: #0e1117; color: #dee2e6; }
    [data-testid="stDataEditor"] { font-size: 1.4rem !important; }
    .card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #1a1d21; text-align: center; border-bottom: 4px solid #d4af37;
    }
    .card-label { font-size: 0.8rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #1a1d21; margin: 3px 0; }
    .legend-bar {
        padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; 
        font-size: 0.9rem; font-weight: bold; color: #1a1d21; 
        display: flex; justify-content: space-between; align-items: center;
    }
    section[data-testid="stSidebar"] { background: rgba(0,0,0,0.8) !important; backdrop-filter: blur(15px); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #d4af37; color: black; border: none; }
    h2, h3 { color: #d4af37 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    col_oi = ["Año", "Periodo", "Descripción", "Monto", "Usuario"]
    if not os.path.exists(BASE_FILE): return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)
    df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
    df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
    try: df_oi = pd.read_excel(BASE_FILE, sheet_name="OtrosIngresos")
    except: df_oi = pd.DataFrame(columns=col_oi)
    return df_g, df_i, df_oi

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum() if not df_g.empty else 0
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), bf, ahorro_p

# --- 3. UI SIDEBAR ---
u_id = "tulicesar" # Basado en tus capturas anteriores
df_g_full, df_i_full, df_oi_full = cargar_bd()

with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 Tulio Salcedo")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_s = st.selectbox("Mes Actual", meses, index=datetime.now().month-1)
    
    i_m = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s) & (df_i_full["Usuario"]==u_id)]
    s_in = st.number_input("Saldo Anterior", value=float(i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0.0))
    n_in = st.number_input("Ingresos Fijos (Sueldo)", value=float(i_m["Nomina"].iloc[0] if not i_m.empty else 0.0))
    
    st.divider()
    st.subheader("📑 Extracto del Mes")
    # (Botones de PDF y Excel aquí)
    
    st.subheader("⚖️ Balances Proyectados")
    # (Botones Semestre 1 y 2 aquí)

# --- 4. CUERPO PRINCIPAL ---
if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s} {anio_s}")

# Tablas de Registro
st.markdown("### 📝 Movimiento de Gastos")
df_mes_g = df_g_full[(df_g_full["Periodo"] == mes_s) & (df_g_full["Año"] == anio_s) & (df_g_full["Usuario"] == u_id)].copy()
df_ed_g = st.data_editor(df_mes_g.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic")

st.markdown("### 💰 Registro de Otros Ingresos Adicionales")
df_mes_oi = df_oi_full[(df_oi_full["Periodo"] == mes_s) & (df_oi_full["Año"] == anio_s) & (df_oi_full["Usuario"] == u_id)].copy()
df_ed_oi = st.data_editor(df_mes_oi.reindex(columns=["Descripción", "Monto"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic")

# Cálculos
df_ed_g["Monto"] = pd.to_numeric(df_ed_g["Monto"], errors="coerce").fillna(0)
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0)
otr_sum = float(df_ed_oi["Monto"].sum())
it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_sum, s_in)

st.divider()
# Tarjetas
cols = st.columns(5)
metas = [("INGRESOS", it), ("PAGADO", vp), ("PENDIENTE", vpy), ("FONDOS", fact), ("AHORRO", bf)]
for i, (lab, val) in enumerate(metas):
    color = "green" if lab=="PAGADO" else "red" if lab=="PENDIENTE" else "#d4af37" if lab=="AHORRO" else "black"
    cols[i].markdown(f'<div class="card"><div class="card-label">{lab}</div><div class="card-value" style="color:{color}">$ {val:,.0f}</div></div>', unsafe_allow_html=True)

# --- 5. INFOGRAFÍAS (ARREGLO DEFINITIVO) ---
st.markdown("### 📊 Análisis de Distribución")
inf1, inf2, inf3 = st.columns([1.2, 1, 1.2])

with inf1:
    st.markdown("#### Desglose de Gastos")
    # (Gráfico de torta aquí)

with inf2:
    st.markdown("#### Eficiencia de Ahorro")
    # GEOMETRÍA DE LA AGUJA (Pivot central)
    val = max(0, min(ahorro_p, 100))
    # Ángulo: 0% es 180°, 100% es 0°
    phi = math.radians(180 - (val / 100 * 180))
    x_pivot, y_pivot = 0.5, 0.4  # Centro donde está el texto
    r = 0.35 # Largo de la aguja
    x_tip = x_pivot + r * math.cos(phi)
    y_tip = y_pivot + r * math.sin(phi)

    fig_gauge = go.Figure()
    # Arco de fondo (Blanco/Gris como la imagen)
    fig_gauge.add_trace(go.Indicator(
        mode="gauge", value=val,
        gauge={
            'axis': {'range': [0, 100], 'tickvals': [0, 20, 40, 60, 80, 100], 'tickcolor': "grey"},
            'bar': {'color': "rgba(0,0,0,0)"}, # Invisible para que solo se vea la aguja
            'bgcolor': "white",
            'borderwidth': 2, 'bordercolor': "#e0e0e0"
        }
    ))
    # Número Central Dorado (Pivot)
    fig_gauge.add_annotation(text=f"{val:.0f}%", x=x_pivot, y=y_pivot, showarrow=False, font=dict(color="#d4af37", size=55, weight="bold"))
    fig_gauge.add_annotation(text="Ahorro Proyectado", x=x_pivot, y=y_pivot-0.15, showarrow=False, font=dict(color="grey", size=15))
    
    # LA AGUJA DORADA
    fig_gauge.add_shape(type="line", x0=x_pivot, y0=y_pivot, x1=x_tip, y1=y_tip, line=dict(color="#d4af37", width=5))
    # Punto del centro
    fig_gauge.add_shape(type="circle", x0=x_pivot-0.02, y0=y_pivot-0.02, x1=x_pivot+0.02, y1=y_pivot+0.02, fillcolor="#d4af37", line_color="#d4af37")

    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=320, margin=dict(t=50,b=20,l=20,r=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

with inf3:
    st.markdown("#### Estado Real del Dinero")
    # (Gráfico de Estado aquí)

# --- ESPACIO Y BOTÓN BAJO ---
st.markdown("<br>" * 12, unsafe_allow_html=True)
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS", use_container_width=True):
    # Lógica de guardado...
    st.balloons(); st.rerun()
