import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
from io import BytesIO
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILO (TU DISEÑO PRO RESTAURADO) ---
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
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
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

def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    if not os.path.exists(BASE_FILE):
        return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        # Asegurar tipos de datos para evitar errores de cálculo
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
    
    # Cálculos limpios
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum()
    fb = it - vp
    
    def calc_pendiente(r):
        ref = float(r["Valor Referencia"])
        mon = float(r["Monto"])
        return max(0.0, ref - mon) if r["Pagado"] else max(ref, mon)
    
    vpy = df_g.apply(calc_pendiente, axis=1).sum()
    return it, vp, vpy, fb, it - (vp + vpy)

# --- 3. ACCESO (LOGIN RESTAURADO) ---
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(LOGO_APP_V): st.image(LOGO_APP_V, use_container_width=True)
        usuarios = cargar_usuarios()
        u_in = st.text_input("Usuario", key="l_u").strip()
        p_in = st.text_input("Contraseña", type="password", key="l_p").strip()
        if st.button("Entrar"):
            if u_in in usuarios and usuarios[u_in]["pass"] == p_in:
                st.session_state.autenticado = True
                st.session_state.usuario_id = u_in
                st.session_state.u_nombre_completo = usuarios[u_in].get("nombre", u_in)
                st.rerun()
            else: st.error("Error de credenciales")
    st.stop()

# --- 4. DASHBOARD ---
df_g_raw, df_i_raw = cargar_bd()
df_g_user = df_g_raw[df_g_raw["Usuario"] == st.session_state.usuario_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == st.session_state.usuario_id].copy()

periodos_list = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    if os.path.exists(LOGO_APP_V): st.image(LOGO_APP_V, width=150)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026, 2027], index=1)
    mes_s = st.selectbox("Mes Actual", periodos_list)
    idx = periodos_list.index(mes_s)
    
    mes_ant = periodos_list[idx - 1] if idx > 0 else periodos_list[11]
    anio_ant = anio_s if idx > 0 else anio_s - 1
    
    # Arrastre automático de saldo
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
    
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# HEADER CON LOGO HORIZONTAL
c_l, c_t = st.columns([1, 4])
with c_l: 
    if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
with c_t: st.markdown(f"<h1 style='margin-top: 15px;'>{mes_s} {anio_s}</h1>", unsafe_allow_html=True)

# --- 🚀 LÓGICA DE RECURRENCIA (SÓLO SI EL MES ESTÁ VACÍO) ---
df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()

# EXPLICACIÓN: Solo buscamos recurrentes si el mes no tiene NADA guardado aún.
# Si tú borras todo y guardas, el mes ya no estará vacío (tendrá 0 filas en el excel pero existirá el registro de ingresos).
if d_act_i.empty and df_mes.empty:
    # Buscamos recurrentes del mes anterior inmediato para no traer basura de hace un año
    df_prev_rec = df_g_user[(df_g_user["Periodo"] == mes_ant) & (df_g_user["Año"] == anio_ant) & (df_g_user["Recurrente"] == True)]
    if not df_prev_rec.empty:
        df_prev_rec = df_prev_rec.copy()
        df_prev_rec["Pagado"] = False
        df_prev_rec["Monto"] = 0
        df_mes = df_prev_rec
        st.info(f"✨ Se cargaron movimientos recurrentes de {mes_ant}.")

df_v = df_mes.reset_index(drop=True)
for c in ["Año", "Periodo", "Usuario"]:
    if c in df_v.columns: df_v = df_v.drop(columns=[c])

# TABLA DE REGISTROS
config_c = {
    "Categoría": st.column_config.SelectboxColumn("Categoría", options=["Hogar", "Salud", "Transporte", "Impuestos", "Obligaciones", "Servicios", "Otros"], required=True),
    "Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f"),
    "Valor Referencia": st.column_config.NumberColumn("Valor Referencia", format="$ %,.0f"),
    "Pagado": st.column_config.CheckboxColumn("¿Pagado?"),
    "Recurrente": st.column_config.CheckboxColumn("Movimiento Recurrente")
}
df_ed = st.data_editor(df_v, column_config=config_c, use_container_width=True, hide_index=True, num_rows="dynamic", key="editor_v4")

# --- MÉTRICAS E INFOGRAFÍA (TU DISEÑO ORIGINAL) ---
it, vp, vpy, fb, bf = calcular_metricas(df_ed, n_in, o_in, s_in)
cards = st.columns(5)
def f_c(v): return f"$ {float(v):,.0f}".replace(",", ".")
metrics = [("💵 INGRESOS", it, "#1a1d21"), ("🏦 FONDOS", fb, "#2575fc"), ("✅ PAGADO", vp, "#28a745"), ("⏳ PENDIENTE", vpy, "#e74c3c"), ("⚖️ FINAL", bf, "#00D2FF")]
for i, (lab, val, col) in enumerate(metrics):
    cards[i].markdown(f'<div class="card"><div class="card-label">{lab}</div><div class="card-value" style="color:{col}">{f_c(val)}</div></div>', unsafe_allow_html=True)

# GRÁFICOS PLOTLY (TU DISEÑO ORIGINAL)
cg1, cg2 = st.columns([2, 1])
with cg1:
    fig = go.Figure(go.Scatter(y=[it, fb, bf], mode='lines+markers', line=dict(color='#d4af37', width=4), fill='tozeroy'))
    fig.update_layout(title="Tendencia", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
    st.plotly_chart(fig, use_container_width=True)
with cg2:
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=(bf/it*100 if it>0 else 0), title={'text': "% Ahorro"}, gauge={'bar':{'color':"#d4af37"}}))
    gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
    st.plotly_chart(gauge, use_container_width=True)

# BOTÓN DE GUARDADO
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    # 1. Filtramos filas vacías
    df_n = df_ed.dropna(subset=["Categoría", "Descripción"], how="all").assign(Periodo=mes_s, Año=anio_s, Usuario=st.session_state.usuario_id)
    
    # 2. Reemplazamos en la base global
    mask_g = (df_g_raw["Periodo"] == mes_s) & (df_g_raw["Año"] == anio_s) & (df_g_raw["Usuario"] == st.session_state.usuario_id)
    df_gf = pd.concat([df_g_raw[~mask_g], df_n], ignore_index=True)
    
    # 3. Guardamos ingresos (esto marca el mes como "ya trabajado")
    df_i_nuevo = pd.DataFrame({"Año":[anio_s], "Periodo":[mes_s], "SaldoAnterior":[s_in], "Nomina":[n_in], "Otros":[o_in], "Usuario":[st.session_state.usuario_id]})
    mask_i = (df_i_raw["Periodo"] == mes_s) & (df_i_raw["Año"] == anio_s) & (df_i_raw["Usuario"] == st.session_state.usuario_id)
    df_if = pd.concat([df_i_raw[~mask_i], df_i_nuevo], ignore_index=True)
    
    with pd.ExcelWriter(BASE_FILE) as w:
        df_gf.to_excel(w, sheet_name="Gastos", index=False)
        df_if.to_excel(w, sheet_name="Ingresos", index=False)
    st.balloons(); st.rerun()
