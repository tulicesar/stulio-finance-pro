import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from streamlit_gsheets import GSheetsConnection

# --- LIBRERÍAS ---
try:
    import plotly.express as px
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:
    st.error("🚨 Faltan librerías. Asegúrate de que estén en requirements.txt")

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Finanzas Tulio Pro", layout="wide", page_icon="⚖️")

# CONEXIÓN DIRECTA (Para que no falle)
URL_EXCEL = "https://docs.google.com/spreadsheets/d/1PfRDWnxk_SX7P45Yi7aaUR9gOIcM1Y5K0yg8EbMmi2g"
conn = st.connection("gsheets", type=GSheetsConnection)

def formato_cop(valor):
    try: return f"$ {float(valor):,.0f}".replace(",", ".")
    except: return "$ 0"

def obtener_fecha_completa():
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    ahora = datetime.now()
    return f"{meses[ahora.month - 1]} {ahora.day} de {ahora.year}"

# --- 2. CARGA DE DATOS (Desde Google Sheets) ---
@st.cache_data(ttl=0)
def cargar_bd():
    df_g = conn.read(spreadsheet=URL_EXCEL, worksheet="Gastos")
    df_i = conn.read(spreadsheet=URL_EXCEL, worksheet="Ingresos")
    df_u = conn.read(spreadsheet=URL_EXCEL, worksheet="Usuarios")
    # Limpiamos nombres de columnas
    for d in [df_g, df_i, df_u]:
        d.columns = [str(c).strip() for c in d.columns]
    return df_g, df_i, df_u

df_gastos_full, df_ingresos_full, df_u_full = cargar_bd()

# --- 3. LÓGICA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔮 STULIO FINANCE")
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Clave", type="password")
        if st.button("Ingresar"):
            df_u_limpio = df_u_full.copy()
            df_u_limpio.columns = [c.lower() for c in df_u_limpio.columns]
            match = df_u_limpio[(df_u_limpio["usuario"].astype(str) == u_in) & (df_u_limpio["pass"].astype(str) == p_in)]
            if not match.empty:
                st.session_state["autenticado"] = True
                st.session_state["user_data"] = {"nombre": match.iloc[0]["nombre"]}
                st.rerun()
            else: st.error("Datos incorrectos")
    st.stop()

# --- 4. CALCULADORA UNIFICADA (Tu lógica original) ---
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

# --- 5. MOTOR DE PDF (Tu lógica original) ---
def generar_pdf_tulio(df_g, df_i, titulo):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, f"REPORTE FINANCIERO: {titulo}")
    # ... (Aquí va tu lógica de dibujo de PDF)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# --- 6. SIDEBAR (Con tu arrastre de saldo) ---
with st.sidebar:
    st.header(f"👤 {st.session_state.get('user_data', {}).get('nombre', 'Tulio Cesar')}")
    if st.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()
    st.divider()
    
    anio_sel = st.selectbox("📅 Año", [2025, 2026, 2027], index=1)
    periodos_lista = ["Diciembre - Enero", "Enero - Febrero", "Febrero - Marzo", "Marzo - Abril", "Abril - Mayo", "Mayo - Junio", 
                      "Junio - Julio", "Julio - Agosto", "Agosto - Septiembre", "Septiembre - Octubre", "Octubre - Noviembre", "Noviembre - Diciembre"]
    mes_sel = st.selectbox("📆 Periodo", periodos_lista)
    idx_mes = periodos_lista.index(mes_sel)

    # Lógica de arrastre
    mes_p = periodos_lista[idx_mes-1] if idx_mes > 0 else periodos_lista[11]
    anio_p = anio_sel if idx_mes > 0 else anio_sel - 1
    i_prev = df_ingresos_full[(df_ingresos_full["Periodo"] == mes_p) & (df_ingresos_full["Año"] == anio_p)]
    g_prev = df_gastos_full[(df_gastos_full["Periodo"] == mes_p) & (df_gastos_full["Año"] == anio_p)]
    
    saldo_auto = 0.0
    if not i_prev.empty:
        total_ing_p = i_prev["SaldoAnterior"].sum() + i_prev["Nomina"].sum() + i_prev["Otros"].sum()
        _, _, saldo_auto, _ = calcular_balance_tulio(g_prev, total_ing_p)

    st.subheader("💰 Ingresos")
    arrastrar = st.toggle("🔄 Arrastrar saldo", value=True)
    ing_act = df_ingresos_full[(df_ingresos_full["Periodo"] == mes_sel) & (df_ingresos_full["Año"] == anio_sel)]
    s_ant = st.number_input("Saldo Anterior", value=float(saldo_auto if arrastrar else (ing_act["SaldoAnterior"].iloc[0] if not ing_act.empty else 0.0)), disabled=arrastrar)
    nom = st.number_input("Nómina", value=float(ing_act["Nomina"].iloc[0] if not ing_act.empty else 0.0))
    otr = st.number_input("Otros", value=float(ing_act["Otros"].iloc[0] if not ing_act.empty else 0.0))
    total_ing_actual = s_ant + nom + otr

# --- 7. CUERPO PRINCIPAL ---
st.title(f"📊 Control Financiero: {mes_sel} {anio_sel}")

df_mes = df_gastos_full[(df_gastos_full["Periodo"] == mes_sel) & (df_gastos_full["Año"] == anio_sel)].copy()

config_t = {
    "Categoría": st.column_config.SelectboxColumn(options=["Obligaciones financieras", "Impuestos", "Hogar", "Transporte", "Alimentación", "Servicios", "Salud", "Otros"], required=True),
    "Monto": st.column_config.NumberColumn("Valor Pagado ($)", format="$ %,.0f"),
    "Valor Referencia": st.column_config.NumberColumn("Valor a Pagar ($)", format="$ %,.0f"),
    "Pagado": st.column_config.CheckboxColumn("¿Pagado?"),
    "Recurrente": st.column_config.CheckboxColumn("🔁")
}

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

# BOTÓN GUARDAR (Ahora en Google Sheets)
if st.button("💾 GUARDAR TODO EL MES", use_container_width=True, type="primary"):
    df_resto_g = df_gastos_full[~((df_gastos_full["Periodo"] == mes_sel) & (df_gastos_full["Año"] == anio_sel))]
    df_g_final = pd.concat([df_resto_g, edited_df.assign(Periodo=mes_sel, Año=anio_sel)], ignore_index=True)
    df_resto_i = df_ingresos_full[~((df_ingresos_full["Periodo"] == mes_sel) & (df_ingresos_full["Año"] == anio_sel))]
    df_i_nuevo = pd.DataFrame({"Año":[anio_sel], "Periodo":[mes_sel], "SaldoAnterior":[s_ant], "Nomina":[nom], "Otros":[otr]})
    df_i_final = pd.concat([df_resto_i, df_i_nuevo], ignore_index=True)
    
    # SUBIDA A LA NUBE
    conn.update(spreadsheet=URL_EXCEL, worksheet="Gastos", data=df_g_final)
    conn.update(spreadsheet=URL_EXCEL, worksheet="Ingresos", data=df_i_final)
    
    st.balloons()
    st.success("¡Sincronizado con Google Sheets!")
    st.rerun()
