import streamlit as st
import pandas as pd

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

# Metemos la dirección directamente aquí para saltarnos el error de los Secrets
URL_USUARIOS = "https://docs.google.com/spreadsheets/d/1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g/gviz/tq?tqx=out:csv&sheet=Usuarios"

# Función de lectura directa (No usa Secrets, no da error 400)
def leer_datos_directo():
    return pd.read_csv(URL_USUARIOS)

# --- 2. ACCESO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

try:
    df_u = leer_datos_directo()
except Exception as e:
    st.error(f"Error al conectar con Google: {e}")
    st.stop()

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔮 STULIO FINANCE")
        t1, t2 = st.tabs(["🔑 Entrar", "📝 Registro"])
        
        with t1:
            u_in = st.text_input("Usuario")
            p_in = st.text_input("Clave", type="password")
            if st.button("Ingresar"):
                # Como la hoja está vacía al principio, esto fallará hasta que haya alguien
                if not df_u.empty and "usuario" in df_u.columns:
                    match = df_u[(df_u["usuario"].astype(str) == u_in) & (df_u["pass"].astype(str) == p_in)]
                    if not match.empty:
                        st.session_state.autenticado = True
                        st.session_state.full_name = match.iloc[0]["nombre"]
                        st.rerun()
                    else: st.error("Datos incorrectos")
                else:
                    st.warning("La base de datos está vacía. Regístrate primero.")
        
        with t2:
            st.info("Para registrarte por primera vez, añade tu usuario manualmente en el Excel de Google.")
            st.write("Debido a los problemas con los Secrets, el registro automático está pausado.")
            st.write("Abre tu Excel y escribe en la primera fila tus datos.")

    st.stop()

# --- 3. DASHBOARD ---
st.success(f"Bienvenido {st.session_state.full_name}")
if st.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()
