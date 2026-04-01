import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="My Finance by Stulio Designs", layout="wide", page_icon="💰")

# Nombre de la App actualizado
APP_NAME = "My Finance"
BY_AUTHOR = "by Stulio Designs"
BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_id' not in st.session_state: 
    st.session_state.usuario_id = ""

# CSS: Diseño Premium Dark & Gold
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .stApp { background: #0e1117; color: #dee2e6; }
    .card {
        background-color: #1f2630;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 10px;
        text-align: center;
        border-top: 3px solid #d4af37;
    }
    .card-label { font-size: 0.8rem; color: #aeb1b5; font-weight: bold; text-transform: uppercase; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #ffffff; margin: 5px 0; }
    section[data-testid="stSidebar"] { background: #161b22 !important; }
    .stButton>button { border-radius: 8px; font-weight: bold; background-color: #d4af37; color: #000; border: none; }
    .stButton>button:hover { background-color: #f1c40f; color: #000; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE DATOS ---
def cargar_usuarios():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            try: return json.load(f)
            except: return {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}
    db = {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}
    with open(USER_DB, "w") as f: json.dump(db, f, indent=4)
    return db

def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    if not os.path.exists(BASE_FILE):
        return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        for col in ["Monto", "Valor Referencia"]:
            df_g[col] = pd.to_numeric(df_g[col], errors='coerce').fillna(0.0)
        df_g["Pagado"] = df_g["Pagado"].fillna(False).astype(bool)
        df_g["Movimiento Recurrente"] = df_g["Movimiento Recurrente"].fillna(False).astype(bool)
        return df_g, df_i
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    if df_g.empty: return it, 0.0, 0.0, it, 0.0
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum()
    # Gastos pendientes basados en Valor de Referencia
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum()
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, bf, ahorro_p

# --- 3. LOGIN ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>{APP_NAME}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; margin-top: -20px;'>{BY_AUTHOR}</p>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔑 Entrar", "📝 Registro"])
        usuarios = cargar_usuarios()
        with tab_log:
            u = st.text_input("Usuario").strip()
            p = st.text_input("Contraseña", type="password").strip()
            if st.button("Iniciar Sesión", use_container_width=True):
                if u in usuarios and usuarios[u]["pass"] == p:
                    st.session_state.autenticado, st.session_state.usuario_id = True, u
                    st.session_state.u_nombre_completo = usuarios[u].get("nombre", u)
                    st.rerun()
                else: st.error("Datos incorrectos")
    st.stop()

# --- 4. DASHBOARD ---
df_g_raw, df_i_raw = cargar_bd()
df_g_user = df_g_raw[df_g_raw["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == st.session_state.usuario_id].copy()
periodos_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    st.markdown(f"<h2 style='color:#d4af37;'>{APP_NAME}</h2>", unsafe_allow_html=True)
    st.write(f"👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    mes_s = st.selectbox("Mes", periodos_list, index=datetime.now().month-1)
    
    # Datos de ingresos
    d_act_i = df_i_user[(df_i_user["Periodo"] == mes_s) & (df_i_user["Año"] == anio_s)]
    s_in = st.number_input("Saldo Anterior", value=float(d_act_i["SaldoAnterior"].iloc[0] if not d_act_i.empty else 0.0))
    n_in = st.number_input("Nómina", value=float(d_act_i["Nomina"].iloc[0] if not d_act_i.empty else 0.0))
    o_in = st.number_input("Otros", value=float(d_act_i["Otros"].iloc[0] if not d_act_i.empty else 0.0))
    
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 5. CUERPO PRINCIPAL ---
c_logo, c_title = st.columns([1, 5])
with c_title:
    st.markdown(f"<h1>{mes_s} {anio_s} <span style='font-size:0.5em; color:#d4af37;'>| {BY_AUTHOR}</span></h1>", unsafe_allow_html=True)

# Carga de movimientos (Lógica de Cadena)
df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()
if df_mes.empty:
    # Busca el mes anterior para heredar recurrentes
    idx_actual = periodos_list.index(mes_s)
    mes_busq = periodos_list[idx_actual-1] if idx_actual > 0 else "Diciembre"
    anio_busq = anio_s if idx_actual > 0 else anio_s - 1
    df_rec = df_g_user[(df_g_user["Periodo"] == mes_busq) & (df_g_user["Año"] == anio_busq) & (df_g_user["Movimiento Recurrente"] == True)]
    if not df_rec.empty:
        df_mes = df_rec.copy().assign(Pagado=False, Monto=0)

# Editor de datos
df_v = df_mes.reset_index(drop=True).drop(columns=["Año", "Periodo", "Usuario"], errors='ignore')
df_ed = st.data_editor(df_v, use_container_width=True, num_rows="dynamic", key=f"ed_{mes_s}")

# METRICAS
it, vp, vpy, bf, ahorro_p = calcular_metricas(df_ed, n_in, o_in, s_in)

m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="card"><div class="card-label">Ingresos Total</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card"><div class="card-label">Gastos Pagados</div><div class="card-value" style="color:#2ecc71;">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="card"><div class="card-label">Gastos Pendientes</div><div class="card-value" style="color:#e74c3c;">$ {vpy:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="card"><div class="card-label">Saldo Final</div><div class="card-value" style="color:#d4af37;">$ {bf:,.0f}</div></div>', unsafe_allow_html=True)

st.divider()

# --- 🚀 INFOGRAFÍAS (COMO LAS IMÁGENES) ---
c_graf1, c_graf2 = st.columns([1, 1])

with c_graf1:
    # Gráfico de Dona: Gastos por Categoría (Inspirado en la imagen 2)
    if not df_ed.empty and df_ed["Monto"].sum() > 0:
        fig_pie = px.pie(df_ed, values='Monto', names='Categoría', hole=0.6,
                         color_discrete_sequence=px.colors.sequential.Gold)
        fig_pie.update_layout(title="Distribución de Gastos", paper_bgcolor='rgba(0,0,0,0)', 
                              plot_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=True,
                              height=350, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Agregue montos para ver el desglose por categorías.")

with c_graf2:
    # Gráfico de Indicador: Porcentaje de Ahorro (Inspirado en la imagen 1)
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = ahorro_p,
        number = {'suffix': "%", 'font': {'size': 60, 'color': "#d4af37"}},
        title = {'text': "Nivel de Ahorro Mensual", 'font': {'size': 20}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#d4af37"},
            'bgcolor': "#1f2630",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 20], 'color': '#c0392b'},
                {'range': [20, 50], 'color': '#f39c12'},
                {'range': [50, 100], 'color': '#27ae60'}]
        }
    ))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=350, margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig_gauge, use_container_width=True)

# Guardar
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    df_n = df_ed.dropna(subset=["Categoría", "Descripción"], how="all").assign(Periodo=mes_s, Año=anio_s, Usuario=st.session_state.usuario_id)
    mask_g = (df_g_raw["Periodo"] == mes_s) & (df_g_raw["Año"] == anio_s) & (df_g_raw["Usuario"] == st.session_state.usuario_id)
    df_gf = pd.concat([df_g_raw[~mask_g], df_n], ignore_index=True)
    
    df_i_nuevo = pd.DataFrame({"Año":[anio_s], "Periodo":[mes_s], "SaldoAnterior":[s_in], "Nomina":[n_in], "Otros":[o_in], "Usuario":[st.session_state.usuario_id]})
    mask_i = (df_i_raw["Periodo"] == mes_s) & (df_i_raw["Año"] == anio_s) & (df_i_raw["Usuario"] == st.session_state.usuario_id)
    df_if = pd.concat([df_i_raw[~mask_i], df_i_nuevo], ignore_index=True)
    
    with pd.ExcelWriter(BASE_FILE) as w:
        df_gf.to_excel(w, sheet_name="Gastos", index=False)
        df_if.to_excel(w, sheet_name="Ingresos", index=False)
    st.balloons(); st.rerun()
