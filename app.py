import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

# Conectamos con Google Sheets usando los Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# Estilo Visual
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1a1d21 0%, #111315 100%); color: #dee2e6; }
    .card { background-color: #ffffff; border-radius: 15px; padding: 20px; color: #1a1d21; text-align: center; border-bottom: 5px solid #d4af37; margin-bottom: 10px; }
    .card-label { font-size: 0.75rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 1.4rem; font-weight: 800; color: #1a1d21; }
    .login-box { max-width: 450px; margin: auto; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 15px; border: 1px solid #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE DATOS ---
def leer_datos(pestaña):
    return conn.read(worksheet=pestaña, ttl=0)

def guardar_datos(pestaña, df):
    conn.update(worksheet=pestaña, data=df)

# --- 3. ACCESO (LOGIN / REGISTRO) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.title("🔮 STULIO FINANCE")
        t1, t2, t3 = st.tabs(["🔑 Entrar", "📝 Registro", "🔄 Recuperar"])
        df_u = leer_datos("Usuarios")

        with t1:
            user_in = st.text_input("Usuario").strip()
            pass_in = st.text_input("Clave", type="password").strip()
            if st.button("Ingresar", use_container_width=True):
                match = df_u[(df_u["usuario"] == user_in) & (df_u["pass"] == pass_in)]
                if not match.empty:
                    st.session_state.autenticado = True
                    st.session_state.username = user_in
                    st.session_state.full_name = match.iloc[0]["nombre"]
                    st.rerun()
                else: st.error("Usuario o clave incorrectos")

        with t2:
            n_f = st.text_input("Nombre Completo")
            n_u = st.text_input("Nombre de Usuario")
            n_e = st.text_input("Email")
            n_p = st.text_input("Contraseña", type="password")
            if st.button("Registrarme", use_container_width=True):
                if n_u in df_u["usuario"].values: st.error("Ese usuario ya existe")
                elif n_f and n_u and n_p:
                    nuevo = pd.DataFrame([[n_f, n_u, n_e, n_p]], columns=df_u.columns)
                    guardar_datos("Usuarios", pd.concat([df_u, nuevo], ignore_index=True))
                    st.success("✅ ¡Registrado! Ahora puedes entrar.")
                else: st.warning("Completa los campos obligatorios")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 4. DASHBOARD PERSONALIZADO ---
periodos = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    st.write(f"### 👤 {st.session_state.full_name}")
    anio_sel = st.selectbox("Año", [2025, 2026, 2027], index=1)
    mes_sel = st.selectbox("Mes", periodos)
    
    # Cargar Ingresos desde Google Sheets
    df_i_all = leer_datos("Ingresos")
    d_i = df_i_all[(df_i_all["Usuario"] == st.session_state.username) & (df_i_all["Año"] == anio_sel) & (df_i_all["Periodo"] == mes_sel)]
    
    s_ant = st.number_input("Saldo Anterior", value=float(d_i["SaldoAnterior"].iloc[0] if not d_i.empty else 0.0))
    nom = st.number_input("Nómina", value=float(d_i["Nomina"].iloc[0] if not d_i.empty else 0.0))
    otr = st.number_input("Otros", value=float(d_i["Otros"].iloc[0] if not d_i.empty else 0.0))
    
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

st.title(f"Balance de {st.session_state.username}: {mes_sel} {anio_sel}")

# Cargar Gastos desde Google Sheets (Filtrado por Usuario)
df_g_all = leer_datos("Gastos")
df_g_user = df_g_all[(df_g_all["Usuario"] == st.session_state.username) & (df_g_all["Año"] == anio_sel) & (df_g_all["Periodo"] == mes_sel)].copy()
df_v = df_g_user.drop(columns=["Usuario", "Año", "Periodo"]).reset_index(drop=True)

# Editor de datos
df_ed = st.data_editor(df_v, num_rows="dynamic", use_container_width=True)

# Cálculos
it = s_ant + nom + otr
monto_pagado = pd.to_numeric(df_ed["Monto"], errors='coerce').fillna(0)
pagado_bool = df_ed["Pagado"].astype(bool)
vp = monto_pagado[pagado_bool].sum()
fb = it - vp

# Tarjetas de Resumen
c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="card"><div class="card-label">Ingresos</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card"><div class="card-label">Fondos</div><div class="card-value">$ {fb:,.0f}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="card"><div class="card-label">Pagado</div><div class="card-value">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)

# --- 5. BOTÓN DE GUARDADO FINAL ---
if st.button("💾 GUARDAR CAMBIOS EN LA NUBE"):
    # Preparar Gastos
    df_g_limpio = df_g_all[~((df_g_all["Usuario"] == st.session_state.username) & (df_g_all["Año"] == anio_sel) & (df_g_all["Periodo"] == mes_sel))]
    df_ed["Usuario"] = st.session_state.username
    df_ed["Año"] = anio_sel
    df_ed["Periodo"] = mes_sel
    guardar_datos("Gastos", pd.concat([df_g_limpio, df_ed], ignore_index=True))
    
    # Preparar Ingresos
    df_i_limpio = df_i_all[~((df_i_all["Usuario"] == st.session_state.username) & (df_i_all["Año"] == anio_sel) & (df_i_all["Periodo"] == mes_sel))]
    nuevo_i = pd.DataFrame([[st.session_state.username, anio_sel, mes_sel, s_ant, nom, otr]], columns=df_i_all.columns)
    guardar_datos("Ingresos", pd.concat([df_i_limpio, nuevo_i], ignore_index=True))
    
    st.balloons()
    st.success("¡Datos guardados exitosamente!")
