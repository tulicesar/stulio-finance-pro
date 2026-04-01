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

# INICIALIZACIÓN DE MEMORIA
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'u_nombre_completo' not in st.session_state:
    st.session_state.u_nombre_completo = "Usuario Pro"
if 'usuario_id' not in st.session_state: # ID único (ej: tulicesar)
    st.session_state.usuario_id = ""
if 'saldo_manual' not in st.session_state:
    st.session_state.saldo_manual = 0.0

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
        db_inicial = {"tulicesar": {"pass": "Thulli.07", "email": "tulio@ejemplo.com", "nombre": "Tulio Salcedo"}}
        with open(USER_DB, "w") as f: json.dump(db_inicial, f)
        return db_inicial
    with open(USER_DB, "r") as f:
        try:
            return json.load(f)
        except: return {}

def guardar_usuarios(db):
    with open(USER_DB, "w") as f: json.dump(db, f)

# --- 3. LÓGICA DE NEGOCIO ---
def cargar_bd():
    columnas_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Usuario"]
    columnas_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    
    if not os.path.exists(BASE_FILE):
        return pd.DataFrame(columns=columnas_g), pd.DataFrame(columns=columnas_i)
    
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        
        # Aseguramos que exista la columna Usuario para el filtro
        if "Usuario" not in df_g.columns: df_g["Usuario"] = "tulicesar"
        if "Usuario" not in df_i.columns: df_i["Usuario"] = "tulicesar"
        
        for col in ["Monto", "Valor Referencia"]:
            df_g[col] = pd.to_numeric(df_g[col], errors='coerce').fillna(0)
        df_g["Pagado"] = df_g["Pagado"].fillna(False).astype(bool)
        return df_g, df_i
    except:
        return pd.DataFrame(columns=columnas_g), pd.DataFrame(columns=columnas_i)

def calcular_metricas(df_g, nom, otr, s_ant):
    if df_g.empty:
        it = float(s_ant) + float(nom) + float(otr)
        return it, 0.0, 0.0, it, it
    mon = pd.to_numeric(df_g["Monto"], errors='coerce').fillna(0)
    ref = pd.to_numeric(df_g["Valor Referencia"], errors='coerce').fillna(0)
    pag = df_g["Pagado"].astype(bool)
    it = float(s_ant) + float(nom) + float(otr)
    vp = mon[pag].sum()
    fb = it - vp
    vpy = 0
    for i in range(len(df_g)):
        r, m = float(ref.iloc[i]), float(mon.iloc[i])
        vpy += max(0.0, r - m) if pag.iloc[i] else max(r, m)
    return it, vp, vpy, fb, it - (vp + vpy)

# --- 4. ACCESO ---
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
                    st.session_state.usuario_id = u_in  # GUARDAMOS EL ID
                    st.session_state.u_nombre_completo = usuarios[u_in].get("nombre", u_in)
                    st.rerun()
                else: st.error("❌ Datos incorrectos")
        
        with tab_reg:
            rn_full = st.text_input("Nombre Completo")
            rn_user = st.text_input("Nombre de Usuario (Login)")
            rn_email = st.text_input("Email")
            rn_pass = st.text_input("Contraseña", type="password")
            if st.button("Crear Cuenta"):
                if rn_full and rn_user and rn_pass:
                    usuarios[rn_user] = {"pass": rn_pass, "email": rn_email, "nombre": rn_full}
                    guardar_usuarios(usuarios)
                    st.success("✅ Cuenta creada. Ya puedes entrar.")
    st.stop()

# --- 5. DASHBOARD FILTRADO POR USUARIO ---
df_g_full, df_i_full = cargar_bd()

# FILTRO: Solo mostramos lo que pertenece al usuario que inició sesión
df_g_user = df_g_full[df_g_full["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_full[df_i_full["Usuario"] == st.session_state.usuario_id].copy()

periodos_list = ["Diciembre - Enero", "Enero - Febrero", "Febrero - Marzo", "Marzo - Abril", "Abril - Mayo", "Mayo - Junio", 
                 "Junio - Julio", "Julio - Agosto", "Agosto - Septiembre", "Septiembre - Octubre", "Octubre - Noviembre", "Noviembre - Diciembre"]

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026, 2027], index=1)
    mes_s = st.selectbox("Periodo", periodos_list)
    
    idx = periodos_list.index(mes_s)
    mes_ant = periodos_list[idx - 1]; anio_ant = anio_s if idx > 0 else anio_s - 1

    st.divider()
    if st.button("🔄 Arrastrar Balance Pasado"):
        # Buscamos en los datos del usuario
        i_ant = df_i_user[(df_i_user["Periodo"] == mes_ant) & (df_i_user["Año"] == anio_ant)]
        g_ant = df_g_user[(df_g_user["Periodo"] == mes_ant) & (df_g_user["Año"] == anio_ant)]
        if not i_ant.empty:
            _, _, _, _, bf_pasado = calcular_metricas(g_ant, i_ant["Nomina"].sum(), i_ant["Otros"].sum(), i_ant["SaldoAnterior"].iloc[0])
            st.session_state.saldo_manual = float(bf_pasado)
            st.success("Saldo arrastrado.")
        else: st.warning("Sin datos previos.")

    d_act_i = df_i_user[(df_i_user["Periodo"] == mes_s) & (df_i_user["Año"] == anio_s)]
    val_s = float(d_act_i["SaldoAnterior"].iloc[0]) if not d_act_i.empty else st.session_state.saldo_manual

    s_in = st.number_input("Saldo Anterior", value=val_s)
    n_in = st.number_input("Ingreso Nómina", value=float(d_act_i["Nomina"].iloc[0] if not d_act_i.empty else 0.0))
    o_in = st.number_input("Otros Ingresos", value=float(d_act_i["Otros"].iloc[0] if not d_act_i.empty else 0.0))
    
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# CUERPO APP
st.markdown(f"<h1>Balance: {mes_s} {anio_s}</h1>", unsafe_allow_html=True)

