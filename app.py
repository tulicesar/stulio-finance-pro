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
    
    /* HACER EL TEXTO DE LAS TABLAS MUCHO MÁS GRANDE */
    [data-testid="stDataEditor"] { font-size: 1.4rem !important; }
    [data-testid="stDataEditor"] div { font-size: 1.4rem !important; }
    [data-testid="stDataEditor"] input { font-size: 1.4rem !important; }
    
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
            except: pass
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
        try: df_oi = pd.read_excel(BASE_FILE, sheet_name="OtrosIngresos")
        except: df_oi = pd.DataFrame(columns=col_oi)
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

def generar_pdf_reporte(df_g_full, df_i_full, meses, titulo, anio):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    
    def head(canvas_obj, t, a):
        canvas_obj.setFillColor(colors.white); canvas_obj.rect(0, 0, 612, 792, fill=1)
        canvas_obj.setFillColor(HexColor("#1a1d21"))
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(50, 765, "My FinanceApp")
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(50, 750, "by Stulio Designs")
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.drawRightString(560, 760, f"{t} - {a}")
        canvas_obj.setStrokeColor(HexColor("#d4af37"))
        canvas_obj.line(50, 740, 560, 740)
        return 710

    y = head(c, titulo, anio)
    
    for m in meses:
        i_m = df_i_full[(df_i_full["Periodo"] == m) & (df_i_full["Año"] == anio) & (df_i_full["Usuario"] == st.session_state.usuario_id)]
        g_m = df_g_full[(df_g_full["Periodo"] == m) & (df_g_full["Año"] == anio) & (df_g_full["Usuario"] == st.session_state.usuario_id)]
        s_ant_m = i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0.0
        it_m, vp_m, vpy_m, _, bf_m, _ = calcular_metricas(g_m, i_m["Nomina"].sum() if not i_m.empty else 0, i_m["Otros"].sum() if not i_m.empty else 0, s_ant_m)
        
        if y < 150: c.showPage(); y = head(c, titulo, anio)
        c.setFillColor(HexColor("#f0f2f6")); c.rect(50, y-60, 510, 65, fill=1, stroke=0)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(60, y-15, f"MES: {m}")
        c.setFont("Helvetica", 9); c.drawString(60, y-30, f"Ingresos: $ {it_m:,.0f} | Pagado: $ {vp_m:,.0f} | Pendiente: $ {vpy_m:,.0f}")
        c.setFillColor(HexColor("#d4af37")); c.drawString(60, y-45, f"AHORRO FINAL: $ {bf_m:,.0f}")
        y -= 85
        if not g_m.empty:
            c.setFillColor(HexColor("#1a1d21")); c.setFont("Helvetica-Bold", 8)
            c.drawString(60, y, "CATEGORÍA"); c.drawString(160, y, "DESCRIPCIÓN"); c.drawRightString(480, y, "MONTO"); c.drawRightString(540, y, "PAGADO")
            c.line(50, y-5, 560, y-5); y -= 15
            c.setFont("Helvetica", 8); c.setFillColor(colors.black)
            for _, fila in g_m.iterrows():
                if y < 50: c.showPage(); y = head(c, titulo, anio); c.setFont("Helvetica", 8)
                c.drawString(60, y, str(fila["Categoría"])); c.drawString(160, y, str(fila["Descripción"])[:45]); c.drawRightString(480, y, f"{fila['Monto']:,.0f}"); c.drawRightString(540, y, "SI" if fila["Pagado"] else "NO"); y -= 12
            y -= 20
        else:
            y -= 25
    c.showPage(); c.save(); buf.seek(0)
    return buf

# --- 3. ACCESO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        try: st.image(LOGO_LOGIN, use_container_width=True)
        except: st.markdown("<h2 style='text-align: center; color:#d4af37;'>My FinanceApp</h2>", unsafe_allow_html=True)
        
        tab_in, tab_reg = st.tabs(["🔑 Login", "📝 Registro"])
        db_u = cargar_usuarios()
        with tab_in:
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.button("Iniciar Sesión", use_container_width=True):
                if u in db_u and db_u[u]["pass"] == p:
                    st.session_state.autenticado = True
                    st.session_state.usuario_id = u
                    st.session_state.u_nombre_completo = db_u[u].get("nombre", u)
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
        with tab_reg:
            rn = st.text_input("Nombre"); ru = st.text_input("ID"); rp = st.text_input("Pass", type="password")
            if st.button("Crear Cuenta"):
                db_u[ru] = {"pass": rp, "nombre": rn}; guardar_usuarios(db_u); st.success("Creado con éxito")
    st.stop()

