import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

# --- 1. CONEXIÓN DIRECTA (Bypass) ---
SHEET_ID = "1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g"

def leer_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    df = pd.read_csv(url)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

# --- 2. LOGUEO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    df_u = leer_pestaña("Usuarios")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔮 STULIO FINANCE")
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            df_u['usuario'] = df_u['usuario'].astype(str).str.strip()
            df_u['pass'] = df_u['pass'].astype(str).str.strip()
            match = df_u[(df_u["usuario"] == u_in) & (df_u["pass"] == p_in)]
            if not match.empty:
                st.session_state.autenticado = True
                st.session_state.full_name = match.iloc[0]["nombre"]
                st.rerun()
            else: st.error("Datos incorrectos")
    st.stop()

# --- 3. INTERFAZ REAL DE LA APP (DASHBOARD) ---
st.sidebar.title(f"Hola, {st.session_state.full_name.split()[0]}")
menu = st.sidebar.radio("Ir a:", ["📊 Resumen", "💸 Gastos", "💰 Ingresos"])

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()

if menu == "📊 Resumen":
    st.title("📊 Resumen Financiero")
    
    # Leemos datos
    df_g = leer_pestaña("Gastos")
    df_i = leer_pestaña("Ingresos")
    
    col1, col2, col3 = st.columns(3)
    total_i = df_i['monto'].sum() if not df_i.empty else 0
    total_g = df_g['monto'].sum() if not df_g.empty else 0
    balance = total_i - total_g
    
    col1.metric("Ingresos Totales", f"$ {total_i:,.0f}")
    col2.metric("Gastos Totales", f"$ {total_g:,.0f}")
    col3.metric("Balance Neto", f"$ {balance:,.0f}", delta=float(balance))

    st.divider()
    
    if not df_g.empty:
        fig = px.pie(df_g, values='monto', names='categoria', title="Distribución de Gastos")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aún no hay gastos registrados en el Excel.")

elif menu == "💸 Gastos":
    st.title("💸 Registro de Gastos")
    st.info("Usa este espacio para ver tus gastos actuales.")
    df_g = leer_pestaña("Gastos")
    st.dataframe(df_g, use_container_width=True)
    
    # Formulario (Visual)
    with st.expander("Añadir nuevo gasto (Próximamente)"):
        st.date_input("Fecha")
        st.text_input("Concepto")
        st.number_input("Monto", min_value=0)
        st.selectbox("Categoría", ["Alimentación", "Vivienda", "Transporte", "Ocio", "Otros"])
        st.button("Guardar Gasto")

elif menu == "💰 Ingresos":
    st.title("💰 Registro de Ingresos")
    df_i = leer_pestaña("Ingresos")
    st.dataframe(df_i, use_container_width=True)
