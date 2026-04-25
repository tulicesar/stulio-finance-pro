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
# --- JUSTO DEBAJO DE LOS IMPORT ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "token" not in st.session_state:
    st.session_state.token = None
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
# --- 1. CONFIGURACIÓN Y ESTILO (REPARADO) ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

# 🔑 INICIALIZACIÓN DE MEMORIA (Session State)
# Esto evita que la app diga que no encuentra el "token"
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "token" not in st.session_state:
    st.session_state.token = None
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

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

# --- CATEGORÍAS Y COLORES (Mantenemos tu estilo) ---
LISTA_CATEGORIAS = [
    "Hogar", "Servicios", "Alimentación", "Transporte", "Gasto Vehiculos",
    "Obligaciones Financieras", "Salud", "Educación", 
    "Cuidado Personal", "Mascotas", "Viajes y Recreación", "Servicios de Streaming",
    "Seguros", "Ahorro e Inversión", "Impuestos", "Otros"
]

COLOR_MAP = {
    "Hogar": "#fca311", "Servicios": "#77B5FE", "Alimentación": "#77DD77",
    "Transporte": "#FF6961", "Gasto Vehiculos": "#FDFD96",
    "Obligaciones Financieras": "#84b6f4", "Salud": "#fdcae1", 
    "Educación": "#B39EB5", "Cuidado Personal": "#FFD1DC",
    "Mascotas": "#CFCFCF", "Viajes y Recreación": "#AEC6CF", 
    "Servicios de Streaming": "#cfcfc4",
    "Seguros": "#836953", "Ahorro e Inversión": "#d4af37", 
    "Impuestos": "#ffda9e", "Otros": "#b2e2f2"
}

# (Tu bloque de st.markdown con CSS sigue aquí igual...)
st.markdown(f"""
    <style>
    header {{ background-color: rgba(0,0,0,0) !important; }}
    .stApp {{ background: #495057; color: #ffffff; }}
    [data-testid="stDataEditor"] div {{ font-size: 2.0rem !important; }}
    .stTabs [aria-selected="true"] {{ color: #fca311 !important; border-bottom-color: #fca311 !important; font-weight: bold; }}
    
    .card {{
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #495057; text-align: center; border-bottom: 5px solid #fca311;
        min-height: 100px; display: flex; flex-direction: column; justify-content: center;
    }}
    .card-label {{ font-size: 0.8rem; color: #495057; font-weight: 800; text-transform: uppercase; line-height: 1.1; opacity: 0.7; }}
    .card-value {{ font-size: 1.6rem; font-weight: 800; color: #495057; margin: 3px 0; }}
    
    .legend-bar {{
        padding: 8px 12px; border-radius: 6px; margin-bottom: 4px; 
        font-size: 0.9rem; font-weight: bold; color: #1a1d21; 
        display: flex; justify-content: space-between; align-items: center;
    }}
    
    section[data-testid="stSidebar"] {{ background-color: #212529 !important; border-right: 1px solid #495057; }}
    .stButton>button {{ border-radius: 10px; font-weight: bold; width: 100%; background-color: #fca311; color: #212529; border: none; }}
    h2, h3 {{ color: #fca311 !important; font-weight: bold !important; }}
    </style>
    """, unsafe_allow_html=True)
# --- 2. MOTOR DE DATOS Y FORMATEO (REPARADO) ---
def format_moneda(valor):
    try:
        n = int(float(valor))
        return f"$ {n:,.0f}".replace(",", ".")
    except:
        return "$ 0"

def parse_moneda(texto):
    if not texto: return 0.0
    clean = re.sub(r'[^\d]', '', str(texto))
    return float(clean) if clean else 0.0