# --- 4. PRE-PROCESAMIENTO ---
df_g_raw, df_i_raw, df_oi_raw = cargar_bd()
u_id = st.session_state.usuario_id

df_g_user = df_g_raw[df_g_raw["Usuario"] == u_id].copy()
df_i_user = df_i_raw[df_i_raw["Usuario"] == u_id].copy()
df_oi_user = df_oi_raw[df_oi_raw["Usuario"] == u_id].copy()

periodos = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# --- 5. SIDEBAR ---
with st.sidebar:
    try:
        st.image(LOGO_SIDEBAR, use_container_width=True)
    except:
        st.markdown("### 💰 My FinanceApp")

    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2025, 2026], index=1)
    mes_s = st.selectbox("Mes Actual", periodos, index=datetime.now().month-1)
    
    idx = periodos.index(mes_s); m_ant = periodos[idx-1] if idx>0 else periodos[11]; a_ant = anio_s if idx>0 else anio_s-1
    i_ant = df_i_user[(df_i_user["Periodo"]==m_ant) & (df_i_user["Año"]==a_ant)]
    g_ant = df_g_user[(df_g_user["Periodo"]==m_ant) & (df_g_user["Año"]==a_ant)]
    s_sug = 0.0
    if not i_ant.empty:
        *_, bf_ant, _ = calcular_metricas(g_ant, i_ant["Nomina"].sum(), i_ant["Otros"].sum(), i_ant["SaldoAnterior"].iloc[0])
        s_sug = float(bf_ant)

    st.divider()
    arr_on = st.toggle(f"Arrastrar de {m_ant}", value=not i_ant.empty)
    
    # Inputs normales sin formato de texto para evitar el error
    s_in = st.number_input("Saldo Anterior ($)", value=s_sug if arr_on else 0.0)
    n_in = st.number_input("Ingresos Fijos (Sueldo) ($)", value=float(df_i_user[(df_i_user["Periodo"]==mes_s) & (df_i_user["Año"]==anio_s)]["Nomina"].iloc[0] if not df_i_user[(df_i_user["Periodo"]==mes_s) & (df_i_user["Año"]==anio_s)].empty else 0.0))
    
    # Placeholder para recibir el dato en vivo y formatearlo como texto (evita error)
    placeholder_otros = st.empty()

    st.divider()
    st.subheader("📑 Extracto Mensual")
    col_pdf, col_xls = st.columns(2)
    with col_pdf:
        if st.button("📄 PDF"):
            pdf = generar_pdf_reporte(df_g_user, df_i_user, [mes_s], f"Extracto {mes_s}", anio_s)
            st.download_button("Descargar PDF", pdf, f"Extracto_{mes_s}.pdf")
    
    with col_xls:
        df_export = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()
        buf_xls = BytesIO()
        df_export.to_excel(buf_xls, index=False)
        st.download_button("📊 Excel", buf_xls.getvalue(), file_name=f"Extracto_{mes_s}.xlsx")
    
    st.subheader("⚖️ Balances Semestrales")
    if st.button("📥 Semestre 1 (Ene-Jun)"):
        pdf1 = generar_pdf_reporte(df_g_user, df_i_user, periodos[0:6], "S1", anio_s)
        st.download_button("Bajar S1.pdf", pdf1, "S1.pdf")
    if st.button("📥 Semestre 2 (Jul-Dic)"):
        pdf2 = generar_pdf_reporte(df_g_user, df_i_user, periodos[6:12], "S2", anio_s)
        st.download_button("Bajar S2.pdf", pdf2, "S2.pdf")

    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 6. CUERPO PRINCIPAL ---
try: st.image(LOGO_APP_H, use_container_width=True)
except: pass
st.markdown(f"## {mes_s} {anio_s}")

# CONFIGURACIÓN PARA QUE LAS TABLAS MUESTREN MONEDA
formato_dinero = st.column_config.NumberColumn(format="$ %,d")

st.markdown("### 📝 Registro de Gastos")
df_mes_g = df_g_user[(df_g_user["Periodo"] == mes_s) & (df_g_user["Año"] == anio_s)].copy()
df_ed_g = st.data_editor(
    df_mes_g.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"]).reset_index(drop=True), 
    use_container_width=True, 
    num_rows="dynamic",
    column_config={"Monto": formato_dinero, "Valor Referencia": formato_dinero}
)

