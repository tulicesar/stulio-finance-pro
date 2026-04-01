import streamlit as st
import pandas as pd

st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

# URL Directa (Bypass de Secrets)
URL_USUARIOS = "https://docs.google.com/spreadsheets/d/1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g/gviz/tq?tqx=out:csv&sheet=Usuarios"

def leer_datos_directo():
    df = pd.read_csv(URL_USUARIOS)
    # LIMPIEZA MÁGICA: Quita espacios y pone todo en minúsculas en los encabezados
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

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
        
        if df_u.empty:
            st.warning("⚠️ El Excel está vacío. Escribe tus datos en la fila 2.")
        else:
            st.success(f"✅ Conectado. {len(df_u)} usuario(s) detectado(s).")

        u_in = st.text_input("Usuario")
        p_in = st.text_input("Clave", type="password")
        
        if st.button("Ingresar"):
            if not df_u.empty:
                # Limpiamos los datos para que coincidan siempre
                df_u['usuario'] = df_u['usuario'].astype(str).str.strip()
                df_u['pass'] = df_u['pass'].astype(str).str.strip()
                
                # Buscamos al usuario
                match = df_u[(df_u["usuario"] == str(u_in).strip()) & (df_u["pass"] == str(p_in).strip())]
                
                if not match.empty:
                    st.session_state.autenticado = True
                    st.session_state.full_name = match.iloc[0]["nombre"]
                    st.rerun()
                else: 
                    st.error("Usuario o clave incorrectos")

    st.stop()

# --- 3. DASHBOARD ---
st.balloons()
st.header(f"👋 ¡Bienvenido al sistema, {st.session_state.full_name}!")
st.info("La conexión con Google Sheets está ACTIVA y funcionando.")

if st.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()
