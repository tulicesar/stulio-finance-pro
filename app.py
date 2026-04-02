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

# Archivos de imagen y rutas
LOGO_LOGIN = "logoapp 1.png"
LOGO_APP_V = "LOGO APP.png"      
LOGO_APP_H = "LOGO H APP.png"    
BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"

# Paleta de Colores Stulio Designs
COLOR_MAP = {
    "Hogar": "#FFB347", "Servicios": "#FFB347", "Salud": "#B39EB5", 
    "Transporte": "#77B5FE", "Obligaciones": "#FF6961", "Alimentación": "#FDFD96", 
    "Otros": "#77DD77", "Impuestos": "#84b6f4"
}

# CSS: Diseño Dark, Eliminación de Header y Tarjetas Premium
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .stApp { background: #0e1117; color: #dee2e6; }
    .card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #1a1d21; text-align: center; border-bottom: 4px solid #d4af37;
    }
    .card-label { font-size: 0.8rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #1a1d21; margin: 3px 0; }
    .legend-bar {
        padding: 10px 15px; border-radius: 8px; margin-bottom: 6px; 
        font-size: 1rem; font-weight: bold; color: #1a1d21; 
        display: flex; justify-content: space-between; align-items: center;
        max-width: 85%; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    section[data-testid="stSidebar"] { background: rgba(0,0,0,0.8) !important; backdrop-filter: blur(15px); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #d4af37; color: black; border: none; }
    .login-box { max-width: 450px; margin: auto; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 15px; border: 1px solid #d4af37; }
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

# --- 3. MÓDULO DE REPORTES ---
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
        c.setStrokeColor(colors.lightgrey); c.setFillColor(HexColor("#f8f8f8"))
        c.roundRect(50, y-80, 510, 85, 10, fill=1, stroke=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(70, y-20, f"MES: {m}")
        c.setFont("Helvetica", 9); c.drawString(70, y-40, f"Ingresos: $ {it_m:,.0f} | Pagados: $ {vp_m:,.0f} | Pendientes: $ {vpy_m:,.0f}")
        c.setFillColor(HexColor("#d4af37")); c.drawString(70, y-65, f"SALDO FINAL (AHORRO): $ {bf_m:,.0f}")
        y -= 100
        if not g_m.empty:
            c.setFont("Helvetica-Bold", 8); c.setFillColor(HexColor("#1a1d21"))
            c.drawString(60, y, "Categoría"); c.drawString(160, y, "Descripción"); c.drawRightString(480, y, "Monto"); c.drawRightString(540, y, "Pagado")
            y -= 12; c.setFont("Helvetica", 8); c.setFillColor(colors.black)
            for _, r in g_m.iterrows():
                if y < 50: c.showPage(); y = head(c, titulo, anio); c.setFont("Helvetica", 8)
                c.drawString(60, y, str(r['Categoría'])); c.drawString(160, y, str(r['Descripción'])[:40])
                c.drawRightString(480, y, f"{r['Monto']:,.0f}"); c.drawRightString(540, y, "SÍ" if r['Pagado'] else "NO")
                y -= 12
            y -= 20
    c.showPage(); c.save(); buf.seek(0)
    return buf

# --- 4. ACCESO (LOGIN CON LOGOAPP 1.PNG) ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        if os.path.exists(LOGO_LOGIN):
            st.image(LOGO_LOGIN, use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center; color: #d4af37;'>My Finance</h1>", unsafe_allow_html=True)
        
        tab_log, tab_reg = st.tabs(["🔑 Entrar", "📝 Registro"])
        usuarios = cargar_usuarios()
        with tab_log:
            u_in = st.text_input("Usuario", key="l_u").strip()
            p_in = st.text_input("Contraseña", type="password", key="l_p").strip()
            if st.button("Iniciar Sesión", use_container_width=True):
                if u_in in usuarios and usuarios[u_in]["pass"] == p_in:
                    st.session_state.autenticado, st.session_state.usuario_id = True, u_in
                    st.session_state.u_nombre_completo = usuarios[u_in].get("nombre", u_in)
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
        with tab_reg:
            rn_full = st.text_input("Nombre Completo")
            rn_user = st.text_input("Nuevo Usuario")
            rn_pass = st.text_input("Nueva Contraseña", type="password")
            if st.button("Crear Cuenta", use_container_width=True):
                if rn_user and rn_pass:
                    usuarios[rn_user] = {"pass": rn_pass, "nombre": rn_full}
                    guardar_usuarios(usuarios); st.success("✅ Cuenta creada.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. DASHBOARD ---
df_g_raw, df_i_raw = cargar_bd()
df_g_user = df_g_raw[df_g_raw["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == st.session_state.usuario_id].copy()
periodos_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    if os.path.exists(LOGO_APP_V): st.image(LOGO_APP_V, width=150)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    mes_s = st.selectbox("Mes Actual", periodos_list, index=datetime.now().month-1)
    
    idx = periodos_list.index(mes_s)
    mes_ant = periodos_list[idx - 1] if idx > 0 else periodos_list[11]
    anio_ant = anio_s if idx > 0 else anio_s - 1
    
    i_prev = df_i_user[(df_i_user["Periodo"] == mes_ant) & (df_i_user["Año"] == anio_ant)]
    g_prev = df_g_user[(df_g_user["Periodo"] == mes_ant) & (df_g_user["Año"] == anio_ant)]
    saldo_auto = 0.0
    if not i_prev.empty:
        *_, bf_pasado, _ = calcular_metricas(g_prev, i_prev["Nomina"].sum(), i_prev["Otros"].sum(), i_prev["SaldoAnterior"].iloc[0])
        saldo_auto = float(bf_pasado)

    st.divider()
    arrastrar = st.toggle(f"Traer saldo de {mes_ant}", value=not i_prev.empty)
    d_act_i = df_i_user[(df_i_user["Periodo"] == mes_s) & (df_i_user["Año"] == anio_s)]
    s_in = st.number_input("Saldo Anterior", value=saldo_auto if arrastrar else (float(d_act_i["SaldoAnterior"].iloc[0]) if not d_act_i.empty else 0.0))
    n_in = st.number_input("Nómina", value=float(d_act_i["Nomina"].iloc[0] if not d_act_i.empty else 0.0))
    o_in = st.number_input("Otros", value=float(d_act_i["Otros"].iloc[0] if not d_act_i.empty else 0.0))

    st.divider()
    st.subheader("📑 Extractos del Mes")
    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        if st.button(f"📄 PDF {mes_s[:3]}"):
            pdf = generar_pdf_reporte(df_g_user, df_i_user, [mes_s], "Extracto Mensual", anio_s)
            st.download_button("Bajar PDF", pdf, f"Extracto_{mes_s}.pdf")
    with col_ex2:
        df_ex = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df_ex.to_excel(writer, index=False)
        st.download_button(f"📊 Excel {mes_s[:3]}", output.getvalue(), f"Excel_{mes_s}.xlsx")

    st.divider()
    st.subheader("📈 Balances Semestrales")
    if st.button("📥 Semestre 1 (Ene-Jun)"):
        pdf_s1 = generar_pdf_reporte(df_g_user, df_i_user, periodos_list[0:6], "Balance S1", anio_s)
        st.download_button("S1.pdf", pdf_s1, "Balance_S1.pdf")

    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 6. HEADER ---
c_logo_h, c_title = st.columns([1, 4])
with c_logo_h: 
    if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
with c_title: st.markdown(f"<h1>{mes_s} {anio_s} <span style='font-size:0.4em; color:#d4af37;'>| by Stulio Designs</span></h1>", unsafe_allow_html=True)

# Lógica de Datos y Recurrencia
df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()
if df_mes.empty:
    df_rec = df_g_user[(df_g_user["Periodo"] == mes_ant) & (df_g_user["Año"] == anio_ant) & (df_g_user["Movimiento Recurrente"] == True)]
    if not df_rec.empty: df_mes = df_rec.copy().assign(Pagado=False, Monto=0)

df_v = df_mes.reset_index(drop=True).drop(columns=["Año", "Periodo", "Usuario"], errors='ignore')
df_ed = st.data_editor(df_v, use_container_width=True, num_rows="dynamic", key=f"ed_{mes_s}", column_config={
    "Categoría": st.column_config.SelectboxColumn("Categoría", options=list(COLOR_MAP.keys()), required=True)
})

# MÉTRICAS (LAS 5 TARJETAS)
it, vp, vpy, fondos_act, saldo_fin, ahorro_p = calcular_metricas(df_ed, n_in, o_in, s_in)
st.markdown("---")
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="card"><div class="card-label">INGRESOS</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card"><div class="card-label">PAGADO</div><div class="card-value" style="color:#2ecc71;">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="card"><div class="card-label">PENDIENTE</div><div class="card-value" style="color:#e74c3c;">$ {vpy:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="card"><div class="card-label">FONDOS ACTUALES</div><div class="card-value" style="color:#2575fc;">$ {fondos_act:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="card"><div class="card-label">AHORRO FINAL</div><div class="card-value" style="color:#d4af37;">$ {saldo_fin:,.0f}</div></div>', unsafe_allow_html=True)

# --- 🚀 INFOGRAFIAS (VELOCÍMETRO CON AGUJA) ---
st.markdown("### 📊 Análisis de Gastos")
c_graf_dona, c_graf_ahorro, c_graf_status = st.columns([1.5, 1, 1.2])

with c_graf_dona:
    st.markdown("**Desglose Presupuestado (Monto + Pendiente)**")
    df_ed['Total_Cat'] = df_ed.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not df_ed.empty and df_ed["Total_Cat"].sum() > 0:
        fig_pie = px.pie(df_ed, values='Total_Cat', names='Categoría', hole=0.6, color='Categoría', color_discrete_map=COLOR_MAP)
        fig_pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
        df_sum = df_ed.groupby("Categoría")["Total_Cat"].sum().reset_index()
        for _, r in df_sum.iterrows():
            st.markdown(f'<div class="legend-bar" style="background:{COLOR_MAP.get(r["Categoría"], "#eee")}">{r["Categoría"]} <span>$ {r["Total_Cat"]:,.0f}</span></div>', unsafe_allow_html=True)

with c_graf_ahorro:
    st.markdown("**Eficiencia de Ahorro**")
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = ahorro_p,
        number = {'suffix': "%", 'font': {'color': '#d4af37'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickcolor': "white"},
            'bar': {'color': "white", 'thickness': 0.25},
            'bgcolor': "#1f2630",
            'steps': [
                {'range': [0, 20], 'color': '#ff4b4b'},
                {'range': [20, 50], 'color': '#ffa500'},
                {'range': [50, 100], 'color': '#00d26a'}
            ],
            'threshold': {
                'line': {'color': "#d4af37", 'width': 6},
                'thickness': 0.85, 'value': ahorro_p
            }
        }
    ))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig_gauge, use_container_width=True)

with c_graf_status:
    st.markdown("**Estado Real del Dinero**")
    labels_status = ['Pagado', 'Pendiente', 'Ahorro (Saldo)']
    values_status = [vp, vpy, saldo_fin]
    colors_status = ['#2ecc71', '#e74c3c', '#d4af37']
    fig_status = go.Figure(data=[go.Pie(labels=labels_status, values=values_status, hole=.65, marker_colors=colors_status, textinfo='percent+label')])
    fig_status.update_layout(showlegend=True, paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=380, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_status, use_container_width=True)

if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    df_n = df_ed.assign(Periodo=mes_s, Año=anio_s, Usuario=st.session_state.usuario_id)
    mask_g = (df_g_raw["Periodo"] == mes_s) & (df_g_raw["Año"] == anio_s) & (df_g_raw["Usuario"] == st.session_state.usuario_id)
    df_gf = pd.concat([df_g_raw[~mask_g], df_n], ignore_index=True)
    df_i_nuevo = pd.DataFrame({"Año":[anio_s], "Periodo":[mes_s], "SaldoAnterior":[s_in], "Nomina":[n_in], "Otros":[o_in], "Usuario":[st.session_state.usuario_id]})
    mask_i = (df_i_raw["Periodo"] == mes_s) & (df_i_raw["Año"] == anio_s) & (df_i_raw["Usuario"] == st.session_state.usuario_id)
    df_if = pd.concat([df_i_raw[~mask_i], df_i_nuevo], ignore_index=True)
    with pd.ExcelWriter(BASE_FILE) as w:
        df_gf.to_excel(w, sheet_name="Gastos", index=False); df_if.to_excel(w, sheet_name="Ingresos", index=False)
    st.balloons(); st.rerun()
