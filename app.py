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
    st.error("🚨 Faltan librerías. La App las instalará automáticamente si están en requirements.txt")

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="Finanzas Tulio Pro", layout="wide", page_icon="⚖️")

# Tu ID de Google Sheets (El que ya funciona)
SHEET_ID = "1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g"

def formato_cop(valor):
    try: return f"$ {float(valor):,.0f}".replace(",", ".")
    except: return "$ 0"

def obtener_fecha_completa():
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    ahora = datetime.now()
    return f"{meses[ahora.month - 1]} {ahora.day} de {ahora.year}"

# --- 2. CARGA DE DATOS DESDE GOOGLE SHEETS (Bypass) ---
def leer_pestaña(nombre_pestaña):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
        df = pd.read_csv(url)
        # Limpieza de columnas para evitar errores de espacios o mayúsculas
        df.columns = [str(c).strip().title() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error leyendo {nombre_pestaña}: {e}")
        return pd.DataFrame()

# --- 3. LÓGICA DE LOGIN (Integrada con tu pestaña Usuarios) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    df_u = leer_pestaña("Usuarios")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔮 STULIO FINANCE")
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Clave", type="password")
        if st.button("🚀 Ingresar"):
            # Ajustamos nombres de columnas de usuarios
            df_u.columns = [c.lower() for c in df_u.columns]
            match = df_u[(df_u["usuario"].astype(str) == u_in) & (df_u["pass"].astype(str) == p_in)]
            if not match.empty:
                st.session_state.autenticado = True
                st.session_state.user_full_name = match.iloc[0]["nombre"]
                st.balloons()
                st.rerun()
            else: st.error("Datos incorrectos")
    st.stop()

# --- 4. CARGA DE DATOS PARA EL DASHBOARD ---
df_gastos_full = leer_pestaña("Gastos")
df_ingresos_full = leer_pestaña("Ingresos")

# --- 5. CALCULADORA UNIFICADA ---
def calcular_balance_tulio(df_g, total_ingresos):
    if df_g.empty: return 0, 0, total_ingresos, total_ingresos
    
    df_temp = df_g.copy()
    df_temp["Monto"] = pd.to_numeric(df_temp["Monto"], errors='coerce').fillna(0)
    df_temp["Valor Referencia"] = pd.to_numeric(df_temp["Valor Referencia"], errors='coerce').fillna(0)
    
    v_pagados = df_temp[df_temp["Pagado"] == True]["Monto"].sum()
    
    def deuda_pendiente(r):
        ref = float(r["Valor Referencia"])
        mon = float(r["Monto"])
        return max(0, ref - mon) if r["Pagado"] else max(ref, mon)
    
    v_a_pagar = df_temp.apply(deuda_pendiente, axis=1).sum()
    fondos = total_ingresos - v_pagados
    saldo_f = fondos - v_a_pagar
    return v_pagados, v_a_pagar, saldo_f, fondos

# --- 6. MOTOR DE PDF ---
def generar_pdf_tulio(df_g, df_i, titulo):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, f"REPORTE: {titulo}")
    # ... (Aquí iría el resto de tu lógica de PDF)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# --- 7. SIDEBAR ---
with st.sidebar:
    st.header(f"👤 {st.session_state.user_full_name}")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()
    st.divider()
    
    anio_sel = st.selectbox("📅 Año", [2025, 2026, 2027], index=1)
    periodos_lista = ["Diciembre - Enero", "Enero - Febrero", "Febrero - Marzo", "Marzo - Abril", "Abril - Mayo", "Mayo - Junio", 
                      "Junio - Julio", "Julio - Agosto", "Agosto - Septiembre", "Septiembre - Octubre", "Octubre - Noviembre", "Noviembre - Diciembre"]
    mes_sel = st.selectbox("📆 Periodo", periodos_lista)

    st.subheader("💰 Ingresos")
    ing_act = df_ingresos_full[(df_ingresos_full["Periodo"] == mes_sel) & (df_ingresos_full["Año"] == anio_sel)]
    
    s_ant = st.number_input("Saldo Anterior", value=float(ing_act["Saldoanterior"].iloc[0] if not ing_act.empty else 0.0))
    nom = st.number_input("Nómina", value=float(ing_act["Nomina"].iloc[0] if not ing_act.empty else 0.0))
    otr = st.number_input("Otros", value=float(ing_act["Otros"].iloc[0] if not ing_act.empty else 0.0))
    total_ing_actual = s_ant + nom + otr

# --- 8. CUERPO PRINCIPAL ---
st.title(f"📊 Control Financiero: {mes_sel} {anio_sel}")

# Filtrar gastos del mes
df_mes = df_gastos_full[(df_gastos_full["Periodo"] == mes_sel) & (df_gastos_full["Año"] == anio_sel)].copy()

if df_mes.empty:
    st.warning("⚠️ No hay datos para este periodo en Google Sheets.")
    edited_df = pd.DataFrame(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Recurrente"])
else:
    # Configuración de columnas para el editor
    config_t = {
        "Categoría": st.column_config.SelectboxColumn(options=["Hogar", "Transporte", "Alimentación", "Salud", "Otros"], required=True),
        "Monto": st.column_config.NumberColumn("Valor Pagado ($)", format="$ %,.0f"),
        "Valor Referencia": st.column_config.NumberColumn("Valor a Pagar ($)", format="$ %,.0f"),
        "Pagado": st.column_config.CheckboxColumn("¿Pagado?"),
        "Recurrente": st.column_config.CheckboxColumn("🔁")
    }
    edited_df = st.data_editor(df_mes.drop(columns=["Año", "Periodo"]), column_config=config_t, num_rows="dynamic", use_container_width=True, hide_index=True)

# Cálculos
v_pag, v_pend, bal_final, fondos_hoy = calcular_balance_tulio(edited_df, total_ing_actual)

# Métricas Visuales
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("💰 Ingreso Total", formato_cop(total_ing_actual))
c2.metric("✅ Pagado", formato_cop(v_pag))
c3.metric("⏳ Pendiente", formato_cop(v_pend))

ca, cb = st.columns(2)
with ca:
    st.info(f"🏦 **Fondos al Hoy**")
    st.markdown(f"<h3 style='color: #1E88E5;'>{formato_cop(fondos_hoy)}</h3>", unsafe_allow_html=True)
with cb:
    st.success(f"💵 **Saldo Final**")
    st.markdown(f"<h3 style='color: #2E7D32;'>{formato_cop(bal_final)}</h3>", unsafe_allow_html=True)

st.warning("Nota: Para guardar cambios permanentes, edita directamente el Google Sheets mientras terminamos de configurar el permiso de escritura.")
