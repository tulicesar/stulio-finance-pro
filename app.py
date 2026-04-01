import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILO (RESTAURADO) ---
st.set_page_config(page_title="STULIO FINANCE PRO", layout="wide", page_icon="🔮")

LOGO_APP_V = "LOGO APP.png"      
LOGO_APP_H = "LOGO H APP.png"    
BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_id' not in st.session_state: 
    st.session_state.usuario_id = ""

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

# --- 2. MOTOR DE DATOS ---
def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    if not os.path.exists(BASE_FILE):
        return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        # Limpieza de columnas viejas si existen
        if "Ítem" in df_g.columns: df_g = df_g.drop(columns=["Ítem"])
        for col in ["Monto", "Valor Referencia"]:
            df_g[col] = pd.to_numeric(df_g[col], errors='coerce').fillna(0.0)
        df_g["Pagado"] = df_g["Pagado"].fillna(False).astype(bool)
        df_g["Recurrente"] = df_g["Recurrente"].fillna(False).astype(bool)
        if "Usuario" not in df_g.columns: df_g["Usuario"] = "tulicesar"
        if "Usuario" not in df_i.columns: df_i["Usuario"] = "tulicesar"
        return df_g, df_i
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    if df_g.empty: return it, 0.0, 0.0, it, it
    temp = df_g.copy()
    temp["Monto"] = pd.to_numeric(temp["Monto"], errors='coerce').fillna(0.0)
    temp["Valor Referencia"] = pd.to_numeric(temp["Valor Referencia"], errors='coerce').fillna(0.0)
    vp = temp[temp["Pagado"] == True]["Monto"].sum()
    fb = it - vp
    def deuda(r):
        ref, mon = float(r["Valor Referencia"]), float(r["Monto"])
        return max(0.0, ref - mon) if r["Pagado"] else max(ref, mon)
    vpy = temp.apply(deuda, axis=1).sum()
    return it, vp, vpy, fb, it - (vp + vpy)

# --- 3. MOTOR PDF (RESTAURADO) ---
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
    c.setFont("Helvetica-Bold", 14); c.drawRightString(560, y, f"Balance {sem_nom} - {anio}")
    y -= 45
    c.setStrokeColor(HexColor("#d4af37")); c.setLineWidth(1.5); c.line(50, y, 560, y); y -= 40
    for m in meses:
        if y < 160: c.showPage(); c.setFillColor(colors.white); c.rect(0,0,612,792,fill=1); y=740
        i_m = df_i_full[(df_i_full["Periodo"] == m) & (df_i_full["Año"] == anio) & (df_i_full["Usuario"] == st.session_state.usuario_id)]
        g_m = df_g_full[(df_g_full["Periodo"] == m) & (df_g_full["Año"] == anio) & (df_g_full["Usuario"] == st.session_state.usuario_id)]
        s_ant_m = i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0.0
        nom_m = i_m["Nomina"].sum() if not i_m.empty else 0.0
        otr_m = i_m["Otros"].sum() if not i_m.empty else 0.0
        it_m, vp_m, vpy_m, fb_m, bf_m = calcular_metricas(g_m, nom_m, otr_m, s_ant_m)
        c.setStrokeColor(HexColor("#dddddd")); c.setFillColor(HexColor("#f2f2f2"))
        c.roundRect(50, y-85, 510, 95, 10, fill=1, stroke=1)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(70, y-20, f"MES: {m}")
        c.setFont("Helvetica", 10); c.drawString(70, y-42, f"Ingresos: $ {it_m:,.0f} | Fondos: $ {fb_m:,.0f}")
        c.drawString(310, y-42, f"Pagado: $ {vp_m:,.0f} | Pendiente: $ {vpy_m:,.0f}")
        c.setFillColor(HexColor("#d4af37")); c.setFont("Helvetica-Bold", 11); c.drawString(70, y-75, f"BALANCE FINAL: $ {bf_m:,.0f}")
        y -= 115
    c.showPage(); c.save(); buf.seek(0)
    return buf