st.markdown("### 💰 Registro Otros Ingresos (Adicionales)")
df_mes_oi = df_oi_user[(df_oi_user["Periodo"] == mes_s) & (df_oi_user["Año"] == anio_s)].copy()
df_ed_oi = st.data_editor(
    df_mes_oi.reindex(columns=["Descripción", "Monto"]).reset_index(drop=True), 
    use_container_width=True, 
    num_rows="dynamic",
    column_config={"Monto": formato_dinero}
)

# Limpiar posibles strings antes de sumar
df_ed_g["Monto"] = pd.to_numeric(df_ed_g["Monto"], errors="coerce").fillna(0.0)
df_ed_g["Valor Referencia"] = pd.to_numeric(df_ed_g["Valor Referencia"], errors="coerce").fillna(0.0)
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0.0)

# CÁLCULO EN TIEMPO REAL
otros_total_vivo = float(df_ed_oi["Monto"].sum())

# Actualizamos el sidebar con un TEXT_INPUT de solo lectura formateado (esto elimina el error de formato)
texto_otros_formateado = f"$ {otros_total_vivo:,.0f}".replace(",", ".")
placeholder_otros.text_input("Otros (Calculado)", value=texto_otros_formateado, disabled=True)

it, vp, vpy, fondos_act, saldo_fin, ahorro_p = calcular_metricas(df_ed_g, n_in, otros_total_vivo, s_in)

st.divider()
m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f'<div class="card"><div class="card-label">INGRESOS</div><div class="card-value">$ {it:,.0f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="card"><div class="card-label">PAGADO</div><div class="card-value" style="color:#2ecc71;">$ {vp:,.0f}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="card"><div class="card-label">PENDIENTE</div><div class="card-value" style="color:#e74c3c;">$ {vpy:,.0f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="card"><div class="card-label">FONDOS ACTUALES</div><div class="card-value" style="color:#2575fc;">$ {fondos_act:,.0f}</div></div>', unsafe_allow_html=True)
m5.markdown(f'<div class="card"><div class="card-label">AHORRO FINAL</div><div class="card-value" style="color:#d4af37;">$ {saldo_fin:,.0f}</div></div>', unsafe_allow_html=True)

# --- 7. ANÁLISIS ---
st.markdown("### 📊 Análisis")
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
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=ahorro_p, number={'suffix': "%", 'font':{'color':'#d4af37'}}, gauge={'axis':{'range':[0,100]},'bar':{'color':"white"},'bgcolor':"#1f2630",'steps':[{'range':[0,20],'color':'#ff4b4b'},{'range':[50,100],'color':'#00d26a'}],'threshold':{'line':{'color':"#d4af37",'width':6},'thickness':0.85,'value':ahorro_p}}))
    gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=50,b=0,l=0,r=0))
    st.plotly_chart(gauge, use_container_width=True)

with c3:
    st.markdown("#### Estado Real del Dinero")
    pie = go.Figure(data=[go.Pie(labels=['Pagado', 'Pendiente', 'Ahorro'], values=[vp, vpy, saldo_fin], hole=.65, marker_colors=['#2ecc71', '#e74c3c', '#d4af37'], textinfo='percent+label')])
    pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=380, margin=dict(t=0,b=0,l=0,r=0))
    st.plotly_chart(pie, use_container_width=True)

if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS"):
    df_g_final = pd.concat([df_g_raw[~((df_g_raw["Periodo"]==mes_s)&(df_g_raw["Año"]==anio_s)&(df_g_raw["Usuario"]==u_id))], df_ed_g.assign(Periodo=mes_s, Año=anio_s, Usuario=u_id)], ignore_index=True)
    df_oi_final = pd.concat([df_oi_raw[~((df_oi_raw["Periodo"]==mes_s)&(df_oi_raw["Año"]==anio_s)&(df_oi_raw["Usuario"]==u_id))], df_ed_oi.assign(Periodo=mes_s, Año=anio_s, Usuario=u_id)], ignore_index=True)
    df_i_final = pd.concat([df_i_raw[~((df_i_raw["Periodo"]==mes_s)&(df_i_raw["Año"]==anio_s)&(df_i_raw["Usuario"]==u_id))], pd.DataFrame([{"Año":anio_s, "Periodo":mes_s, "SaldoAnterior":s_in, "Nomina":n_in, "Otros":otros_total_vivo, "Usuario":u_id}])], ignore_index=True)
    
    with pd.ExcelWriter(BASE_FILE) as w:
        df_g_final.to_excel(w, sheet_name="Gastos", index=False)
        df_i_final.to_excel(w, sheet_name="Ingresos", index=False)
        df_oi_final.to_excel(w, sheet_name="OtrosIngresos", index=False)
    st.balloons(); st.rerun()
