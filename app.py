import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

# Rutas de Archivos
LOGO_LOGIN = "logoapp 1.png"
LOGO_DARK = "logoapp 2.jpg"    # Modo Oscuro
LOGO_LIGHT = "logoapp3.jpg"   # Modo Claro
LOGO_APP_H = "LOGOapp horizontal.png" 
BASE_FILE = "base.xlsx"
USER_DB = "usuarios.json"

# --- 2. GESTIÓN DE ESTADO Y MODO (CLARO/OSCURO) ---
if 'modo_oscuro' not in st.session_state:
    st.session_state.modo_oscuro = True  # Por defecto oscuro

with st.sidebar:
    # Selector de tema basado en logos adjuntos
    st.session_state.modo_oscuro = st.toggle('Modo Oscuro 🌙', value=st.session_state.modo_oscuro)
    
    # Definición dinámica de colores según el logo
    if st.session_state.modo_oscuro:
        # Paleta logoapp 2.jpg (Oscuro)
        bg_app = "#10141D"
        bg_sidebar = "#1A1F2B"
        bg_card = "#1A1F2B"
        text_main = "#FFFFFF"
        text_sec = "#A0AAB5"
        accent = "#38EF7D"  # Verde flecha
        logo_sidebar = LOGO_DARK
        color_map_graficos = {
            "Hogar": "#5DADE2", "Servicios": "#F4D03F", "Salud": "#EC7063", 
            "Transporte": "#AF7AC5", "Obligaciones": "#EB984E", "Alimentación": "#A569BD", 
            "Otros": "#82E0AA", "Impuestos": "#F1948A"
        }
    else:
        # Paleta logoapp3.jpg (Claro)
        bg_app = "#F8F9FA"
        bg_sidebar = "#FFFFFF"
        bg_card = "#FFFFFF"
        text_main = "#10141D"
        text_sec = "#5D6D7E"
        accent = "#11998E"  # Verde profundo
        logo_sidebar = LOGO_LIGHT
        color_map_graficos = {
            "Hogar": "#3498DB", "Servicios": "#F1C40F", "Salud": "#E74C3C", 
            "Transporte": "#8E44AD", "Obligaciones": "#E67E22", "Alimentación": "#884EA0", 
            "Otros": "#2ECC71", "Impuestos": "#E06666"
        }

