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
    .card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #1a1d21; text-align: center; border-bottom: 4px solid #d4af37;
    }
    .card-label { font-size: 0.8rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #1a1d21; margin: 3px 0; }
    .legend-bar {
        padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; 
        font-size: 0.9rem; font-weight: bold; color: #1a1d21; 
        display: flex; justify-content: space-between; align-items: center;
    }
    section[data-testid="stSidebar"] { background: rgba(0,0,0,0.8) !important; backdrop-filter: blur(15px); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #d4af37; color: black; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
def sanitize(df):
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
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        try: df_oi = pd.read_excel(BASE_FILE, sheet_name="OtrosIngresos")
        except: df_oi = pd.DataFrame(columns=col_oi)
        return sanitize(df_g), sanitize(df_i), sanitize(df_oi)
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum() if not df_g.empty else 0
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), bf, ahorro_p

# --- 3. REPORTE PDF DETALLADO ---
def generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses, titulo, anio, u_id):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    buf = BytesIO(); c = canvas.Canvas(buf, pagesize=letter)
    def head(canvas_obj, t, a):
        canvas_obj.setFillColor(colors.white); canvas_obj.rect(0, 0, 612, 792, fill=1)
        canvas_obj.setFillColor(HexColor("#1a1d21")); canvas_obj.setFont("Helvetica-Bold", 16); canvas_obj.drawString(50, 765, "My FinanceApp")
        canvas_obj.setFont("Helvetica", 10); canvas_obj.drawString(50, 750, "by Stulio Designs")
        canvas_obj.setFont("Helvetica-Bold", 12); canvas_obj.drawRightString(560, 760, f"{t} - {a}")
        canvas_obj.setStrokeColor(HexColor("#d4af37")); canvas_obj.line(50, 740, 560, 740)
        canvas_obj.setFont("Helvetica-Oblique", 8); canvas_obj.setFillColor(colors.grey)
        fecha_gen = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        canvas_obj.drawString(50, 30, f"Documento generado el: {fecha_gen}"); return 710
    y = head(c, titulo, anio)
    for m in meses:
        i_m = df_i_full[(df_i_full["Periodo"] == m) & (df_i_full["Año"] == anio) & (df_i_full["Usuario"] == u_id)]
        g_m = df_g_full[(df_g_full["Periodo"] == m) & (df_g_full["Año"] == anio) & (df_g_full["Usuario"] == u_id)]
        oi_m = df_oi_full[(df_oi_full["Periodo"] == m) & (df_oi_full["Año"] == anio) & (df_oi_full["Usuario"] == u_id)]
        s_ant = i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0
        nom = i_m["Nomina"].iloc[0] if not i_m.empty else 0
        otr_sum = oi_m["Monto"].sum() if not oi_m.empty else 0
        it, vp, vpy, _, bf, _ = calcular_metricas(g_m, nom, otr_sum, s_ant)
        if y < 250: c.showPage(); y = head(c, titulo, anio)
        c.setFillColor(HexColor("#f8f9fa")); c.rect(50, y-55, 510, 60, fill=1, stroke=0)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(60, y-15, f"MES: {m}")
        c.setFont("Helvetica", 9); c.drawString(60, y-30, f"Ingresos: $ {it:,.0f} | Pagado: $ {vp:,.0f} | Pendiente: $ {vpy:,.0f}")
        c.setFillColor(HexColor("#d4af37")); c.drawString(60, y-45, f"AHORRO FINAL: $ {bf:,.0f}"); y -= 80
        c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "RELACIÓN DE INGRESOS"); y -= 15
        c.setFont("Helvetica", 8); c.drawString(60, y, f"Saldo Ant: $ {s_ant:,.0f} | Nómina: $ {nom:,.0f} | Extras: $ {otr_sum:,.0f}"); y -= 30
        c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "RELACIÓN DE GASTOS"); y -= 15
        for _, row in g_m.iterrows():
            if y < 60: c.showPage(); y = head(c, titulo, anio); c.setFont("Helvetica", 8)
            c.drawString(60, y, f"{row['Categoría']} - {row['Descripción']}"[:65]); c.drawRightString(480, y, f"{row['Monto']:,.0f}"); c.drawRightString(540, y, "SI" if row["Pagado"] else "NO"); y -= 12
        y -= 20
    c.showPage(); c.save(); buf.seek(0); return buf

# --- 4. CARGA Y SIDEBAR ---
u_id = "tulicesar" # Hardcoded para el ejemplo
df_g_full, df_i_full, df_oi_full = cargar_bd()