# --- 4. ACCESO ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        if os.path.exists(LOGO_APP_V): st.image(LOGO_APP_V, use_container_width=True)
        u_in = st.text_input("Usuario", key="l_u").strip()
        p_in = st.text_input("Contraseña", type="password", key="l_p").strip()
        if st.button("Entrar", use_container_width=True):
            if u_in == "tulicesar" and p_in == "Thulli.07":
                st.session_state.autenticado = True
                st.session_state.usuario_id = u_in
                st.rerun()
            else: st.error("❌ Datos incorrectos")
    st.stop()

# --- 5. DASHBOARD ---
df_g_raw, df_i_raw = cargar_bd()
df_g_user = df_g_raw[df_g_raw["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == st.session_state.usuario_id].copy()

periodos_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    if os.path.exists(LOGO_APP_V): st.image(LOGO_APP_V, width=150)
    anio_s = st.selectbox("Año", [2025, 2026, 2027], index=1)
    mes_s = st.selectbox("Mes Actual", periodos_list)
    idx = periodos_list.index(mes_s)
    
    mes_ant = periodos_list[idx - 1] if idx > 0 else periodos_list[11]
    anio_ant = anio_s if idx > 0 else anio_s - 1
    
    i_prev = df_i_user[(df_i_user["Periodo"] == mes_ant) & (df_i_user["Año"] == anio_ant)]
    g_prev = df_g_user[(df_g_user["Periodo"] == mes_ant) & (df_g_user["Año"] == anio_ant)]
    saldo_auto = 0.0
    if not i_prev.empty:
        _, _, _, _, bf_pasado = calcular_metricas(g_prev, i_prev["Nomina"].sum(), i_prev["Otros"].sum(), i_prev["SaldoAnterior"].iloc[0])
        saldo_auto = float(bf_pasado)

    st.divider()
    arrastrar = st.toggle(f"Arrastrar saldo de {mes_ant}", value=not i_prev.empty)
    d_act_i = df_i_user[(df_i_user["Periodo"] == mes_s) & (df_i_user["Año"] == anio_s)]
    s_in = st.number_input("Saldo Anterior", value=saldo_auto if arrastrar else (float(d_act_i["SaldoAnterior"].iloc[0]) if not d_act_i.empty else 0.0), disabled=arrastrar)
    n_in = st.number_input("Nómina", value=float(d_act_i["Nomina"].iloc[0] if not d_act_i.empty else 0.0))
    o_in = st.number_input("Otros", value=float(d_act_i["Otros"].iloc[0] if not d_act_i.empty else 0.0))

    st.divider()
    st.subheader("📄 Generar Balances")
    if st.button("📥 S1 (Ene-Jun)"):
        pdf = generar_pdf_profesional(df_g_user, df_i_user, periodos_list[0:6], "1er Semestre", anio_s)
        st.download_button(f"S1_{anio_s}.pdf", pdf, f"S1_{anio_s}.pdf")
    if st.button("📥 S2 (Jul-Dic)"):
        pdf = generar_pdf_profesional(df_g_user, df_i_user, periodos_list[6:12], "2do Semestre", anio_s)
        st.download_button(f"S2_{anio_s}.pdf", pdf, f"S2_{anio_s}.pdf")
    
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- HEADER ---
c_l, c_t = st.columns([1, 4])
with c_l: 
    if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
with c_t: st.markdown(f"<h1 style='margin-top: 15px;'>{mes_s} {anio_s}</h1>", unsafe_allow_html=True)

# --- 🚀 REGISTRO ---
st.markdown("### 📝 Registro de Movimientos")
df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()

# BOTÓN MANUAL PARA RECURRENTES (AQUÍ TÚ TIENES EL CONTROL TOTAL)
with st.expander("🛠️ Herramientas de Carga"):
    st.write("Si quieres traer tus movimientos recurrentes de meses pasados, usa el botón de abajo:")
    if st.button("📥 Cargar mis Recurrentes"):
        df_recurrentes_master = df_g_user[df_g_user["Recurrente"] == True].sort_values(by="Año", ascending=False).drop_duplicates(subset=["Descripción"])
        if not df_recurrentes_master.empty:
            df_recurrentes_master["Pagado"] = False
            df_recurrentes_master["Monto"] = 0
            # Solo agregamos los que no existan ya en el mes actual
            nombres_actuales = df_mes["Descripción"].tolist()
            faltantes = df_recurrentes_master[~df_recurrentes_master["Descripción"].isin(nombres_actuales)]
            df_mes = pd.concat([df_mes, faltantes], ignore_index=True)
            st.success("Movimientos cargados con éxito. No olvides Guardar Cambios.")

df_v = df_mes.reset_index(drop=True)
for c in ["Año", "Periodo", "Usuario", "Ítem"]:
    if c in df_v.columns: df_v = df_v.drop(columns=[c])

config_c = {
    "Categoría": st.column_config.SelectboxColumn("Categoría", options=["Hogar", "Salud", "Transporte", "Impuestos", "Obligaciones", "Servicios", "Otros"], required=True),
    "Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f"),
    "Valor Referencia": st.column_config.NumberColumn("Valor Referencia", format="$ %,.0f"),
    "Pagado": st.column_config.CheckboxColumn("¿Pagado?"),
    "Recurrente": st.column_config.CheckboxColumn("Movimiento Recurrente")
}
# La clave (key) incluye el mes para que el editor se limpie al cambiar de periodo
df_ed = st.data_editor(df_v, column_config=config_c, use_container_width=True, hide_index=True, num_rows="dynamic", key=f"editor_{mes_s}")

# MÉTRICAS (INFOGRAFÍA RESTAURADA)
it, vp, vpy, fb, bf = calcular_metricas(df_ed, n_in, o_in, s_in)
cards = st.columns(5)
def f_c(v): return f"$ {float(v):,.0f}".replace(",", ".")
metrics = [("💵 Ingresos", it, "#1a1d21"), ("🏦 Fondos", fb, "#2575fc"), ("✅ Pagado", vp, "#28a745"), ("⏳ Pendiente", vpy, "#e74c3c"), ("⚖️ Final", bf, "#00D2FF")]
for i, (lab, val, col) in enumerate(metrics):
    cards[i].markdown(f'<div class="card"><div class="card-label">{lab}</div><div class="card-value" style="color:{col}">{f_c(val)}</div></div>', unsafe_allow_html=True)

# GRÁFICOS (PLOTLY RESTAURADO)
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
    # Reemplazo estricto en la base global
    mask_g = (df_g_raw["Periodo"] == mes_s) & (df_g_raw["Año"] == anio_s) & (df_g_raw["Usuario"] == st.session_state.usuario_id)
    df_gf = pd.concat([df_g_raw[~mask_g], df_n], ignore_index=True)
    
    df_i_nuevo = pd.DataFrame({"Año":[anio_s], "Periodo":[mes_s], "SaldoAnterior":[s_in], "Nomina":[n_in], "Otros":[o_in], "Usuario":[st.session_state.usuario_id]})
    mask_i = (df_i_raw["Periodo"] == mes_s) & (df_i_raw["Año"] == anio_s) & (df_i_raw["Usuario"] == st.session_state.usuario_id)
    df_if = pd.concat([df_i_raw[~mask_i], df_i_nuevo], ignore_index=True)
    
    with pd.ExcelWriter(BASE_FILE) as w:
        df_gf.to_excel(w, sheet_name="Gastos", index=False)
        df_if.to_excel(w, sheet_name="Ingresos", index=False)
    st.balloons(); st.rerun()
