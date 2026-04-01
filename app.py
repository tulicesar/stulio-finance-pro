import streamlit as st
import pandas as pd

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

# ID de tu hoja (sacado de tu enlace)
SHEET_ID = "1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g"

# Función para leer datos de forma directa (sin errores de HTTP)
def leer_datos(pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestaña}"
    return pd.read_csv(url)

# Función para guardar (aquí sí usamos la conexión de Streamlit)
def guardar_datos(pestaña, df):
    try:
        conn = st.connection("gsheets", type=st.connection.GSheetsConnection)
        conn.update(worksheet=pestaña, data=df)
    except:
        st.error("Error al conectar para guardar. Revisa los Secrets.")

# --- 2. ACCESO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# Cargamos usuarios con la nueva función directa
try:
    df_u = leer_datos("Usuarios")
except Exception as e:
    st.error(f"Error crítico al leer la base de datos: {e}")
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
                match = df_u[(df_u["usuario"] == u_in) & (df_u["pass"].astype(str) == p_in)]
                if not match.empty:
                    st.session_state.autenticado = True
                    st.session_state.username = u_in
                    st.session_state.full_name = match.iloc[0]["nombre"]
                    st.rerun()
                else: st.error("Datos incorrectos")
        
        with t2:
            st.info("Para registrarte, escribe tus datos y dale a guardar.")
            n_f = st.text_input("Nombre Completo")
            n_u = st.text_input("Usuario (Login)")
            n_p = st.text_input("Contraseña")
            if st.button("Crear Cuenta"):
                nuevo = pd.DataFrame([[n_f, n_u, "email@test.com", n_p]], columns=df_u.columns)
                guardar_datos("Usuarios", pd.concat([df_u, nuevo], ignore_index=True))
                st.success("¡Registrado! Refresca la página e inicia sesión.")

    st.stop()

# --- 3. DASHBOARD (Solo si está autenticado) ---
st.success(f"Bienvenido {st.session_state.full_name}")
if st.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()