# Filtramos por mes y año sobre los datos del usuario
df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()
df_v = df_mes.reset_index(drop=True)
# Ocultamos columnas de control en el editor
for c in ["Año", "Periodo", "Usuario"]:
    if c in df_v.columns: df_v = df_v.drop(columns=[c])

config_c = {
    "Categoría": st.column_config.SelectboxColumn("Categoría", options=["Hogar", "Salud", "Transporte", "Impuestos", "Obligaciones", "Otros"], required=True),
    "Monto": st.column_config.NumberColumn("Valor Pagado", format="$ %,d"),
    "Valor Referencia": st.column_config.NumberColumn("Valor Referencia", format="$ %,d"),
    "Pagado": st.column_config.CheckboxColumn("¿Pagado?")
}

df_ed = st.data_editor(df_v, column_config=config_c, use_container_width=True, hide_index=True, num_rows="dynamic", key="master_ed_v2")

# TIEMPO REAL
it, vp, vpy, fb, bf = calcular_metricas(df_ed, n_in, o_in, s_in)

# TARJETAS DE MÉTRICAS
cards = st.columns(5)
def f_c(v): return f"$ {float(v):,.0f}".replace(",", ".")
metrics = [("💵 Ingresos", it, "#1a1d21"), ("🏦 Fondos", fb, "#2575fc"), ("✅ Pagado", vp, "#28a745"), ("⏳ Pendiente", vpy, "#e74c3c"), ("⚖️ Final", bf, "#00D2FF")]
for i, (lab, val, col) in enumerate(metrics):
    cards[i].markdown(f'<div class="card"><div class="card-label">{lab}</div><div class="card-value" style="color:{col}">{f_c(val)}</div></div>', unsafe_allow_html=True)

# GRÁFICOS
cg1, cg2 = st.columns([2, 1])
with cg1:
    fig = go.Figure(go.Scatter(y=[it, fb, bf], mode='lines+markers', line=dict(color='#d4af37', width=4), fill='tozeroy'))
    fig.update_layout(title="Tendencia", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
    st.plotly_chart(fig, use_container_width=True)
with cg2:
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=(bf/it*100 if it>0 else 0), title={'text': "% Ahorro"}, gauge={'bar':{'color':"#d4af37"}}))
    gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
    st.plotly_chart(gauge, use_container_width=True)

# BOTÓN GUARDAR (SIN BORRAR A OTROS USUARIOS)
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    # 1. Nuevos datos del mes para este usuario
    df_n = df_ed.dropna(subset=["Categoría", "Descripción"], how="all").assign(
        Periodo=mes_s, 
        Año=anio_s, 
        Usuario=st.session_state.usuario_id
    )
    
    # 2. Reconstruimos Gastos: Todo lo que NO sea este usuario+mes + los nuevos datos
    mask_g = (df_g_full["Periodo"] == mes_s) & (df_g_full["Año"] == anio_s) & (df_g_full["Usuario"] == st.session_state.usuario_id)
    df_gf = pd.concat([df_g_full[~mask_g], df_n], ignore_index=True)
    
    # 3. Reconstruimos Ingresos
    df_i_nuevo = pd.DataFrame({
        "Año":[anio_s], "Periodo":[mes_s], "SaldoAnterior":[s_in], 
        "Nomina":[n_in], "Otros":[o_in], "Usuario":[st.session_state.usuario_id]
    })
    mask_i = (df_i_full["Periodo"] == mes_s) & (df_i_full["Año"] == anio_s) & (df_i_full["Usuario"] == st.session_state.usuario_id)
    df_if = pd.concat([df_i_full[~mask_i], df_i_nuevo], ignore_index=True)
    
    with pd.ExcelWriter(BASE_FILE) as w:
        df_gf.to_excel(w, sheet_name="Gastos", index=False)
        df_if.to_excel(w, sheet_name="Ingresos", index=False)
    
    st.balloons(); st.rerun()
