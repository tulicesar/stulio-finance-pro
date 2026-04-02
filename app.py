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

LOGO_LOGIN = "logoapp 1.png"
LOGO_SIDEBAR = "logoapp 2.png" 
LOGO_APP_H = "LOGOapp horizontal.png" 
BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"

COLOR_MAP = {
    "Hogar": "#FFB347", "Servicios": "#FFB347", "Salud": "#B39EB5", 
    "Transporte": "#77B5FE", "Obligaciones": "#FF6961", "Alimentación": "#FDFD96", 
    "Otros": "#77DD77", "Impuestos": "#84b6f4"
}

# --- AJUSTE DE TAMAÑO DE TEXTO PARA MÓVIL ---
st.markdown("""
    <style>
    header { background-color: rgba(0,0,0,0) !important; }
    .stApp { background: #0e1117; color: #dee2e6; }
    
    /* TAMAÑO DE TEXTO DENTRO DE LAS TABLAS (DATA EDITOR) */
    [data-testid="stDataEditor"] div {
        font-size: 1.8rem !important; /* Texto mucho más grande para digitar en celular */
    }
    
    /* TAMAÑO DE LOS ENCABEZADOS DE LAS COLUMNAS */
    [data-testid="stDataEditor"] th div {
        font-size: 1.4rem !important;
    }

    .stTabs [aria-selected="true"] { color: #d4af37 !important; border-bottom-color: #d4af37 !important; font-weight: bold; }
    
    .card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #1a1d21; text-align: center; border-bottom: 4px solid #d4af37;
    }
    .card-label { font-size: 1rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 2rem; font-weight: 800; color: #1a1d21; margin: 3px 0; }
    
    section[data-testid="stSidebar"] { background: rgba(0,0,0,0.8) !important; backdrop-filter: blur(15px); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; height: 3.5rem; font-size: 1.5rem !important; background-color: #d4af37; color: black; border: none; }
    
    h2, h3 { color: #d4af37 !important; font-weight: bold !important; font-size: 2.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS (Mantiene tu lógica anterior) ---
def cargar_usuarios():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            try: return json.load(f)
            except: pass
    return {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}

def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    col_oi = ["Año", "Periodo", "Descripción", "Monto", "Usuario"]
    if not os.path.exists(BASE_FILE): return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        try: df_oi = pd.read_excel(BASE_FILE, sheet_name="OtrosIngresos")
        except: df_oi = pd.DataFrame(columns=col_oi)
        return df_g, df_i, df_oi
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum() if not df_g.empty else 0
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), bf, ahorro_p

# --- ACCESO Y SIDEBAR ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    # (Tu lógica de login aquí)
    st.session_state.autenticado = True
    st.session_state.usuario_id = "tulicesar"
    st.session_state.u_nombre_completo = "Tulio Salcedo"

u_id = st.session_state.usuario_id
df_g_full, df_i_full, df_oi_full = cargar_bd()

with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_s = st.selectbox("Mes Actual", meses_lista, index=datetime.now().month-1)
    
    # Arrastre de saldo
    idx = meses_lista.index(mes_s)
    m_ant = meses_lista[idx-1] if idx > 0 else "Diciembre"
    a_ant = anio_s if idx > 0 else anio_s-1
    i_m_act = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s) & (df_i_full["Usuario"]==u_id)]
    
    st.divider()
    s_in = st.number_input("Saldo Anterior", value=float(i_m_act["SaldoAnterior"].iloc[0] if not i_m_act.empty else 0.0))
    n_in = st.number_input("Ingresos Fijos", value=float(i_m_act["Nomina"].iloc[0] if not i_m_act.empty else 0.0))

# --- CUERPO PRINCIPAL ---
if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s}")

# TABLAS CON TEXTO GRANDE
st.markdown("### 📝 Movimiento de Gastos")
df_mes_g = df_g_full[(df_g_full["Periodo"] == mes_s) & (df_g_full["Año"] == anio_s) & (df_g_full["Usuario"] == u_id)].copy()
df_ed_g = st.data_editor(df_mes_g.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", key="g_ed")

st.markdown("### 💰 Otros Ingresos")
df_mes_oi = df_oi_full[(df_oi_full["Periodo"] == mes_s) & (df_oi_full["Año"] == anio_s) & (df_oi_full["Usuario"] == u_id)].copy()
df_ed_oi = st.data_editor(df_mes_oi.reindex(columns=["Descripción", "Monto"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", key="oi_ed")

# Métricas e Infografías (Misma lógica, botón con margen)
df_ed_g["Monto"] = pd.to_numeric(df_ed_g["Monto"], errors="coerce").fillna(0)
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0)
otr_vivos = float(df_ed_oi["Monto"].sum())
it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_vivos, s_in)

st.divider()
# (Tus tarjetas y gráficas aquí...)

st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS", use_container_width=True):
    # (Tu lógica de guardado aquí)
    st.success("¡Información Guardada!"); st.rerun()
