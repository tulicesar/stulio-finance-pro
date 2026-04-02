import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from io import BytesIO
from datetime import datetime
import math

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

LOGO_LOGIN = "logoapp 1.png"
LOGO_SIDEBAR = "logoapp 2.png" 
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
    [data-testid="stDataEditor"] { font-size: 1.4rem !important; }
    .card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #1a1d21; text-align: center; border-bottom: 4px solid #d4af37;
    }
    .card-label { font-size: 0.8rem; color: #6c757d; font-weight: 800; text-transform: uppercase; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #1a1d21; margin: 3px 0; }
    .legend-bar {
        padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; 
        font-size: 0.9rem; font-weight: bold; color: #1a1d21; 
        display: flex; justify-content: space-between; align-items: center;
    }
    section[data-testid="stSidebar"] { background: rgba(0,0,0,0.8) !important; backdrop-filter: blur(15px); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #d4af37; color: black; border: none; }
    h2, h3 { color: #d4af37 !important; font-weight: bold !important; }
    
    /* Estilo para la caja de métricas del velocímetro */
    .metric-box-gauge {
        background: #f8f9fa; border: 1px solid #d4af37; border-radius: 10px;
        padding: 10px; color: #1a1d21; font-size: 0.85rem; line-height: 1.4;
        text-align: left; font-weight: bold; margin-top: -20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
def cargar_usuarios():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            try: return json.load(f)
            except: pass
    return {"tulicesar": {"pass": "Thulli.07", "nombre": "Tulio Salcedo"}}

def guardar_usuarios(db):
    with open(USER_DB, "w") as f: json.dump(db, f, indent=4)

def cargar_bd():
    col_g = ["Año", "Periodo", "Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente", "Usuario"]
    col_i = ["Año", "Periodo", "SaldoAnterior", "Nomina", "Otros", "Usuario"]
    col_oi = ["Año", "Periodo", "Descripción", "Monto", "Usuario"]
    if not os.path.exists(BASE_FILE): return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)
    try:
        df_g = pd.read_excel(BASE_FILE, sheet_name="Gastos")
        df_i = pd.read_excel(BASE_FILE, sheet_name="Ingresos")
        try: df_oi = pd.read_excel(BASE_FILE, sheet_name="OtrosIngresos")
        except: df_oi = pd.DataFrame(columns=col_oi)
        return df_g, df_i, df_oi
    except: return pd.DataFrame(columns=col_g), pd.DataFrame(columns=col_i), pd.DataFrame(columns=col_oi)

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    vpy = df_g[df_g["Pagado"] == False]["Valor Referencia"].sum() if not df_g.empty else 0
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), bf, ahorro_p

# --- 3. ACCESO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN): st.image(LOGO_LOGIN, use_container_width=True)
        u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
        if st.button("Ingresar", use_container_width=True):
            db_u = cargar_usuarios()
            if u in db_u and db_u[u]["pass"] == p:
                st.session_state.autenticado, st.session_state.usuario_id, st.session_state.u_nombre_completo = True, u, db_u[u]["nombre"]
                st.rerun()
            else: st.error("❌ Credenciales incorrectas")
    st.stop()

# --- 4. SIDEBAR ---
u_id = st.session_state.usuario_id
df_g_full, df_i_full, df_oi_full = cargar_bd()

with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    mes_s = st.selectbox("Mes Actual", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=datetime.now().month-1)
    
    i_m = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s) & (df_i_full["Usuario"]==u_id)]
    s_in = st.number_input("Saldo Anterior", value=float(i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0.0))
    n_in = st.number_input("Sueldo Fijo", value=float(i_m["Nomina"].iloc[0] if not i_m.empty else 0.0))
    
    st.divider(); st.subheader("📑 Extracto del Mes")
    if st.button("Bajar PDF"): pass # Aquí iría tu función de PDF
    st.subheader("⚖️ Balances Proyectados")
    if st.button("Semestre 1"): pass
    if st.button("Semestre 2"): pass
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 5. CUERPO ---
if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s} {anio_s}")

