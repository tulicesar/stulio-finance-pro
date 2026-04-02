import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from io import BytesIO
from datetime import datetime
import math
import pytz 

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
    
    /* --- TABLAS XL PARA CELULAR --- */
    [data-testid="stDataEditor"] div {
        font-size: 2.0rem !important; 
    }

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
    h2, h3 { color: #d4af37 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
def cargar_usuarios():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            try: return json.load(f)
            except: pass
    return {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}

def guardar_usuarios(db):
    with open(USER_DB, "w") as f: json.dump(db, f, indent=4)

def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    col_oi = ["Año", "Periodo", "Descripción", "Monto", "Usuario"]
    if not os.path.exists(BASE_FILE): return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        df_oi = pd.read_excel(BASE_FILE, sheet_name="OtrosIngresos")
        return df_g, df_i, df_oi
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum() if not df_g.empty else 0
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), bf, ahorro_p

# --- 3. REPORTE PDF ---
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
        
        # HORA COLOMBIA Y TEXTO PEQUEÑO
        try:
            tz_local = pytz.timezone('America/Bogota') 
            fecha_gen = datetime.now(tz_local).strftime("%d/%m/%Y %H:%M:%S")
        except:
            fecha_gen = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        canvas_obj.setFont("Helvetica-Oblique", 6)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(50, 30, f"Documento generado el: {fecha_gen}")
        return 710

    y = head(c, titulo, anio)
    for m in meses:
        # Lógica de datos por mes
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
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "RELACIÓN DE INGRESOS"); y -= 15
        c.setFont("Helvetica", 8); c.drawString(60, y, f"Saldo Ant: $ {s_ant:,.0f} | Nómina: $ {nom:,.0f} | Extras: $ {otr_sum:,.0f}"); y -= 30
        c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "RELACIÓN DE GASTOS"); y -= 15
        for _, row in g_m.iterrows():
            if y < 60: c.showPage(); y = head(c, titulo, anio); c.setFont("Helvetica", 8)
            c.drawString(60, y, f"{row['Categoría']} - {row['Descripción']}"[:65]); c.drawRightString(480, y, f"{row['Monto']:,.0f}"); c.drawRightString(540, y, "SI" if row["Pagado"] else "NO"); y -= 12
        y -= 20
    c.showPage(); c.save(); buf.seek(0); return buf

# --- 4. ACCESO (REGISTRO RESTAURADO) ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN): st.image(LOGO_LOGIN, use_container_width=True)
        tab_in, tab_reg = st.tabs(["🔑 Iniciar Sesión", "📝 Registro"])
        db_u = cargar_usuarios()
        with tab_in:
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.button("Ingresar", use_container_width=True):
                if u in db_u and db_u[u]["pass"] == p:
                    st.session_state.autenticado, st.session_state.usuario_id, st.session_state.u_nombre_completo = True, u, db_u[u].get("nombre", u)
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
        with tab_reg:
            rn = st.text_input("Nombre Completo"); ru = st.text_input("ID de Usuario"); rp = st.text_input("Contraseña de Registro", type="password")
            if st.button("Crear Cuenta"):
                if ru in db_u: st.error("Este usuario ya existe.")
                else:
                    db_u[ru] = {"pass": rp, "nombre": rn}; guardar_usuarios(db_u)
                    st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
    st.stop()

# --- 5. LÓGICA APP ---
u_id = st.session_state.usuario_id
df_g_full, df_i_full, df_oi_full = cargar_bd()

with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_s = st.selectbox("Mes Actual", meses_lista, index=datetime.now().month-1)
    
    # Arrastre
    idx = meses_lista.index(mes_s)
    m_ant = meses_lista[idx-1] if idx > 0 else "Diciembre"
    a_ant = anio_s if idx > 0 else anio_s-1
    i_ant_row = df_i_full[(df_i_full["Periodo"] == m_ant) & (df_i_full["Año"] == a_ant) & (df_i_full["Usuario"] == u_id)]
    g_ant_df = df_g_full[(df_g_full["Periodo"] == m_ant) & (df_g_full["Año"] == a_ant) & (df_g_full["Usuario"] == u_id)]
    oi_ant_df = df_oi_full[(df_oi_full["Periodo"] == m_ant) & (df_oi_full["Año"] == a_ant) & (df_oi_full["Usuario"] == u_id)]
    
    s_sug = 0.0
    if not i_ant_row.empty:
        _, _, _, _, bf_ant, _ = calcular_metricas(g_ant_df, i_ant_row["Nomina"].sum(), oi_ant_df["Monto"].sum(), i_ant_row["SaldoAnterior"].iloc[0])
        s_sug = float(bf_ant)

    st.divider()
    arr_on = st.toggle(f"Arrastrar saldo de {m_ant}", value=not i_ant_row.empty)
    i_m_act = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s) & (df_i_full["Usuario"]==u_id)]
    s_in = st.number_input("Saldo Anterior", value=s_sug if arr_on else float(i_m_act["SaldoAnterior"].iloc[0] if not i_m_act.empty else 0.0))
    n_in = st.number_input("Ingresos Fijos (Sueldo)", value=float(i_m_act["Nomina"].iloc[0] if not i_m_act.empty else 0.0))

    st.divider(); st.subheader("📑 Extracto")
    c_pdf, c_xls = st.columns(2)
    with c_pdf:
        if st.button("📄 PDF"):
            pdf = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, [mes_s], f"Extracto {mes_s}", anio_s, u_id)
            st.download_button(f"Descargar PDF", pdf, f"Extracto_{mes_s}.pdf")
    with c_xls:
        buf_xls = BytesIO()
        with pd.ExcelWriter(buf_xls, engine='xlsxwriter') as writer:
            df_g_full[(df_g_full["Periodo"]==mes_s)&(df_g_full["Usuario"]==u_id)].to_excel(writer, sheet_name='Gastos', index=False)
            df_oi_full[(df_oi_full["Periodo"]==mes_s)&(df_oi_full["Usuario"]==u_id)].to_excel(writer, sheet_name='OtrosIngresos', index=False)
        st.download_button("📊 Excel", buf_xls.getvalue(), f"Reporte_{mes_s}.xlsx")
    
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 6. CUERPO ---
if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s} {anio_s}")

