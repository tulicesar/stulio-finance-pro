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

# Rutas de archivos
LOGO_LOGIN = "logoapp 1.png"
LOGO_SIDEBAR = "logoapp 2.jpg" 
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
    header { background-color: rgba(0,0,0,0) !important; }
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
    return {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}

def guardar_usuarios(db):
    with open(USER_DB, "w") as f: json.dump(db, f, indent=4)

def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    col_oi = ["Año", "Periodo", "Descripción", "Monto", "Usuario"]
    
    if not os.path.exists(BASE_FILE): 
        return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)
    
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        try:
            df_oi = pd.read_excel(BASE_FILE, sheet_name="OtrosIngresos")
        except:
            df_oi = pd.DataFrame(columns=col_oi)
        
        df_g["Pagado"] = df_g["Pagado"].fillna(False).astype(bool)
        return df_g, df_i, df_oi
    except:
        return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum() if not df_g.empty else 0
    saldo_fin = it - vp - vpy
    ahorro_p = (saldo_fin / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), saldo_fin, ahorro_p

# --- 3. ACCESO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN): st.image(LOGO_LOGIN, use_container_width=True)
        tab_in, tab_reg = st.tabs(["🔑 Login", "📝 Registro"])
        db_u = cargar_usuarios()
        with tab_in:
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.button("Iniciar Sesión", use_container_width=True):
                if u in db_u and db_u[u]["pass"] == p:
                    st.session_state.autenticado, st.session_state.usuario_id = True, u
                    st.session_state.u_nombre_completo = db_u[u].get("nombre", u); st.rerun()
        with tab_reg:
            rn, ru, rp = st.text_input("Nombre"), st.text_input("ID"), st.text_input("Pass", type="password")
            if st.button("Crear Cuenta"):
                db_u[ru] = {"pass": rp, "nombre": rn}; guardar_usuarios(db_u); st.success("Creado")
    st.stop()

# --- 4. DASHBOARD ---
df_g_raw, df_i_raw, df_oi_raw = cargar_bd()
u_id = st.session_state.usuario_id
df_g_user = df_g_raw[df_g_raw["Usuario"] == u_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == u_id].copy()
df_oi_user = df_oi_raw[df_oi_raw["Usuario"] == u_id].copy()

periodos = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

with st.sidebar:
    # 1. LOGO SIDEBAR RESTAURADO
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    mes_s = st.selectbox("Mes Actual", periodos, index=datetime.now().month-1)
    
    # Arrastre automático
    idx = periodos.index(mes_s); m_ant = periodos[idx-1] if idx>0 else periodos[11]; a_ant = anio_s if idx>0 else anio_s-1
    i_ant = df_i_user[(df_i_user["Periodo"]==m_ant) & (df_i_user["Año"]==a_ant)]
    g_ant = df_g_user[(df_g_user["Periodo"]==m_ant) & (df_g_user["Año"]==a_ant)]
    s_sug = 0.0
    if not i_ant.empty:
        *_, bf_ant, _ = calcular_metricas(g_ant, i_ant["Nomina"].sum(), i_ant["Otros"].sum(), i_ant["SaldoAnterior"].iloc[0])
        s_sug = float(bf_ant)

    st.divider()
    arr_on = st.toggle(f"Arrastrar de {m_ant}", value=not i_ant.empty)
    s_in = st.number_input("Saldo Anterior", value=s_sug if arr_on else 0.0)
    n_in = st.number_input("Ingresos Fijos (Sueldo)", value=float(df_i_user[df_i_user["Periodo"]==mes_s]["Nomina"].iloc[0] if not df_i_user[df_i_user["Periodo"]==mes_s].empty else 0.0))
    
    # 2. SUMA EXCLUSIVA DEL MES PARA "OTROS"
    oi_mes_db = df_oi_user[(df_oi_user["Periodo"] == mes_s) & (df_oi_user["Año"] == anio_s)]
    otros_calc = oi_mes_db["Monto"].sum()
    st.number_input("Otros (Calculado)", value=float(otros_calc), disabled=True)

    # 3. REPORTES RESTAURADOS
    st.divider(); st.subheader("📑 Extracto Mensual")
    c_pdf, c_xls = st.columns(2)
    with c_pdf: st.button("📄 PDF")
    with c_xls:
        out = BytesIO()
        df_g_user[df_g_user["Periodo"]==mes_s].to_excel(out, index=False)
        st.download_button("📊 Excel", out.getvalue(), f"Extracto_{mes_s}.xlsx")
    
    st.subheader("⚖️ Balances Semestrales")
    st.button("📥 Semestre 1"); st.button("📥 Semestre 2")

    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 5. CUERPO ---
if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## {mes_s} {anio_s}")

