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
def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    if not os.path.exists(BASE_FILE):
        return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        for col in ["Monto", "Valor Referencia"]:
            df_g[col] = pd.to_numeric(df_g[col], errors='coerce').fillna(0)
        df_g["Pagado"] = df_g["Pagado"].fillna(False).astype(bool)
        df_g["Recurrente"] = df_g["Recurrente"].fillna(False).astype(bool)
        return df_g, df_i
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    if df_g.empty: return it, 0.0, 0.0, it, it
    mon = pd.to_numeric(df_g["Monto"], errors='coerce').fillna(0)
    ref = pd.to_numeric(df_g["Valor Referencia"], errors='coerce').fillna(0)
    pag = df_g["Pagado"].astype(bool)
    vp = mon[pag].sum()
    vpy = df_g.apply(lambda r: max(0, float(r["Valor Referencia"]) - float(r["Monto"])) if r["Pagado"] else max(float(r["Valor Referencia"]), float(r["Monto"])), axis=1).sum()
    fb = it - vp
    return it, vp, vpy, fb, it - (vp + vpy)

# --- 3. LOGIN (SIMPLIFICADO) ---
if not st.session_state.autenticado:
    # (Aquí va tu lógica de login habitual que ya tienes)
    # Solo asegúrate de setear st.session_state.usuario_id
    st.session_state.autenticado = True # Ejemplo para que entres directo al probar
    st.session_state.usuario_id = "tulicesar"
    st.session_state.u_nombre_completo = "Tulio Salcedo"

# --- 4. DASHBOARD ---
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
    
    # Arrastre de saldo automático
    i_prev = df_i_user[(df_i_user["Periodo"] == mes_ant) & (df_i_user["Año"] == anio_ant)]
    g_prev = df_g_user[(df_g_user["Periodo"] == mes_ant) & (df_g_user["Año"] == anio_ant)]
    saldo_auto = 0.0
    if not i_prev.empty:
        _, _, _, _, bf_pasado = calcular_metricas(g_prev, i_prev["Nomina"].sum(), i_prev["Otros"].sum(), i_prev["SaldoAnterior"].iloc[0])
        saldo_auto = float(bf_pasado)

    arrastrar = st.toggle(f"Arrastrar saldo de {mes_ant}", value=not i_prev.empty)
    d_act_i = df_i_user[(df_i_user["Periodo"] == mes_s) & (df_i_user["Año"] == anio_s)]
    s_in = st.number_input("Saldo Anterior", value=saldo_auto if arrastrar else (float(d_act_i["SaldoAnterior"].iloc[0]) if not d_act_i.empty else 0.0), disabled=arrastrar)
    n_in = st.number_input("Nómina", value=float(d_act_i["Nomina"].iloc[0] if not d_act_i.empty else 0.0))
    o_in = st.number_input("Otros", value=float(d_act_i["Otros"].iloc[0] if not d_act_i.empty else 0.0))

# --- HEADER ---
st.markdown(f"<h1>{mes_s} {anio_s}</h1>", unsafe_allow_html=True)

# --- 🚀 LÓGICA DE RECURRENCIA REAL (SIN INVENTAR DATOS) ---
df_mes = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()

# Solo si el usuario tiene recurrentes guardados en su HISTORIAL REAL
if not df_g_user.empty:
    # Buscamos los que el usuario marcó como Recurrente y nos quedamos con el último valor de referencia
    df_rec_master = df_g_user[df_g_user["Recurrente"] == True].sort_values(by=["Año"], ascending=False).drop_duplicates(subset=["Descripción"])
    
    # Comparamos con lo que hay en el mes actual para no duplicar
    nombres_actuales = df_mes["Descripción"].tolist() if not df_mes.empty else []
    faltantes = df_rec_master[~df_rec_master["Descripción"].isin(nombres_actuales)].copy()
    
    if not faltantes.empty:
        faltantes["Pagado"] = False
        faltantes["Monto"] = 0
        df_mes = pd.concat([df_mes, faltantes], ignore_index=True)

# Limpieza de columnas para el editor
df_v = df_mes.reset_index(drop=True)
for c in ["Año", "Periodo", "Usuario"]:
    if c in df_v.columns: df_v = df_v.drop(columns=[c])

config_c = {
    "Categoría": st.column_config.SelectboxColumn("Categoría", options=["Hogar", "Salud", "Transporte", "Impuestos", "Obligaciones", "Servicios", "Otros"], required=True),
    "Monto": st.column_config.NumberColumn("Monto", format="$ %,d"),
    "Valor Referencia": st.column_config.NumberColumn("Valor Referencia", format="$ %,d"),
    "Pagado": st.column_config.CheckboxColumn("¿Pagado?"),
    "Recurrente": st.column_config.CheckboxColumn("Movimiento Recurrente")
}
df_ed = st.data_editor(df_v, column_config=config_c, use_container_width=True, hide_index=True, num_rows="dynamic")

# MÉTRICAS
it, vp, vpy, fb, bf = calcular_metricas(df_ed, n_in, o_in, s_in)
c1, c2, c3, c4, c5 = st.columns(5)
def f_c(v): return f"$ {float(v):,.0f}".replace(",", ".")
c1.metric("💵 Ingresos", f_c(it))
c2.metric("🏦 Fondos", f_c(fb))
c3.metric("✅ Pagado", f_c(vp))
c4.metric("⏳ Pendiente", f_c(vpy))
c5.metric("⚖️ Final", f_c(bf))

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