# 🛡️ CARGAR USUARIOS (Versión Silenciosa)
def cargar_usuarios():
    """Solo intenta cargar si hay un token, de lo contrario devuelve vacío"""
    try:
        # Si no hay token en la sesión, ni lo intentamos para evitar el error rojo
        if not st.session_state.get("token"):
            return {}
            
        res = supabase.table("usuarios").select("*").execute()
        return {user['usuario_id']: {"pass": user['password'], "nombre": user['nombre_completo']} for user in res.data}
    except Exception:
        return {}

# 📊 CARGAR BASE DE DATOS (Con llave de seguridad)
@st.cache_data(ttl=5)
def cargar_bd(u_id):
    # 🔑 LE PRESENTAMOS LA IDENTIDAD A SUPABASE ANTES DE PEDIR DATOS
    if st.session_state.get("token"):
        supabase.postgrest.auth(st.session_state.token)
    
    try:
        r_g = supabase.table("gastos").select("*").eq("usuario_id", u_id).execute()
        r_i = supabase.table("ingresos_base").select("*").eq("usuario_id", u_id).execute()
        r_oi = supabase.table("otros_ingresos").select("*").eq("usuario_id", u_id).execute()
        
        df_g = pd.DataFrame(r_g.data) if r_g.data else pd.DataFrame(columns=["anio", "periodo", "categoria", "descripcion", "monto", "valor_referencia", "pagado", "recurrente", "usuario_id"])
        df_i = pd.DataFrame(r_i.data) if r_i.data else pd.DataFrame(columns=["anio", "periodo", "saldo_anterior", "nomina", "otros", "usuario_id"])
        df_oi = pd.DataFrame(r_oi.data) if r_oi.data else pd.DataFrame(columns=["anio", "periodo", "descripcion", "monto", "usuario_id"])
        
        # Mapeo de nombres para tu interfaz
        df_g = df_g.rename(columns={"anio":"Año", "periodo":"Periodo", "categoria":"Categoría", "descripcion":"Descripción", "monto":"Monto", "valor_referencia":"Valor Referencia", "pagado":"Pagado", "recurrente":"Movimiento Recurrente", "usuario_id":"Usuario"})
        df_i = df_i.rename(columns={"anio":"Año", "periodo":"Periodo", "saldo_anterior":"SaldoAnterior", "nomina":"Nomina", "otros":"Otros", "usuario_id":"Usuario"})
        df_oi = df_oi.rename(columns={"anio":"Año", "periodo":"Periodo", "descripcion":"Descripción", "monto":"Monto", "usuario_id":"Usuario"})
        
        for df in [df_g, df_i, df_oi]:
            if "Año" in df.columns:
                df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(0).astype(int)
        
        return df_g, df_i, df_oi
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)
    vp = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    vpy = df_g[df_g["Pagado"] == False].apply(lambda x: x["Monto"] if x["Monto"] > 0 else x["Valor Referencia"], axis=1).sum() if not df_g.empty else 0
    bf = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), bf, ahorro_p
