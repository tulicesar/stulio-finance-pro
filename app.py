import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
import re
from io import BytesIO
from datetime import datetime
import pytz
from supabase import create_client, Client

# --- 0. CONEXION A SUPABASE ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error en Secrets de Supabase.")

# --- 1. CONFIGURACION ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

USER_DB = "usuarios.json"
LOGO_LOGIN = "logoapp 1.png"
LOGO_SIDEBAR = "logoapp 2.png" 
LOGO_APP_H = "LOGOapp horizontal.png" 

# Lista sin tildes para evitar errores de encoding
LISTA_CATEGORIAS = ["Alimentacion", "Cuidado Personal", "Educacion", "Entretenimiento", "Hogar", "Impuestos", "Inversiones", "Mascotas", "Obligaciones Financieras", "Otros", "Regalos", "Salud", "Seguros", "Servicios", "Suscripciones", "Transporte"]

st.markdown("""<style>
    .stApp { background: #0e1117; color: #dee2e6; }
    .card { background-color: #ffffff; border-radius: 12px; padding: 15px; color: #1a1d21; text-align: center; border-bottom: 4px solid #d4af37; }
    .card-label { font-size: 0.8rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #1a1d21; }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #d4af37; color: black; }
    h2, h3 { color: #d4af37 !important; font-weight: bold !important; }
</style>""", unsafe_allow_html=True)

# --- 2. FUNCIONES MOTOR ---
def format_moneda(valor):
    try: return f"$ {int(float(valor)):,.0f}".replace(",", ".")
    except: return "$ 0"

def parse_moneda(texto):
    clean = re.sub(r'[^\d]', '', str(texto))
    return float(clean) if clean else 0.0

def cargar_usuarios():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            try: return json.load(f)
            except: pass
    return {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}

