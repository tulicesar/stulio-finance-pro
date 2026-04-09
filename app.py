import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
import re
from io import BytesIO
from datetime import datetime
import math
import pytz 
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

# Conexión a Supabase
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Error conectando a Supabase. Revisa los Secrets.")
    st.stop()

LOGO_LOGIN = "logoapp 1.png"
LOGO_SIDEBAR = "logoapp 2.png" 
LOGO_APP_H = "LOGOapp horizontal.png" 
USER_DB = "usuarios.json"

LISTA_CATEGORIAS = [
    "Hogar", "Servicios", "Alimentación", "Transporte", 
    "Obligaciones Financieras", "Salud", "Educación", 
    "Cuidado Personal", "Mascotas", "Viajes y Recreación", 
    "Seguros", "Ahorro e Inversión", "Impuestos", "Otros"
]

COLOR_MAP = {
    "Hogar": "#FFB347", "Servicios": "#FFB347", "Alimentación": "#FDFD96",
    "Transporte": "#77B5FE", "Obligaciones Financieras": "#FF6961", 
    "Salud": "#B39EB5", "Educación": "#84b6f4", "Cuidado Personal": "#FFD1DC",
    "Mascotas": "#CFCFCF", "Viajes y Recreación": "#77DD77", 
    "Seguros": "#AEC6CF", "Ahorro e Inversión": "#d4af37", 
    "Impuestos": "#84b6f4", "Otros": "#77DD77"
}

