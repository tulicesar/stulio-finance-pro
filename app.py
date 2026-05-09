import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import re
import base64
from io import BytesIO
from datetime import datetime
import pytz
from supabase import create_client, Client

# ── Importar módulos propios ──────────────────────────────
from auth    import mostrar_login, cerrar_sesion, mostrar_eliminar_cuenta
from data    import cargar_bd, calcular_metricas, guardar_bd
from reports import generar_pdf_reporte, generar_excel_reporte

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

# --- 2. INICIALIZACIÓN DE SESSION STATE ---
for key, default in {
    "autenticado": False,
    "token": None,
    "usuario_id": None,
    "u_nombre_completo": "",
    "mostrar_eliminar": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- 3. CONEXIÓN A SUPABASE ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)
    if st.session_state.autenticado and st.session_state.token:
        supabase.postgrest.auth(st.session_state.token)
except Exception:
    st.error("Error conectando a Supabase. Revisa los Secrets.")
    st.stop()

# --- 4. CONSTANTES ---
LOGO_LOGIN   = "logoapp 1.png"
LOGO_SIDEBAR = "logoapp 2.png"
LOGO_APP_H   = "LOGOapp horizontal.png"
SF_FONT      = "SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif"

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

# --- 5. FUENTE SF PRO DISPLAY + ESTILOS ---
def embed_font(path, weight):
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"""
    @font-face {{
        font-family: 'SF Pro Display';
        src: url(data:font/otf;base64,{data}) format('opentype');
        font-weight: {weight};
    }}
    """
    except Exception:
        return ""

