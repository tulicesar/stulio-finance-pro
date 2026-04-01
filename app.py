import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="My Finance by Stulio Designs", layout="wide", page_icon="💰")

LOGO_APP_V = "LOGO APP.png"      
LOGO_APP_H = "LOGO H APP.png"    
BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"

# CSS: Premium Dark & Gold + Ocultar Header (ELIMINA EL RENGLÓN GRIS)
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .stApp { background: #0e1117; color: #dee2e6; }
    .card {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        margin-bottom: 15px;
        color: #1a1d21;
        text-align: center;
        border-bottom: 5px solid #d4af37;
    }
    .card-label { font-size: 0.75rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 1.5rem; font-weight: 800; color: #1a1d21; margin: 5px 0; }
    section[data-testid="stSidebar"] { background: rgba(0,0,0,0.5) !important; backdrop-filter: blur(15px); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #d4af37; color: black; border: none; }
    .stButton>button:hover { background-color: #f1c40f; }
    .login-box { max-width: 450px; margin: auto; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 15px; border: 1px solid #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS Y USUARIOS ---
def cargar_usuarios():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            try: return json.load(f)
            except: return {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}
    db = {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}
    with open(USER_DB, "w") as f: json.dump(db, f, indent=4)
    return db

def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    if not os.path.exists(BASE_FILE):
        return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        if "Ítem" in df_g.columns: df_g = df_g.drop(columns=["Ítem"])
        for col in ["Monto", "Valor Referencia"]:
            df_g[col] = pd.to_numeric(df_g[col], errors='coerce').fillna(0.0)
        df_g["Pagado"] = df_g["Pagado"].fillna(False).astype(bool)
        df_g["Movimiento Recurrente"] = df_g["Movimiento Recurrente"].fillna(False).astype(bool)
        return df_g, df_i
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    if df_g.empty: return it, 0.0, 0.0, it, 0.0
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum()
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum()
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, bf, ahorro_p

# --- 3. MOTOR PDF DETALLADO ---
def generar_pdf_profesional(df_g_full, df_i_full, meses, titulo_reporte, anio):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    
    def header_pdf(canvas_obj, t, a):
        canvas_obj.setFillColor(colors.white); canvas_obj.rect(0, 0, 612, 792, fill=1)
        canvas_obj.setFillColor(HexColor("#1a1d21"))
        canvas_obj.setFont("Helvetica-Bold", 18); canvas_obj.drawString(50, 750, "MY FINANCE")
        canvas_obj.setFont("Helvetica-Bold", 12); canvas_obj.drawRightString(560, 750, f"{t} - {a}")
        canvas_obj.setStrokeColor(HexColor("#d4af37")); canvas_obj.setLineWidth(1.5); canvas_obj.line(50, 740, 560, 740)
        return 710

    y = header_pdf(c, titulo_reporte, anio)
    for m in meses:
        i_m = df_i_full[(df_i_full["Periodo"] == m) & (df_i_full["Año"] == anio) & (df_i_full["Usuario"] == st.session_state.usuario_id)]
        g_m = df_g_full[(df_g_full["Periodo"] == m) & (df_g_full["Año"] == anio) & (df_g_full["Usuario"] == st.session_state.usuario_id)]
        s_ant_m = i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0.0
        it_m, vp_m, vpy_m, bf_m, _ = calcular_metricas(g_m, i_m["Nomina"].sum() if not i_m.empty else 0, i_m["Otros"].sum() if not i_m.empty else 0, s_ant_m)
        
        if y < 250: c.showPage(); y = header_pdf(c, titulo_reporte, anio)
        c.setStrokeColor(HexColor("#dddddd")); c.setFillColor(HexColor("#f2f2f2"))
        c.roundRect(50, y-85, 510, 95, 10, fill=1, stroke=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(70, y-20, f"MES: {m}")
        c.setFont("Helvetica", 10); c.drawString(70, y-42, f"Ingresos: $ {it_m:,.0f} | Pagado: $ {vp_m:,.0f}")
        c.setFillColor(HexColor("#d4af37")); c.setFont("Helvetica-Bold", 11); c.drawString(70, y-75, f"BALANCE FINAL: $ {bf_m:,.0f}")
        y -= 110
        
        if not g_m.empty:
            c.setFillColor(HexColor("#1a1d21")); c.setFont("Helvetica-Bold", 9)
            c.drawString(55, y, "Categoría"); c.drawString(150, y, "Descripción"); c.drawRightString(400, y, "Ref."); c.drawRightString(480, y, "Monto"); c.drawRightString(550, y, "Estado")
            y -= 15; c.setFont("Helvetica", 8); c.setFillColor(colors.black)
            for _, row in g_m.iterrows():
                if y < 50: c.showPage(); y = header_pdf(c, titulo_reporte, anio); c.setFont("Helvetica", 8)
                c.drawString(55, y, str(row['Categoría'])); c.drawString(150, y, str(row['Descripción'])[:30])
                c.drawRightString(400, y, f"{row['Valor Referencia']:,.0f}"); c.drawRightString(480, y, f"{row['Monto']:,.0f}")
                c.drawRightString(550, y, "PAGADO" if row['Pagado'] else "PEND.")
                y -= 12
            y -= 20
    c.showPage(); c.save(); buf.seek(0)
    return buf

# --- 4. ACCESO ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>My Finance</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; margin-top: -20px;'>by Stulio Designs</p>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔑 Entrar", "📝 Registro"])
        usuarios = cargar_usuarios()
        with tab_log:
            u_in = st.text_input("Usuario").strip()
            p_in = st.text_input("Contraseña", type="password").strip()
            if st.button("Iniciar Sesión", use_container_width=True):
                if u_in in usuarios and usuarios[u_in]["pass"] == p_in:
                    st.session_state.autenticado, st.session_state.usuario_id = True, u_in
                    st.session_state.u_nombre_completo = usuarios[u_in].get("nombre", u_in)
                    st.rerun()
                else: st.error("❌ Datos incorrectos")
        with tab_reg:
            rn_full = st.text_input("Nombre Completo")
            rn_user = st.text_input("Nuevo Usuario")
            rn_pass = st.text_input("Nueva Contraseña", type="password")
            if st.button("Crear Cuenta", use_container_width=True):
                if rn_user and rn_pass:
                    usuarios[rn_user] = {"pass": rn_pass, "nombre": rn_full}
                    with open(USER_DB, "w") as f: json.dump(usuarios, f)
                    st.success("✅ Cuenta creada.")
    st.stop()

# --- 5. DASHBOARD ---
df_g_raw, df_i_raw = cargar_bd()
df_g_user = df_g_raw[df_g_raw["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == st.session_state.usuario_id].copy()
periodos_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    if os.path.exists(LOGO_APP_V): st.image(LOGO_APP_V, width=150)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=datetime.now().year - 2025)
    mes_s = st.selectbox("Mes Actual", periodos_list, index=datetime.now().month-1)
    
    # Saldo anterior automático
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
    arrastrar = st.toggle(f"Arrastrar saldo de {mes_ant}", value=not i_prev.empty)
    d_act_i = df_i_user[(df_i_user["Periodo"] == mes_s) & (df_i_user["Año"] == anio_s)]
    s_in = st.number_input("Saldo Anterior", value=saldo_auto if arrastrar else (float(d_act_i["SaldoAnterior"].iloc[0]) if not d_act_i.empty else 0.0), disabled=arrastrar)
    n_in = st.number_input("Nómina", value=float(d_act_i["Nomina"].iloc[0] if not d_act_i.empty else 0.0))
    o_in = st.number_input("Otros", value=float(d_act_i["Otros"].iloc[0] if not d_act_i.empty else 0.0))

    st.divider()
    st.subheader("📊 Reportes")
    c_r1, c_r2 = st.columns(2)
    with c_r1:
        if st.button(f"📄 PDF {mes_s[:3]}"):
            p = generar_pdf_profesional(df_g_user, df_i_user, [mes_s], f"Extracto {mes_s}", anio_s)
            st.download_button(f"PDF_{mes_s}.pdf", p, f"PDF_{mes_s}.pdf")
    with c_r2:
        df_ex = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)]
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_ex.to_excel(wr, index=False)
        st.download_button(f"📊 Excel {mes_s[:3]}", out.getvalue(), f"Excel_{mes_s}.xlsx")
    
    if st.button(f"📥 Balance Semestre 1 ({anio_s})"):
        p = generar_pdf_profesional(df_g_user, df_i_user, periodos_list[0:6], "Balance S1", anio_s)
        st.download_button("S1.pdf", p, "S1.pdf")
    if st.button(f"📥 Balance Semestre 2 ({anio_s})"):
        p = generar_pdf_profesional(df_g_user, df_i_user, periodos_list[6:12], "Balance S2", anio_s)
        st.download_button("S2.pdf", p, "S2.pdf")

    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 6. CUERPO PRINCIPAL ---
c_logo_h, c_title = st.columns([1, 4])
with c_logo_h: 
    if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
with c_title: st.markdown(f"<h1>{mes_s} {anio_s} <span style='font-size:0.4em; color:#d4af37;'>| by Stulio Designs</span></h1>", unsafe_allow_html=True)

# Lógica de Recurrencia (Cadena)
df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()
if df_mes.empty:
    df_rec = df_g_user[(df_g_user["Periodo"] == mes_ant) & (df_g_user["Año"] == anio_ant) & (df_g_user["Movimiento Recurrente"] == True)]
    if not df_rec.empty: df_mes = df_rec.copy().assign(Pagado=False, Monto=0)

df_v = df_mes.reset_index(drop=True).drop(columns=["Año", "Periodo", "Usuario"], errors='ignore')
df_ed = st.data_editor(df_v, use_container_width=True, num_rows="dynamic", key=f"ed_{mes_s}", column_config={
    "Categoría": st.column_config.SelectboxColumn("Categoría", options=["Hogar", "Salud", "Transporte", "Impuestos", "Obligaciones", "Servicios", "Otros"], required=True),
    "Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f"),
    "Valor Referencia": st.column_config.NumberColumn("Valor Referencia", format="$ %,.0f")
})

# METRICAS
it, vp, vpy, bf, ahorro_p = calcular_metricas(df_ed, n_in, o_in, s_in)
m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="card"><div class="card-label">Ingresos Total</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card"><div class="card-label">Pagado</div><div class="card-value" style="color:#2ecc71;">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="card"><div class="card-label">Pendiente</div><div class="card-value" style="color:#e74c3c;">$ {vpy:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="card"><div class="card-label">Saldo Final</div><div class="card-value" style="color:#d4af37;">$ {bf:,.0f}</div></div>', unsafe_allow_html=True)

# --- 🚀 INFOGRAFIAS (FIXED COLORS) ---
st.divider()
c_g1, c_g2 = st.columns(2)
with c_g1:
    if not df_ed.empty and df_ed["Monto"].sum() > 0:
        # Aquí corregí el error: usamos una lista manual de colores dorados
        dorados = ["#d4af37", "#f1c40f", "#9a7d0a", "#f39c12", "#e5c100", "#b8860b"]
        fig = px.pie(df_ed, values='Monto', names='Categoría', hole=0.6, 
                     color_discrete_sequence=dorados)
        fig.update_layout(title="Gastos por Categoría", paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=350, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("ℹ️ Agregue gastos con montos para ver el desglose.")

with c_g2:
    fig_g = go.Figure(go.Indicator(mode="gauge+number", value=ahorro_p, number={'suffix': "%", 'font':{'color':'#d4af37'}},
        title={'text': "Nivel de Ahorro Mensual", 'font':{'color':'white', 'size': 18}},
        gauge={'axis':{'range':[None, 100], 'tickcolor': "white"}, 'bar':{'color':"#d4af37"}, 'bgcolor':"#1f2630",
               'steps':[{'range':[0,20],'color':'#c0392b'},{'range':[20,50],'color':'#f39c12'},{'range':[50,100],'color':'#27ae60'}]}))
    fig_g.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350, font_color="white")
    st.plotly_chart(fig_g, use_container_width=True)

# GUARDAR
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    df_n = df_ed.dropna(subset=["Categoría", "Descripción"], how="all").assign(Periodo=mes_s, Año=anio_s, Usuario=st.session_state.usuario_id)
    mask_g = (df_g_raw["Periodo"] == mes_s) & (df_g_raw["Año"] == anio_s) & (df_g_raw["Usuario"] == st.session_state.usuario_id)
    df_gf = pd.concat([df_g_raw[~mask_g], df_n], ignore_index=True)
    df_i_nuevo = pd.DataFrame({"Año":[anio_s], "Periodo":[mes_s], "SaldoAnterior":[s_in], "Nomina":[n_in], "Otros":[o_in], "Usuario":[st.session_state.usuario_id]})
    mask_i = (df_i_raw["Periodo"] == mes_s) & (df_i_raw["Año"] == anio_s) & (df_i_raw["Usuario"] == st.session_state.usuario_id)
    df_if = pd.concat([df_i_raw[~mask_i], df_i_nuevo], ignore_index=True)
    with pd.ExcelWriter(BASE_FILE) as w:
        df_gf.to_excel(w, sheet_name="Gastos", index=False); df_if.to_excel(w, sheet_name="Ingresos", index=False)
    st.balloons(); st.rerun()
