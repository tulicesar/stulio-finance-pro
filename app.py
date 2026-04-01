import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="💰")

# Estilo personalizado para las tarjetas (CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 20px; border-radius: 10px; shadow: 2px 2px 5px rgba(0,0,0,0.3); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIÓN (Bypass que ya sabemos que funciona) ---
SHEET_ID = "1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g"

def leer_pestaña(nombre_pestaña):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
        df = pd.read_csv(url)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# --- 3. LÓGICA DE LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    df_u = leer_pestaña("Usuarios")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔮 STULIO FINANCE")
        st.subheader("Control de Gastos Pro")
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Clave", type="password")
        if st.button("🚀 Ingresar al Sistema"):
            df_u['usuario'] = df_u['usuario'].astype(str).str.strip()
            df_u['pass'] = df_u['pass'].astype(str).str.strip()
            match = df_u[(df_u["usuario"] == u_in) & (df_u["pass"] == p_in)]
            if not match.empty:
                st.session_state.autenticado = True
                st.session_state.full_name = match.iloc[0]["nombre"]
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Datos incorrectos. Revisa tu usuario o clave.")
    st.stop()

# --- 4. INTERFAZ PRINCIPAL (DASHBOARD) ---
# Barra lateral
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1611/1611154.png", width=100)
st.sidebar.title(f"Bienvenido, \n{st.session_state.full_name}")
menu = st.sidebar.selectbox("MENÚ PRINCIPAL", ["📊 Tablero de Resumen", "💸 Mis Gastos", "💰 Mis Ingresos"])

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()

# --- PANTALLA: RESUMEN ---
if menu == "📊 Tablero de Resumen":
    st.title("📊 Tablero de Control Financiero")
    
    df_g = leer_pestaña("Gastos")
    df_i = leer_pestaña("Ingresos")
    
    # Cálculos de métricas
    total_i = df_i['monto'].sum() if not df_i.empty else 0
    total_g = df_g['monto'].sum() if not df_g.empty else 0
    balance = total_i - total_g
    
    # Fila de tarjetas (Métricas)
    m1, m2, m3 = st.columns(3)
    m1.metric("INGRESOS TOTALES", f"$ {total_i:,.0f}", delta_color="normal")
    m2.metric("GASTOS TOTALES", f"$ {total_g:,.0f}", delta="-", delta_color="inverse")
    m3.metric("SALDO DISPONIBLE", f"$ {balance:,.0f}", delta=f"{balance:,.0f}")

    st.markdown("---")
    
    # Gráficos
    g1, g2 = st.columns(2)
    
    with g1:
        if not df_g.empty:
            st.subheader("🍕 Distribución por Categoría")
            fig_pie = px.pie(df_g, values='monto', names='categoria', hole=.4, 
                             color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sin datos de gastos para mostrar gráficos.")

    with g2:
        if not df_g.empty:
            st.subheader("📈 Histórico de Gastos")
            fig_line = px.line(df_g, x='fecha', y='monto', markers=True, 
                               line_shape="spline", title="Evolución del Gasto")
            st.plotly_chart(fig_line, use_container_width=True)

# --- PANTALLA: GASTOS ---
elif menu == "💸 Mis Gastos":
    st.title("💸 Gestión de Gastos")
    df_g = leer_pestaña("Gastos")
    
    col_tab, col_form = st.columns([2, 1])
    
    with col_tab:
        st.subheader("Lista de Movimientos")
        st.dataframe(df_g, use_container_width=True, height=400)
    
    with col_form:
        st.subheader("📝 Registrar Nuevo")
        with st.form("nuevo_gasto"):
            fecha = st.date_input("Fecha", datetime.now())
            monto = st.number_input("Monto ($)", min_value=0)
            cat = st.selectbox("Categoría", ["Alimentación", "Vivienda", "Servicios", "Ocio", "Otros"])
            desc = st.text_input("Descripción")
            if st.form_submit_button("Guardar en Google Sheets"):
                st.warning("⚠️ La función de GUARDAR se activará una vez arreglemos los Secrets.")

# --- PANTALLA: INGRESOS ---
elif menu == "💰 Mis Ingresos":
    st.title("💰 Gestión de Ingresos")
    df_i = leer_pestaña("Ingresos")
    st.table(df_i) # Versión tabla simple