css_fonts = (
    embed_font("SFNSDisplay-Regular.otf",  "400") +
    embed_font("SFNSDisplay-Medium.otf",   "500") +
    embed_font("SFNSDisplay-Semibold.otf", "600") +
    embed_font("SFNSDisplay-Bold.otf",     "700")
)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
    {css_fonts}

    /* ── FUENTE GENERAL ── */
    html, body, .stApp, [data-testid="stWidgetLabel"], [data-testid="stMarkdownContainer"],
    p, h1, h2, h3, h4, h5, h6, label, table, div {{
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    /* ── PROTEGER ÍCONOS MATERIAL DE STREAMLIT ── */
    [data-testid="stIconMaterial"] {{
        font-family: 'Material Symbols Rounded' !important;
        font-size: 1.5rem !important;
        color: rgba(255, 255, 255, 0.6) !important;
    }}

    header {{ background-color: rgba(0,0,0,0) !important; }}
    .stApp {{ background: #495057; color: #ffffff; }}

    /* ── TABLAS ── */
    [data-testid="stDataEditor"] {{ border-radius: 10px; overflow: hidden; }}
    [data-testid="stDataEditor"] div {{ font-size: 0.85rem !important; }}
    [data-testid="stDataEditor"] tr:nth-child(even) td {{ background-color: #3a3f44 !important; }}
    [data-testid="stDataEditor"] tr:nth-child(odd)  td {{ background-color: #2d3238 !important; }}
    [data-testid="stDataEditor"] th {{ background-color: #14213d !important; color: #fca311 !important; font-weight: 700 !important; }}

    /* ── TABS ── */
    .stTabs [aria-selected="true"] {{ color: #fca311 !important; border-bottom-color: #fca311 !important; font-weight: bold; }}

    /* ── KPI CARDS ── */
    .card {{
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #495057; text-align: center; border-bottom: 5px solid #fca311;
        min-height: 100px; display: flex; flex-direction: column; justify-content: center;
    }}
    .card-label {{ font-size: 0.8rem; color: #495057; font-weight: 800; text-transform: uppercase; line-height: 1.1; opacity: 0.7; }}
    .card-value {{ font-size: 1.6rem; font-weight: 800; color: #495057; margin: 3px 0; }}

    /* ── LEGEND BARS ── */
    .legend-bar {{
        padding: 8px 12px; border-radius: 6px; margin-bottom: 4px;
        font-size: 0.9rem; font-weight: bold; color: #1a1d21;
        display: flex; justify-content: space-between; align-items: center;
    }}

    /* ── CHART CARDS ── */
    .chart-card {{
        background-color: #3a3f44; border-radius: 14px; padding: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.35); margin-bottom: 8px;
        border-top: 3px solid #fca311;
    }}
    .chart-title {{
        font-size: 0.85rem; font-weight: 800; text-transform: uppercase;
        color: #fca311; letter-spacing: 0.05em; margin-bottom: 10px;
    }}

    /* ── SECTION HEADERS ── */
    .section-header {{
        display: flex; align-items: center; gap: 10px;
        background: linear-gradient(90deg, #212529 0%, rgba(33,37,41,0) 100%);
        border-left: 4px solid #fca311; border-radius: 4px;
        padding: 8px 14px; margin: 18px 0 10px 0;
    }}
    .section-header span {{ font-size: 1.05rem; font-weight: 800;
        color: #ffffff; text-transform: uppercase; letter-spacing: 0.04em; }}

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] {{ background-color: #212529 !important; border-right: 1px solid #495057; }}

    /* ── BOTÓN CERRAR SIDEBAR MÓVIL ── */
    #close-sidebar-btn {{ display: none; }}

    /* ── BANNER DATOS PENDIENTES ── */
    .banner-pendiente {{
        position: fixed; top: 0; left: 0; right: 0; z-index: 999999;
        background: linear-gradient(90deg, #fca311, #e8940a);
        color: #14213d; padding: 10px 20px;
        font-weight: 800; font-size: 0.85rem;
        text-align: center; letter-spacing: 0.05em;
        text-transform: uppercase;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}

    /* ── BOTONES SIDEBAR ── */
    .stButton>button {{
        border-radius: 50px !important; font-weight: 700 !important;
        font-size: 0.85rem !important; letter-spacing: 0.05em !important;
        text-transform: uppercase !important; width: 100% !important;
        border: none !important; background: #14213d !important;
        color: #fca311 !important; box-shadow: 0 4px 0 #fca311 !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
        padding: 10px 20px !important;
    }}
    .stButton>button:hover {{
        background: #1e3260 !important; transform: translateY(-1px) !important;
        box-shadow: 0 5px 0 #fca311 !important;
    }}
    .stButton>button:active {{ transform: translateY(4px) !important; box-shadow: none !important; }}

    /* ── BOTÓN GUARDAR ── */
    .save-btn button {{
        border-radius: 50px !important; font-weight: 800 !important;
        font-size: 1.05rem !important; letter-spacing: 0.08em !important;
        text-transform: uppercase !important; background: #fca311 !important;
        color: #14213d !important; border: none !important;
        box-shadow: 0 6px 0 #14213d !important; padding: 16px !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
    }}
    .save-btn button:hover {{
        filter: brightness(1.06) !important; transform: translateY(-1px) !important;
        box-shadow: 0 7px 0 #14213d !important;
    }}
    .save-btn button:active {{ transform: translateY(5px) !important; box-shadow: none !important; }}

    /* ── TÍTULOS ── */
    h2 {{ color: #ffffff !important; font-weight: 800 !important;
         border-bottom: 2px solid #fca311; padding-bottom: 6px; }}
    h3 {{ color: #fca311 !important; font-weight: bold !important; }}
    h4 {{ color: #adb5bd !important; font-weight: 600 !important;
         font-size: 0.9rem !important; text-transform: uppercase; }}

    /* ── DIVIDER ── */
    hr {{ border-color: rgba(252,163,17,0.3) !important; }}

    /* ── EXPANDER CONFIGURACIÓN ── */
    .streamlit-expanderHeader {{
        color: #fca311 !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 5b. SESSION STATE PARA DATOS MODIFICADOS ---
if "datos_modificados" not in st.session_state:
    st.session_state.datos_modificados = False

# --- 6. FUNCIONES DE FORMATO ---
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

# --- 7. LAYOUT BASE PLOTLY (con SF Pro) ---
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family=SF_FONT, color="#ffffff"),
)

# --- 11. PANTALLA DE LOGIN ---
if not st.session_state.autenticado:
    mostrar_login(supabase, LOGO_LOGIN)
    st.stop()

# --- 12. APP PRINCIPAL ---
u_id  = st.session_state.usuario_id
token = st.session_state.token

supabase.postgrest.auth(token)
try:
    df_g_full, df_i_full, df_oi_full = cargar_bd(supabase, u_id, token)
except Exception as e:
    if "JWT" in str(e) or "expired" in str(e).lower():
        st.warning("⚠️ Tu sesión expiró. Por favor inicia sesión nuevamente.")
        cerrar_sesion()
        st.stop()
    else:
        st.error(f"Error al cargar datos: {e}")
        st.stop()
if "Periodo" not in df_i_full.columns:
    df_i_full = pd.DataFrame(columns=["Periodo","Año","Nomina","SaldoAnterior"])
if "Periodo" not in df_g_full.columns:
    df_g_full = pd.DataFrame(columns=["Periodo","Año","Categoría","Descripción","Monto","Valor Referencia","Pagado","Movimiento Recurrente","Fecha Pago","Es Proyectado","Presupuesto Asociado"])
if "Periodo" not in df_oi_full.columns:
    df_oi_full = pd.DataFrame(columns=["Periodo","Año","Descripción","Monto"])

meses_lista = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR):
        st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")

    anio_s = st.selectbox("Año", [2026, 2027, 2028], index=0)
    mes_s  = st.selectbox("Mes Actual", meses_lista, index=datetime.now().month - 1)

    i_m_act = df_i_full[(df_i_full["Periodo"] == mes_s) & (df_i_full["Año"] == anio_s)]

    idx   = meses_lista.index(mes_s)
    m_ant = meses_lista[idx-1] if idx > 0 else "Diciembre"
    a_ant = anio_s if idx > 0 else anio_s - 1

    i_ant  = df_i_full[(df_i_full["Periodo"]==m_ant) & (df_i_full["Año"]==a_ant)]
    g_ant  = df_g_full[(df_g_full["Periodo"]==m_ant) & (df_g_full["Año"]==a_ant)]
    oi_ant = df_oi_full[(df_oi_full["Periodo"]==m_ant) & (df_oi_full["Año"]==a_ant)]

    s_sug = 0.0
    if not i_ant.empty:
        _, _, _, _, bf_a, _ = calcular_metricas(g_ant, i_ant["Nomina"].sum(), oi_ant["Monto"].sum(), i_ant["SaldoAnterior"].iloc[0])
        s_sug = float(bf_a)

    st.divider()
    arr_on = st.toggle(f"Arrastrar saldo de {m_ant} {a_ant}", value=True)

    val_s_init = s_sug if arr_on else float(i_m_act["SaldoAnterior"].iloc[0] if not i_m_act.empty else 0.0)
    s_txt = st.text_input("Saldo Anterior", value=format_moneda(val_s_init))
    s_in  = parse_moneda(s_txt)

    val_n_init = float(i_m_act["Nomina"].iloc[0] if not i_m_act.empty else 0.0)
    n_txt = st.text_input("Ingreso Fijo (Sueldo o Nomina)", value=format_moneda(val_n_init))
    n_in  = parse_moneda(n_txt)

    placeholder_otros = st.empty()

    st.divider()
    st.subheader("📑 Extractos")
    c_pdf, c_xls = st.columns(2)
    with c_pdf:
        if st.button("📄 PDF"):
            pdf = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, [mes_s], f"Extracto {mes_s}", anio_s, u_id)
            st.download_button("Descargar PDF", pdf, f"Extracto_{mes_s}.pdf")
    with c_xls:
        if st.button("📊 Excel"):
            i_m_xls  = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s)]
            oi_m_xls = df_oi_full[(df_oi_full["Periodo"]==mes_s) & (df_oi_full["Año"]==anio_s)]
            n_xls = float(i_m_xls["Nomina"].iloc[0])        if not i_m_xls.empty else 0.0
            s_xls = float(i_m_xls["SaldoAnterior"].iloc[0]) if not i_m_xls.empty else 0.0
            o_xls = float(oi_m_xls["Monto"].sum())          if not oi_m_xls.empty else 0.0
            buf_xls = generar_excel_reporte(
                df_g_full, df_i_full, df_oi_full,
                mes_s, anio_s, u_id, n_xls, o_xls, s_xls
            )
            st.download_button("Descargar Excel", buf_xls, f"Reporte_{mes_s}_{anio_s}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.subheader("⚖️ Proyecciones")
    if st.button("📥 Semestre 1"):
        p1 = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses_lista[0:6], "Balance Proyectado Enero - Junio", anio_s, u_id)
        st.download_button("Descargar S1", p1, f"Balance_S1_{anio_s}.pdf")
    if st.button("📥 Semestre 2"):
        p2 = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses_lista[6:12], "Balance Proyectado Julio - Diciembre", anio_s, u_id)
        st.download_button("Descargar S2", p2, f"Balance_S2_{anio_s}.pdf")

    st.divider()

    # ── ⚙️ CONFIGURACIÓN ──────────────────────────────────
    with st.expander("Configuración de cuenta"):
        st.markdown(
            '<p style="color:#adb5bd;font-size:0.78rem;margin-bottom:10px">'
            'Opciones avanzadas de tu cuenta</p>',
            unsafe_allow_html=True
        )
        if st.button("🗑️ Eliminar mi cuenta", key="btn_abrir_eliminar"):
            st.session_state.mostrar_eliminar = not st.session_state.get("mostrar_eliminar", False)
        if st.session_state.get("mostrar_eliminar", False):
            mostrar_eliminar_cuenta(
                supabase, token, u_id,
                st.session_state.get("u_email", "")
            )

    st.divider()
    if st.button("🚪 Salir"):
        cerrar_sesion()

# --- CUERPO PRINCIPAL ---
if os.path.exists(LOGO_APP_H):
    st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s} {anio_s}")

df_mes_g = df_g_full[(df_g_full["Periodo"]==mes_s) & (df_g_full["Año"]==anio_s)].copy()

if df_mes_g.empty:
    meses_map_r  = {m: i for i, m in enumerate(meses_lista)}
    gastos_hist  = df_g_full.copy()
    if not gastos_hist.empty:
        p_actual = (anio_s * 12) + meses_lista.index(mes_s)
        gastos_hist["lt"] = (gastos_hist["Año"] * 12) + gastos_hist["Periodo"].map(meses_map_r)
        registros_previos = gastos_hist[gastos_hist["lt"] < p_actual]
        if not registros_previos.empty:
            ultimo_lt   = registros_previos["lt"].max()
            foto        = registros_previos[registros_previos["lt"] == ultimo_lt]
            activos     = foto[foto["Movimiento Recurrente"] == True].copy()
            if not activos.empty:
                df_mes_g = activos.reindex(columns=["Categoría","Descripción","Monto","Valor Referencia","Pagado","Movimiento Recurrente"])
                df_mes_g["Pagado"]               = False
                df_mes_g["Fecha Pago"]           = pd.NaT
                df_mes_g["Es Proyectado"]        = df_mes_g.get("Es Proyectado", False)
                df_mes_g["Presupuesto Asociado"] = df_mes_g.get("Presupuesto Asociado", None)
                df_mes_g = df_mes_g.sort_values(["Categoría","Descripción"], ascending=[True,True]).reset_index(drop=True)

if "Fecha Pago" not in df_mes_g.columns:
    df_mes_g["Fecha Pago"] = pd.NaT
else:
    df_mes_g["Fecha Pago"] = pd.to_datetime(df_mes_g["Fecha Pago"], errors="coerce")
df_mes_g["Fecha Pago"] = df_mes_g["Fecha Pago"].where(df_mes_g["Fecha Pago"].notna(), other=pd.NaT)

if "Es Proyectado" not in df_mes_g.columns:
    df_mes_g["Es Proyectado"] = False
else:
    df_mes_g["Es Proyectado"] = df_mes_g["Es Proyectado"].fillna(False).astype(bool)
if "Presupuesto Asociado" not in df_mes_g.columns:
    df_mes_g["Presupuesto Asociado"] = None

descripciones_históricas = sorted(df_g_full["Descripción"].dropna().unique().tolist()) if not df_g_full.empty else []

# ══════════════════════════════════════════════════════════
# TABLA 1: GASTOS / EGRESOS PROYECTADOS
# Aquí se planifica: qué se espera gastar este mes
# ══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span>📅 Gastos / Egresos Proyectados</span></div>', unsafe_allow_html=True)
st.caption("Define aquí los gastos que proyectas para el mes. Estos sirven como presupuesto de referencia.")

# Separar filas proyectadas del df_mes_g
df_proy_rows = df_mes_g[df_mes_g["Es Proyectado"] == True].copy()
df_proy_rows["📋"] = False  # columna para copiar val.ref → monto al registrar

config_proy = {
    "Categoría":             st.column_config.SelectboxColumn("Categoría", options=LISTA_CATEGORIAS, width="medium"),
    "Descripción":           st.column_config.TextColumn("Descripción", width="large"),
    "Valor Referencia":      st.column_config.NumberColumn("Valor Proyectado", format="$ %,.0f", width="small",
                                 help="Monto que proyectas gastar en este ítem"),
    "📋":                    st.column_config.CheckboxColumn("📋 Copiar al registrar", default=False, width="small",
                                 help="Cuando registres este gasto, copia automáticamente el valor proyectado como monto"),
    "Movimiento Recurrente": st.column_config.CheckboxColumn("🔁 Recurrente", default=False, width="small",
                                 help="Se repite todos los meses automáticamente"),
}

df_base_proy = df_proy_rows.reindex(
    columns=["Categoría", "Descripción", "Valor Referencia", "📋", "Movimiento Recurrente"]
).sort_values(["Categoría", "Descripción"], ascending=[True, True]).reset_index(drop=True)

df_ed_proy = st.data_editor(
    df_base_proy,
    use_container_width=True,
    num_rows="dynamic",
    column_config=config_proy,
    key="proy_ed"
)

# Limpiar columna 📋 (es de uso visual solamente — la lógica se aplica al registrar el movimiento)
df_ed_proy_clean = df_ed_proy.copy()
df_ed_proy_clean["📋"] = df_ed_proy_clean.get("📋", False)

# Construir lista de ítems proyectados para el dropdown de la tabla de movimientos
items_proyectados = df_ed_proy_clean["Descripción"].dropna().tolist()
# Añadir también los que ya estaban guardados en BD (por si se editó la tabla proyectada antes de guardar)
items_proy_bd = df_mes_g[df_mes_g["Es Proyectado"] == True]["Descripción"].dropna().tolist()
items_proyectados = sorted(set(items_proyectados + items_proy_bd))

# ── Detectar cambios en tabla proyectados ──
if not df_ed_proy.equals(df_base_proy):
    st.session_state.datos_modificados = True

# ══════════════════════════════════════════════════════════
# TABLA 2: EDITAR / AGREGAR MOVIMIENTOS (registro diario)
# Aquí se registra lo que realmente se gastó / se pagó
# ══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span>✏️ Editar / Agregar Movimientos</span></div>', unsafe_allow_html=True)
st.caption("Registra aquí los gastos del día a día. Asocia cada uno a su ítem proyectado si aplica.")

# Filas NO proyectadas = movimientos reales del día a día
df_mov_rows = df_mes_g[df_mes_g["Es Proyectado"] == False].copy()

config_mov = {
    "Categoría":            st.column_config.SelectboxColumn("Categoría", options=LISTA_CATEGORIAS, width="medium"),
    "Descripción":          st.column_config.TextColumn("Descripción", width="large"),
    "Monto":                st.column_config.NumberColumn("Monto", format="$ %,.0f", width="small"),
    "Presupuesto Asociado": st.column_config.SelectboxColumn("Ítem Proyectado", options=items_proyectados, width="medium",
                                help="Ítem proyectado al que pertenece este gasto"),
    "Pagado":               st.column_config.CheckboxColumn("✅ Pagado", default=False, width="small"),
    "Fecha Pago":           st.column_config.DateColumn("Fecha", format="DD/MM/YY", width="small"),
}

df_base_mov = df_mov_rows.reindex(
    columns=["Categoría", "Descripción", "Monto", "Presupuesto Asociado", "Pagado", "Fecha Pago"]
).sort_values(["Categoría", "Descripción"], ascending=[True, True]).reset_index(drop=True)

# ── 📋 COPIAR AL REGISTRAR ────────────────────────────────────────────────────
# Cuando el usuario marca 📋 en un ítem proyectado, se crea automáticamente una
# fila nueva en la tabla de movimientos con Categoría, Descripción y Monto copiados.
# Si ya existe una fila con esa misma Descripción en movimientos, NO se duplica.
if not df_ed_proy_clean.empty:
    proy_con_copia = df_ed_proy_clean[df_ed_proy_clean["📋"] == True].copy()
    if not proy_con_copia.empty:
        filas_nuevas = []
        descripciones_existentes = df_base_mov["Descripción"].str.strip().str.upper().tolist()
        for _, proy_row in proy_con_copia.iterrows():
            desc_proy  = str(proy_row.get("Descripción", "")).strip()
            cat_proy   = str(proy_row.get("Categoría", ""))
            val_proy   = float(proy_row.get("Valor Referencia", 0) or 0)
            # Solo agrega si no existe ya una fila con esa descripción (sin distinción mayúsculas)
            if desc_proy.upper() not in descripciones_existentes:
                filas_nuevas.append({
                    "Categoría":            cat_proy,
                    "Descripción":          desc_proy,
                    "Monto":                val_proy,
                    "Presupuesto Asociado": desc_proy,  # se auto-asocia al proyectado
                    "Pagado":               False,
                    "Fecha Pago":           pd.NaT,
                })
            else:
                # Ya existe: solo actualiza el monto si está en 0
                mask = df_base_mov["Descripción"].str.strip().str.upper() == desc_proy.upper()
                df_base_mov.loc[mask & (df_base_mov["Monto"].fillna(0) == 0), "Monto"] = val_proy
        if filas_nuevas:
            df_nuevas = pd.DataFrame(filas_nuevas)
            df_base_mov = pd.concat([df_base_mov, df_nuevas], ignore_index=True).sort_values(
                ["Categoría", "Descripción"], ascending=[True, True]
            ).reset_index(drop=True)

df_ed_mov = st.data_editor(
    df_base_mov,
    use_container_width=True,
    num_rows="dynamic",
    column_config=config_mov,
    key="mov_ed"
)

# ── Detectar cambios en tabla de movimientos ──
if not df_ed_mov.equals(df_base_mov):
    st.session_state.datos_modificados = True

# ══════════════════════════════════════════════════════════
# RECONSTRUIR df_ed_g unificado para toda la lógica downstream
# (KPIs, gráficas, presupuesto vs ejecución, guardar)
# ══════════════════════════════════════════════════════════

# Preparar tabla proyectada con todas las columnas necesarias
df_proy_final = df_ed_proy_clean.copy()
df_proy_final["Es Proyectado"]   = True
df_proy_final["Pagado"]          = False
df_proy_final["Monto"]           = 0.0
df_proy_final["Presupuesto Asociado"] = None
df_proy_final["Fecha Pago"]      = pd.NaT
# Asegurar columna Movimiento Recurrente
if "Movimiento Recurrente" not in df_proy_final.columns:
    df_proy_final["Movimiento Recurrente"] = False

# Preparar tabla de movimientos con todas las columnas necesarias
df_mov_final = df_ed_mov.copy()
df_mov_final["Es Proyectado"]      = False
df_mov_final["Valor Referencia"]   = 0.0
df_mov_final["Movimiento Recurrente"] = False

# Unificar en df_ed_g
df_ed_g = pd.concat([df_proy_final, df_mov_final], ignore_index=True)

# Asegurar tipos
df_ed_g["Monto"]             = pd.to_numeric(df_ed_g["Monto"],           errors="coerce").fillna(0)
df_ed_g["Valor Referencia"]  = pd.to_numeric(df_ed_g["Valor Referencia"],errors="coerce").fillna(0)
df_ed_g["Pagado"]            = df_ed_g["Pagado"].fillna(False).astype(bool)
df_ed_g["Es Proyectado"]     = df_ed_g["Es Proyectado"].fillna(False).astype(bool)
df_ed_g["Movimiento Recurrente"] = df_ed_g["Movimiento Recurrente"].fillna(False).astype(bool)

# ── ANTI-DUPLICACIÓN EN KPIs ──────────────────────────────────────────────────
# Si un ítem proyectado tiene el mismo nombre (o está asociado) a un movimiento
# pagado → se marca como pagado en df_ed_g para que calcular_metricas no lo cuente
# como obligación pendiente.
_desc_pagadas_kpi = set(
    df_ed_g[df_ed_g["Pagado"] == True]["Descripción"]
    .dropna().str.strip().str.upper().tolist()
)
if "Presupuesto Asociado" in df_ed_g.columns:
    _proy_con_pago_kpi = set(
        df_ed_g[df_ed_g["Pagado"] == True]["Presupuesto Asociado"]
        .dropna().astype(str).str.strip().str.upper().tolist()
    )
    _desc_pagadas_kpi = _desc_pagadas_kpi | _proy_con_pago_kpi

for _idx, _row in df_ed_g.iterrows():
    if bool(_row.get("Es Proyectado", False)) and not bool(_row.get("Pagado", False)):
        _desc = str(_row.get("Descripción", "")).strip().upper()
        if _desc in _desc_pagadas_kpi:
            df_ed_g.loc[_idx, "Pagado"] = True  # no doble-conteo

# df_base unificado para detección de cambios
df_base = df_ed_g.copy()

st.markdown('<div class="section-header"><span>💰 Ingresos Adicionales</span></div>', unsafe_allow_html=True)
df_mes_oi = df_oi_full[(df_oi_full["Periodo"]==mes_s) & (df_oi_full["Año"]==anio_s)].copy()
df_ed_oi  = st.data_editor(
    df_mes_oi.reindex(columns=["Descripción","Monto"]).reset_index(drop=True),
    use_container_width=True, num_rows="dynamic",
    column_config={"Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f")},
    key="oi_ed"
)

# ── CALCULAR MÉTRICAS (antes de renderizar KPIs) ─────────
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0)
otr_v = float(df_ed_oi["Monto"].sum())
placeholder_otros.text_input("Otros Ingresos (Total)", value=f"$ {otr_v:,.0f}", disabled=True)
it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_v, s_in)
label_ahorro = "SALDO A FAVOR" if bf >= 0 else "DÉFICIT"

# ── BANNER DATOS PENDIENTES ──────────────────────────────
if st.session_state.get("datos_modificados", False):
    st.markdown("""
    <div class="banner-pendiente">
        ⚠️ Tienes datos pendientes por guardar — presiona 💾 GUARDAR CAMBIOS DEFINITIVOS
    </div>
    <div style="height:40px"></div>
    """, unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────
st.divider()
c_kpi = st.columns(5)
tarj = [
    ("INGRESOS",           it,   "black"),
    ("OBLIG. PAGADAS",     vp,   "green"),
    ("OBLIG. PENDIENTES",  vpy,  "red"),
    ("DINERO DISPONIBLE",  fact, "blue"),
    (label_ahorro,         bf,   "#fca311")
]
for i, (l, v, col) in enumerate(tarj):
    c_kpi[i].markdown(
        f'<div class="card"><div class="card-label">{l}</div><div class="card-value" style="color:{col}">$ {v:,.0f}</div></div>',
        unsafe_allow_html=True
    )
st.divider()

st.markdown('<div class="section-header"><span>📝 Movimiento de Gastos</span></div>', unsafe_allow_html=True)

if not df_mes_g.empty:
    df_mes_g = df_mes_g.sort_values(["Categoría","Descripción"], ascending=[True,True]).reset_index(drop=True)


def render_resumen_gastos(df):
    if df.empty:
        st.info("No hay gastos registrados para este mes.")
        return

    def make_tabla(df_sub, titulo, color_header, col_extra_label, es_pagado):
        if df_sub.empty:
            return ""
        filas = ""
        total = 0
        for i, (_, row) in enumerate(df_sub.iterrows()):
            bg    = "#2d3238" if i % 2 == 0 else "#3a3f44"
            cat   = str(row.get("Categoría",""))
            col   = COLOR_MAP.get(cat, "#aaaaaa")
            badge = f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;background:{col}22;color:{col}">{cat}</span>'
            desc  = str(row.get("Descripción",""))
            monto = float(row.get("Monto",0) or 0)
            vref  = float(row.get("Valor Referencia",0) or 0)
            val   = monto if monto > 0 else vref
            total += val
            recur = row.get("Movimiento Recurrente", False)
            recur_str = ' <span style="color:#2ecc71">🔁</span>' if recur else ""
            if es_pagado:
                fp = row.get("Fecha Pago", None)
                if fp is not None and str(fp) not in ["NaT","None",""]:
                    try: extra = pd.to_datetime(fp).strftime("%d/%m/%Y")
                    except: extra = "—"
                else: extra = "—"
            else:
                extra = f"$ {vref:,.0f}" if vref > 0 else "—"
            filas += f'<tr style="background:{bg}">'
            filas += f'<td style="padding:6px 10px">{badge}</td>'
            filas += f'<td style="padding:6px 10px;color:#fff;font-size:12px">{desc}{recur_str}</td>'
            filas += f'<td style="padding:6px 10px;color:#fff;font-size:12px;text-align:right">$ {val:,.0f}</td>'
            filas += f'<td style="padding:6px 10px;color:#adb5bd;font-size:11px;text-align:right">{extra}</td>'
            filas += '</tr>'
        filas += f'<tr style="background:{color_header}"><td colspan="2" style="padding:8px 10px;font-weight:800;font-size:12px;color:#14213d;text-transform:uppercase">TOTAL {titulo}</td><td style="padding:8px 10px;font-weight:800;font-size:13px;color:#14213d;text-align:right">$ {total:,.0f}</td><td></td></tr>'
        th = f'<th style="padding:9px 10px;color:{color_header};font-size:11px;text-transform:uppercase;font-weight:700'
        html  = '<div style="border-radius:10px;overflow:hidden;margin-bottom:12px"><table style="width:100%;border-collapse:collapse;font-family:\'SF Pro Display\',-apple-system,sans-serif"><thead><tr style="background:#14213d">'
        html += th + ';text-align:left">Categoría</th>'
        html += th + ';text-align:left">Descripción</th>'
        html += th + ';text-align:right">Monto</th>'
        html += th + f';text-align:right">{col_extra_label}</th>'
        html += f'</tr></thead><tbody>{filas}</tbody></table></div>'
        return html

    df_pagados_t  = df[df["Pagado"] == True].copy()
    df_pendientes = df[df["Pagado"] == False].copy()

    # ── ANTI-DUPLICACIÓN ───────────────────────────────────────────────────────
    # Si un ítem proyectado (Es Proyectado=True) tiene el mismo nombre que un
    # movimiento ya PAGADO en la tabla de movimientos, no aparece como pendiente.
    # Esto evita que QUINCENA OSIRIS figure como pendiente si ya fue registrada y pagada.
    descripciones_pagadas = set(
        df_pagados_t["Descripción"].dropna().str.strip().str.upper().tolist()
    )
    # También verificar si el proyectado está asociado a un movimiento pagado
    if "Presupuesto Asociado" in df.columns:
        items_proy_con_pago = set(
            df[df["Pagado"] == True]["Presupuesto Asociado"]
            .dropna().astype(str).str.strip().str.upper().tolist()
        )
        descripciones_pagadas = descripciones_pagadas | items_proy_con_pago

    def es_proyectado_ya_cubierto(row):
        """Retorna True si este ítem proyectado ya tiene un movimiento pagado asociado."""
        if not bool(row.get("Es Proyectado", False)):
            return False
        desc = str(row.get("Descripción", "")).strip().upper()
        return desc in descripciones_pagadas

    df_pend_adj = df_pendientes[
        ~df_pendientes.apply(es_proyectado_ya_cubierto, axis=1)
    ].copy()

    # Para ítems proyectados aún pendientes: descontar lo que ya fue ejecutado
    if "Es Proyectado" in df_pend_adj.columns and "Presupuesto Asociado" in df.columns:
        for idx, row in df_pend_adj.iterrows():
            if bool(row.get("Es Proyectado", False)):
                nombre = str(row.get("Descripción",""))
                _pa = df["Presupuesto Asociado"].astype(str).str.strip()
                df_asoc_pend = df[
                    (_pa == nombre.strip()) &
                    (_pa != "nan") & (_pa != "None") & (_pa != "")
                ].copy()
                df_asoc_pend["_val"]  = pd.to_numeric(df_asoc_pend["Monto"], errors="coerce").fillna(0)
                df_asoc_pend["_vref"] = pd.to_numeric(df_asoc_pend["Valor Referencia"], errors="coerce").fillna(0)
                df_asoc_pend["_real"] = df_asoc_pend["_val"].where(df_asoc_pend["_val"] > 0, df_asoc_pend["_vref"])
                asociados_monto = df_asoc_pend["_real"].sum()
                vref_orig = float(row.get("Valor Referencia", 0) or 0)
                df_pend_adj.loc[idx, "Valor Referencia"] = max(vref_orig - asociados_monto, 0)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div style="color:#2ecc71;font-weight:800;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px">✅ Obligaciones Pagadas</div>', unsafe_allow_html=True)
        html_p = make_tabla(df_pagados_t, "PAGADO", "#2ecc71", "Fecha Pago", True)
        if html_p: st.markdown(html_p, unsafe_allow_html=True)
        else: st.info("Sin pagos registrados.")
    with col2:
        st.markdown('<div style="color:#e74c3c;font-weight:800;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px">⏳ Obligaciones Pendientes</div>', unsafe_allow_html=True)
        html_n = make_tabla(df_pend_adj, "PENDIENTE", "#fca311", "Val.Ref", False)
        if html_n: st.markdown(html_n, unsafe_allow_html=True)
        else: st.success("¡Sin obligaciones pendientes!")


render_resumen_gastos(df_mes_g)

# ══════════════════════════════════════════════
# PRESUPUESTO VS EJECUCIÓN POR CATEGORÍA
# ══════════════════════════════════════════════
st.markdown('<div class="section-header"><span>📊 Presupuesto vs Ejecución por Categoría</span></div>', unsafe_allow_html=True)

df_mes_bd = df_g_full[
    (df_g_full["Periodo"] == mes_s) &
    (df_g_full["Año"] == anio_s)
].copy()

df_proyectados = df_mes_bd[df_mes_bd["Es Proyectado"] == True].copy() if "Es Proyectado" in df_mes_bd.columns else pd.DataFrame()

if "Presupuesto Asociado" in df_mes_bd.columns:
    _pa = df_mes_bd["Presupuesto Asociado"].astype(str).str.strip()
    df_asociados = df_mes_bd[
        _pa.notna() & (_pa != "") & (_pa != "None") & (_pa != "nan") & (_pa != "NaN")
    ].copy()
else:
    df_asociados = pd.DataFrame()

cats_con_ref   = df_ed_g[df_ed_g["Valor Referencia"] > 0].groupby("Categoría")["Valor Referencia"].sum()
df_pagados     = df_ed_g[df_ed_g["Pagado"] == True] if "Pagado" in df_ed_g.columns else pd.DataFrame()
cats_ejecutado = df_pagados.groupby("Categoría")["Monto"].sum() if not df_pagados.empty else pd.Series(dtype=float)
todas_cats     = sorted(cats_con_ref.index.tolist())

if todas_cats:
    tarjetas_html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;margin-bottom:16px;">'
    for cat in todas_cats:
        presup    = float(cats_con_ref.get(cat, 0))
        ejecutado = float(cats_ejecutado.get(cat, 0))
        color     = COLOR_MAP.get(cat, "#aaaaaa")
        if presup > 0:
            disponible = presup - ejecutado
            pct        = min((ejecutado / presup * 100), 100) if presup > 0 else 0
            excedido   = ejecutado > presup
            bar_color  = "#e74c3c" if excedido else color
            disp_color = "#e74c3c" if excedido else "#2ecc71"
            disp_label = "Excedido" if excedido else "Disponible"
            disp_val   = abs(disponible)
            pct_txt    = f"⚠️ {ejecutado/presup*100:.0f}% — Excedido" if excedido else f"{pct:.0f}% usado"
            pct_color  = "#e74c3c" if excedido else color
            tarjetas_html += f"""
            <div style="background:#3a3f44;border-radius:10px;padding:12px 14px;border-left:4px solid {color}">
              <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.05em;color:{color};margin-bottom:8px">{cat}</div>
              <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                <div style="text-align:center"><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Presupuesto</div><div style="font-size:13px;font-weight:700;color:#fca311">$ {presup:,.0f}</div></div>
                <div style="text-align:center"><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Ejecutado</div><div style="font-size:13px;font-weight:700;color:#ffffff">$ {ejecutado:,.0f}</div></div>
                <div style="text-align:center"><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">{disp_label}</div><div style="font-size:13px;font-weight:700;color:{disp_color}">$ {disp_val:,.0f}</div></div>
              </div>
              <div style="background:#2d3238;border-radius:20px;height:8px;overflow:hidden;margin-top:4px">
                <div style="width:{pct:.0f}%;height:8px;border-radius:20px;background:{bar_color}"></div>
              </div>
              <div style="display:flex;justify-content:space-between;margin-top:4px">
                <span style="font-size:10px;color:#adb5bd">0%</span>
                <span style="font-size:10px;font-weight:700;color:{pct_color}">{pct_txt}</span>
                <span style="font-size:10px;color:#adb5bd">100%</span>
              </div>
            </div>"""
        else:
            tarjetas_html += f"""
            <div style="background:#3a3f44;border-radius:10px;padding:12px 14px;border-left:4px solid {color}">
              <div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.05em;color:{color};margin-bottom:8px">{cat}</div>
              <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                <div style="text-align:center"><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Presupuesto</div><div style="font-size:12px;font-weight:700;color:#6c757d">Sin definir</div></div>
                <div style="text-align:center"><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Ejecutado</div><div style="font-size:13px;font-weight:700;color:#ffffff">$ {ejecutado:,.0f}</div></div>
                <div style="text-align:center"><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Disponible</div><div style="font-size:12px;font-weight:700;color:#6c757d">—</div></div>
              </div>
              <div style="background:#2d3238;border-radius:20px;height:8px;margin-top:4px"></div>
              <div style="text-align:center;margin-top:4px"><span style="font-size:10px;color:#6c757d">Sin presupuesto asignado</span></div>
            </div>"""
    tarjetas_html += '</div>'
    st.markdown(tarjetas_html, unsafe_allow_html=True)
else:
    st.info("Agrega movimientos con Valor de Referencia para ver el presupuesto vs ejecución.")

# ── SEGUIMIENTO POR ÍTEM PROYECTADO ──────────────────────
if not df_proyectados.empty:
    st.markdown('<div class="section-header"><span>🎯 Seguimiento de Ítems Proyectados</span></div>', unsafe_allow_html=True)
    items_html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;margin-bottom:16px;">'
    for _, proy in df_proyectados.iterrows():
        nombre_proy = str(proy["Descripción"])
        presup_item = float(proy.get("Valor Referencia", 0) or 0)
        cat         = str(proy.get("Categoría",""))
        color       = COLOR_MAP.get(cat, "#aaaaaa")
        if not df_asociados.empty and "Presupuesto Asociado" in df_asociados.columns:
            match = df_asociados[df_asociados["Presupuesto Asociado"].astype(str).str.strip() == nombre_proy.strip()]
            gastos_item = float(pd.to_numeric(match["Monto"], errors="coerce").fillna(0).sum())
        else:
            gastos_item = 0.0
        disponible = presup_item - gastos_item
        excedido   = gastos_item > presup_item
        pct        = min((gastos_item / presup_item * 100), 100) if presup_item > 0 else 0
        bar_color  = "#e74c3c" if excedido else color
        disp_color = "#e74c3c" if excedido else "#2ecc71"
        disp_label = "Excedido" if excedido else "Disponible"
        pct_txt    = f"⚠️ {gastos_item/presup_item*100:.0f}% — Excedido" if excedido else f"{pct:.0f}% ejecutado"
        gastos_lista = ""
        if not df_asociados.empty and "Presupuesto Asociado" in df_asociados.columns:
            assoc = df_asociados[df_asociados["Presupuesto Asociado"] == nombre_proy]
            for _, ag in assoc.iterrows():
                gastos_lista += f'<div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #495057"><span style="font-size:10px;color:#adb5bd">{ag["Descripción"]}</span><span style="font-size:10px;color:#fff">$ {float(ag["Monto"]):,.0f}</span></div>'
        bloque_gastos = ""
        if gastos_lista:
            bloque_gastos = '<div style="border-top:1px solid #495057;padding-top:6px">' + gastos_lista + '</div>'
        card  = '<div style="background:#3a3f44;border-radius:10px;padding:12px 14px;border-left:4px solid ' + color + '">'
        card += '<div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.05em;color:' + color + ';margin-bottom:6px">💰 ' + nombre_proy + '</div>'
        card += '<div style="font-size:9px;color:#adb5bd;margin-bottom:8px">' + cat + '</div>'
        card += '<div style="display:flex;justify-content:space-between;margin-bottom:8px">'
        card += '<div style="text-align:center"><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Presupuesto</div><div style="font-size:13px;font-weight:700;color:#fca311">$ ' + f"{presup_item:,.0f}" + '</div></div>'
        card += '<div style="text-align:center"><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Ejecutado</div><div style="font-size:13px;font-weight:700;color:#fff">$ ' + f"{gastos_item:,.0f}" + '</div></div>'
        card += '<div style="text-align:center"><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">' + disp_label + '</div><div style="font-size:13px;font-weight:700;color:' + disp_color + '">$ ' + f"{abs(disponible):,.0f}" + '</div></div>'
        card += '</div>'
        card += '<div style="background:#2d3238;border-radius:20px;height:8px;overflow:hidden">'
        card += '<div style="width:' + f"{pct:.0f}" + '%;height:8px;border-radius:20px;background:' + bar_color + '"></div></div>'
        card += '<div style="display:flex;justify-content:space-between;margin-top:4px;margin-bottom:8px">'
        card += '<span style="font-size:10px;color:#adb5bd">0%</span>'
        card += '<span style="font-size:10px;font-weight:700;color:' + bar_color + '">' + pct_txt + '</span>'
        card += '<span style="font-size:10px;color:#adb5bd">100%</span></div>'
        card += bloque_gastos + '</div>'
        items_html += card
    items_html += '</div>'
    st.markdown(items_html, unsafe_allow_html=True)

# ── GRÁFICAS ─────────────────────────────────────────────
st.markdown('<div class="section-header"><span>📊 Análisis de Distribución</span></div>', unsafe_allow_html=True)
inf1, inf2, inf3 = st.columns([1.2, 1, 1.2])

with inf1:
    st.markdown('<div class="chart-card"><div class="chart-title">Desglose de Gastos</div>', unsafe_allow_html=True)
    t_df = df_ed_g.copy()
    t_df['V'] = t_df.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    if not t_df.empty and t_df['V'].sum() > 0:
        total_v = t_df['V'].sum()
        res = t_df.groupby("Categoría")['V'].sum().reset_index()
        res['pct'] = res['V'] / total_v * 100
        res = res.sort_values('V', ascending=False)
        barras_html = ""
        for _, r in res.iterrows():
            c_cat = COLOR_MAP.get(r['Categoría'], "#6c757d")
            pct   = r['pct']
            monto = r['V']
            barras_html += f"""
            <div style="margin-bottom:6px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
                <span style="font-size:0.78rem; font-weight:700; color:#ffffff;">{r['Categoría']}</span>
                <span style="font-size:0.78rem; color:#ffffff;">$ {monto:,.0f} &nbsp;<b style="color:{c_cat};">{pct:.1f}%</b></span>
              </div>
              <div style="background:#2d3238; border-radius:6px; height:10px; width:100%;">
                <div style="background:{c_cat}; width:{pct:.1f}%; height:10px; border-radius:6px;"></div>
              </div>
            </div>
            """
        st.markdown(barras_html, unsafe_allow_html=True)

with inf2:
    st.markdown('<div class="chart-card"><div class="chart-title">Eficiencia de Ahorro</div>', unsafe_allow_html=True)
    v_cl = max(0, min(ahorro_p, 100))
    META = 20
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=v_cl,
        number={
            'suffix': "%",
            'font': {'color': '#fca311', 'size': 50, 'family': SF_FONT},
            'valueformat': '.0f'
        },
        gauge={
            'axis': {'range': [0, 100], 'tickfont': {'family': SF_FONT, 'color': '#ffffff'}},
            'bar': {'color': "#fca311"},
            'bgcolor': "white",
            'steps': [
                {'range': [0, META],  'color': '#f8d7da'},
                {'range': [META, 100],'color': '#d4edda'},
            ],
            'threshold': {
                'line': {'color': "#2ecc71", 'width': 3},
                'thickness': 0.85,
                'value': META
            }
        }
    ))
    fig2.update_layout(**PLOTLY_LAYOUT, height=280, margin=dict(t=50,b=0,l=25,r=25))
    st.plotly_chart(fig2, use_container_width=True)
    if v_cl >= META:
        st.markdown(f'<div style="text-align:center;color:#2ecc71;font-weight:bold;font-size:0.85rem">✅ ¡Meta alcanzada! Ahorraste {v_cl:.0f}% (Meta: {META}%)</div>', unsafe_allow_html=True)
    else:
        falta = META - v_cl
        st.markdown(f'<div style="text-align:center;color:#e74c3c;font-weight:bold;font-size:0.85rem">⚠️ Te falta {falta:.0f}% para la meta recomendada del {META}%</div>', unsafe_allow_html=True)

with inf3:
    st.markdown('<div class="chart-card"><div class="chart-title">Estado Real del Dinero</div>', unsafe_allow_html=True)
    centro_valor = format_moneda(bf)
    centro_label = "FAVOR" if bf >= 0 else "DÉFICIT"
    centro_color = "#fca311" if bf >= 0 else "#e74c3c"
    fig3 = go.Figure(data=[go.Pie(
        labels=['Pagado','Pendiente','Ahorro'],
        values=[vp, vpy, bf if bf > 0 else 0],
        hole=.7,
        marker_colors=['#2ecc71','#e74c3c','#fca311'],
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>$ %{value:,.0f}<br>%{percent}<extra></extra>'
    )])
    fig3.update_layout(
        **PLOTLY_LAYOUT,
        showlegend=False,
        height=250,
        margin=dict(t=0,b=0,l=0,r=0),
        annotations=[
            dict(text=centro_label, x=0.5, y=0.58, font_size=13, showarrow=False,
                 font_color="#495057", font=dict(family=SF_FONT)),
            dict(text=centro_valor, x=0.5, y=0.42, font_size=15, showarrow=False,
                 font_color=centro_color, font=dict(family=SF_FONT)),
        ]
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown(f'<div class="legend-bar" style="background:#2ecc71">Obligaciones Pagadas <span>$ {vp:,.0f}</span></div>',    unsafe_allow_html=True)
    st.markdown(f'<div class="legend-bar" style="background:#e74c3c">Obligaciones Pendientes <span>$ {vpy:,.0f}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="legend-bar" style="background:#fca311">{label_ahorro} <span>$ {bf:,.0f}</span></div>',          unsafe_allow_html=True)

# --- GUARDAR ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="save-btn">', unsafe_allow_html=True)
if st.button("💾  GUARDAR CAMBIOS DEFINITIVOS", use_container_width=True):
    # df_ed_g ya es el DataFrame unificado (proyectados + movimientos)
    # Solo descartamos filas completamente vacías
    df_g_limpio = df_ed_g.dropna(subset=["Categoría", "Descripción"], how="all")
    # Para proyectados sin monto (monto = 0) los mantenemos, son válidos si tienen Valor Referencia
    df_g_limpio = df_g_limpio[
        (df_g_limpio["Valor Referencia"] > 0) | (df_g_limpio["Monto"] > 0) |
        (df_g_limpio["Descripción"].notna() & (df_g_limpio["Descripción"].str.strip() != ""))
    ].copy()
    df_oi_limpio = df_ed_oi.dropna(subset=["Descripción","Monto"], how="all")
    if df_g_limpio.empty and df_oi_limpio.empty and n_in == 0:
        st.error("🛑 No hay datos suficientes para guardar.")
    else:
        try:
            with st.spinner("Sincronizando con Supabase..."):
                guardar_bd(supabase, token, u_id, mes_s, anio_s,
                           df_g_limpio, df_oi_limpio, s_in, n_in, otr_v)
                st.session_state.datos_modificados = False
                st.balloons()
                st.success("✅ ¡Todo guardado y sincronizado de forma segura!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")