# --- 3. REPORTE PDF (TOTALMENTE INTEGRADO) ---
def generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses, titulo, anio, u_id):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    import os

    nombre_usuario = st.session_state.get("u_nombre_completo", u_id)
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    
    C_AZUL = HexColor("#14213d")
    C_NARANJA = HexColor("#fca311")
    C_GRIS = HexColor("#e5e5e5")
    C_NEGRO = HexColor("#000000")

    total_periodo_nomina, total_periodo_otros, total_periodo_gastos = 0, 0, 0

    def head(canvas_obj, t, a, user_name):
        canvas_obj.setFillColor(colors.white); canvas_obj.rect(0, 0, 612, 792, fill=1)
        logo_path = "LOGOapp horizontal.png"
        if os.path.exists(logo_path):
            canvas_obj.drawImage(logo_path, 55, 670, width=500, height=100, preserveAspectRatio=True, anchor='c')
        canvas_obj.setFont("Helvetica-BoldOblique", 9); canvas_obj.setFillColor(C_AZUL)
        canvas_obj.drawString(50, 650, f"Usuario: {user_name}")
        canvas_obj.drawRightString(560, 650, f"{t} {a}")
        canvas_obj.setStrokeColor(C_NARANJA); canvas_obj.setLineWidth(2); canvas_obj.line(50, 645, 560, 645)
        tz = pytz.timezone('America/Bogota'); fecha_gen = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
        canvas_obj.setFont("Helvetica", 7); canvas_obj.setFillColor(colors.grey); canvas_obj.drawString(50, 30, f"Documento generado el: {fecha_gen}")
        return 620

    y = head(c, titulo, anio, nombre_usuario)
    
    for m in meses:
        i_m = df_i_full[(df_i_full["Periodo"] == m) & (df_i_full["Año"] == anio) & (df_i_full["Usuario"] == u_id)]
        g_m = df_g_full[(df_g_full["Periodo"] == m) & (df_g_full["Año"] == anio) & (df_g_full["Usuario"] == u_id)]
        oi_m = df_oi_full[(df_oi_full["Periodo"] == m) & (df_oi_full["Año"] == anio) & (df_oi_full["Usuario"] == u_id)]
        
        s_ant = (i_m["SaldoAnterior"].iloc[0] if not i_m.empty else 0)
        nom = (i_m["Nomina"].iloc[0] if not i_m.empty else 0)
        otr_sum = oi_m["Monto"].sum() if not oi_m.empty else 0
        
        it, vp, vpy, _, bf, _ = calcular_metricas(g_m, nom, otr_sum, s_ant)
        total_periodo_nomina += nom; total_periodo_otros += otr_sum; total_periodo_gastos += (vp + vpy)
        
        if y < 250: c.showPage(); y = head(c, titulo, anio, nombre_usuario)
        
        c.setFillColor(C_GRIS); c.rect(50, y-55, 510, 60, fill=1, stroke=0)
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 11); c.drawString(60, y-15, f"MES: {m}")
        c.setFont("Helvetica", 9); c.drawString(60, y-30, f"Ingresos: $ {it:,.0f} | Pagadas: $ {vp:,.0f} | Pendientes: $ {vpy:,.0f}")
        c.setFillColor(C_NARANJA); c.setFont("Helvetica-Bold", 9); c.drawString(60, y-45, f"SALDO A FAVOR FINAL: $ {bf:,.0f}"); y -= 80
        
        # Relación Ingresos
        c.setFont("Helvetica-Bold", 9); c.setFillColor(C_AZUL); c.drawString(60, y, "RELACIÓN DE INGRESOS"); y -= 15
        c.setFont("Helvetica", 8); c.setFillColor(C_NEGRO); c.drawString(60, y, "Saldo Anterior"); c.drawRightString(480, y, f"$ {s_ant:,.0f}"); y -= 10
        c.drawString(60, y, "Nómina"); c.drawRightString(480, y, f"$ {nom:,.0f}"); y -= 5
        
        if not oi_m.empty:
            c.setStrokeColor(colors.lightgrey); c.line(60, y, 480, y); y -= 12
            c.setFont("Helvetica-BoldOblique", 7); c.setFillColor(colors.darkgrey); c.drawString(60, y, "Ingresos Variables"); y -= 10
            for _, r_oi in oi_m.iterrows():
                c.setFont("Helvetica", 8); c.setFillColor(C_NEGRO); c.drawString(65, y, f"● {r_oi['Descripción']}"); c.drawRightString(480, y, f"$ {r_oi['Monto']:,.0f}"); y -= 10
            c.setFont("Helvetica-Bold", 8); c.line(60, y+5, 480, y+5); c.drawRightString(480, y-5, f"Total Otros Ingresos: $ {otr_sum:,.0f}"); y -= 25
        else: y -= 15
        
        # Relación Gastos
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "RELACIÓN DE GASTOS"); y -= 15
        c.setFont("Helvetica-Bold", 8); c.drawString(60, y, "CATEGORÍA - DESCRIPCIÓN"); c.drawRightString(480, y, "MONTO"); c.drawRightString(540, y, "PAGADO"); y -= 12
        c.setFont("Helvetica", 8); c.setFillColor(C_NEGRO)
        for _, row in g_m.iterrows():
            if y < 60: c.showPage(); y = head(c, titulo, anio, nombre_usuario); c.setFont("Helvetica", 8)
            c.drawString(60, y, f"{row['Categoría']} - {row['Descripción']}"[:65]); c.drawRightString(480, y, f"{row['Monto']:,.0f}"); c.drawRightString(540, y, "SI" if row["Pagado"] else "NO"); y -= 12
        y -= 20

    if len(meses) > 1:
        if y < 150: c.showPage(); y = head(c, titulo, anio, nombre_usuario)
        y -= 20; c.setFillColor(C_NARANJA); c.setStrokeColor(C_AZUL); c.setLineWidth(2); c.rect(50, y-100, 510, 110, fill=1, stroke=1)
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 12); c.drawString(70, y-5, f"RESUMEN: {titulo.upper()}")
        ing_totales = total_periodo_nomina + total_periodo_otros; saldo_final_periodo = ing_totales - total_periodo_gastos
        c.setFont("Helvetica", 10); c.setFillColor(C_AZUL); c.drawString(70, y-25, f"Total Nómina Percibida: $ {total_periodo_nomina:,.0f}")
        c.drawString(70, y-40, f"Total Ingresos Adicionales: $ {total_periodo_otros:,.0f}"); c.drawString(70, y-55, f"Total Gastos del Periodo: $ {total_periodo_gastos:,.0f}")
        c.setFont("Helvetica-Bold", 12); c.drawString(70, y-85, f"SALDO TOTAL AL CIERRE: $ {abs(saldo_final_periodo):,.0f}"); y -= 150

    # 📊 HISTÓRICO ESTILO RECIBO LUZ EN EL PDF
    if y < 150: c.showPage(); y = head(c, titulo, anio, nombre_usuario)
    y -= 30; c.setStrokeColor(C_AZUL); c.setLineWidth(1); c.line(50, y, 560, y); y -= 20
    c.setFont("Helvetica-Bold", 10); c.setFillColor(C_AZUL); c.drawString(50, y, "TENDENCIA DE AHORRO (Últimos 6 meses)")
    y -= 70; meses_lista_h = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    hist_pdf = []; m_idx_ref = meses_lista_h.index(meses[-1])
    for i in range(5, -1, -1):
        idx = m_idx_ref - i; a_h = anio
        if idx < 0: idx += 12; a_h -= 1
        m_n = meses_lista_h[idx]; i_h = df_i_full[(df_i_full["Periodo"] == m_n) & (df_i_full["Año"] == a_h) & (df_i_full["Usuario"] == u_id)]
        if not i_h.empty:
            g_h = df_g_full[(df_g_full["Periodo"] == m_n) & (df_g_full["Año"] == a_h) & (df_g_full["Usuario"] == u_id)]
            oi_h = df_oi_full[(df_oi_full["Periodo"] == m_n) & (df_oi_full["Año"] == a_h) & (df_oi_full["Usuario"] == u_id)]
            _, _, _, _, bf_h, _ = calcular_metricas(g_h, i_h["Nomina"].iloc[0], oi_h["Monto"].sum() if not oi_h.empty else 0, i_h["SaldoAnterior"].iloc[0])
            hist_pdf.append((f"{m_n[:3]}", bf_h))
    if hist_pdf:
        x_bar = 70; max_val = max([abs(v[1]) for v in hist_pdf] + [1])
        for m_n, val in hist_pdf:
            h_bar = (val / max_val) * 60 if val > 0 else 2
            c.setFillColor(C_NARANJA); c.rect(x_bar, y, 35, h_bar, fill=1, stroke=0)
            c.setFillColor(C_NEGRO); c.setFont("Helvetica-Bold", 7); c.drawCentredString(x_bar + 17, y - 12, m_n)
            c.setFont("Helvetica", 6); c.drawCentredString(x_bar + 17, y + h_bar + 5, f"${val:,.0f}")
            x_bar += 55
    c.showPage(); c.save(); buf.seek(0); return buf