st.markdown("### 📝 Movimiento de Gastos")
df_mes_g = df_g_full[(df_g_full["Periodo"] == mes_s) & (df_g_full["Año"] == anio_s) & (df_g_full["Usuario"] == u_id)].copy()
df_ed_g = st.data_editor(df_mes_g.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", key="g_ed")

st.markdown("### 💰 Otros Ingresos")
df_mes_oi = df_oi_full[(df_oi_full["Periodo"] == mes_s) & (df_oi_full["Año"] == anio_s) & (df_oi_full["Usuario"] == u_id)].copy()
df_ed_oi = st.data_editor(df_mes_oi.reindex(columns=["Descripción", "Monto"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", key="oi_ed")

# Cálculos e Infografías
df_ed_g["Monto"] = pd.to_numeric(df_ed_g["Monto"], errors="coerce").fillna(0)
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0)
otr_vivos = float(df_ed_oi["Monto"].sum())
it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_vivos, s_in)

st.divider()
c1, c2, c3, c4, c5 = st.columns(5)
tarjetas = [("INGRESOS", it, "black"), ("PAGADO", vp, "green"), ("PENDIENTE", vpy, "red"), ("FONDOS", fact, "blue"), ("AHORRO", bf, "#d4af37")]
for i, (l, v, c) in enumerate(tarjetas):
    st.columns(5)[i].markdown(f'<div class="card"><div class="card-label">{l}</div><div class="card-value" style="color:{c}">$ {v:,.0f}</div></div>', unsafe_allow_html=True)

# Velocímetro
inf1, inf2, inf3 = st.columns([1.2, 1, 1.2])
with inf2:
    st.markdown("#### Eficiencia de Ahorro")
    val_cl = max(0, min(ahorro_p, 100))
    phi = math.radians(180 - (val_cl / 100 * 180))
    x_p, y_p = 0.5, 0.42
    x_t, y_t = x_p + 0.32 * math.cos(phi), y_p + 0.32 * math.sin(phi)
    fig2 = go.Figure()
    fig2.add_trace(go.Indicator(mode="gauge", value=val_cl, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "rgba(0,0,0,0)"}, 'bgcolor': "white", 'steps': [{'range': [0, 100], 'color': '#f8f9fa'}]}))
    fig2.add_annotation(text=f"{val_cl:.0f}%", x=x_p, y=y_p-0.05, showarrow=False, font=dict(color="#d4af37", size=55, weight="bold"))
    fig2.add_shape(type="line", x0=x_p, y0=y_p, x1=x_t, y1=y_t, line=dict(color="#d4af37", width=5))
    fig2.add_shape(type="circle", x0=x_p-0.02, y0=y_p-0.02, x1=x_p+0.02, y1=y_p+0.02, fillcolor="#d4af37", line_color="#d4af37")
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=50,b=20,l=25,r=25))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS", use_container_width=True):
    df_g_final = pd.concat([df_g_full[~((df_g_full["Periodo"]==mes_s)&(df_g_full["Año"]==anio_s)&(df_g_full["Usuario"]==u_id))], df_ed_g.assign(Periodo=mes_s, Año=anio_s, Usuario=u_id)], ignore_index=True)
    df_oi_final = pd.concat([df_oi_full[~((df_oi_full["Periodo"]==mes_s)&(df_oi_full["Año"]==anio_s)&(df_oi_full["Usuario"]==u_id))], df_ed_oi.assign(Periodo=mes_s, Año=anio_s, Usuario=u_id)], ignore_index=True)
    df_i_final = pd.concat([df_i_full[~((df_i_full["Periodo"]==mes_s)&(df_i_full["Año"]==anio_s)&(df_i_full["Usuario"]==u_id))], pd.DataFrame([{"Año":anio_s, "Periodo":mes_s, "SaldoAnterior":s_in, "Nomina":n_in, "Otros":otr_vivos, "Usuario":u_id}])], ignore_index=True)
    with pd.ExcelWriter(BASE_FILE) as w:
        df_g_final.to_excel(w, sheet_name="Gastos", index=False); df_i_final.to_excel(w, sheet_name="Ingresos", index=False); df_oi_final.to_excel(w, sheet_name="OtrosIngresos", index=False)
    st.balloons(); st.rerun()