# --- 3. CARGA DE DATOS (REPARADO SIN TILDES) ---
def cargar_bd():
    cols_g = ["Anio", "Periodo", "Categoria", "Descripcion", "Monto", "Referencia", "Pagado", "Recurrente", "Usuario"]
    cols_i = ["Anio", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    cols_oi = ["Anio", "Periodo", "Descripcion", "Monto", "Usuario"]

    try:
        rg = supabase.table("gastos").select("*").execute()
        ri = supabase.table("ingresos_base").select("*").execute()
        roi = supabase.table("otros_ingresos").select("*").execute()

        # Mapeo exacto de tus columnas de Supabase (minúsculas) a la App (Mayúsculas sin tildes)
        df_g = pd.DataFrame(rg.data).rename(columns={"anio":"Anio","periodo":"Periodo","categoria":"Categoria","descripcion":"Descripcion","monto":"Monto","valor_referencia":"Referencia","pagado":"Pagado","recurrente":"Recurrente","usuario_id":"Usuario"}) if rg.data else pd.DataFrame(columns=cols_g)
        df_i = pd.DataFrame(ri.data).rename(columns={"anio":"Anio","periodo":"Periodo","saldo_anterior":"SaldoAnterior","nomina":"Nomina","otros":"Otros","usuario_id":"Usuario"}) if ri.data else pd.DataFrame(columns=cols_i)
        df_oi = pd.DataFrame(roi.data).rename(columns={"anio":"Anio","periodo":"Periodo","descripcion":"Descripcion","monto":"Monto","usuario_id":"Usuario"}) if roi.data else pd.DataFrame(columns=cols_oi)

        # Asegurar columnas para evitar KeyError
        for df, cols in [(df_g, cols_g), (df_i, cols_i), (df_oi, cols_oi)]:
            for c in cols:
                if c not in df.columns: df[c] = None

        return df_g, df_i, df_oi
    except Exception as e:
        # Esto nos dirá el error real en la pantalla de la app
        error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        st.error(f"Error real detectado: {error_msg}")
        return pd.DataFrame(columns=cols_g), pd.DataFrame(columns=cols_i), pd.DataFrame(columns=cols_oi)

# --- 4. ACCESO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN): st.image(LOGO_LOGIN, use_container_width=True)
        db_u = cargar_usuarios()
        u, p = st.text_input("Usuario"), st.text_input("Pass", type="password")
        if st.button("Ingresar"):
            if u in db_u and db_u[u]["pass"] == p:
                st.session_state.autenticado, st.session_state.usuario_id, st.session_state.u_nombre_completo = True, u, db_u[u]["nombre"]
                st.rerun()
            else: st.error("Credenciales incorrectas")
    st.stop()

# --- 5. LOGICA DASHBOARD ---
u_id = st.session_state.usuario_id
df_g_full, df_i_full, df_oi_full = cargar_bd()

with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Anio", [2025, 2026, 2027], index=1)
    meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_s = st.selectbox("Mes Actual", meses_lista, index=datetime.now().month-1)
    
    # Filtro de ingresos (Sin tildes en las claves)
    i_m_act = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Anio"]==anio_s) & (df_i_full["Usuario"]==u_id)]
    
    val_s_init = i_m_act["SaldoAnterior"].iloc[0] if not i_m_act.empty else 0.0
    val_n_init = i_m_act["Nomina"].iloc[0] if not i_m_act.empty else 0.0
    
    s_in = parse_moneda(st.text_input("Saldo Anterior", value=format_moneda(val_s_init)))
    n_in = parse_moneda(st.text_input("Ingreso Fijo", value=format_moneda(val_n_init)))
    if st.button("Salir"): st.session_state.autenticado = False; st.rerun()

if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestion de {mes_s} {anio_s}")

# Editores de datos
df_ed_g = st.data_editor(df_g_full[(df_g_full["Periodo"] == mes_s) & (df_g_full["Anio"] == anio_s) & (df_g_full["Usuario"] == u_id)].reindex(columns=["Categoria", "Descripcion", "Monto", "Referencia", "Pagado", "Recurrente"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", column_config={"Categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS)})
df_ed_oi = st.data_editor(df_oi_full[(df_oi_full["Periodo"] == mes_s) & (df_oi_full["Anio"] == anio_s) & (df_oi_full["Usuario"] == u_id)].reindex(columns=["Descripcion", "Monto"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic")

# Calculos
otr_v = float(df_ed_oi["Monto"].sum()) if not df_ed_oi.empty else 0.0
g_pagado = df_ed_g[df_ed_g["Pagado"]==True]["Monto"].sum() if not df_ed_g.empty else 0
g_pend = df_ed_g[df_ed_g["Pagado"]==False]["Monto"].sum() if not df_ed_g.empty else 0
it = s_in + n_in + otr_v
bf = it - g_pagado - g_pend

# KPIs
st.divider()
c1, c2, c3, c4, c5 = st.columns(5)
tarj = [("INGRESOS", it, "black"), ("PAGADO", g_pagado, "green"), ("PENDIENTE", g_pend, "red"), ("DISPONIBLE", it-g_pagado, "blue"), ("SALDO FINAL", bf, "#d4af37")]
for i, (l, v, color) in enumerate(tarj): 
    with [c1, c2, c3, c4, c5][i]:
        st.markdown(f'<div class="card"><div class="card-label">{l}</div><div class="card-value" style="color:{color}">$ {v:,.0f}</div></div>', unsafe_allow_html=True)

# --- 6. GUARDAR ---
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS", use_container_width=True):
    try:
        supabase.table("gastos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
        supabase.table("otros_ingresos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
        supabase.table("ingresos_base").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()

        g_save = df_ed_g.assign(periodo=mes_s, anio=anio_s, usuario_id=u_id).rename(columns={"Categoria":"categoria","Descripcion":"descripcion","Monto":"monto","Referencia":"valor_referencia","Pagado":"pagado","Recurrente":"recurrente"}).to_dict(orient="records")
        oi_save = df_ed_oi.assign(periodo=mes_s, anio=anio_s, usuario_id=u_id).rename(columns={"Descripcion":"descripcion","Monto":"monto"}).to_dict(orient="records")
        i_save = {"anio": anio_s, "periodo": mes_s, "saldo_anterior": s_in, "nomina": n_in, "otros": otr_v, "usuario_id": u_id}

        if g_save: supabase.table("gastos").insert(g_save).execute()
        if oi_save: supabase.table("otros_ingresos").insert(oi_save).execute()
        supabase.table("ingresos_base").insert(i_save).execute()

        st.balloons(); st.success("Sincronizado"); st.rerun()
    except Exception as e: st.error(f"Error al guardar. Revisa los datos.")