# --- 4. ACCESO BLINDADO (VERSIÓN SUPABASE OFICIAL) ---
if 'autenticado' not in st.session_state: 
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN): st.image(LOGO_LOGIN, use_container_width=True)
        t_in, t_reg = st.tabs(["🔑 Login", "📝 Registro"])
        
        with t_in:
            u = st.text_input("Email o Usuario", key="login_u")
            p = st.text_input("Contraseña", type="password", key="login_p")
            if st.button("Ingresar", use_container_width=True):
                try:
                    # 🚀 LOGIN OFICIAL: Esto genera el Token de seguridad
                    res = supabase.auth.sign_in_with_password({"email": u, "password": p})
                    
                    # Guardamos los datos en la sesión
                    st.session_state.autenticado = True
                    st.session_state.usuario_id = res.user.id  # <--- Este es el ID real (UUID)
                    st.session_state.u_nombre_completo = u.split('@')[0]
                    st.session_state.token = res.session.access_token
                    
                    # 🔑 ACTIVAMOS LA PULSERA DE ACCESO
                    supabase.postgrest.auth(st.session_state.token)
                    
                    st.success("✅ ¡Ingreso exitoso!")
                    st.rerun()
                except Exception as e:
                    st.error("❌ Usuario o contraseña incorrectos. (Asegúrate de usar un Email)")
        
        with t_reg:
            st.markdown("### Registro de Nuevo Usuario")
            rn = st.text_input("Nombre Completo", key="reg_n")
            ru = st.text_input("Email (Obligatorio)", key="reg_u")
            rp = st.text_input("Contraseña", type="password", key="reg_p")
            
            if st.button("Crear Cuenta", use_container_width=True):
                if not ru or not rp:
                    st.warning("⚠️ El Email y la Contraseña son obligatorios")
                else:
                    try:
                        # 🚀 REGISTRO OFICIAL EN SUPABASE AUTH
                        res = supabase.auth.sign_up({"email": ru, "password": rp})
                        st.success(f"✅ ¡Registrado! Revisa tu email o intenta loguearte.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Error al registrar: {e}")
    st.stop()