df_mes_g = df_g_full[(df_g_full["Periodo"] == mes_s) & (df_g_full["Año"] == anio_s) & (df_g_full["Usuario"] == u_id)].copy()
df_ed_g = st.data_editor(df_mes_g.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic")

df_mes_oi = df_oi_full[(df_oi_full["Periodo"] == mes_s) & (df_oi_full["Año"] == anio_s) & (df_oi_full["Usuario"] == u_id)].copy()
df_ed_oi = st.data_editor(df_mes_oi.reindex(columns=["Descripción", "Monto"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic")

df_ed_g["Monto"] = pd.to_numeric(df_ed_g["Monto"], errors="coerce").fillna(0)
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0)
otr_sum = float(df_ed_oi["Monto"].sum())
it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_sum, s_in)

# --- 6. NUEVA INFOGRAFÍA OPCIÓN A ---
st.markdown("### 📊 Análisis de Distribución y Rendimiento")
inf1, inf2, inf3 = st.columns([1, 1.2, 1])

with inf1:
    st.markdown("#### Desglose de Gastos")
    t_df = df_ed_g.copy(); t_df['V'] = t_df.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not t_df.empty and t_df['V'].sum() > 0:
        fig1 = px.pie(t_df, values='V', names='Categoría', hole=0.7, color_discrete_map=COLOR_MAP)
        fig1.update_layout(showlegend=False, height=250, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig1, use_container_width=True)

with inf2:
    st.markdown("#### Eficiencia de Ahorro Premium")
    val = max(0, min(ahorro_p, 100))
    # Cálculo aguja
    phi = math.radians(180 - (val / 100 * 180))
    x_pivot, y_pivot = 0.5, 0.42
    x_tip = x_pivot + 0.35 * math.cos(phi)
    y_tip = y_pivot + 0.35 * math.sin(phi)
    
    # Texto de estado
    estado = "EXCELENTE" if val > 70 else "BUENO" if val > 30 else "ATENCIÓN"
    col_est = "#2ecc71" if val > 70 else "#f1c40f" if val > 30 else "#e74c3c"

    fig2 = go.Figure()
    fig2.add_trace(go.Indicator(
        mode="gauge", value=val,
        gauge={
            'axis': {'range': [0, 100], 'tickvals': [0, 20, 40, 60, 80, 100]},
            'bar': {'color': "rgba(0,0,0,0)"},
            'bgcolor': "white", 'borderwidth': 2, 'bordercolor': "#ccc",
            'steps': [
                {'range': [0, 30], 'color': "#ffcccc"},
                {'range': [30, 70], 'color': "#fff3cd"},
                {'range': [70, 100], 'color': "#d1e7dd"}
            ]
        }
    ))
    # Aguja y Centro
    fig2.add_annotation(text=f"{val:.0f}%", x=x_pivot, y=y_pivot, showarrow=False, font=dict(color="#d4af37", size=50, weight="bold"))
    fig2.add_annotation(text=estado, x=x_pivot, y=y_pivot+0.3, showarrow=False, font=dict(color=col_est, size=20, weight="bold"))
    fig2.add_shape(type="line", x0=x_pivot, y0=y_pivot, x1=x_tip, y1=y_tip, line=dict(color="#d4af37", width=5))
    fig2.add_shape(type="circle", x0=x_pivot-0.02, y0=y_pivot-0.02, x1=x_pivot+0.02, y1=y_pivot+0.02, fillcolor="#d4af37", line_color="#d4af37")
    
    fig2.update_layout(height=300, margin=dict(t=30,b=0,l=20,r=20))
    st.plotly_chart(fig2, use_container_width=True)
    
    # CAJA DE MÉTRICAS GRABADA
    st.markdown(f"""
        <div class="metric-box-gauge">
            INGRESOS TOTALES (EST.): $ {it:,.0f}<br>
            GASTOS TOTALES (EST.): $ {vp+vpy:,.0f}<br>
            AHORRO PROYECTADO: $ {bf:,.0f}
        </div>
    """, unsafe_allow_html=True)

with inf3:
    st.markdown("#### Estado Real del Dinero")
    fig3 = go.Figure(data=[go.Pie(labels=['Pagado', 'Pendiente', 'Ahorro'], values=[vp, vpy, bf], hole=.7, marker_colors=['#2ecc71', '#e74c3c', '#d4af37'])])
    fig3.update_layout(showlegend=False, height=250, margin=dict(t=0,b=0,l=0,r=0))
    st.plotly_chart(fig3, use_container_width=True)

# ESPACIO PARA BAJAR EL BOTÓN
st.markdown("<br>" * 15, unsafe_allow_html=True)
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS", use_container_width=True):
    # (Lógica de guardado a Excel aquí...)
    st.balloons(); st.rerun()
