import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

LOGO_LOGIN = "logoapp 1.png"
LOGO_SIDEBAR = "logoapp 2.png" 
LOGO_APP_H = "LOGOapp horizontal.png" 
BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"

COLOR_MAP = {
    "Hogar": "#FFB347", "Servicios": "#FFB347", "Salud": "#B39EB5", 
    "Transporte": "#77B5FE", "Obligaciones": "#FF6961", "Alimentación": "#FDFD96", 
    "Otros": "#77DD77", "Impuestos": "#84b6f4"
}

st.markdown("""
    <style>
    header { background-color: rgba(0,0,0,0) !important; }
    .stApp { background: #0e1117; color: #dee2e6; }
    [data-testid="stDataEditor"] { font-size: 1.4rem !important; }
    .stTabs [aria-selected="true"] { color: #d4af37 !important; border-bottom-color: #d4af37 !important; font-weight: bold; }
    .card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #1a1d21; text-align: center; border-bottom: 4px solid #d4af37;
    }
    .card-label { font-size: 0.8rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #1a1d21; margin: 3px 0; }
    section[data-testid="stSidebar"] { background: rgba(0,0,0,0.8) !important; backdrop-filter: blur(15px); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #d4af37; color: black; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
def sanitize(df, is_gastos=False, is_oi=False):
    if df.empty: return df
    if "Año" in df.columns: df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(0).astype(int)
    if "Periodo" in df.columns: df["Periodo"] = df["Periodo"].astype(str).str.strip()
    if "Usuario" in df.columns: df["Usuario"] = df["Usuario"].astype(str).str.strip()
    return df

def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    col_oi = ["Año", "Periodo", "Descripción", "Monto", "Usuario"]
    if not os.path.exists(BASE_FILE): return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)
    df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
    df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
    try: df_oi = pd.read_excel(BASE_FILE, sheet_name="OtrosIngresos")
    except: df_oi = pd.DataFrame(columns=col_oi)
    return sanitize(df_g), sanitize(df_i), sanitize(df_oi)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum() if not df_g.empty else 0
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), bf, ahorro_p

# --- NUEVO REPORTE PDF CON DETALLE DE INGRESOS ---
def generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses, titulo, anio):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    
    def head(canvas_obj, t, a):
        canvas_obj.setFillColor(colors.white); canvas_obj.rect(0, 0, 612, 792, fill=1)
        canvas_obj.setFillColor(HexColor("#1a1d21")); canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(50, 765, "My FinanceApp"); canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(50, 750, "by Stulio Designs")
        canvas_obj.setFont("Helvetica-Bold", 12); canvas_obj.drawRightString(560, 760, f"{t} - {a}")
        canvas_obj.setStrokeColor(HexColor("#d4af37")); canvas_obj.line(50, 740, 560, 740)
        # Fecha de generación
        canvas_obj.setFont("Helvetica-Oblique", 8); canvas_obj.setFillColor(colors.grey)
        fecha_gen = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        canvas_obj.drawString(50, 30, f"Documento generado el: {fecha_gen}")
        return 710

    y = head(c, titulo, anio)
    
    for m in meses:
        i_m = df_i_full[(df_i_full["Periodo"] == m) & (df_i_full["Año"] == anio)]
        g_m = df_g_full[(df_g_full["Periodo"] == m) & (df_g_full["Año"] == anio)]
        oi_m = df_oi_full[(df_oi_full["Periodo"] == m) & (df_oi_full["Año"] == anio)]
        
        s_ant = i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0
        nom = i_m["Nomina"].iloc[0] if not i_m.empty else 0
        otr_sum = oi_m["Monto"].sum() if not oi_m.empty else 0
        it, vp, vpy, _, bf, _ = calcular_metricas(g_m, nom, otr_sum, s_ant)

        if y < 250: c.showPage(); y = head(c, titulo, anio)
        
        # Resumen de Mes
        c.setFillColor(HexColor("#f8f9fa")); c.rect(50, y-55, 510, 60, fill=1, stroke=0)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(60, y-15, f"MES: {m}")
        c.setFont("Helvetica", 9); c.drawString(60, y-30, f"Ingresos Totales: $ {it:,.0f} | Pagado: $ {vp:,.0f} | Pendiente: $ {vpy:,.0f}")
        c.setFillColor(HexColor("#d4af37")); c.drawString(60, y-45, f"AHORRO PROYECTADO: $ {bf:,.0f}"); y -= 80

        # --- TABLA DE INGRESOS ---
        c.setFillColor(HexColor("#1a1d21")); c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "DETALLE DE INGRESOS"); y -= 15
        c.setFont("Helvetica-Bold", 8); c.drawString(60, y, "CONCEPTO"); c.drawRightString(540, y, "MONTO")
        c.line(50, y-3, 560, y-3); y -= 15; c.setFont("Helvetica", 8)
        
        c.drawString(60, y, "Saldo Anterior"); c.drawRightString(540, y, f"{s_ant:,.0f}"); y -= 12
        c.drawString(60, y, "Sueldo (Nómina)"); c.drawRightString(540, y, f"{nom:,.0f}"); y -= 12
        for _, row in oi_m.iterrows():
            c.drawString(60, y, f"Ingreso Extra: {row['Descripción']}"); c.drawRightString(540, y, f"{row['Monto']:,.0f}"); y -= 12
        y -= 15

        # --- TABLA DE GASTOS ---
        c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "DETALLE DE GASTOS"); y -= 15
        c.setFont("Helvetica-Bold", 8); c.drawString(60, y, "CATEGORÍA / DESCRIPCIÓN"); c.drawRightString(480, y, "MONTO"); c.drawRightString(540, y, "PAGADO")
        c.line(50, y-3, 560, y-3); y -= 15; c.setFont("Helvetica", 8)
        
        for _, row in g_m.iterrows():
            if y < 60: c.showPage(); y = head(c, titulo, anio); c.setFont("Helvetica", 8)
            desc = f"{row['Categoría']} - {row['Descripción']}"[:60]
            c.drawString(60, y, desc); c.drawRightString(480, y, f"{row['Monto']:,.0f}"); c.drawRightString(540, y, "SI" if row["Pagado"] else "NO"); y -= 12
        y -= 30

    c.showPage(); c.save(); buf.seek(0)
    return buf

# --- INICIO DE APP ---
df_g, df_i, df_oi = cargar_bd()

with st.sidebar:
    try: st.image(LOGO_SIDEBAR, use_container_width=True)
    except: st.title("My FinanceApp")
    
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    mes_s = st.selectbox("Mes Actual", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=datetime.now().month-1)
    
    # Cálculos de Arrastre
    idx = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"].index(mes_s)
    m_ant = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][idx-1] if idx > 0 else "Diciembre"
    a_ant = anio_s if idx > 0 else anio_s-1
    
    i_ant_row = df_i[(df_i["Periodo"] == m_ant) & (df_i["Año"] == a_ant)]
    g_ant_df = df_g[(df_g["Periodo"] == m_ant) & (df_g["Año"] == a_ant)]
    oi_ant_df = df_oi[(df_oi["Periodo"] == m_ant) & (df_oi["Año"] == a_ant)]
    
    s_sug = 0.0
    if not i_ant_row.empty:
        it_a, vp_a, vpy_a, _, bf_a, _ = calcular_metricas(g_ant_df, i_ant_row["Nomina"].sum(), oi_ant_df["Monto"].sum(), i_ant_row["SaldoAnterior"].iloc[0])
        s_sug = float(bf_a)

    arr_on = st.toggle(f"Arrastrar de {m_ant}", value=not i_ant_row.empty)
    s_in = st.number_input("Saldo Anterior", value=s_sug if arr_on else 0.0)
    n_in = st.number_input("Nómina/Sueldo", value=float(df_i[(df_i["Periodo"] == mes_s) & (df_i["Año"] == anio_s)]["Nomina"].iloc[0] if not df_i[(df_i["Periodo"] == mes_s) & (df_i["Año"] == anio_s)].empty else 0.0))
    
    st.divider()
    st.subheader("📑 Reportes")
    if st.button("📄 Generar Extracto Mensual"):
        pdf = generar_pdf_reporte(df_g, df_i, df_oi, [mes_s], f"Extracto {mes_s}", anio_s)
        st.download_button(f"Descargar Extracto {mes_s}.pdf", pdf, f"Extracto_{mes_s}.pdf")

    # SOLICITUD: Balances Proyectados
    st.subheader("⚖️ Balances Proyectados")
    if st.button("📥 Semestre 1 (Ene-Jun)"):
        pdf1 = generar_pdf_reporte(df_g, df_i, df_oi, ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"], "Balance S1", anio_s)
        st.download_button("Descargar S1.pdf", pdf1, "S1_Proyectado.pdf")
    if st.button("📥 Semestre 2 (Jul-Dic)"):
        pdf2 = generar_pdf_reporte(df_g, df_i, df_oi, ["Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], "Balance S2", anio_s)
        st.download_button("Descargar S2.pdf", pdf2, "S2_Proyectado.pdf")

# --- CUERPO PRINCIPAL (Mantiene lógica anterior de tablas y guardado) ---
st.header(f"Gestión de {mes_s} {anio_s}")
# ... (Aquí sigue el resto del código de tablas y métricas que ya tienes funcionando perfectamente) ...