st.markdown("""
    <style>
    header { background-color: rgba(0,0,0,0) !important; }
    .stApp { background: #0e1117; color: #dee2e6; }
    [data-testid="stDataEditor"] div { font-size: 2.0rem !important; }
    .stTabs [aria-selected="true"] { color: #d4af37 !important; border-bottom-color: #d4af37 !important; font-weight: bold; }
    .card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #1a1d21; text-align: center; border-bottom: 4px solid #d4af37;
        min-height: 100px; display: flex; flex-direction: column; justify-content: center;
    }
    .card-label { font-size: 0.8rem; color: #6c757d; font-weight: 800; text-transform: uppercase; line-height: 1.1; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #1a1d21; margin: 3px 0; }
    .legend-bar {
        padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; 
        font-size: 0.9rem; font-weight: bold; color: #1a1d21; 
        display: flex; justify-content: space-between; align-items: center;
    }
    section[data-testid="stSidebar"] { background: rgba(0,0,0,0.8) !important; backdrop-filter: blur(15px); }
    .stButton>button { border-radius: 10px; font-weight: bold; width: 100%; background-color: #d4af37; color: black; border: none; }
    h2, h3 { color: #d4af37 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS Y FORMATEO ---
def format_moneda(valor):
    """Convierte un número a formato string: $ 1.000.000"""
    try:
        n = int(float(valor))
        return f"$ {n:,.0f}".replace(",", ".")
    except:
        return "$ 0"

def parse_moneda(texto):
    """Limpia el string formateado para obtener el número puro"""
    if not texto: return 0.0
    clean = re.sub(r'[^\d]', '', str(texto))
    return float(clean) if clean else 0.0

def cargar_usuarios():
    """Carga los usuarios desde la tabla 'usuarios' en Supabase"""
    try:
        # 🌟 CONSULTA A SUPABASE 🌟
        res = supabase.table("usuarios").select("*").execute()
        # Mapeamos tus columnas: 'usuario_id', 'password' y 'nombre_completo'
        db_dict = {
            user['usuario_id']: {
                "pass": user['password'], 
                "nombre": user['nombre_completo']
            } for user in res.data
        }
        return db_dict
    except Exception as e:
        # Si la tabla está vacía o hay error, devolvemos un diccionario vacío
        return {}

# Nota: La función guardar_usuarios(db) se elimina porque ahora usaremos .upsert() directamente

@st.cache_data(ttl=5) # Cache corto para rapidez con Supabase
def cargar_bd(u_id):
    # Consultamos las tablas de movimientos
    r_g = supabase.table("gastos").select("*").eq("usuario_id", u_id).execute()
    r_i = supabase.table("ingresos_base").select("*").eq("usuario_id", u_id).execute()
    r_oi = supabase.table("otros_ingresos").select("*").eq("usuario_id", u_id).execute()
    
    df_g = pd.DataFrame(r_g.data) if r_g.data else pd.DataFrame(columns=["anio", "periodo", "categoria", "descripcion", "monto", "valor_referencia", "pagado", "recurrente", "usuario_id"])
    df_i = pd.DataFrame(r_i.data) if r_i.data else pd.DataFrame(columns=["anio", "periodo", "saldo_anterior", "nomina", "otros", "usuario_id"])
    df_oi = pd.DataFrame(r_oi.data) if r_oi.data else pd.DataFrame(columns=["anio", "periodo", "descripcion", "monto", "usuario_id"])
    
    # Renombramos para compatibilidad con el resto del código
    df_g = df_g.rename(columns={"anio":"Año", "periodo":"Periodo", "categoria":"Categoría", "descripcion":"Descripción", "monto":"Monto", "valor_referencia":"Valor Referencia", "pagado":"Pagado", "recurrente":"Movimiento Recurrente", "usuario_id":"Usuario"})
    df_i = df_i.rename(columns={"anio":"Año", "periodo":"Periodo", "saldo_anterior":"SaldoAnterior", "nomina":"Nomina", "otros":"Otros", "usuario_id":"Usuario"})
    df_oi = df_oi.rename(columns={"anio":"Año", "periodo":"Periodo", "descripcion":"Descripción", "monto":"Monto", "usuario_id":"Usuario"})
    
    # Aseguramos que el Año sea entero
    for df in [df_g, df_i, df_oi]:
        if "Año" in df.columns:
            df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(0).astype(int)
    
    return df_g, df_i, df_oi

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    if not df_g.empty:
        vpy = df_g[df_g["Pagado"] == False].apply(lambda x: x["Monto"] if x["Monto"] > 0 else x["Valor Referencia"], axis=1).sum()
    else:
        vpy = 0
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), bf, ahorro_p

# --- 3. REPORTE PDF (TU CÓDIGO ORIGINAL INTACTO) ---
def generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses, titulo, anio, u_id):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    nombre_usuario = st.session_state.get("u_nombre_completo", u_id)
    buf = BytesIO(); c = canvas.Canvas(buf, pagesize=letter)
    total_periodo_nomina, total_periodo_otros, total_periodo_gastos = 0, 0, 0

    def head(canvas_obj, t, a, user_name):
        canvas_obj.setFillColor(colors.white); canvas_obj.rect(0, 0, 612, 792, fill=1)
        canvas_obj.setFillColor(HexColor("#1a1d21")); canvas_obj.setFont("Helvetica-Bold", 16); canvas_obj.drawString(50, 765, "My FinanceApp")
        canvas_obj.setFont("Helvetica", 10); canvas_obj.drawString(50, 750, "by Stulio Designs")
        canvas_obj.setFont("Helvetica-BoldOblique", 9); canvas_obj.setFillColor(HexColor("#d4af37")); canvas_obj.drawString(50, 735, f"Usuario: {user_name}")
        canvas_obj.setFillColor(HexColor("#1a1d21")); canvas_obj.setFont("Helvetica-Bold", 12); canvas_obj.drawRightString(560, 760, f"{t} - {a}")
        canvas_obj.setStrokeColor(HexColor("#d4af37")); canvas_obj.line(50, 725, 560, 725)
        tz = pytz.timezone('America/Bogota'); fecha_gen = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
        canvas_obj.setFont("Helvetica", 7); canvas_obj.setFillColor(colors.grey); canvas_obj.drawString(50, 30, f"Documento generado el: {fecha_gen}")
        return 700

    y = head(c, titulo, anio, nombre_usuario)
    for m in meses:
        i_m = df_i_full[(df_i_full["Periodo"] == m) & (df_i_full["Año"] == anio) & (df_i_full["Usuario"] == u_id)]
        g_m = df_g_full[(df_g_full["Periodo"] == m) & (df_g_full["Año"] == anio) & (df_g_full["Usuario"] == u_id)]
        oi_m = df_oi_full[(df_oi_full["Periodo"] == m) & (df_oi_full["Año"] == anio) & (df_oi_full["Usuario"] == u_id)]
        s_ant, nom = (i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0), (i_m["Nomina"].iloc[0] if not i_m.empty else 0)
        otr_sum = oi_m["Monto"].sum() if not oi_m.empty else 0
        g_mensual_sum = g_m.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1).sum() if not g_m.empty else 0
        total_periodo_nomina += nom; total_periodo_otros += otr_sum; total_periodo_gastos += g_mensual_sum
        it, vp, vpy, _, bf, _ = calcular_metricas(g_m, nom, otr_sum, s_ant)
        label_pdf_ahorro = "SALDO A FAVOR" if bf >= 0 else "DÉFICIT"
        if y < 250: c.showPage(); y = head(c, titulo, anio, nombre_usuario)
        c.setFillColor(HexColor("#f8f9fa")); c.rect(50, y-55, 510, 60, fill=1, stroke=0)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(60, y-15, f"MES: {m}")
        c.setFont("Helvetica", 9); c.drawString(60, y-30, f"Ingresos: $ {it:,.0f} | Oblig. Pagadas: $ {vp:,.0f} | Oblig. Pendientes: $ {vpy:,.0f}")
        c.setFillColor(HexColor("#d4af37")); c.drawString(60, y-45, f"{label_pdf_ahorro} FINAL: $ {bf:,.0f}"); y -= 80
        c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.black); c.drawString(60, y, "RELACIÓN DE INGRESOS"); y -= 15
        c.setFont("Helvetica", 8); c.drawString(60, y, "Saldo Anterior"); c.drawRightString(480, y, f"$ {s_ant:,.0f}"); y -= 10
        c.drawString(60, y, "Nómina"); c.drawRightString(480, y, f"$ {nom:,.0f}"); y -= 5
        if not oi_m.empty:
            c.setStrokeColor(colors.lightgrey); c.line(60, y, 480, y); y -= 12
            c.setFont("Helvetica-BoldOblique", 7); c.setFillColor(colors.darkgrey); c.drawString(60, y, "Ingresos Variables"); y -= 10
            for _, r_oi in oi_m.iterrows():
                c.setFont("Helvetica", 8); c.setFillColor(colors.black); c.drawString(65, y, f"● {r_oi['Descripción']}"); c.drawRightString(480, y, f"$ {r_oi['Monto']:,.0f}"); y -= 10
            c.setFont("Helvetica-Bold", 8); c.line(60, y+5, 480, y+5); c.drawRightString(480, y-5, f"Total Otros Ingresos: $ {otr_sum:,.0f}"); y -= 25
        else: y -= 15
        c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "RELACIÓN DE GASTOS"); y -= 15
        c.setFont("Helvetica-Bold", 8); c.drawString(60, y, "CATEGORÍA - DESCRIPCIÓN"); c.drawRightString(480, y, "MONTO"); c.drawRightString(540, y, "PAGADO"); y -= 12
        c.setFont("Helvetica", 8)
        for _, row in g_m.iterrows():
            if y < 60: c.showPage(); y = head(c, titulo, anio, nombre_usuario); c.setFont("Helvetica", 8)
            c.drawString(60, y, f"{row['Categoría']} - {row['Descripción']}"[:65]); c.drawRightString(480, y, f"{row['Monto']:,.0f}"); c.drawRightString(540, y, "SI" if row["Pagado"] else "NO"); y -= 12
        y -= 20
    if len(meses) > 1:
        if y < 150: c.showPage(); y = head(c, titulo, anio, nombre_usuario)
        y -= 20; c.setFillColor(HexColor("#f8f9fa")); c.setStrokeColor(HexColor("#d4af37")); c.setLineWidth(2); c.rect(50, y-100, 510, 110, fill=1, stroke=1)
        c.setFillColor(HexColor("#1a1d21")); c.setFont("Helvetica-Bold", 12); c.drawString(70, y-5, "RESUMEN GENERAL DEL PERIODO")
        ing_totales = total_periodo_nomina + total_periodo_otros; saldo_final = ing_totales - total_periodo_gastos
        c.setFont("Helvetica", 10); c.setFillColor(colors.black); c.drawString(70, y-25, f"Total Nómina Percibida: $ {total_periodo_nomina:,.0f}")
        c.drawString(70, y-40, f"Total Ingresos Adicionales: $ {total_periodo_otros:,.0f}"); c.drawString(70, y-55, f"Total Gastos del Periodo: $ {total_periodo_gastos:,.0f}")
        if saldo_final >= 0: c.setFillColor(colors.darkgreen); label = "SALDO A FAVOR"
        else: c.setFillColor(colors.red); label = "DÉFICIT"
        c.setFont("Helvetica-Bold", 12); c.drawString(70, y-85, f"{label}: $ {abs(saldo_final):,.0f}")
    c.showPage(); c.save(); buf.seek(0); return buf

# --- 4. ACCESO BLINDADO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN): st.image(LOGO_LOGIN, use_container_width=True)
        t_in, t_reg = st.tabs(["🔑 Login", "📝 Registro"])
        db_u = cargar_usuarios()
        with t_in:
            u = st.text_input("Usuario", key="login_u")
            p = st.text_input("Pass", type="password", key="login_p")
            if st.button("Ingresar", use_container_width=True):
                if u in db_u:
                    u_data = db_u[u]
                    password_correcta = (u_data.get("pass") == p) if isinstance(u_data, dict) else (u_data == p)
                    nombre_final = u_data.get("nombre", u) if isinstance(u_data, dict) else u
                    if password_correcta:
                        st.session_state.autenticado, st.session_state.usuario_id, st.session_state.u_nombre_completo = True, u, nombre_final
                        st.rerun()
                    else: st.error("❌ Contraseña incorrecta")
                else: st.error("❌ Usuario no encontrado")
        with t_reg:
            rn, ru, rp = st.text_input("Nombre", key="reg_n"), st.text_input("ID Usuario", key="reg_u"), st.text_input("Pass", type="password", key="reg_p")
            if st.button("Crear/Actualizar Cuenta"):
                if ru in db_u and isinstance(db_u[ru], dict) and db_u[ru].get("pass") != rp:
                    st.error("❌ El usuario existe y la contraseña no coincide")
                else:
                    db_u[ru] = {"pass": rp, "nombre": rn}
                    guardar_usuarios(db_u); st.success("✅ Cuenta configurada con éxito")
    st.stop()

# --- 5. LÓGICA SIDEBAR ORIGINAL ---
u_id = st.session_state.usuario_id
df_g_full, df_i_full, df_oi_full = cargar_bd(u_id)

with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    anio_s = st.selectbox("Año", [2026, 2027, 2028], index=0)
    meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_s = st.selectbox("Mes Actual", meses_lista, index=datetime.now().month-1)
    
    i_m_act = df_i_full[(df_i_full["Periodo"]==mes_s)&(df_i_full["Año"]==anio_s)]
    idx = meses_lista.index(mes_s); m_ant = meses_lista[idx-1] if idx > 0 else "Diciembre"; a_ant = anio_s if idx > 0 else anio_s-1
    i_ant = df_i_full[(df_i_full["Periodo"] == m_ant) & (df_i_full["Año"] == a_ant)]
    g_ant = df_g_full[(df_g_full["Periodo"] == m_ant) & (df_g_full["Año"] == a_ant)]
    oi_ant = df_oi_full[(df_oi_full["Periodo"] == m_ant) & (df_oi_full["Año"] == a_ant)]
    
    s_sug = 0.0
    if not i_ant.empty:
        _, _, _, _, bf_a, _ = calcular_metricas(g_ant, i_ant["Nomina"].sum(), oi_ant["Monto"].sum(), i_ant["SaldoAnterior"].iloc[0]); s_sug = float(bf_a)
    
    st.divider(); arr_on = st.toggle(f"Arrastrar saldo de {m_ant}", value=False)
    
    val_s_init = s_sug if arr_on else float(i_m_act["SaldoAnterior"].iloc[0] if not i_m_act.empty else 0.0)
    s_txt = st.text_input("Saldo Anterior", value=format_moneda(val_s_init))
    s_in = parse_moneda(s_txt)
    
    val_n_init = float(i_m_act["Nomina"].iloc[0] if not i_m_act.empty else 0.0)
    n_txt = st.text_input("Ingreso Fijo (Sueldo o Nomina)", value=format_moneda(val_n_init))
    n_in = parse_moneda(n_txt)
    
    placeholder_otros = st.empty()
    st.divider(); st.subheader("📑 Extractos")
    c_pdf, c_xls = st.columns(2)
    with c_pdf:
        if st.button("📄 PDF"):
            pdf = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, [mes_s], f"Extracto {mes_s}", anio_s, u_id)
            st.download_button("Descargar PDF", pdf, f"Extracto_{mes_s}.pdf")
    with c_xls:
        buf_xls = BytesIO()
        with pd.ExcelWriter(buf_xls, engine='xlsxwriter') as writer:
            df_g_full[df_g_full["Periodo"]==mes_s].to_excel(writer, sheet_name='Gastos', index=False)
            df_oi_full[df_oi_full["Periodo"]==mes_s].to_excel(writer, sheet_name='OtrosIngresos', index=False)
        st.download_button("📊 Excel", buf_xls.getvalue(), f"Reporte_{mes_s}.xlsx")
    st.subheader("⚖️ Proyecciones")
    if st.button("📥 Semestre 1"):
        p1 = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses_lista[0:6], "S1", anio_s, u_id); st.download_button("S1.pdf", p1, "S1.pdf")
    if st.button("📥 Semestre 2"):
        p2 = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses_lista[6:12], "S2", anio_s, u_id); st.download_button("S2.pdf", p2, "S2.pdf")
    if st.button("🚪 Salir"): st.session_state.autenticado = False; st.rerun()

# --- 6. CUERPO PRINCIPAL ---
if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s} {anio_s}")

df_mes_g = df_g_full[(df_g_full["Periodo"] == mes_s) & (df_g_full["Año"] == anio_s)].copy()
# Lógica original para recuperar recurrentes
if df_mes_g.empty:
    mes_actual_idx = meses_lista.index(mes_s)
    gastos_previos = df_g_full[df_g_full["Año"] == anio_s].copy()
    if not gastos_previos.empty:
        meses_map = {m: i for i, m in enumerate(meses_lista)}
        gastos_previos["mes_idx"] = gastos_previos["Periodo"].map(meses_map)
        gastos_previos = gastos_previos[gastos_previos["mes_idx"] < mes_actual_idx]
        if not gastos_previos.empty:
            gastos_previos = gastos_previos.sort_values(by="mes_idx", ascending=False)
            ultimas_decisiones = gastos_previos.drop_duplicates(subset=["Categoría", "Descripción"])
            activos = ultimas_decisiones[ultimas_decisiones["Movimiento Recurrente"] == True].copy()
            if not activos.empty:
                df_mes_g = activos.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"])
                df_mes_g["Pagado"] = False 

config_g = {
    "Categoría": st.column_config.SelectboxColumn("Categoría", options=LISTA_CATEGORIAS, width="medium"),
    "Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f"),
    "Valor Referencia": st.column_config.NumberColumn("Valor Referencia", format="$ %,.0f"),
    "Pagado": st.column_config.CheckboxColumn("Pagado", default=False),
    "Movimiento Recurrente": st.column_config.CheckboxColumn("Recurrente", default=False)
}

st.markdown("### 📝 Movimiento de Gastos")
df_ed_g = st.data_editor(df_mes_g.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", column_config=config_g, key="g_ed")

st.markdown("### 💰 Ingresos Adicionales")
df_mes_oi = df_oi_full[(df_oi_full["Periodo"] == mes_s) & (df_oi_full["Año"] == anio_s)].copy()
df_ed_oi = st.data_editor(df_mes_oi.reindex(columns=["Descripción", "Monto"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", column_config={"Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f")}, key="oi_ed")

df_ed_g["Monto"] = pd.to_numeric(df_ed_g["Monto"], errors="coerce").fillna(0)
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0)
otr_v = float(df_ed_oi["Monto"].sum()); placeholder_otros.text_input("Otros Ingresos (Total)", value=f"$ {otr_v:,.0f}", disabled=True)
it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_v, s_in)
label_ahorro = "SALDO A FAVOR" if bf >= 0 else "DÉFICIT"

st.divider(); c_kpi = st.columns(5)
tarj = [("INGRESOS", it, "black"), ("OBLIG. PAGADAS", vp, "green"), ("OBLIG. PENDIENTES", vpy, "red"), ("DINERO DISPONIBLE", fact, "blue"), (label_ahorro, bf, "#d4af37")]
for i, (l, v, c) in enumerate(tarj): c_kpi[i].markdown(f'<div class="card"><div class="card-label">{l}</div><div class="card-value" style="color:{c}">$ {v:,.0f}</div></div>', unsafe_allow_html=True)

st.markdown("### 📊 Análisis de Distribución"); inf1, inf2, inf3 = st.columns([1.2, 1, 1.2])
with inf1:
    st.markdown("#### Desglose de Gastos")
    t_df = df_ed_g.copy(); t_df['V'] = t_df.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not t_df.empty and t_df['V'].sum() > 0:
        fig1 = px.pie(t_df, values='V', names='Categoría', hole=0.7, color='Categoría', color_discrete_map=COLOR_MAP); fig1.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(t=0,b=0,l=0,r=0)); st.plotly_chart(fig1, use_container_width=True)
        res = t_df.groupby("Categoría")['V'].sum().reset_index()
        for _, r in res.iterrows():
            col = COLOR_MAP.get(r['Categoría'], "#6c757d"); st.markdown(f'<div class="legend-bar" style="background:{col}">{r["Categoría"]} <span>$ {r["V"]:,.0f}</span></div>', unsafe_allow_html=True)
with inf2:
    st.markdown("#### Eficiencia de Ahorro"); v_cl = max(0, min(ahorro_p, 100))
    fig2 = go.Figure(go.Indicator(mode="gauge+number", value=v_cl, number={'suffix': "%", 'font': {'color': '#d4af37', 'size': 50}, 'valueformat': '.0f'}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#d4af37"}, 'bgcolor': "white"}))
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(t=50,b=0,l=25,r=25)); st.plotly_chart(fig2, use_container_width=True)
with inf3:
    st.markdown("#### Estado Real del Dinero")
    fig3 = go.Figure(data=[go.Pie(labels=['Obligaciones Pagadas', 'Obligaciones pendientes', 'Ahorro'], values=[vp, vpy, bf], hole=.7, marker_colors=['#2ecc71', '#e74c3c', '#d4af37'], textinfo='percent')]); fig3.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(t=0,b=0,l=0,r=0), annotations=[dict(text='Estado', x=0.5, y=0.5, font_size=20, showarrow=False, font_color="#d4af37")]); st.plotly_chart(fig3, use_container_width=True)
    st.markdown(f'<div class="legend-bar" style="background:#2ecc71">Obligaciones Pagadas <span>$ {vp:,.0f}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="legend-bar" style="background:#e74c3c">Obligaciones pendientes <span>$ {vpy:,.0f}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="legend-bar" style="background:#d4af37">{label_ahorro} Proyectado <span>$ {bf:,.0f}</span></div>', unsafe_allow_html=True)

# --- 7. GUARDAR EN SUPABASE (BLINDAJE TOTAL V2) ---
st.markdown("<br><br>", unsafe_allow_html=True)

# 1. Preparamos los datos PRIMERO para saber qué tenemos
df_g_limpio = df_ed_g.dropna(how="all", subset=["Categoría", "Monto"])
g_save = df_g_limpio.assign(periodo=mes_s, anio=anio_s, usuario_id=u_id).rename(columns={
    "Categoría":"categoria", "Descripción":"descripcion", "Monto":"monto", "Valor Referencia":"valor_referencia", 
    "Pagado":"pagado", "Movimiento Recurrente":"recurrente"
}).to_dict(orient="records")

df_oi_limpio = df_ed_oi.dropna(how="all", subset=["Monto"])
oi_save = df_oi_limpio.assign(periodo=mes_s, anio=anio_s, usuario_id=u_id).rename(columns={
    "Descripción":"descripcion", "Monto":"monto"
}).to_dict(orient="records")

# 2. El Botón con lógica de protección
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS", use_container_width=True):
    # Verificación de emergencia: ¿Estamos intentando guardar un mes vacío teniendo datos en el servidor?
    if not g_save and not oi_save and s_in == 0 and n_in == 0:
        st.error("🛑 ¡DETENIDO! No puedes guardar una pantalla vacía. Si quieres borrar el mes, hazlo manualmente en la base de datos.")
    else:
        try:
            with st.spinner("Protegiendo tus datos y sincronizando..."):
                # --- GUARDADO DE GASTOS (Solo si hay datos en pantalla) ---
                if g_save:
                    supabase.table("gastos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
                    supabase.table("gastos").insert(g_save).execute()
                
                # --- GUARDADO DE INGRESOS EXTRA (Solo si hay datos en pantalla) ---
                if oi_save:
                    supabase.table("otros_ingresos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
                    supabase.table("otros_ingresos").insert(oi_save).execute()

                # --- GUARDADO DE INGRESOS BASE (Siempre se guarda porque s_in y n_in siempre existen) ---
                supabase.table("ingresos_base").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
                i_save = {"anio": anio_s, "periodo": mes_s, "saldo_anterior": s_in, "nomina": n_in, "otros": otr_v, "usuario_id": u_id}
                supabase.table("ingresos_base").insert(i_save).execute()

                st.balloons()
                st.cache_data.clear() 
                st.success(f"✅ ¡Datos de {mes_s} guardados de forma segura!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error crítico: {e}")
