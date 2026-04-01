import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- PROTECCIÓN DE LIBRERÍAS ---
try:
    import plotly.express as px
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:
    st.error("🚨 Faltan librerías. Asegúrate de tener plotly y reportlab.")

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Finanzas Tulio Pro", layout="wide", page_icon="⚖️")

# CONEXIÓN GOOGLE (Bypass)
SHEET_ID = "1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g"

def formato_cop(valor):
    try: return f"$ {float(valor):,.0f}".replace(",", ".")
    except: return "$ 0"

def obtener_fecha_completa():
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    ahora = datetime.now()
    return f"{meses[ahora.month - 1]} {ahora.day} de {ahora.year}"

# --- 2. CARGA DE DATOS (Cambiado para Google Sheets) ---
def cargar_bd_google(pestaña):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestaña}"
        df = pd.read_csv(url)
        # Forzamos los nombres de columnas que tu código espera
        if pestaña == "Gastos":
            df.columns = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Recurrente"]
        return df
    except:
        return pd.DataFrame()

# --- LÓGICA DE LOGIN (Para que no de error la línea 104) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    # Leemos usuarios para validar
    try:
        url_u = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Usuarios"
        df_u = pd.read_csv(url_u)
        df_u.columns = [c.lower() for c in df_u.columns]
    except:
        st.error("Error cargando base de usuarios")
        st.stop()

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔮 STULIO FINANCE")
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            match = df_u[(df_u["usuario"].astype(str) == u_in) & (df_u["pass"].astype(str) == p_in)]
            if not match.empty:
                st.session_state["autenticado"] = True
                # Guardamos los datos igual que en tu código original
                st.session_state["user_data"] = {"nombre": match.iloc[0]["nombre"]}
                st.balloons()
                st.rerun()
            else:
                st.error("Datos incorrectos")
    st.stop()

# --- SI LLEGA AQUÍ ES PORQUE ESTÁ AUTENTICADO ---
df_gastos_full = cargar_bd_google("Gastos")
# Para ingresos usamos una carga simple
url_i = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Ingresos"
df_ingresos_full = pd.read_csv(url_i)

# --- 3. CALCULADORA UNIFICADA (Tu lógica original) ---
def calcular_balance_tulio(df_g, total_ingresos):
    df_temp = df_g.copy()
    df_temp["Monto"] = pd.to_numeric(df_temp["Monto"], errors='coerce').fillna(0)
    df_temp["Valor Referencia"] = pd.to_numeric(df_temp["Valor Referencia"], errors='coerce').fillna(0)
    v_pagados = df_temp[df_temp["Pagado"] == True]["Monto"].sum()
    
    def deuda_pendiente(r):
        ref = float(r["Valor Referencia"])
        mon = float(r["Monto"])
        if r["Pagado"]: return max(0, ref - mon)
        return max(ref, mon)
    
    v_a_pagar = df_temp.apply(deuda_pendiente, axis=1).sum() if not df_temp.empty else 0
    fondos = total_ingresos - v_pagados
    saldo_f = fondos - v_a_pagar
    return v_pagados, v_a_pagar, saldo_f, fondos

# --- 5. SIDEBAR (Tu diseño original) ---
with st.sidebar:
    # AQUÍ ESTABA EL ERROR: Usamos .get como tenías antes
    nombre_usuario = st.session_state.get('user_data', {}).get('nombre', 'Tulio Cesar')
    st.header(f"👤 {nombre_usuario}")
    
    if st.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()
    st.divider()
    
    anio_sel = st.selectbox("📅 Seleccione Año", [2025, 2026, 2027], index=1)
    periodos_lista = ["Diciembre - Enero", "Enero - Febrero", "Febrero - Marzo", "Marzo - Abril", "Abril - Mayo", "Mayo - Junio", 
                      "Junio - Julio", "Julio - Agosto", "Agosto - Septiembre", "Septiembre - Octubre", "Octubre - Noviembre", "Noviembre - Diciembre"]
    mes_sel = st.selectbox("📆 Seleccione Periodo", periodos_lista)

    st.subheader("💰 Ingresos")
    # Buscamos ingresos en el DF que bajamos de Google
    ing_act = df_ingresos_full[(df_ingresos_full["Periodo"] == mes_sel) & (df_ingresos_full["Año"] == anio_sel)]
    
    s_ant = st.number_input("Saldo Anterior", value=float(ing_act["SaldoAnterior"].iloc[0] if not ing_act.empty else 0.0))
    nom = st.number_input("Nómina", value=float(ing_act["Nomina"].iloc[0] if not ing_act.empty else 0.0))
    otr = st.number_input("Otros", value=float(ing_act["Otros"].iloc[0] if not ing_act.empty else 0.0))
    total_ing_actual = s_ant + nom + otr

# --- 6. CUERPO PRINCIPAL (Tu diseño original) ---
st.title(f"📊 Control Financiero: {mes_sel} {anio_sel}")

df_mes = df_gastos_full[(df_gastos_full["Periodo"] == mes_sel) & (df_gastos_full["Año"] == anio_sel)].copy()

config_t = {
    "Categoría": st.column_config.SelectboxColumn(options=["Obligaciones financieras", "Impuestos", "Hogar", "Transporte", "Alimentación", "Servicios", "Servicio de Entretenimiento", "Salud", "Otros"], required=True),
    "Monto": st.column_config.NumberColumn("Valor Pagado ($)", format="$ %,.0f"),
    "Valor Referencia": st.column_config.NumberColumn("Valor a Pagar ($)", format="$ %,.0f"),
    "Pagado": st.column_config.CheckboxColumn("¿Pagado?"),
    "Recurrente": st.column_config.CheckboxColumn("🔁")
}

if df_mes.empty:
    st.info("No hay datos para este mes en el Excel.")
    edited_df = pd.DataFrame(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Recurrente"])
else:
    edited_df = st.data_editor(df_mes.drop(columns=["Año", "Periodo"]), column_config=config_t, num_rows="dynamic", use_container_width=True, hide_index=True)

# EJECUTAR CÁLCULOS
v_pag, v_pend, bal_final, fondos_hoy = calcular_balance_tulio(edited_df, total_ing_actual)

st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("💰 Ingreso Total", formato_cop(total_ing_actual))
c2.metric("✅ Valores Pagados", formato_cop(v_pag))
c3.metric("⏳ Valores a Pagar", formato_cop(v_pend))

ca, cb = st.columns(2)
with ca:
    st.info(f"🏦 **Fondos al {obtener_fecha_completa()}**")
    st.markdown(f"<h3 style='color: #1E88E5;'>{formato_cop(fondos_hoy)}</h3>", unsafe_allow_html=True)
with cb:
    st.success(f"💵 **Saldo a Favor Final**")
    st.markdown(f"<h3 style='color: #2E7D32;'>{formato_cop(bal_final)}</h3>", unsafe_allow_html=True)

st.warning("⚠️ Los cambios que hagas aquí son visuales. Para guardar permanentemente, edita tu Google Sheet directamente.")