# --- 3. INYECCIÓN DE CSS (CORREGIDO SYNTAX ERROR) ---
st.markdown(f"""
    <style>
    /* Usamos doble llave {{ }} para que Python no crea que son variables */
    button[kind="headerNoSpacing"] {{ display: flex !important; visibility: visible !important; color: {accent} !important; }}
    header {{ background-color: rgba(0,0,0,0) !important; }}
    [data-testid="stHeader"] {{ background: none !important; }}

    .stApp {{ background-color: {bg_app} !important; color: {text_main} !important; }}
    
    section[data-testid="stSidebar"] {{ 
        background-color: {bg_sidebar} !important; 
        border-right: 1px solid {accent}44;
    }}

    /* Texto de Tabla */
    [data-testid="stDataEditor"] div {{ font-size: 1.2rem !important; color: {text_main}; }}
    
    /* Tarjetas Premium */
    .card {{
        background-color: {bg_card}; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2); margin-bottom: 10px;
        text-align: center; border-bottom: 4px solid {accent};
        color: {text_main} !important;
    }}
    .card-label {{ font-size: 0.8rem; color: {text_sec}; font-weight: 800; text-transform: uppercase; }}
    .card-value {{ font-size: 1.6rem; font-weight: 800; margin: 3px 0; }}
    
    .legend-bar {{
        padding: 10px 15px; border-radius: 8px; margin-bottom: 6px; 
        font-size: 1rem; font-weight: bold; color: #1a1d21; 
        display: flex; justify-content: space-between; align-items: center;
        max-width: 95%; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }}
    
    .stButton>button {{ 
        border-radius: 10px; font-weight: bold; width: 100%; 
        background-color: {accent}; color: white; border: none; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. MOTOR DE DATOS ---
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
        return df_g, df_i
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0.0
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum() if not df_g.empty else 0.0
    fondos_act = it - vp
    saldo_fin = it - vp - vpy
    ahorro_p = (saldo_fin / it * 100) if it > 0 else 0
    return it, vp, vpy, fondos_act, saldo_fin, ahorro_p

def generar_pdf_reporte(df_g_full, df_i_full, meses, titulo, anio):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, f"Reporte: {titulo} - {anio}")
    y = 720
    for m in meses:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Mes: {m}")
        y -= 20
    c.save(); buf.seek(0)
    return buf

# --- 5. ACCESO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN): st.image(LOGO_LOGIN, use_container_width=True)
        usuarios = cargar_usuarios()
        u_in = st.text_input("Usuario")
        p_in = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if u_in in usuarios and usuarios[u_in]["pass"] == p_in:
                st.session_state.autenticado, st.session_state.usuario_id = True, u_in
                st.session_state.u_nombre_completo = usuarios[u_in].get("nombre", u_in)
                st.rerun()
    st.stop()

# --- 6. SIDEBAR Y LOGICA ---
df_g_raw, df_i_raw = cargar_bd()
df_g_user = df_g_raw[df_g_raw["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == st.session_state.usuario_id].copy()
periodos_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    if os.path.exists(logo_sidebar): st.image(logo_sidebar, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    mes_s = st.selectbox("Mes Actual", periodos_list, index=datetime.now().month-1)
    
    # ARRASTRE DE SALDO
    idx = periodos_list.index(mes_s); mes_ant = periodos_list[idx-1] if idx>0 else periodos_list[11]; anio_ant = anio_s if idx>0 else anio_s-1
    i_pas = df_i_user[(df_i_user["Periodo"]==mes_ant) & (df_i_user["Año"]==anio_ant)]
    g_pas = df_g_user[(df_g_user["Periodo"]==mes_ant) & (df_g_user["Año"]==anio_ant)]
    saldo_auto = 0.0
    if not i_pas.empty:
        *_, bf_p, _ = calcular_metricas(g_pas, i_pas["Nomina"].sum(), i_pas["Otros"].sum(), i_pas["SaldoAnterior"].iloc[0])
        saldo_auto = float(bf_p)

    st.divider()
    arr_on = st.toggle(f"Traer saldo de {mes_ant}", value=not i_pas.empty)
    s_in = st.number_input("Saldo Anterior", value=saldo_auto if arr_on else (float(df_i_user[df_i_user["Periodo"]==mes_s]["SaldoAnterior"].iloc[0]) if not df_i_user[df_i_user["Periodo"]==mes_s].empty else 0.0))
    n_in = st.number_input("Nómina", value=float(df_i_user[df_i_user["Periodo"]==mes_s]["Nomina"].iloc[0] if not df_i_user[df_i_user["Periodo"]==mes_s].empty else 0.0))
    o_in = st.number_input("Otros", value=float(df_i_user[df_i_user["Periodo"]==mes_s]["Otros"].iloc[0] if not df_i_user[df_i_user["Periodo"]==mes_s].empty else 0.0))

    st.divider()
    st.subheader("📑 Reportes")
    ca, cb = st.columns(2)
    with ca:
        if st.button("📄 PDF"):
            pdf = generar_pdf_reporte(df_g_user, df_i_user, [mes_s], "Extracto", anio_s)
            st.download_button("Bajar PDF", pdf, f"Reporte_{mes_s}.pdf")
    with cb:
        df_ex = df_g_user[df_g_user["Periodo"] == mes_s].copy()
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_ex.to_excel(wr, index=False)
        st.download_button("📊 Excel", out.getvalue(), f"Excel_{mes_s}.xlsx")

    st.subheader("📈 Balances Semestrales")
    if st.button("📥 Semestre 1"):
        pdf1 = generar_pdf_reporte(df_g_user, df_i_user, periodos_list[0:6], "S1", anio_s)
        st.download_button("S1.pdf", pdf1, "Balance_S1.pdf")
    if st.button("📥 Semestre 2"):
        pdf2 = generar_pdf_reporte(df_g_user, df_i_user, periodos_list[6:12], "S2", anio_s)
        st.download_button("S2.pdf", pdf2, "Balance_S2.pdf")

# --- 7. CUERPO PRINCIPAL ---
c_logo, _ = st.columns([3, 1])
with c_logo:
    if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"<h1 style='text-align: left; margin-top: -10px;'>{mes_s} {anio_s}</h1>", unsafe_allow_html=True)

df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()
df_v = df_mes.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"]).reset_index(drop=True)
df_ed = st.data_editor(df_v, use_container_width=True, num_rows="dynamic", key=f"ed_{mes_s}")

it, vp, vpy, fondos_act, saldo_fin, ahorro_p = calcular_metricas(df_ed, n_in, o_in, s_in)
st.markdown("---")
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="card"><div class="card-label">INGRESOS</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card"><div class="card-label">PAGADO</div><div class="card-value" style="color:#2ecc71;">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="card"><div class="card-label">PENDIENTE</div><div class="card-value" style="color:#e74c3c;">$ {vpy:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="card"><div class="card-label">FONDOS ACTUALES</div><div class="card-value" style="color:#2575fc;">$ {fondos_act:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="card"><div class="card-label">AHORRO FINAL</div><div class="card-value" style="color:{accent};">$ {saldo_fin:,.0f}</div></div>', unsafe_allow_html=True)

# --- INFOGRAFIAS ---
st.markdown("### 📊 Análisis de Gastos")
c1, c2, c3 = st.columns([1.5, 1, 1.2])
with c1:
    st.markdown("**Desglose Presupuestado**")
    t_df = df_ed.copy(); t_df['V'] = t_df.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not t_df.empty and t_df['V'].sum() > 0:
        fig = px.pie(t_df, values='V', names='Categoría', color='Categoría', hole=0.6, color_discrete_map=color_map_graficos)
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
        res = t_df.groupby("Categoría")['V'].sum().reset_index()
        for _, r in res.iterrows():
            st.markdown(f'<div class="legend-bar" style="background:{color_map_graficos.get(r["Categoría"],"#eee")}">{r["Categoría"]} <span>$ {r["V"]:,.0f}</span></div>', unsafe_allow_html=True)

with c2:
    st.markdown("**Eficiencia de Ahorro**")
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=ahorro_p, number={'suffix': "%", 'font':{'color':accent}}, gauge={'axis':{'range':[0,100]},'bar':{'color':text_main},'bgcolor':bg_card,'steps':[{'range':[0,20],'color':'#ff4b4b'},{'range':[20,50],'color':'#ffa500'},{'range':[50,100],'color':'#00d26a'}],'threshold':{'line':{'color':accent,'width':6},'thickness':0.85,'value':ahorro_p}}))
    gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': text_main}, height=350, margin=dict(t=50,b=0,l=0,r=0))
    st.plotly_chart(gauge, use_container_width=True)

with c3:
    st.markdown("**Estado Real**")
    pie = go.Figure(data=[go.Pie(labels=['Pagado', 'Pendiente', 'Ahorro'], values=[vp, vpy, saldo_fin], hole=.65, marker_colors=['#2ecc71', '#e74c3c', accent], textinfo='percent+label')])
    pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=380, margin=dict(t=0,b=0,l=0,r=0))
    st.plotly_chart(pie, use_container_width=True)

if st.button("💾 GUARDAR CAMBIOS"):
    df_n = df_ed.assign(Periodo=mes_s, Año=anio_s, Usuario=st.session_state.usuario_id)
    mask_g = (df_g_raw["Periodo"] == mes_s) & (df_g_raw["Año"] == anio_s) & (df_g_raw["Usuario"] == st.session_state.usuario_id)
    df_gf = pd.concat([df_g_raw[~mask_g], df_n], ignore_index=True)
    df_if = pd.concat([df_i_raw[~((df_i_raw["Periodo"] == mes_s) & (df_i_raw["Año"] == anio_s) & (df_i_raw["Usuario"] == st.session_state.usuario_id))], pd.DataFrame([{"Año":anio_s, "Periodo":mes_s, "SaldoAnterior":s_in, "Nomina":n_in, "Otros":o_in, "Usuario":st.session_state.usuario_id}])], ignore_index=True)
    with pd.ExcelWriter(BASE_FILE) as w:
        df_gf.to_excel(w, sheet_name="Gastos", index=False); df_if.to_excel(w, sheet_name="Ingresos", index=False)
    st.balloons(); st.rerun()
