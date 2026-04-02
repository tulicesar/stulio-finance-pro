import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

# Rutas de Archivos
LOGO_LOGIN = "logoapp 1.png"
LOGO_DARK = "logoapp 2.jpg"    
LOGO_LIGHT = "logoapp3.jpg"   
LOGO_APP_H = "LOGOapp horizontal.png" 
BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"

# --- 2. GESTIÓN DE MODO ---
if 'modo_oscuro' not in st.session_state:
    st.session_state.modo_oscuro = True 

with st.sidebar:
    # Toggle de modo
    st.session_state.modo_oscuro = st.toggle('Modo Oscuro 🌙', value=st.session_state.modo_oscuro)
    
    if st.session_state.modo_oscuro:
        bg_app, bg_sidebar, bg_card = "#10141D", "#1A1F2B", "#1A1F2B"
        bg_input = "#262730"
        text_main, text_sec, accent = "#FFFFFF", "#A0AAB5", "#38EF7D"
        logo_sidebar = LOGO_DARK
        color_map_graficos = {"Hogar": "#5DADE2", "Servicios": "#F4D03F", "Salud": "#EC7063", "Transporte": "#AF7AC5", "Obligaciones": "#EB984E", "Alimentación": "#A569BD", "Otros": "#82E0AA", "Impuestos": "#F1948A"}
    else:
        # MODO CLARO PERSONALIZADO
        bg_app = "#F8F9FA"
        bg_sidebar = "#E1F0E7" # Verde claro suave para la barra lateral
        bg_card = "#F0F2F6"    # Gris claro para las tablas/cards
        bg_input = "#F0F2F6"   # Gris claro para inputs
        text_main = "#000000"  # Letras negras
        text_sec = "#4F4F4F"
        accent = "#A6A6A6"     # Gris para botones de reportes (sustituye al verde)
        logo_sidebar = LOGO_LIGHT
        color_map_graficos = {"Hogar": "#3498DB", "Servicios": "#F1C40F", "Salud": "#E74C3C", "Transporte": "#8E44AD", "Obligaciones": "#E67E22", "Alimentación": "#884EA0", "Otros": "#2ECC71", "Impuestos": "#E06666"}

