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

# Nombres de archivos en GitHub
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
    button[kind="headerNoSpacing"] { display: flex !important; visibility: visible !important; color: #d4af37 !important; }
    header { background-color: rgba(0,0,0,0) !important; }
    [data-testid="stHeader"] { background: none !important; }
    .stApp { background: #0e1117; color: #dee2e6; }
    
    /* TABLA EXPANDIDA Y CÓMODA */
    [data-testid="stDataEditor"] div { font-size: 1.2rem !important; }
    
    .card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #1a1d21; text-align: center; border-bottom: 4px solid #d4af37;
    }
    .card-label { font-size: 0.8rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #1a1d21; margin: 3px 0; }
    
    .legend-bar {
        padding: 12px 20px; border-radius: 8px; margin-bottom: 8px; 
        font-size: 1.1rem; font-weight: bold; color: #1a1d21; 
        display: flex; justify-content: space-between; align-items: center;
        max-width: 95%; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    
    section[data-testid="stSidebar"] { background: rgba(0,0,0,0.8) !important; backdrop-filter: blur(15px); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #d4af37; color: black; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
def cargar_usuarios():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            try: return json.load(f)
            except: return {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}
    db = {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}; guardar_usuarios(db); return db

def guardar_usuarios(db):
    with open(USER_DB, "w") as f: json.dump(db, f, indent=4)

def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    if not os.path.exists(BASE_FILE): return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        for col in ["Monto", "Valor Referencia"]: df_g[col] = pd.to_numeric(df_g[col], errors='coerce').fillna(0.0)
        df_g["Pagado"] = df_g["Pagado"].fillna(False).astype(bool)
        df_g["Movimiento Recurrente"] = df_g["Movimiento Recurrente"].fillna(False).astype(bool)
        return df_g, df_i
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    if df_g.empty: return it, 0.0, 0.0, it, it, 0.0
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum()
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum()
    fondos_act = it - vp
    saldo_fin = it - vp - vpy
    ahorro_p = (saldo_fin / it * 100) if it > 0 else 0
    return it, vp, vpy, fondos_act, saldo_fin, ahorro_p

# --- 3. MÓDULO DE REPORTES (RESTAURADO) ---
def generar_pdf_reporte(df_g_full, df_i_full, meses, titulo, anio):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    def head(canvas_obj, t, a):
        canvas_obj.setFillColor(colors.white); canvas_obj.rect(0, 0, 612, 792, fill=1)
        canvas_obj.setFillColor(HexColor("#1a1d21"))
        canvas_obj.setFont("Helvetica-Bold", 18); canvas_obj.drawString(50, 750, "MY FINANCE")
        canvas_obj.setFont("Helvetica-Bold", 12); canvas_obj.drawRightString(560, 750, f"{t} - {a}")
        canvas_obj.setStrokeColor(HexColor("#d4af37")); canvas_obj.line(50, 740, 560, 740)
        return 710
    y = head(c, titulo, anio)
    for m in meses:
        i_m = df_i_full[(df_i_full["Periodo"] == m) & (df_i_full["Año"] == anio) & (df_i_full["Usuario"] == st.session_state.usuario_id)]
        g_m = df_g_full[(df_g_full["Periodo"] == m) & (df_g_full["Año"] == anio) & (df_g_full["Usuario"] == st.session_state.usuario_id)]
        s_ant_m = i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0.0
        it_m, vp_m, vpy_m, _, bf_m, _ = calcular_metricas(g_m, i_m["Nomina"].sum() if not i_m.empty else 0, i_m["Otros"].sum() if not i_m.empty else 0, s_ant_m)
        if y < 220: c.showPage(); y = head(c, titulo, anio)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(70, y-20, f"MES: {m}")
        c.setFont("Helvetica", 9); c.drawString(70, y-40, f"Ingresos: $ {it_m:,.0f} | Pagado: $ {vp_m:,.0f} | Saldo: $ {bf_m:,.0f}")
        y -= 80
    c.showPage(); c.save(); buf.seek(0)
    return buf

# --- 4. ACCESO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN): st.image(LOGO_LOGIN, use_container_width=True)
        usuarios = cargar_usuarios()
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión", use_container_width=True):
            if u_in in usuarios and usuarios[u_in]["pass"] == p_in:
                st.session_state.autenticado, st.session_state.usuario_id = True, u_in
                st.session_state.u_nombre_completo = usuarios[u_in].get("nombre", u_in)
                st.rerun()
    st.stop()

# --- 5. DASHBOARD ---
df_g_raw, df_i_raw = cargar_bd()
df_g_user = df_g_raw[df_g_raw["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == st.session_state.usuario_id].copy()
periodos_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    mes_s = st.selectbox("Mes Actual", periodos_list, index=datetime.now().month-1)
    
    idx = periodos_list.index(mes_s); mes_ant = periodos_list[idx-1] if idx>0 else periodos_list[11]; anio_ant = anio_s if idx>0 else anio_s-1
    i_pas = df_i_user[(df_i_user["Periodo"]==mes_ant) & (df_i_user["Año"]==anio_ant)]
    g_pas = df_g_user[(df_g_user["Periodo"]==mes_ant) & (df_g_user["Año"]==anio_ant)]
    saldo_auto = 0.0
    if not i_pas.empty:
        *_, bf_p, _ = calcular_metricas(g_pas, i_pas["Nomina"].sum(), i_pas["Otros"].sum(), i_pas["SaldoAnterior"].iloc[0])
        saldo_auto = float(bf_p)

    st.divider()
    s_in = st.number_input("Saldo Anterior", value=saldo_auto)
    n_in = st.number_input("Nómina", value=float(df_i_user[(df_i_user["Periodo"]==mes_s)]["Nomina"].iloc[0] if not df_i_user[df_i_user["Periodo"]==mes_s].empty else 0.0))
    o_in = st.number_input("Otros", value=float(df_i_user[(df_i_user["Periodo"]==mes_s)]["Otros"].iloc[0] if not df_i_user[df_i_user["Periodo"]==mes_s].empty else 0.0))

    # --- REPORTE Y BALANCES (RECUPERADOS) ---
    st.divider()
    st.subheader("📑 Extractos del Mes")
    if st.button(f"📄 PDF {mes_s[:3]}"):
        pdf = generar_pdf_reporte(df_g_user, df_i_user, [mes_s], "Extracto", anio_s)
        st.download_button("Descargar PDF", pdf, f"Extracto_{mes_s}.pdf")
    
    st.divider()
    st.subheader("📈 Balances Semestrales")
    if st.button("📥 Semestre 1 (Ene-Jun)"):
        pdf1 = generar_pdf_reporte(df_g_user, df_i_user, periodos_list[0:6], "S1", anio_s)
        st.download_button("S1.pdf", pdf1, "Balance_S1.pdf")
    if st.button("📥 Semestre 2 (Jul-Dic)"):
        pdf2 = generar_pdf_reporte(df_g_user, df_i_user, periodos_list[6:12], "S2", anio_s)
        st.download_button("S2.pdf", pdf2, "Balance_S2.pdf")
    
    st.divider()
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 6. CABECERA (LOGO GIGANTE) ---
if os.path.exists(LOGO_APP_H): 
    st.image(LOGO_APP_H, use_container_width=True)

st.markdown(f"<h1 style='text-align: center; margin-top: -10px;'>{mes_s} {anio_s}</h1>", unsafe_allow_html=True)

# --- REGISTRO DE MOVIMIENTOS ---
st.markdown("### 📝 Registro de Movimientos")
df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()
if df_mes.empty:
    df_rec = df_g_user[(df_g_user["Periodo"] == mes_ant) & (df_g_user["Año"] == anio_ant) & (df_g_user["Movimiento Recurrente"] == True)]
    if not df_rec.empty: df_mes = df_rec.copy().assign(Pagado=False, Monto=0)

# MOSTRAR SOLO COLUMNAS REALES (Total_Cat ELIMINADA AQUÍ)
cols_a_mostrar = ["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"]
df_v = df_mes.reindex(columns=cols_a_mostrar).reset_index(drop=True)

df_ed = st.data_editor(df_v, use_container_width=True, num_rows="dynamic", key=f"ed_{mes_s}")

# MÉTRICAS
it, vp, vpy, fondos_act, saldo_fin, ahorro_p = calcular_metricas(df_ed, n_in, o_in, s_in)
st.markdown("---")
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="card"><div class="card-label">INGRESOS</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card"><div class="card-label">PAGADO</div><div class="card-value" style="color:#2ecc71;">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="card"><div class="card-label">PENDIENTE</div><div class="card-value" style="color:#e74c3c;">$ {vpy:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="card"><div class="card-label">FONDOS ACTUALES</div><div class="card-value" style="color:#2575fc;">$ {fondos_act:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="card"><div class="card-label">AHORRO FINAL</div><div class="card-value" style="color:#d4af37;">$ {saldo_fin:,.0f}</div></div>', unsafe_allow_html=True)

# --- 🚀 INFOGRAFIAS ---
st.markdown("### 📊 Análisis de Gastos")
c1, c2, c3 = st.columns([1.5, 1, 1.2])

with c1:
    st.markdown("**Desglose Presupuestado**")
    temp_calc = df_ed.copy()
    temp_calc['V'] = temp_calc.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not temp_calc.empty and temp_calc['V'].sum() > 0:
        fig = px.pie(temp_calc, values='V', names='Categoría', hole=0.6, color_discrete_map=COLOR_MAP)
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
        res = temp_calc.groupby("Categoría")['V'].sum().reset_index()
        for _, r in res.iterrows():
            st.markdown(f'<div class="legend-bar" style="background:{COLOR_MAP.get(r["Categoría"], "#eee")}">{r["Categoría"]} <span>$ {r["V"]:,.0f}</span></div>', unsafe_allow_html=True)

with c2:
    st.markdown("**Eficiencia de Ahorro**")
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=ahorro_p, number={'suffix': "%", 'font':{'color':'#d4af37'}}, gauge={'axis':{'range':[0,100]},'bar':{'color':"white"},'bgcolor':"#1f2630",'steps':[{'range':[0,20],'color':'#ff4b4b'},{'range':[20,50],'color':'#ffa500'},{'range':[50,100],'color':'#00d26a'}],'threshold':{'line':{'color':"#d4af37",'width':6},'thickness':0.85,'value':ahorro_p}}))
    gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=50,b=0,l=0,r=0))
    st.plotly_chart(gauge, use_container_width=True)

with c3:
    st.markdown("**Estado Real**")
    pie = go.Figure(data=[go.Pie(labels=['Pagado', 'Pendiente', 'Ahorro'], values=[vp, vpy, saldo_fin], hole=.65, marker_colors=['#2ecc71', '#e74c3c', '#d4af37'], textinfo='percent+label')])
    pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=380, margin=dict(t=0,b=0,l=0,r=0))
    st.plotly_chart(pie, use_container_width=True)

if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    df_n = df_ed.assign(Periodo=mes_s, Año=anio_s, Usuario=st.session_state.usuario_id)
    mask_g = (df_g_raw["Periodo"] == mes_s) & (df_g_raw["Año"] == anio_s) & (df_g_raw["Usuario"] == st.session_state.usuario_id)
    df_gf = pd.concat([df_g_raw[~mask_g], df_n], ignore_index=True)
    df_i_nuevo = pd.DataFrame([{"Año":anio_s, "Periodo":mes_s, "SaldoAnterior":s_in, "Nomina":n_in, "Otros":o_in, "Usuario":st.session_state.usuario_id}])
    mask_i = (df_i_raw["Periodo"] == mes_s) & (df_i_raw["Año"] == anio_s) & (df_i_raw["Usuario"] == st.session_state.usuario_id)
    df_if = pd.concat([df_i_raw[~mask_i], df_i_nuevo], ignore_index=True)
    with pd.ExcelWriter(BASE_FILE) as w:
        df_gf.to_excel(w, sheet_name="Gastos", index=False); df_if.to_excel(w, sheet_name="Ingresos", index=False)
    st.balloons(); st.rerun()