# --- 5. LÓGICA SIDEBAR (VERSIÓN SEGURA Y BLINDADA) ---
if st.session_state.autenticado:
    u_id = st.session_state.usuario_id
    
    # 🔑 PASO MAESTRO: Inyectamos el token de seguridad antes de llamar a la base de datos
    if st.session_state.token:
        supabase.postgrest.auth(st.session_state.token)
    
    # Ahora sí cargamos los datos con la "pulsera de acceso" puesta
    df_g_full, df_i_full, df_oi_full = cargar_bd(u_id)

    with st.sidebar:
        if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
        st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
        
        # Selector de Año y Mes
        anio_s = st.selectbox("Año", [2026, 2027, 2028], index=0)
        meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_s = st.selectbox("Mes Actual", meses_lista, index=datetime.now().month-1)
        
        # 1. Buscamos el mes actual en la BD
        i_m_act = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s)]
        
        # 2. Lógica para detectar el MES y AÑO anterior
        idx = meses_lista.index(mes_s)
        if idx > 0:
            m_ant = meses_lista[idx-1]
            a_ant = anio_s
        else:
            m_ant = "Diciembre"
            a_ant = anio_s - 1
        
        # 3. Traemos los datos de ese mes anterior
        i_ant = df_i_full[(df_i_full["Periodo"] == m_ant) & (df_i_full["Año"] == a_ant)]
        g_ant = df_g_full[(df_g_full["Periodo"] == m_ant) & (df_g_full["Año"] == a_ant)]
        oi_ant = df_oi_full[(df_oi_full["Periodo"] == m_ant) & (df_oi_full["Año"] == a_ant)]
        
        # 4. Calculamos cuánto sobró el mes pasado
        s_sug = 0.0
        if not i_ant.empty:
            # Usamos la función de métricas que ya tienes definida
            _, _, _, _, bf_a, _ = calcular_metricas(g_ant, i_ant["Nomina"].sum(), oi_ant["Monto"].sum(), i_ant["SaldoAnterior"].iloc[0])
            s_sug = float(bf_a)
        
        st.divider()
        arr_on = st.toggle(f"Arrastrar saldo de {m_ant} {a_ant}", value=True)
        
        # 5. Definimos los valores iniciales de los inputs
        val_s_init = s_sug if arr_on else float(i_m_act["SaldoAnterior"].iloc[0] if not i_m_act.empty else 0.0)
        s_txt = st.text_input("Saldo Anterior", value=format_moneda(val_s_init))
        s_in = parse_moneda(s_txt)
        
        val_n_init = float(i_m_act["Nomina"].iloc[0] if not i_m_act.empty else 0.0)
        n_txt = st.text_input("Ingreso Fijo (Sueldo o Nomina)", value=format_moneda(val_n_init))
        n_in = parse_moneda(n_txt)
        
        placeholder_otros = st.empty()
        
        # --- BOTONES DE ACCIÓN ---
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
            titulo_s1 = "Balance Proyectado Enero - Junio"
            p1 = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses_lista[0:6], titulo_s1, anio_s, u_id)
            st.download_button(f"Descargar {titulo_s1}", p1, f"Balance_S1_{anio_s}.pdf")

        if st.button("📥 Semestre 2"):
            titulo_s2 = "Balance Proyectado Julio - Diciembre"
            p2 = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses_lista[6:12], titulo_s2, anio_s, u_id)
            st.download_button(f"Descargar {titulo_s2}", p2, f"Balance_S2_{anio_s}.pdf")
        
        if st.button("🚪 Salir"): 
            st.session_state.autenticado = False
            st.rerun()