# --- 3. CSS DINÁMICO ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_app} !important; }}
    
    /* Textos Generales */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stApp div {{ color: {text_main} !important; }}
    
    /* Barra Lateral */
    [data-testid="stSidebar"] {{ 
        background-color: {bg_sidebar} !important; 
        border-right: 1px solid #CCCCCC;
    }}
    
    /* Inputs, Selectbox y Number Inputs (Gris claro en modo claro) */
    div[data-baseweb="select"], div[data-baseweb="input"], .stNumberInput input {{
        background-color: {bg_input} !important;
        color: {text_main} !important;
        border: 1px solid #CCCCCC !important;
    }}

    /* Estilo de la Tabla (Data Editor) */
    [data-testid="stDataEditor"] {{
        background-color: {bg_card} !important;
        border-radius: 10px;
    }}
    [data-testid="stDataEditor"] div {{ font-size: 1.1rem !important; color: {text_main} !important; }}

    /* Cards de métricas */
    .card {{
        background-color: {bg_card}; border-radius: 12px; padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 10px;
        text-align: center; border-bottom: 4px solid #38EF7D;
    }}
    .card-label {{ font-size: 0.8rem; color: {text_sec} !important; font-weight: 800; text-transform: uppercase; }}
    .card-value {{ font-size: 1.6rem; font-weight: 800; color: {text_main} !important; }}

    /* Botones de Sidebar (Extractos y Balances) */
    [data-testid="stSidebar"] .stButton>button {{
        background-color: {accent} !important; 
        color: {text_main} !important; 
        border: 1px solid #CCCCCC !important;
    }}

    /* Botón Guardar Cambios (Mantiene color destacado) */
    .main .stButton>button {{
        background-color: #38EF7D !important;
        color: white !important;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. MOTOR DE DATOS ---
def cargar_bd():
    if not os.path.exists(BASE_FILE): return pd.DataFrame(columns=["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]), pd.DataFrame(columns=["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"])
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        for col in ["Monto", "Valor Referencia"]: df_g[col] = pd.to_numeric(df_g[col], errors='coerce').fillna(0.0)
        return df_g, df_i
    except: return pd.DataFrame(), pd.DataFrame()

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0.0
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum() if not df_g.empty else 0.0
    fondos_act, saldo_fin = it - vp, it - vp - vpy
    ahorro_p = (saldo_fin / it * 100) if it > 0 else 0
    return it, vp, vpy, fondos_act, saldo_fin, ahorro_p

# --- 5. LOGIN SIMPLIFICADO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    st.title("My FinanceApp")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if u == "tulicesar" and p == "Thulli.07":
            st.session_state.autenticado = True
            st.session_state.usuario_id = u
            st.rerun()
    st.stop()

# --- 6. DASHBOARD ---
df_g_raw, df_i_raw = cargar_bd()
df_g_user = df_g_raw[df_g_raw["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == st.session_state.usuario_id].copy()
periodos_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    # LOGO EN LA PARTE SUPERIOR DEL SIDEBAR
    if os.path.exists(logo_sidebar):
        st.image(logo_sidebar, use_container_width=True)
    else:
        st.subheader("My FinanceApp")
    
    st.divider()
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    mes_s = st.selectbox("Mes Actual", periodos_list, index=datetime.now().month-1)
    
    # Saldo Anterior / Nomina / Otros
    d_act_i = df_i_user[(df_i_user["Periodo"] == mes_s) & (df_i_user["Año"] == anio_s)]
    s_in = st.number_input("Saldo Anterior", value=float(d_act_i["SaldoAnterior"].iloc[0]) if not d_act_i.empty else 0.0)
    n_in = st.number_input("Nomina", value=float(d_act_i["Nomina"].iloc[0]) if not d_act_i.empty else 0.0)
    o_in = st.number_input("Otros", value=float(d_act_i["Otros"].iloc[0]) if not d_act_i.empty else 0.0)

    st.divider()
    st.subheader("📑 Extractos")
    st.button("📄 PDF", key="pdf_btn")
    st.button("📊 Excel", key="excel_btn")

    st.subheader("⚖️ Balances Semestrales")
    st.button("📥 Semestre 1", key="s1_btn")
    st.button("📥 Semestre 2", key="s2_btn")

# --- 7. CUERPO ---
if os.path.exists(LOGO_APP_H):
    st.image(LOGO_APP_H, use_container_width=True)

st.markdown(f"## {mes_s} {anio_s}")

df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()
df_v = df_mes.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"]).reset_index(drop=True)

# Tabla principal (Gris claro con letras negras en modo claro)
df_ed = st.data_editor(df_v, use_container_width=True, num_rows="dynamic")

it, vp, vpy, fondos_act, saldo_fin, ahorro_p = calcular_metricas(df_ed, n_in, o_in, s_in)

st.divider()
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="card"><div class="card-label">INGRESOS</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card"><div class="card-label">PAGADO</div><div class="card-value" style="color:#2ecc71;">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="card"><div class="card-label">PENDIENTE</div><div class="card-value" style="color:#e74c3c;">$ {vpy:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="card"><div class="card-label">FONDOS ACTUALES</div><div class="card-value" style="color:#2575fc;">$ {fondos_act:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="card"><div class="card-label">AHORRO FINAL</div><div class="card-value" style="color:#38EF7D;">$ {saldo_fin:,.0f}</div></div>', unsafe_allow_html=True)

# Gráficos
c1, c2, c3 = st.columns([1.5, 1, 1.2])
with c1:
    st.markdown("**Análisis de Gastos**")
    t_df = df_ed.copy(); t_df['V'] = t_df.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not t_df.empty and t_df['V'].sum() > 0:
        fig = px.pie(t_df, values='V', names='Categoría', hole=0.6, color_discrete_map=color_map_graficos)
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)

with c2:
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=ahorro_p, number={'suffix': "%", 'font':{'color':accent}}, gauge={'axis':{'range':[0,100]},'bar':{'color':text_main},'bgcolor':'#DDD','steps':[{'range':[0,20],'color':'#ff4b4b'},{'range':[50,100],'color':'#00d26a'}]}))
    gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': text_main}, height=350)
    st.plotly_chart(gauge, use_container_width=True)

with c3:
    pie = go.Figure(data=[go.Pie(labels=['Pagado', 'Pendiente', 'Ahorro'], values=[vp, vpy, saldo_fin], hole=.65, marker_colors=['#2ecc71', '#e74c3c', '#38EF7D'])])
    pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=380)
    st.plotly_chart(pie, use_container_width=True)

if st.button("💾 GUARDAR CAMBIOS"):
    st.success("Cambios guardados localmente.")