st.markdown("### 📝 Registro de Gastos")
df_ed_g = st.data_editor(df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic")

st.markdown("### 💰 Registro Otros Ingresos (Adicionales)")
# Editor de otros ingresos del mes
df_ed_oi = st.data_editor(df_oi_user[(df_oi_user["Periodo"] == mes_s) & (df_oi_user["Año"] == anio_s)].reindex(columns=["Descripción", "Monto"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", key="oi_edit")

# Recalcular métricas con los datos en vivo del editor
it, vp, vpy, fondos_act, saldo_fin, ahorro_p = calcular_metricas(df_ed_g, n_in, df_ed_oi["Monto"].sum(), s_in)

st.divider()
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="card"><div class="card-label">INGRESOS</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card"><div class="card-label">PAGADO</div><div class="card-value" style="color:#2ecc71;">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="card"><div class="card-label">PENDIENTE</div><div class="card-value" style="color:#e74c3c;">$ {vpy:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="card"><div class="card-label">FONDOS ACTUALES</div><div class="card-value" style="color:#2575fc;">$ {fondos_act:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="card"><div class="card-label">AHORRO FINAL</div><div class="card-value" style="color:#d4af37;">$ {saldo_fin:,.0f}</div></div>', unsafe_allow_html=True)

# --- 6. ANÁLISIS ---
st.markdown("### 📊 Análisis de Gastos")
c1, c2, c3 = st.columns([1.5, 1, 1.2])
with c1:
    st.markdown("#### Desglose de Gastos")
    t_df = df_ed_g.copy(); t_df['V'] = t_df.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not t_df.empty and t_df['V'].sum() > 0:
        fig = px.pie(t_df, values='V', names='Categoría', color='Categoría', hole=0.6, color_discrete_map=COLOR_MAP)
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
        res = t_df.groupby("Categoría")['V'].sum().reset_index()
        for _, r in res.iterrows():
            st.markdown(f'<div class="legend-bar" style="background:{COLOR_MAP.get(r["Categoría"],"#eee")}">{r["Categoría"]} <span>$ {r["V"]:,.0f}</span></div>', unsafe_allow_html=True)

with c2:
    st.markdown("#### Eficiencia de Ahorro")
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=ahorro_p, number={'suffix': "%", 'font':{'color':'#d4af37'}}, gauge={'axis':{'range':[0,100]},'bar':{'color':"white"},'bgcolor':"#1f2630",'steps':[{'range':[0,20],'color':'#ff4b4b'},{'range':[50,100],'color':'#00d26a'}]}))
    gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=50,b=0,l=0,r=0))
    st.plotly_chart(gauge, use_container_width=True)

with c3:
    st.markdown("#### Estado Real del Dinero")
    pie = go.Figure(data=[go.Pie(labels=['Pagado', 'Pendiente', 'Ahorro'], values=[vp, vpy, saldo_fin], hole=.65, marker_colors=['#2ecc71', '#e74c3c', '#d4af37'], textinfo='percent+label')])
    pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=380, margin=dict(t=0,b=0,l=0,r=0))
    st.plotly_chart(pie, use_container_width=True)

if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    # Limpiar y concatenar gastos
    df_g_final = pd.concat([df_g_raw[~((df_g_raw["Periodo"]==mes_s)&(df_g_raw["Año"]==anio_s)&(df_g_raw["Usuario"]==u_id))], df_ed_g.assign(Periodo=mes_s, Año=anio_s, Usuario=u_id)], ignore_index=True)
    # Limpiar y concatenar otros ingresos
    df_oi_final = pd.concat([df_oi_raw[~((df_oi_raw["Periodo"]==mes_s)&(df_oi_raw["Año"]==anio_s)&(df_oi_raw["Usuario"]==u_id))], df_ed_oi.assign(Periodo=mes_s, Año=anio_s, Usuario=u_id)], ignore_index=True)
    # Guardar ingresos base
    df_i_final = pd.concat([df_i_raw[~((df_i_raw["Periodo"]==mes_s)&(df_i_raw["Año"]==anio_s)&(df_i_raw["Usuario"]==u_id))], pd.DataFrame([{"Año":anio_s, "Periodo":mes_s, "SaldoAnterior":s_in, "Nomina":n_in, "Otros":df_ed_oi["Monto"].sum(), "Usuario":u_id}])], ignore_index=True)
    
    with pd.ExcelWriter(BASE_FILE) as w:
        df_g_final.to_excel(w, sheet_name="Gastos", index=False)
        df_i_final.to_excel(w, sheet_name="Ingresos", index=False)
        df_oi_final.to_excel(w, sheet_name="OtrosIngresos", index=False)
    st.balloons(); st.rerun()