else:
    # Si no está autenticado, simplemente no hacemos nada aquí
    # El Bloque 4 se encargará de mostrar el login y detener la ejecución.
    st.stop()

# --- 6. CUERPO PRINCIPAL (RESTAURADO Y CON LÓGICA DE COPIA ESTRICTA) ---
if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s} {anio_s}")

# 1. Intentamos cargar los datos que ya existen para este mes
df_mes_g = df_g_full[(df_g_full["Periodo"] == mes_s) & (df_g_full["Año"] == anio_s)].copy()

# 2. LÓGICA DE COPIA INTELIGENTE (Solo si el mes está totalmente vacío)
if df_mes_g.empty:
    meses_map_r = {m: i for i, m in enumerate(meses_lista)}
    gastos_hist = df_g_full.copy()
    
    if not gastos_hist.empty:
        # Calculamos la línea de tiempo del mes que queremos abrir
        p_actual = (anio_s * 12) + meses_lista.index(mes_s)
        gastos_hist["lt"] = (gastos_hist["Año"] * 12) + gastos_hist["Periodo"].map(meses_map_r)
        
        # BUSCAMOS ÚNICAMENTE EL MES ANTERIOR MÁS CERCANO QUE TENGA DATOS
        registros_previos = gastos_hist[gastos_hist["lt"] < p_actual]
        
        if not registros_previos.empty:
            ultimo_mes_con_info_lt = registros_previos["lt"].max()
            # Tomamos la "foto" exacta de ese último mes
            foto_ultimo_mes = registros_previos[registros_previos["lt"] == ultimo_mes_con_info_lt]
            
            # FILTRO CRÍTICO: Solo traemos lo que esté marcado como RECURRENTE en ESE mes específico.
            # Si lo borraste en ese mes, no existe en la foto. 
            # Si le quitaste el check de recurrente, este filtro lo deja fuera.
            activos = foto_ultimo_mes[foto_ultimo_mes["Movimiento Recurrente"] == True].copy()
            
            if not activos.empty:
                df_mes_g = activos.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"])
                df_mes_g["Pagado"] = False # Nada empieza pagado en el mes nuevo

