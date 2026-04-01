import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from io import BytesIO

# --- PROTECCIÓN DE LIBRERÍAS ---
try:
    import plotly.express as px
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:
    st.error("🚨 Faltan librerías. Ejecuta: **python -m pip install plotly reportlab openpyxl**")
    st.stop()

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Finanzas Tulio Pro", layout="wide", page_icon="⚖️")

USER_DB = "usuarios.json"
BASE_FILE = "base.xlsx"

def formato_cop(valor):
    try: return f"$ {float(valor):,.0f}".replace(",", ".")
    except: return "$ 0"

def obtener_fecha_completa():
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    ahora = datetime.now()
    return f"{meses[ahora.month - 1]} {ahora.day} de {ahora.year}"

# --- 2. CARGA DE DATOS ---
def cargar_bd():
    cols_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Recurrente"]
    if not os.path.exists(BASE_FILE):
        return pd.DataFrame(columns=cols_g), pd.DataFrame(columns=["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros"])
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        df_g["Monto"] = pd.to_numeric(df_g["Monto"], errors='coerce').fillna(0)
        df_g["Valor Referencia"] = pd.to_numeric(df_g["Valor Referencia"], errors='coerce').fillna(0)
        df_g["Pagado"] = df_g["Pagado"].fillna(False).astype(bool)
        df_g["Recurrente"] = df_g["Recurrente"].fillna(False).astype(bool)
        return df_g, df_i
    except:
        return pd.DataFrame(columns=cols_g), pd.DataFrame(columns=["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros"])

df_gastos_full, df_ingresos_full = cargar_bd()

# --- 3. CALCULADORA UNIFICADA (PROTEGIDA CONTRA VACÍOS) ---
def calcular_balance_tulio(df_g, total_ingresos):
    # Aseguramos que los datos sean números antes de operar
    df_temp = df_g.copy()
    df_temp["Monto"] = pd.to_numeric(df_temp["Monto"], errors='coerce').fillna(0)
    df_temp["Valor Referencia"] = pd.to_numeric(df_temp["Valor Referencia"], errors='coerce').fillna(0)
    
    v_pagados = df_temp[df_temp["Pagado"] == True]["Monto"].sum()
    
    def deuda_pendiente(r):
        # Conversión segura para evitar el error de NoneType
        ref = float(r["Valor Referencia"])
        mon = float(r["Monto"])
        if r["Pagado"]:
            return max(0, ref - mon)
        return max(ref, mon)
    
    v_a_pagar = df_temp.apply(deuda_pendiente, axis=1).sum() if not df_temp.empty else 0
    fondos = total_ingresos - v_pagados
    saldo_f = fondos - v_a_pagar
    return v_pagados, v_a_pagar, saldo_f, fondos

