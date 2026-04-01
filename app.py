import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

# Conexión oficial con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer datos
def leer_datos(pestaña):
    # ttl=0 para que no guarde memoria vieja y lea siempre lo último de Google
    return conn.read(worksheet=pestaña, ttl=0)

# Función para guardar datos (Registro de nuevos usuarios)
def guardar_datos(pestaña, df):
    try:
        conn.update(worksheet=pestaña, data=df)
        return True
    except Exception as e:
        st.error(f"Error técnico al intentar guardar: {e}")
        return False

# --- 2. LÓGICA DE ACCESO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- AQUÍ ESTÁ LA CORRECCIÓN DE DETECCIÓN DE ERRORES ---
try:
    # Intentamos leer la pestaña de Usuarios
    df_u = leer_datos("Usuarios")
except Exception as e:
    st.error(f"❌ Error de conexión detallado: {e}")
    st.info("Revisa que el nombre de la pestaña en Google Sheets sea exactamente 'Usuarios' (sin espacios).")
    st.stop()

# --- INTERFAZ DE LOGIN / REGISTRO ---
if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔮 STULIO FINANCE")
        t1, t2 = st.tabs(["🔑 Entrar", "📝 Registro"])
        
        with t1:
            u_in = st.text_input("Usuario")
            p_in = st.text_input("Clave", type="password")
            if st.button("Ingresar"):
                # Verificamos si coinciden usuario y contraseña
                user_match = df_u[(df_u["usuario"].astype(str) == u_in) & (df_u["pass"].astype(str) == p_in)]
                if not user_match.empty:
                    st.session_state.autenticado = True
                    st.session_state.username = u_in
                    st.session_state.full_name = user_match.iloc[0]["nombre"]
                    st.rerun()
                else:
                    st.error("Usuario o clave incorrectos")
        
        with t2:
            st.info("Crea tu cuenta para empezar a usar la App")
            n_f = st.text_input("Nombre Completo")
            n_u = st.text_input("Usuario (Login)")
            n_p = st.text_input("Contraseña")
            
            if st.button("Crear Cuenta"):
                if n_f and n_u and n_p:
                    # Creamos la nueva fila para el Excel
                    nueva_fila = pd.DataFrame([[n_f, n_u, "test@mail.com", n_p]], columns=df_u.columns)
                    df_final = pd.concat([df_u, nueva_fila], ignore_index=True)
                    
                    if guardar_datos("Usuarios", df_final):
                        st.success("¡Usuario creado con éxito! Ahora puedes ir a la pestaña 'Entrar'.")
                        st.balloons()
                else:
                    st.warning("Por favor, llena todos los campos.")

    st.stop()

# --- 3. DASHBOARD PRINCIPAL (Cuando ya entraste) ---
st.header(f"👋 Bienvenido, {st.session_state.full_name}")

# Aquí puedes empezar a poner tus gráficas y funciones de gastos
st.write("Has ingresado exitosamente a tu sistema financiero.")

if st.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()