# --- SECCIÓN 1: TABLA DE GASTOS ---
st.markdown("### 📝 Movimiento de Gastos")
config_g = {
    "Categoría": st.column_config.SelectboxColumn("Categoría", options=LISTA_CATEGORIAS, width="medium"),
    "Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f"),
    "Valor Referencia": st.column_config.NumberColumn("Valor Referencia", format="$ %,.0f"),
    "Pagado": st.column_config.CheckboxColumn("Pagado", default=False),
    "Movimiento Recurrente": st.column_config.CheckboxColumn("Recurrente", default=False)
}
df_ed_g = st.data_editor(df_mes_g.reindex(columns=["Categoría", "Descripción", "Monto", "Valor Referencia", "Pagado", "Movimiento Recurrente"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", column_config=config_g, key="g_ed")

# --- SECCIÓN 2: TABLA DE INGRESOS ADICIONALES ---
st.markdown("### 💰 Ingresos Adicionales")
df_mes_oi = df_oi_full[(df_oi_full["Periodo"] == mes_s) & (df_oi_full["Año"] == anio_s)].copy()
df_ed_oi = st.data_editor(df_mes_oi.reindex(columns=["Descripción", "Monto"]).reset_index(drop=True), use_container_width=True, num_rows="dynamic", column_config={"Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f")}, key="oi_ed")

# --- SECCIÓN 3: CÁLCULOS Y KPIs ---
df_ed_g["Monto"] = pd.to_numeric(df_ed_g["Monto"], errors="coerce").fillna(0)
df_ed_g["Valor Referencia"] = pd.to_numeric(df_ed_g["Valor Referencia"], errors="coerce").fillna(0)
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0)

otr_v = float(df_ed_oi["Monto"].sum())
placeholder_otros.text_input("Otros Ingresos (Total)", value=f"$ {otr_v:,.0f}", disabled=True)

it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_v, s_in)
label_ahorro = "SALDO A FAVOR" if bf >= 0 else "DÉFICIT"

st.divider()
c_kpi = st.columns(5)
tarj = [
    ("INGRESOS", it, "black"), 
    ("OBLIG. PAGADAS", vp, "green"), 
    ("OBLIG. PENDIENTES", vpy, "red"), 
    ("DINERO DISPONIBLE", fact, "blue"), 
    (label_ahorro, bf, "#fca311")
]
for i, (l, v, col) in enumerate(tarj):
    c_kpi[i].markdown(f'<div class="card"><div class="card-label">{l}</div><div class="card-value" style="color:{col}">$ {v:,.0f}</div></div>', unsafe_allow_html=True)

# --- SECCIÓN 4: LAS 3 INFOGRAFÍAS ORIGINALES ---
st.markdown("### 📊 Análisis de Distribución")
inf1, inf2, inf3 = st.columns([1.2, 1, 1.2])

with inf1:
    st.markdown("#### Desglose de Gastos")
    t_df = df_ed_g.copy()
    t_df['V'] = t_df.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not t_df.empty and t_df['V'].sum() > 0:
        fig1 = px.pie(t_df, values='V', names='Categoría', hole=0.7, color='Categoría', color_discrete_map=COLOR_MAP)
        fig1.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig1, use_container_width=True)
        res = t_df.groupby("Categoría")['V'].sum().reset_index()
        for _, r in res.iterrows():
            c_cat = COLOR_MAP.get(r['Categoría'], "#6c757d")
            st.markdown(f'<div class="legend-bar" style="background:{c_cat}">{r["Categoría"]} <span>$ {r["V"]:,.0f}</span></div>', unsafe_allow_html=True)

