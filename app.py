import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

# ID de tu hoja
SHEET_ID = "1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g"

# Conexión oficial de Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

def leer_datos(pestaña):
    # Leemos usando la conexión configurada en Secrets
    return conn.read(worksheet=pestaña, ttl=0)

def guardar_datos(pestaña, df):
    try:
        # Actualizamos la hoja completa con el nuevo DataFrame
        conn.update(worksheet=pestaña, data=df)
        return True
    except Exception as e:
        st.error(f"Error técnico al guardar: {e}")
        return False

# --- 2. LÓGICA DE ACCESO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

try:
    df_u = leer_datos("Usuarios")
except:
    st.error("No se pudo leer la base de datos. Revisa los Secrets.")
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
                # Filtramos para ver si el usuario y pass coinciden
                user_match = df_u[(df_u["usuario"].astype(str) == u_in) & (df_u["pass"].astype(str) == p_in)]
                if not user_match.empty:
                    st.session_state.autenticado = True
                    st.session_state.username = u_in
                    st.session_state.full_name = user_match.iloc[0]["nombre"]
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos")
        
        with t2:
            st.info("Crea tu cuenta para empezar")
            n_f = st.text_input("Nombre Completo")
            n_u = st.text_input("Usuario (Login)")
            n_p = st.text_input("Contraseña")
            if st.button("Crear Cuenta"):
                if n_f and n_u and n_p:
                    # Creamos la nueva fila
                    nueva_fila = pd.DataFrame([[n_f, n_u, "test@mail.com", n_p]], columns=df_u.columns)
                    df_final = pd.concat([df_u, nueva_fila], ignore_index=True)
                    
                    if guardar_datos("Usuarios", df_final):
                        st.success("¡Usuario creado con éxito! Ya puedes entrar.")
                else:
                    st.warning("Por favor llena todos los campos")

    st.stop()

# --- 3. DASHBOARD (Si ya entró) ---
st.header(f"Bienvenido, {st.session_state.full_name}")
if st.button("Salir"):
    st.session_state.autenticado = False
    st.rerun()