with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_s = st.selectbox("Mes Actual", meses_lista, index=datetime.now().month-1)
    
    idx = meses_lista.index(mes_s); m_ant = meses_lista[idx-1] if idx>0 else "Diciembre"; a_ant = anio_s if idx>0 else anio_s-1
    i_m_act = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s) & (df_i_full["Usuario"]==u_id)]
    
    s_in = st.number_input("Saldo Anterior", value=float(i_m_act["SaldoAnterior"].iloc[0] if not i_m_act.empty else 0.0))
    n_in = st.number_input("Nómina/Sueldo", value=float(i_m_act["Nomina"].iloc[0] if not i_m_act.empty else 0.0))
    placeholder_otros = st.empty()

    st.divider(); st.subheader("📑 Reportes")
    c_pdf, c_xls = st.columns(2)
    with c_pdf:
        if st.button("📄 PDF"):
            pdf = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, [mes_s], f"Extracto {mes_s}", anio_s, u_id)
            st.download_button(f"Bajar PDF", pdf, f"Extracto_{mes_s}.pdf")
    with c_xls:
        buf_xls = BytesIO()
        with pd.ExcelWriter(buf_xls, engine='xlsxwriter') as writer:
            df_g_full[(df_g_full["Periodo"]==mes_s)&(df_g_full["Usuario"]==u_id)].to_excel(writer, sheet_name='Gastos', index=False)
            df_oi_full[(df_oi_full["Periodo"]==mes_s)&(df_oi_full["Usuario"]==u_id)].to_excel(writer, sheet_name='OtrosIngresos', index=False)
        st.download_button("📊 Excel", buf_xls.getvalue(), f"Reporte_{mes_s}.xlsx")

    st.subheader("⚖️ Balances Proyectados")
    if st.button("📥 Semestre 1 (Ene-Jun)"):
        pdf1 = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses_lista[0:6], "Proyección S1", anio_s, u_id)
        st.download_button("Bajar S1.pdf", pdf1, "S1_Proyectado.pdf")

# --- 5. CUERPO PRINCIPAL ---
if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s} {anio_s}")

config_moneda = st.column_config.NumberColumn("Monto", format="$ %d")
df_mes_g = df_g_full[(df_g_full["Periodo"] == mes_s) & (df_g_full["Año"] == anio_s) & (df_g_full["Usuario"] == u_id)].copy()
df_ed_g = st.data_editor(df_mes_g.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", column_config={"Monto": config_moneda, "Valor Referencia": config_moneda}, key="g_ed")

df_mes_oi = df_oi_full[(df_oi_full["Periodo"] == mes_s) & (df_oi_full["Año"] == anio_s) & (df_oi_full["Usuario"] == u_id)].copy()
df_ed_oi = st.data_editor(df_mes_oi.reindex(columns=["Descripción", "Monto"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", column_config={"Monto": config_moneda}, key="oi_ed")

# CÁLCULOS
df_ed_g["Monto"] = pd.to_numeric(df_ed_g["Monto"], errors="coerce").fillna(0)
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0)
otr_vivos = float(df_ed_oi["Monto"].sum())
placeholder_otros.text_input("Otros Ingresos (Total)", value=f"$ {otr_vivos:,.0f}", disabled=True)

it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_vivos, s_in)

st.divider()
c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(f'<div class="card"><div class="card-label">INGRESOS</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card"><div class="card-label">PAGADO</div><div class="card-value" style="color:green;">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="card"><div class="card-label">PENDIENTE</div><div class="card-value" style="color:red;">$ {vpy:,.0f}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="card"><div class="card-label">FONDOS ACTUALES</div><div class="card-value" style="color:blue;">$ {fact:,.0f}</div></div>', unsafe_allow_html=True)
c5.markdown(f'<div class="card"><div class="card-label">AHORRO PROYECTADO</div><div class="card-value" style="color:#d4af37;">$ {bf:,.0f}</div></div>', unsafe_allow_html=True)

# --- 6. INFOGRAFÍAS (RESTAURADAS) ---
st.markdown("### 📊 Análisis de Distribución")
inf1, inf2, inf3 = st.columns([1.2, 1, 1.2])

with inf1:
    st.markdown("#### Desglose de Gastos")
    t_df = df_ed_g.copy(); t_df['V'] = t_df.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not t_df.empty and t_df['V'].sum() > 0:
        fig1 = px.pie(t_df, values='V', names='Categoría', hole=0.7, color='Categoría', color_discrete_map=COLOR_MAP)
        fig1.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig1, use_container_width=True)
        res = t_df.groupby("Categoría")['V'].sum().reset_index()
        for _, r in res.iterrows():
            st.markdown(f'<div class="legend-bar" style="background:{COLOR_MAP.get(r["Categoría"],"#eee")}">{r["Categoría"]} <span>$ {r["V"]:,.0f}</span></div>', unsafe_allow_html=True)

with inf2:
    st.markdown("#### Eficiencia de Ahorro")
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number", value=ahorro_p,
        number={'suffix': "%", 'font': {'color': '#d4af37', 'size': 50}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#d4af37", 'thickness': 0.25},
            'bgcolor': "white",
            'borderwidth': 2, 'bordercolor': "#e0e0e0",
            'steps': [{'range': [0, 100], 'color': '#f0f0f0'}]
        }
    ))
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(t=40,b=0,l=20,r=20))
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("<p style='text-align:center; font-weight:bold; color:#d4af37;'>Ahorro Proyectado</p>", unsafe_allow_html=True)

with inf3:
    st.markdown("#### Estado Real del Dinero")
    fig3 = go.Figure(data=[go.Pie(labels=['Pagado', 'Pendiente', 'Ahorro'], values=[vp, vpy, bf], hole=.7, marker_colors=['#2ecc71', '#e74c3c', '#d4af37'])])
    fig3.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(t=0,b=0,l=0,r=0))
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown(f"""
        <div style='font-size:0.9rem; font-weight:bold;'>
        <span style='color:#2ecc71;'>● Pagado: $ {vp:,.0f}</span><br>
        <span style='color:#e74c3c;'>● Pendiente: $ {vpy:,.0f}</span><br>
        <span style='color:#d4af37;'>● Ahorro: $ {bf:,.0f}</span>
        </div>
    """, unsafe_allow_html=True)

if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    # (Lógica de guardado...)
    st.balloons(); st.rerun()
