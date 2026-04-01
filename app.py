import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

LOGO_APP_V = "LOGO APP.png"      
LOGO_APP_H = "LOGO H APP.png"    
BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_id' not in st.session_state: 
    st.session_state.usuario_id = ""
if 'u_nombre_completo' not in st.session_state:
    st.session_state.u_nombre_completo = "Usuario Pro"

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1a1d21 0%, #111315 100%); color: #dee2e6; }
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
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; }
    .login-box { max-width: 450px; margin: auto; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 15px; border: 1px solid #d4af37; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE USUARIOS ---
def cargar_usuarios():
    if not os.path.exists(USER_DB):
        db_inicial = {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}
        with open(USER_DB, "w") as f: json.dump(db_inicial, f)
        return db_inicial
    with open(USER_DB, "r") as f:
        try: return json.load(f)
        except: return {}

def guardar_usuarios(db):
    with open(USER_DB, "w") as f: json.dump(db, f)

# --- 3. LÓGICA DE NEGOCIO ---
def cargar_bd():
    columnas_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Recurrente", "Usuario"]
    columnas_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    if not os.path.exists(BASE_FILE):
        return pd.DataFrame(columns=columnas_g), pd.DataFrame(columns=columnas_i)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        if "Usuario" not in df_g.columns: df_g["Usuario"] = "tulicesar"
        if "Usuario" not in df_i.columns: df_i["Usuario"] = "tulicesar"
        for col in ["Monto", "Valor Referencia"]:
            df_g[col] = pd.to_numeric(df_g[col], errors='coerce').fillna(0)
        df_g["Pagado"] = df_g["Pagado"].fillna(False).astype(bool)
        df_g["Recurrente"] = df_g["Recurrente"].fillna(False).astype(bool)
        return df_g, df_i
    except:
        return pd.DataFrame(columns=columnas_g), pd.DataFrame(columns=columnas_i)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    if df_g.empty: return it, 0.0, 0.0, it, it
    mon = pd.to_numeric(df_g["Monto"], errors='coerce').fillna(0)
    ref = pd.to_numeric(df_g["Valor Referencia"], errors='coerce').fillna(0)
    pag = df_g["Pagado"].astype(bool)
    vp = mon[pag].sum()
    fb = it - vp
    vpy = 0
    for i in range(len(df_g)):
        r, m = float(ref.iloc[i]), float(mon.iloc[i])
        vpy += max(0.0, r - m) if pag.iloc[i] else max(r, m)
    return it, vp, vpy, fb, it - (vp + vpy)

# --- 4. MOTOR DE PDF ---
def generar_pdf_profesional(df_g_full, df_i_full, meses, sem_nom, anio):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFillColor(colors.white); c.rect(0, 0, 612, 792, fill=1)
    y = 750
    c.setFillColor(HexColor("#1a1d21"))
    c.setFont("Helvetica-Bold", 18); c.drawString(50, y, "STULIO FINANCE")
    c.setFont("Helvetica", 10); c.drawString(50, y-15, f"Propietario: {st.session_state.u_nombre_completo}")
    c.drawString(50, y-28, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.setFont("Helvetica-Bold", 14); c.drawRightString(560, y, f"Balance Semestral {sem_nom} - {anio}")
    y -= 45
    c.setStrokeColor(HexColor("#d4af37")); c.setLineWidth(1.5); c.line(50, y, 560, y); y -= 40
    for m in meses:
        if y < 160: c.showPage(); c.setFillColor(colors.white); c.rect(0,0,612,792,fill=1); y=740
        i_m = df_i_full[(df_i_full["Periodo"] == m) & (df_i_full["Año"] == anio)]
        g_m = df_g_full[(df_g_full["Periodo"] == m) & (df_g_full["Año"] == anio)]
        s_ant_m = i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0.0
        nom_m = i_m["Nomina"].sum() if not i_m.empty else 0.0
        otr_m = i_m["Otros"].sum() if not i_m.empty else 0.0
        it_m, vp_m, vpy_m, fb_m, bf_m = calcular_metricas(g_m, nom_m, otr_m, s_ant_m)
        c.setStrokeColor(HexColor("#dddddd")); c.setFillColor(HexColor("#f2f2f2"))
        c.roundRect(50, y-85, 510, 95, 10, fill=1, stroke=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(70, y-20, f"MES: {m}")
        c.setFont("Helvetica", 10); c.drawString(70, y-42, f"Ingresos: $ {it_m:,.0f} | Fondos: $ {fb_m:,.0f}")
        c.drawString(310, y-42, f"Pagado: $ {vp_m:,.0f} | Proyectado: $ {vpy_m:,.0f}")
        c.setFillColor(HexColor("#d4af37")); c.setFont("Helvetica-Bold", 11); c.drawString(70, y-75, f"BALANCE FINAL: $ {bf_m:,.0f}")
        y -= 115
    c.showPage(); c.save(); buf.seek(0)
    return buf

# --- 5. ACCESO ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        if os.path.exists(LOGO_APP_V): st.image(LOGO_APP_V, use_container_width=True)
        tab_login, tab_reg = st.tabs(["🔑 Entrar", "📝 Registro"])
        usuarios = cargar_usuarios()
        with tab_login:
            u_in = st.text_input("Usuario", key="l_u").strip()
            p_in = st.text_input("Contraseña", type="password", key="l_p").strip()
            if st.button("Iniciar Sesión", use_container_width=True):
                if u_in in usuarios and usuarios[u_in]["pass"] == p_in:
                    st.session_state.autenticado = True
                    st.session_state.usuario_id = u_in
                    st.session_state.u_nombre_completo = usuarios[u_in].get("nombre", u_in)
                    st.rerun()
                else: st.error("❌ Datos incorrectos")
        with tab_reg:
            rn_full = st.text_input("Nombre Completo")
            rn_user = st.text_input("Usuario (Login)")
            rn_pass = st.text_input("Contraseña", type="password")
            if st.button("Crear Cuenta"):
                if rn_full and rn_user and rn_pass:
                    usuarios[rn_user] = {"pass": rn_pass, "nombre": rn_full}
                    guardar_usuarios(usuarios)
                    st.success("✅ Cuenta creada.")
    st.stop()

# --- 6. DASHBOARD ---
df_g_raw, df_i_raw = cargar_bd()
df_g_user = df_g_raw[df_g_raw["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == st.session_state.usuario_id].copy()

periodos_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    if os.path.exists(LOGO_APP_V): st.image(LOGO_APP_V, width=150)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026, 2027], index=1)
    mes_s = st.selectbox("Mes Actual", periodos_list)
    idx = periodos_list.index(mes_s)
    
    mes_ant = periodos_list[idx - 1] if idx > 0 else periodos_list[11]
    anio_ant = anio_s if idx > 0 else anio_s - 1
    
    i_prev = df_i_user[(df_i_user["Periodo"] == mes_ant) & (df_i_user["Año"] == anio_ant)]
    g_prev = df_g_user[(df_g_user["Periodo"] == mes_ant) & (df_g_user["Año"] == anio_ant)]
    
    saldo_auto = 0.0
    hay_datos_previos = not i_prev.empty
    if hay_datos_previos:
        _, _, _, _, bf_pasado = calcular_metricas(g_prev, i_prev["Nomina"].sum(), i_prev["Otros"].sum(), i_prev["SaldoAnterior"].iloc[0])
        saldo_auto = float(bf_pasado)

    st.divider()
    st.subheader("💰 Balance de Ingresos")
    arrastrar = st.toggle(f"Arrastrar saldo de {mes_ant}", value=hay_datos_previos)
    
    d_act_i = df_i_user[(df_i_user["Periodo"] == mes_s) & (df_i_user["Año"] == anio_s)]
    val_s_actual = float(d_act_i["SaldoAnterior"].iloc[0]) if not d_act_i.empty else 0.0
    
    s_in = st.number_input("Saldo Anterior", value=saldo_auto if arrastrar else val_s_actual, disabled=arrastrar)
    n_in = st.number_input("Ingreso Nómina", value=float(d_act_i["Nomina"].iloc[0] if not d_act_i.empty else 0.0))
    o_in = st.number_input("Otros Ingresos", value=float(d_act_i["Otros"].iloc[0] if not d_act_i.empty else 0.0))
    
    st.divider()
    st.subheader("📄 Reportes")
    col_pdf1, col_pdf2 = st.columns(2)
    with col_pdf1:
        if st.button("📥 Ene-Jun"):
            pdf1 = generar_pdf_profesional(df_g_user, df_i_user, periodos_list[0:6], "1er Semestre", anio_s)
            st.download_button(f"S1_{anio_s}.pdf", pdf1, f"S1_{anio_s}.pdf")
    with col_pdf2:
        if st.button("📥 Jul-Dic"):
            pdf2 = generar_pdf_profesional(df_g_user, df_i_user, periodos_list[6:12], "2do Semestre", anio_s)
            st.download_button(f"S2_{anio_s}.pdf", pdf2, f"S2_{anio_s}.pdf")
    
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- HEADER ---
c_l, c_t = st.columns([1, 4])
with c_l: 
    if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
with c_t: st.markdown(f"<h1 style='margin-top: 15px;'>{mes_s} {anio_s}</h1>", unsafe_allow_html=True)

# --- 🚀 LÓGICA DE RECURRENCIA (SIN REPLICAR 'PAGADO') ---
st.markdown("### 📝 Registro de Movimientos")
df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()

# Obtenemos la lista de movimientos marcados como recurrentes en cualquier parte del historial
df_rec_master = df_g_user[df_g_user["Recurrente"] == True].drop_duplicates(subset=["Descripción"])

# Identificamos qué recurrentes NO están en el mes actual
nombres_actuales = df_mes["Descripción"].tolist() if not df_mes.empty else []
nuevos_items = df_rec_master[~df_rec_master["Descripción"].isin(nombres_actuales)].copy()

if not nuevos_items.empty:
    # ⚠️ AQUÍ ESTÁ LA CLAVE: Forzamos el reset de Pagado y Monto para el nuevo mes
    nuevos_items["Pagado"] = False
    nuevos_items["Monto"] = 0
    df_mes = pd.concat([df_mes, nuevos_items], ignore_index=True)

df_v = df_mes.reset_index(drop=True)
for c in ["Año", "Periodo", "Usuario", "Ítem"]:
    if c in df_v.columns: df_v = df_v.drop(columns=[c])

config_c = {
    "Categoría": st.column_config.SelectboxColumn("Categoría", options=["Hogar", "Salud", "Transporte", "Impuestos", "Obligaciones", "Servicios", "Otros"], required=True),
    "Monto": st.column_config.NumberColumn("Monto", format="$ %,d"),
    "Valor Referencia": st.column_config.NumberColumn("Valor Referencia", format="$ %,d"),
    "Pagado": st.column_config.CheckboxColumn("¿Pagado?"),
    "Recurrente": st.column_config.CheckboxColumn("Movimiento Recurrente")
}
df_ed = st.data_editor(df_v, column_config=config_c, use_container_width=True, hide_index=True, num_rows="dynamic", key="master_ed_v2")

# MÉTRICAS Y GRÁFICOS
it, vp, vpy, fb, bf = calcular_metricas(df_ed, n_in, o_in, s_in)
cards = st.columns(5)
def f_c(v): return f"$ {float(v):,.0f}".replace(",", ".")
metrics = [("💵 Ingresos", it, "#1a1d21"), ("🏦 Fondos", fb, "#2575fc"), ("✅ Pagado", vp, "#28a745"), ("⏳ Pendiente", vpy, "#e74c3c"), ("⚖️ Final", bf, "#00D2FF")]
for i, (lab, val, col) in enumerate(metrics):
    cards[i].markdown(f'<div class="card"><div class="card-label">{lab}</div><div class="card-value" style="color:{col}">{f_c(val)}</div></div>', unsafe_allow_html=True)

cg1, cg2 = st.columns([2, 1])
with cg1:
    fig = go.Figure(go.Scatter(y=[it, fb, bf], mode='lines+markers', line=dict(color='#d4af37', width=4), fill='tozeroy'))
    fig.update_layout(title="Tendencia", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
    st.plotly_chart(fig, use_container_width=True)
with cg2:
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=(bf/it*100 if it>0 else 0), title={'text': "% Ahorro"}, gauge={'bar':{'color':"#d4af37"}}))
    gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
    st.plotly_chart(gauge, use_container_width=True)

# GUARDAR
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    df_n = df_ed.dropna(subset=["Categoría", "Descripción"], how="all").assign(Periodo=mes_s, Año=anio_s, Usuario=st.session_state.usuario_id)
    mask_g = (df_g_raw["Periodo"] == mes_s) & (df_g_raw["Año"] == anio_s) & (df_g_raw["Usuario"] == st.session_state.usuario_id)
    df_gf = pd.concat([df_g_raw[~mask_g], df_n], ignore_index=True)
    df_i_nuevo = pd.DataFrame({"Año":[anio_s], "Periodo":[mes_s], "SaldoAnterior":[s_in], "Nomina":[n_in], "Otros":[o_in], "Usuario":[st.session_state.usuario_id]})
    mask_i = (df_i_raw["Periodo"] == mes_s) & (df_i_raw["Año"] == anio_s) & (df_i_raw["Usuario"] == st.session_state.usuario_id)
    df_if = pd.concat([df_i_raw[~mask_i], df_i_nuevo], ignore_index=True)
    with pd.ExcelWriter(BASE_FILE) as w:
        df_gf.to_excel(w, sheet_name="Gastos", index=False)
        df_if.to_excel(w, sheet_name="Ingresos", index=False)
    st.balloons(); st.rerun()
