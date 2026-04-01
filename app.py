import streamlit as st
import pandas as pd

st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

# URL Directa
URL_USUARIOS = "https://docs.google.com/spreadsheets/d/1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g/gviz/tq?tqx=out:csv&sheet=Usuarios"

def leer_datos_directo():
    # El parámetro index_col=False asegura que lea bien las columnas
    return pd.read_csv(URL_USUARIOS)

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

try:
    df_u = leer_datos_directo()
    # --- LÍNEA DE DEBUG (Borrar luego) ---
    # st.write("Datos detectados en el Excel:", df_u) 
except Exception as e:
    st.error(f"Error al conectar con Google: {e}")
    st.stop()

if not st.session_state.autenticado:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔮 STULIO FINANCE")
        
        # VISOR DE SEGURIDAD: Esto te dirá si la App está leyendo algo o no
        if df_u.empty:
            st.warning("⚠️ Atención: La App lee el archivo pero lo ve VACÍO.")
            st.info("Revisa que en tu Excel los datos empiecen en la FILA 2.")
        else:
            st.success(f"✅ Conexión exitosa. Se detectaron {len(df_u)} usuarios.")

        u_in = st.text_input("Usuario")
        p_in = st.text_input("Clave", type="password")
        
        if st.button("Ingresar"):
            if not df_u.empty:
                # Limpiamos espacios por si acaso
                df_u['usuario'] = df_u['usuario'].astype(str).str.strip()
                df_u['pass'] = df_u['pass'].astype(str).str.strip()
                
                match = df_u[(df_u["usuario"] == u_in) & (df_u["pass"] == p_in)]
                if not match.empty:
                    st.session_state.autenticado = True
                    st.session_state.full_name = match.iloc[0]["nombre"]
                    st.rerun()
                else: 
                    st.error("Usuario o clave incorrectos")
            else:
                st.error("No hay datos para comparar.")

    st.stop()

# --- DASHBOARD ---
st.header(f"👋 Bienvenido, {st.session_state.full_name}")
if st.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()