# --- 4. MOTOR DE PDF SEMESTRAL ---
def generar_pdf_tulio(df_g, df_i, titulo):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, f"REPORTE FINANCIERO: {titulo}")
    
    ing_ini = df_i["SaldoAnterior"].iloc[0] if not df_i.empty else 0
    total_ing_sem = df_i["Nomina"].sum() + df_i["Otros"].sum() + ing_ini
    
    pag, pend, bal, _ = calcular_balance_tulio(df_g, total_ing_sem)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 710, "RESUMEN DE BALANCE PROYECTADO")
    c.setFont("Helvetica", 11)
    c.drawString(60, 690, f"Total Ingresos del Periodo: {formato_cop(total_ing_sem)}")
    c.drawString(60, 675, f"Total Gastos Pagados: {formato_cop(pag)}")
    c.drawString(60, 660, f"Total Gastos Proyectados (Pendientes): {formato_cop(pend)}")
    c.line(60, 650, 350, 650)
    
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.darkgreen if bal >= 0 else colors.red)
    c.drawString(60, 635, f"BALANCE FINAL (SALDO A FAVOR): {formato_cop(bal)}")
    c.setFillColor(colors.black)
    
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header(f"👤 {st.session_state.get('user_data', {}).get('nombre', 'Tulio Cesar')}")
    if st.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.rerun()
    st.divider()
    
    anio_sel = st.selectbox("📅 Seleccione Año", [2025, 2026, 2027], index=1)
    periodos_lista = ["Diciembre - Enero", "Enero - Febrero", "Febrero - Marzo", "Marzo - Abril", "Abril - Mayo", "Mayo - Junio", 
                      "Junio - Julio", "Julio - Agosto", "Agosto - Septiembre", "Septiembre - Octubre", "Octubre - Noviembre", "Noviembre - Diciembre"]
    mes_sel = st.selectbox("📆 Seleccione Periodo", periodos_lista)
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
    s_ant = st.number_input("Saldo Anterior", value=saldo_auto if arrastrar else float(ing_act["SaldoAnterior"].iloc[0] if not ing_act.empty else 0.0), disabled=arrastrar)
    nom = st.number_input("Nómina", value=float(ing_act["Nomina"].iloc[0] if not ing_act.empty else 0.0))
    otr = st.number_input("Otros", value=float(ing_act["Otros"].iloc[0] if not ing_act.empty else 0.0))
    total_ing_actual = s_ant + nom + otr

    st.divider()
    st.subheader("📄 Reportes PDF")
    col_pdf1, col_pdf2 = st.columns(2)
    with col_pdf1:
        if st.button("Ene - Jun"):
            meses_s1 = periodos_lista[1:7]
            d_g = df_gastos_full[(df_gastos_full["Año"] == anio_sel) & (df_gastos_full["Periodo"].isin(meses_s1))]
            d_i = df_ingresos_full[(df_ingresos_full["Año"] == anio_sel) & (df_ingresos_full["Periodo"].isin(meses_s1))]
            pdf1 = generar_pdf_tulio(d_g, d_i, f"Primer Semestre {anio_sel}")
            st.download_button("📥 Descargar", pdf1, f"Reporte_S1_{anio_sel}.pdf")
    with col_pdf2:
        if st.button("Jun - Dic"):
            meses_s2 = periodos_lista[6:12]
            d_g = df_gastos_full[(df_gastos_full["Año"] == anio_sel) & (df_gastos_full["Periodo"].isin(meses_s2))]
            d_i = df_ingresos_full[(df_ingresos_full["Año"] == anio_sel) & (df_ingresos_full["Periodo"].isin(meses_s2))]
            pdf2 = generar_pdf_tulio(d_g, d_i, f"Segundo Semestre {anio_sel}")
            st.download_button("📥 Descargar", pdf2, f"Reporte_S2_{anio_sel}.pdf")

# --- 6. CUERPO PRINCIPAL ---
st.title(f"📊 Control Financiero: {mes_sel} {anio_sel}")

df_mes = df_gastos_full[(df_gastos_full["Periodo"] == mes_sel) & (df_gastos_full["Año"] == anio_sel)].copy()
# Carga de recurrentes
if df_mes.empty and idx_mes > 0:
    rec = df_gastos_full[(df_gastos_full["Periodo"] == mes_p) & (df_gastos_full["Año"] == anio_p) & (df_gastos_full["Recurrente"] == True)].copy()
    if not rec.empty:
        rec["Periodo"], rec["Año"], rec["Pagado"] = mes_sel, anio_sel, False
        df_mes = rec

config_t = {
    "Categoría": st.column_config.SelectboxColumn(options=["Obligaciones financieras", "Impuestos", "Hogar", "Transporte", "Alimentación", "Servicios", "Servicio de Entretenimiento", "Salud", "Otros"], required=True),
    "Monto": st.column_config.NumberColumn("Valor Pagado ($)", format="$ %,.0f"),
    "Valor Referencia": st.column_config.NumberColumn("Valor a Pagar ($)", format="$ %,.0f"),
    "Pagado": st.column_config.CheckboxColumn("¿Pagado?"),
    "Recurrente": st.column_config.CheckboxColumn("🔁")
}

edited_df = st.data_editor(df_mes.drop(columns=["Año", "Periodo"]), column_config=config_t, num_rows="dynamic", use_container_width=True, hide_index=True)

# EJECUTAR CÁLCULOS (PROTEGIDOS)
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

if st.button("💾 GUARDAR TODO EL MES", use_container_width=True, type="primary"):
    df_resto_g = df_gastos_full[~((df_gastos_full["Periodo"] == mes_sel) & (df_gastos_full["Año"] == anio_sel))]
    df_g_final = pd.concat([df_resto_g, edited_df.assign(Periodo=mes_sel, Año=anio_sel)], ignore_index=True)
    df_resto_i = df_ingresos_full[~((df_ingresos_full["Periodo"] == mes_sel) & (df_ingresos_full["Año"] == anio_sel))]
    df_i_nuevo = pd.DataFrame({"Año":[anio_sel], "Periodo":[mes_sel], "SaldoAnterior":[s_ant], "Nomina":[nom], "Otros":[otr]})
    df_i_final = pd.concat([df_resto_i, df_i_nuevo], ignore_index=True)
    with pd.ExcelWriter(BASE_FILE) as writer:
        df_g_final.to_excel(writer, sheet_name="Gastos", index=False)
        df_i_final.to_excel(writer, sheet_name="Ingresos", index=False)
    st.balloons()
    st.rerun()