with inf2:
    st.markdown("#### Eficiencia de Ahorro")
    v_cl = max(0, min(ahorro_p, 100))
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number", value=v_cl, 
        number={'suffix': "%", 'font': {'color': '#fca311', 'size': 50}, 'valueformat': '.0f'},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#fca311"}, 'bgcolor': "white"}
    ))
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(t=50,b=0,l=25,r=25))
    st.plotly_chart(fig2, use_container_width=True)

with inf3:
    st.markdown("#### Estado Real del Dinero")
    fig3 = go.Figure(data=[go.Pie(
        labels=['Pagado', 'Pendiente', 'Ahorro'], 
        values=[vp, vpy, bf if bf > 0 else 0], 
        hole=.7, 
        marker_colors=['#2ecc71', '#e74c3c', '#fca311'], 
        textinfo='percent'
    )])
    fig3.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(t=0,b=0,l=0,r=0),
                       annotations=[dict(text='Estado', x=0.5, y=0.5, font_size=20, showarrow=False, font_color="#fca311")])
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown(f'<div class="legend-bar" style="background:#2ecc71">Obligaciones Pagadas <span>$ {vp:,.0f}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="legend-bar" style="background:#e74c3c">Obligaciones Pendientes <span>$ {vpy:,.0f}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="legend-bar" style="background:#fca311">{label_ahorro} <span>$ {bf:,.0f}</span></div>', unsafe_allow_html=True)

# --- 7. GUARDAR EN SUPABASE (VERSIÓN REPARADA CON TOKEN) ---
st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS", use_container_width=True):
    df_g_limpio = df_ed_g.dropna(subset=["Categoría", "Descripción", "Monto"], how="all")
    df_oi_limpio = df_ed_oi.dropna(subset=["Descripción", "Monto"], how="all")

    if df_g_limpio.empty and df_oi_limpio.empty and n_in == 0:
        st.error("🛑 No hay datos suficientes para guardar.")
    else:
        try:
            with st.spinner("Sincronizando con Supabase..."):
                # 🔑 LA LLAVE MAESTRA: Sin esta línea, Supabase da error 42501
                supabase.postgrest.auth(st.session_state.token) 
                
                # 1. Limpiamos datos viejos para evitar duplicados
                supabase.table("gastos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
                supabase.table("otros_ingresos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
                supabase.table("ingresos_base").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()

                # 2. Insertamos los nuevos Gastos
                if not df_g_limpio.empty:
                    gastos_db = []
                    for _, row in df_g_limpio.iterrows():
                        gastos_db.append({
                            "anio": int(anio_s), "periodo": str(mes_s), "categoria": str(row["Categoría"]),
                            "descripcion": str(row["Descripción"]), "monto": float(row["Monto"]),
                            "valor_referencia": float(row["Valor Referencia"]), "pagado": bool(row["Pagado"]),
                            "recurrente": bool(row["Movimiento Recurrente"]), "usuario_id": str(u_id)
                        })
                    supabase.table("gastos").insert(gastos_db).execute()

                # 3. Insertamos Ingresos Adicionales
                if not df_oi_limpio.empty:
                    otros_db = [{"anio": int(anio_s), "periodo": str(mes_s), "descripcion": str(row["Descripción"]), "monto": float(row["Monto"]), "usuario_id": str(u_id)} for _, row in df_oi_limpio.iterrows()]
                    supabase.table("otros_ingresos").insert(otros_db).execute()

                # 4. Insertamos Ingreso Base
                supabase.table("ingresos_base").insert({
                    "anio": int(anio_s), "periodo": str(mes_s), "saldo_anterior": float(s_in),
                    "nomina": float(n_in), "otros": float(otr_v), "usuario_id": str(u_id)
                }).execute()

                st.balloons()
                st.cache_data.clear()
                st.success("✅ ¡Todo guardado y sincronizado de forma segura!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error de Seguridad/Conexión: {e}")
