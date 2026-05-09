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
from data    import cargar_bd, calcular_metricas, guardar_bd, cargar_bd_usuario, cargar_vinculos, buscar_usuario_por_email
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

def calcular_pendientes(df):
    """
    Lógica unificada de pendientes — usada tanto en KPIs como en la tabla visual.

    Casos:
    A) Proyectado con Es Referencia=True  → aparece con saldo (Valor Ref - ejecutado asociado).
                                            Si saldo=0 → desaparece.
    B) Proyectado con Es Referencia=False → aparece como pendiente normal por su Valor Referencia,
                                            SALVO que ya exista un movimiento real PAGADO con
                                            la misma Descripción → desaparece.
    C) Movimiento normal sin Presupuesto Asociado, no pagado → aparece normal por su Monto.
    D) Movimiento con Presupuesto Asociado cuyo proyectado tiene Es Referencia=True
                                          → NO aparece solo (absorbido por el proyectado).
    E) Movimiento con Presupuesto Asociado cuyo proyectado tiene Es Referencia=False
                                          → aparece normal por su Monto.
    """
    if df.empty:
        return pd.DataFrame(columns=df.columns)

    col_pa = "Presupuesto Asociado"

    # ── Set de ítems proyectados CON referencia activa ────────────────────────
    items_con_referencia = set()
    if "Es Referencia" in df.columns and "Es Proyectado" in df.columns:
        items_con_referencia = set(
            df[
                (df["Es Proyectado"].fillna(False).astype(bool)) &
                (df["Es Referencia"].fillna(False).astype(bool))
            ]["Descripción"].dropna().str.strip().str.upper().tolist()
        )

    # ── Set de descripciones ya PAGADAS en movimientos reales ─────────────────
    # (filas que NO son proyectadas y tienen Pagado=True)
    df_movs_reales = df[df["Es Proyectado"].fillna(False).astype(bool) == False]
    descripciones_pagadas = set(
        df_movs_reales[df_movs_reales["Pagado"].fillna(False).astype(bool)]
        ["Descripción"].dropna().str.strip().str.upper().tolist()
    )
    # También incluir ítems asociados a proyectados con referencia que estén pagados
    if col_pa in df.columns:
        items_proy_pagados = set(
            df[df["Pagado"].fillna(False).astype(bool)][col_pa]
            .dropna().astype(str).str.strip().str.upper().tolist()
        ) - {"", "NAN", "NONE", "NAN"}
        descripciones_pagadas = descripciones_pagadas | items_proy_pagados

    # ── Mapa de ejecución para ítems CON referencia ───────────────────────────
    mapa_ejecutado       = {}
    mapa_pagado_completo = {}
    if col_pa in df.columns and items_con_referencia:
        df_asoc = df[
            df[col_pa].notna() &
            (~df[col_pa].astype(str).str.strip().isin(["", "nan", "None", "NaN"]))
        ].copy()
        df_asoc["_monto"] = pd.to_numeric(df_asoc["Monto"], errors="coerce").fillna(0)
        df_asoc["_key"]   = df_asoc[col_pa].astype(str).str.strip().str.upper()
        df_asoc = df_asoc[df_asoc["_key"].isin(items_con_referencia)]
        for key, grp in df_asoc.groupby("_key"):
            mapa_ejecutado[key]       = float(grp["_monto"].sum())
            mapa_pagado_completo[key] = bool(grp["Pagado"].fillna(False).all())

    df_pendientes = df[df["Pagado"].fillna(False).astype(bool) == False].copy()
    filas_pendientes = []

    for _, row in df_pendientes.iterrows():
        es_proy = bool(row.get("Es Proyectado", False))
        es_ref  = bool(row.get("Es Referencia", False))
        col_pa_v = str(row.get(col_pa, "")).strip() if col_pa in df.columns else ""
        tiene_asociado = col_pa_v not in ("", "nan", "None", "NaN")
        desc_key = str(row.get("Descripción", "")).strip().upper()

        if es_proy:
            if es_ref:
                # Caso A: proyectado con referencia → saldo disponible
                vref      = float(row.get("Valor Referencia", 0) or 0)
                ejecutado = mapa_ejecutado.get(desc_key, 0.0)
                pag_comp  = mapa_pagado_completo.get(desc_key, False)
                saldo     = max(vref - ejecutado, 0)
                if saldo == 0 or (pag_comp and ejecutado >= vref):
                    continue
                fila = row.copy()
                fila["Valor Referencia"] = saldo
                filas_pendientes.append(fila)
            else:
                # Caso B: proyectado sin referencia → solo si NO hay movimiento pagado igual
                if desc_key in descripciones_pagadas:
                    continue  # ya fue pagado → no duplicar
                filas_pendientes.append(row)

        elif tiene_asociado:
            key_pa = col_pa_v.upper()
            if key_pa in items_con_referencia:
                continue  # Caso D: absorbido por proyectado con referencia
            else:
                filas_pendientes.append(row)  # Caso E: aparece normal

        else:
            # Caso C: movimiento normal sin asociado
            filas_pendientes.append(row)

    return pd.DataFrame(filas_pendientes).reset_index(drop=True) if filas_pendientes else pd.DataFrame(columns=df.columns)

# --- 7. LAYOUT BASE PLOTLY (con SF Pro) ---
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family=SF_FONT, color="#ffffff"),
)

# --- 11. PANTALLA DE LOGIN ---
if not st.session_state.autenticado:

    # ── Detectar token de recuperación ──────────────────────
    # Cuando Supabase redirige después de verificar, añade el access_token
    # en el hash. Lo capturamos con JS y redirigimos con query param.
    _recovery_token = st.query_params.get("recovery_token", "")

    if not _recovery_token:
        # JS que lee el hash y redirige con query param legible por Streamlit
        st.components.v1.html("""
        <script>
        (function() {
            var hash = window.parent.location.hash || window.location.hash;
            if (hash && hash.indexOf('type=recovery') !== -1) {
                var pairs = hash.replace('#','').split('&');
                var token = '';
                for (var i = 0; i < pairs.length; i++) {
                    var kv = pairs[i].split('=');
                    if (kv[0] === 'access_token') { token = decodeURIComponent(kv[1]); break; }
                }
                if (token) {
                    var base = window.parent.location.href.split('#')[0].split('?')[0];
                    window.parent.location.replace(base + '?recovery_token=' + encodeURIComponent(token));
                }
            }
        })();
        </script>
        """, height=0)
        mostrar_login(supabase, LOGO_LOGIN)
        st.stop()

    # ── Formulario de nueva contraseña ────────────────────────
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN):
            st.image(LOGO_LOGIN, use_container_width=True)
        st.markdown("### 🔓 Crear nueva contraseña")
        st.caption("Ingresa tu nueva contraseña para acceder a tu cuenta.")

        nueva_pwd  = st.text_input("Nueva contraseña", type="password", key="nueva_pwd",
                                    placeholder="Mínimo 8 caracteres, una mayúscula y un número")
        nueva_pwd2 = st.text_input("Confirmar contraseña", type="password", key="nueva_pwd2",
                                    placeholder="Repite la contraseña")

        if st.button("✅ Guardar nueva contraseña", use_container_width=True, key="btn_nueva_pwd"):
            if not nueva_pwd or not nueva_pwd2:
                st.error("❌ Por favor completa ambos campos.")
            elif nueva_pwd != nueva_pwd2:
                st.error("❌ Las contraseñas no coinciden.")
            else:
                from auth import _validar_password
                valida, msg = _validar_password(nueva_pwd)
                if not valida:
                    st.error(f"❌ {msg}")
                else:
                    try:
                        # Establecer sesión con el access_token antes de actualizar
                        _refresh_token = st.query_params.get("refresh_token", "")
                        res_session = supabase.auth.set_session(
                            access_token=_recovery_token,
                            refresh_token=_refresh_token if _refresh_token else _recovery_token
                        )
                        if res_session and res_session.session:
                            supabase.postgrest.auth(res_session.session.access_token)
                            supabase.auth.update_user({"password": nueva_pwd})
                            st.success("✅ ¡Contraseña actualizada correctamente!")
                            st.info("Ya puedes ingresar con tu nueva contraseña.")
                            st.query_params.clear()
                            import time; time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Sesión inválida. Solicita un nuevo enlace de recuperación.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}. Solicita un nuevo enlace.")
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
    df_g_full = pd.DataFrame(columns=["Periodo","Año","Categoría","Descripción","Monto","Valor Referencia","Pagado","Movimiento Recurrente","Fecha Pago","Es Proyectado","Presupuesto Asociado","Es Referencia"])
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
        mostrar_eliminar_cuenta(
            supabase, token, u_id,
            st.session_state.get("u_email", "")
        )

        # ── Desvincular usuarios ───────────────────────────
        _vinculos_cfg = cargar_vinculos(supabase, u_id, token)
        _vinculos_activos_cfg = [v for v in _vinculos_cfg if v.get("estado") == "activo"]
        if _vinculos_activos_cfg:
            st.markdown("---")
            st.markdown('<p style="color:#adb5bd;font-size:0.78rem;margin-bottom:6px">Vínculos activos</p>', unsafe_allow_html=True)
            for _v in _vinculos_activos_cfg:
                _otro_id   = _v["usuario_id_b"] if str(_v.get("usuario_id_a","")) == str(u_id) else _v["usuario_id_a"]
                _nombre_g  = _v.get("nombre_grupo", "Finanzas Grupales")
                try:
                    _r_n = supabase.table("usuarios").select("nombre_completo").eq("usuario_id", _otro_id).execute()
                    _nombre_otro = _r_n.data[0]["nombre_completo"] if _r_n.data else "Usuario vinculado"
                except:
                    _nombre_otro = "Usuario vinculado"
                col_vk1, col_vk2 = st.columns([2, 1])
                with col_vk1:
                    st.caption(f"👥 {_nombre_g}\n{_nombre_otro}")
                with col_vk2:
                    if st.button("🔗 Desvincular", key=f"btn_desvincular_{_v['id']}"):
                        st.session_state[f"confirmar_desvincular_{_v['id']}"] = True
                        st.rerun()
                if st.session_state.get(f"confirmar_desvincular_{_v['id']}"):
                    st.warning(f"⚠️ ¿Seguro que quieres desvincular **{_nombre_g}**? El otro usuario también perderá acceso a la vista consolidada.")
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        if st.button("✅ Sí, desvincular", key=f"btn_ok_desv_{_v['id']}"):
                            try:
                                supabase.postgrest.auth(token)
                                supabase.table("vinculos_usuarios").delete().eq("id", _v["id"]).execute()
                                st.session_state.pop(f"confirmar_desvincular_{_v['id']}", None)
                                st.session_state["vista_consolidada"] = False
                                st.success("✅ Vínculo eliminado correctamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    with col_c2:
                        if st.button("✗ Cancelar", key=f"btn_cancel_desv_{_v['id']}"):
                            st.session_state.pop(f"confirmar_desvincular_{_v['id']}", None)
                            st.rerun()

    # ── 👥 VISTA CONSOLIDADA ───────────────────────────────
    vinculos_activos  = cargar_vinculos(supabase, u_id, token)
    vinculos_aceptados = [v for v in vinculos_activos if v.get("estado") == "activo"]

    st.divider()
    if vinculos_aceptados:
        if st.sidebar.button("👥 Vista Consolidada", use_container_width=True, key="btn_vista_cons"):
            st.session_state["vista_consolidada"] = not st.session_state.get("vista_consolidada", False)
            st.rerun()
        if st.session_state.get("vista_consolidada"):
            st.sidebar.caption("✅ Vista consolidada activa")
    else:
        with st.expander("👥 Finanzas Grupales"):
            st.caption("Vincula tu cuenta con otro usuario para ver un dashboard consolidado.")
            email_vincular = st.text_input("Email del otro usuario", key="email_vincular", placeholder="usuario@ejemplo.com")
            nombre_grupo   = st.text_input("Nombre del grupo", key="nombre_grupo", placeholder="Ej: Familia García")
            if st.button("📨 Enviar invitación", key="btn_invitar", use_container_width=True):
                if not email_vincular:
                    st.error("❌ Ingresa un email.")
                elif email_vincular.strip().lower() == st.session_state.get("u_email","").lower():
                    st.error("❌ No puedes vincularte contigo mismo.")
                else:
                    try:
                        import uuid as _uuid, smtplib
                        from email.mime.text import MIMEText
                        from email.mime.multipart import MIMEMultipart

                        _token_inv = str(_uuid.uuid4())[:8].upper()
                        supabase.postgrest.auth(token)
                        supabase.table("vinculos_usuarios").insert({
                            "usuario_id_a":      str(u_id),
                            "email_b":           email_vincular.strip().lower(),
                            "nombre_grupo":      nombre_grupo.strip() or "Finanzas Grupales",
                            "estado":            "pendiente",
                            "token_invitacion":  _token_inv
                        }).execute()

                        # Enviar correo de invitación
                        _gmail_user = st.secrets.get("gmail", {}).get("email", "")
                        _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")
                        _nombre_a   = st.session_state.get("u_nombre_completo", "Un usuario")
                        if _gmail_user and _gmail_pass:
                            _msg = MIMEMultipart("alternative")
                            _msg["Subject"] = f"👥 {_nombre_a} te invita a compartir finanzas en My FinanceApp"
                            _msg["From"]    = _gmail_user
                            _msg["To"]      = email_vincular.strip()
                            _html = f"""
                            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
                                <h2 style="color:#fca311">👥 Invitación a Finanzas Grupales</h2>
                                <p><b>{_nombre_a}</b> te ha invitado a compartir un dashboard financiero consolidado en <b>My FinanceApp</b>.</p>
                                <p><b>Grupo:</b> {nombre_grupo.strip() or "Finanzas Grupales"}</p>
                                <div style="background:#f8f9fa;border-radius:8px;padding:16px;margin:20px 0;text-align:center">
                                    <p style="margin:0;font-size:0.9rem;color:#495057">Tu código de invitación:</p>
                                    <p style="font-size:2rem;font-weight:800;color:#fca311;margin:8px 0;letter-spacing:0.2em">{_token_inv}</p>
                                    <p style="margin:0;font-size:0.8rem;color:#6c757d">Ingresa este código en My FinanceApp → Finanzas Grupales → Aceptar invitación</p>
                                </div>
                                <p style="color:#adb5bd;font-size:0.8rem">Si no conoces a esta persona, ignora este correo.</p>
                            </div>
                            """
                            _msg.attach(MIMEText(_html, "html"))
                            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as _smtp:
                                _smtp.login(_gmail_user, _gmail_pass)
                                _smtp.sendmail(_gmail_user, email_vincular.strip(), _msg.as_string())
                        st.success(f"✅ Invitación enviada a {email_vincular}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

            st.divider()
            st.caption("¿Tienes un código de invitación?")
            codigo_inv = st.text_input("Código de invitación", key="codigo_inv", placeholder="Ej: AB12CD34").upper()
            if st.button("✅ Aceptar invitación", key="btn_aceptar_inv", use_container_width=True):
                if not codigo_inv:
                    st.error("❌ Ingresa el código.")
                else:
                    try:
                        supabase.postgrest.auth(token)
                        r_inv = supabase.table("vinculos_usuarios").select("*").eq("token_invitacion", codigo_inv).eq("estado", "pendiente").execute()
                        if not r_inv.data:
                            st.error("❌ Código inválido o ya usado.")
                        else:
                            vinculo = r_inv.data[0]
                            supabase.table("vinculos_usuarios").update({
                                "usuario_id_b": str(u_id),
                                "estado": "activo"
                            }).eq("id", vinculo["id"]).execute()
                            st.success("✅ ¡Vinculación exitosa! Recarga la app para ver la Vista Consolidada.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    st.divider()
    if st.button("🚪 Salir"):
        cerrar_sesion()

# --- CUERPO PRINCIPAL ---

# ══════════════════════════════════════════════════════════
# VISTA CONSOLIDADA (si está activa)
# ══════════════════════════════════════════════════════════
if st.session_state.get("vista_consolidada") and vinculos_aceptados:
    if os.path.exists(LOGO_APP_H):
        st.image(LOGO_APP_H, use_container_width=True)

    st.markdown(f"## 👥 Dashboard Consolidado — {mes_s} {anio_s}")
    st.caption("Vista combinada de todos los usuarios vinculados.")

    # Botón para volver al dashboard personal
    if st.button("◀ Volver a mi dashboard personal", key="btn_salir_consolidado"):
        st.session_state["vista_consolidada"] = False
        st.rerun()

    # Cargar datos de todos los usuarios vinculados
    todos_g  = [df_g_full.copy()]
    todos_i  = [df_i_full.copy()]
    todos_oi = [df_oi_full.copy()]
    nombres_usuarios = [st.session_state.get("u_nombre_completo", "Yo")]

    for v in vinculos_aceptados:
        otro_id = v["usuario_id_b"] if str(v["usuario_id_a"]) == str(u_id) else v["usuario_id_a"]
        if otro_id:
            _g, _i, _oi = cargar_bd_usuario(supabase, otro_id, token)
            todos_g.append(_g)
            todos_i.append(_i)
            todos_oi.append(_oi)
            # Buscar nombre del otro usuario
            try:
                r_n = supabase.table("usuarios").select("nombre_completo").eq("usuario_id", otro_id).execute()
                nombres_usuarios.append(r_n.data[0]["nombre_completo"] if r_n.data else "Usuario vinculado")
            except:
                nombres_usuarios.append("Usuario vinculado")

    # Consolidar datos del mes
    df_g_cons  = pd.concat([g[(g["Periodo"]==mes_s) & (g["Año"]==anio_s)] for g in todos_g if not g.empty], ignore_index=True) if todos_g else pd.DataFrame()
    df_i_cons  = pd.concat([i[(i["Periodo"]==mes_s) & (i["Año"]==anio_s)] for i in todos_i if not i.empty], ignore_index=True) if todos_i else pd.DataFrame()
    df_oi_cons = pd.concat([oi[(oi["Periodo"]==mes_s) & (oi["Año"]==anio_s)] for oi in todos_oi if not oi.empty], ignore_index=True) if todos_oi else pd.DataFrame()

    # Métricas consolidadas
    nom_cons = float(df_i_cons["Nomina"].sum()) if not df_i_cons.empty and "Nomina" in df_i_cons.columns else 0.0
    sal_cons = float(df_i_cons["SaldoAnterior"].sum()) if not df_i_cons.empty else 0.0
    otr_cons = float(df_oi_cons["Monto"].sum()) if not df_oi_cons.empty else 0.0
    it_c, vp_c, vpy_c, fact_c, bf_c, aho_c = calcular_metricas(df_g_cons, nom_cons, otr_cons, sal_cons)
    label_bf_c = "SALDO A FAVOR" if bf_c >= 0 else "DÉFICIT"

    # ── KPIs consolidados ─────────────────────────────────
    st.divider()
    c_kpi_c = st.columns(5)
    tarj_c = [
        ("INGRESOS TOTALES", it_c,   "black"),
        ("OBLIG. PAGADAS",   vp_c,   "green"),
        ("OBLIG. PENDIENTES",vpy_c,  "red"),
        ("DINERO DISPONIBLE",fact_c, "blue"),
        (label_bf_c,         bf_c,   "#fca311")
    ]
    for i, (l, v, col) in enumerate(tarj_c):
        c_kpi_c[i].markdown(
            f'<div class="card"><div class="card-label">{l}</div>'
            f'<div class="card-value" style="color:{col}">$ {v:,.0f}</div></div>',
            unsafe_allow_html=True
        )
    st.divider()

    # ── Resumen por usuario ───────────────────────────────
    st.markdown('<div class="section-header"><span>👤 Resumen por Usuario</span></div>', unsafe_allow_html=True)
    cols_u = st.columns(len(nombres_usuarios))
    for idx_u, (nombre_u, df_g_u, df_i_u, df_oi_u) in enumerate(zip(nombres_usuarios, todos_g, todos_i, todos_oi)):
        df_g_m  = df_g_u[(df_g_u["Periodo"]==mes_s) & (df_g_u["Año"]==anio_s)] if not df_g_u.empty else pd.DataFrame()
        df_i_m  = df_i_u[(df_i_u["Periodo"]==mes_s) & (df_i_u["Año"]==anio_s)] if not df_i_u.empty else pd.DataFrame()
        df_oi_m = df_oi_u[(df_oi_u["Periodo"]==mes_s) & (df_oi_u["Año"]==anio_s)] if not df_oi_u.empty else pd.DataFrame()
        nom_u = float(df_i_m["Nomina"].sum()) if not df_i_m.empty else 0.0
        sal_u = float(df_i_m["SaldoAnterior"].sum()) if not df_i_m.empty else 0.0
        otr_u = float(df_oi_m["Monto"].sum()) if not df_oi_m.empty else 0.0
        it_u, vp_u, vpy_u, _, bf_u, _ = calcular_metricas(df_g_m, nom_u, otr_u, sal_u)
        color_bf = "#2ecc71" if bf_u >= 0 else "#e74c3c"
        with cols_u[idx_u]:
            st.markdown(f"""
            <div style="background:#3a3f44;border-radius:12px;padding:16px;border-top:3px solid #fca311;text-align:center">
                <div style="font-size:0.85rem;font-weight:800;color:#fca311;margin-bottom:12px;text-transform:uppercase">{nombre_u}</div>
                <div style="display:flex;justify-content:space-around;margin-bottom:8px">
                    <div><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Ingresos</div><div style="font-size:12px;font-weight:700;color:#fff">$ {it_u:,.0f}</div></div>
                    <div><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Pagado</div><div style="font-size:12px;font-weight:700;color:#2ecc71">$ {vp_u:,.0f}</div></div>
                    <div><div style="font-size:9px;color:#adb5bd;text-transform:uppercase">Pendiente</div><div style="font-size:12px;font-weight:700;color:#e74c3c">$ {vpy_u:,.0f}</div></div>
                </div>
                <div style="font-size:11px;color:#adb5bd">Saldo a favor</div>
                <div style="font-size:1.4rem;font-weight:800;color:{color_bf}">$ {bf_u:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Gastos por categoría consolidado ──────────────────
    st.markdown('<div class="section-header"><span>📊 Gastos Consolidados por Categoría</span></div>', unsafe_allow_html=True)
    if not df_g_cons.empty:
        df_g_cons["_v"] = df_g_cons.apply(
            lambda r: float(r.get("Monto",0) or 0) if float(r.get("Monto",0) or 0) > 0
                      else float(r.get("Valor Referencia",0) or 0), axis=1
        )
        por_cat_c = df_g_cons.groupby("Categoría")["_v"].sum().sort_values(ascending=False)
        total_c   = por_cat_c.sum()
        barras_c  = ""
        for cat_c, val_c in por_cat_c.items():
            if val_c > 0:
                color_c = COLOR_MAP.get(cat_c, "#6c757d")
                pct_c   = val_c / total_c * 100 if total_c > 0 else 0
                barras_c += f"""
                <div style="margin-bottom:8px">
                    <div style="display:flex;justify-content:space-between;margin-bottom:2px">
                        <span style="font-size:0.8rem;color:#fff;font-weight:700">{cat_c}</span>
                        <span style="font-size:0.8rem;color:#fff">$ {val_c:,.0f} <b style="color:{color_c}">{pct_c:.1f}%</b></span>
                    </div>
                    <div style="background:#2d3238;border-radius:6px;height:10px">
                        <div style="background:{color_c};width:{pct_c:.1f}%;height:10px;border-radius:6px"></div>
                    </div>
                </div>"""
        st.markdown(barras_c, unsafe_allow_html=True)

    # ── Extractos consolidados ────────────────────────────
    st.divider()
    st.markdown('<div class="section-header"><span>📑 Extractos del Dashboard Consolidado</span></div>', unsafe_allow_html=True)
    col_pdf_c, col_xls_c = st.columns(2)
    with col_pdf_c:
        if st.button("📄 PDF Consolidado", use_container_width=True, key="btn_pdf_cons"):
            try:
                pdf_c = generar_pdf_reporte(
                    df_g_cons, df_i_cons, df_oi_cons,
                    [mes_s], f"Consolidado {mes_s} — {' + '.join(nombres_usuarios)}", anio_s, u_id
                )
                st.download_button("⬇️ Descargar PDF", pdf_c, f"Consolidado_{mes_s}.pdf", key="dl_pdf_cons")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    with col_xls_c:
        if st.button("📊 Excel Consolidado", use_container_width=True, key="btn_xls_cons"):
            try:
                buf_xls_c = generar_excel_reporte(
                    df_g_cons, df_i_cons, df_oi_cons,
                    mes_s, anio_s, u_id, nom_cons, otr_cons, sal_cons
                )
                st.download_button("⬇️ Descargar Excel", buf_xls_c, f"Consolidado_{mes_s}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_xls_cons")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    st.stop()  # No mostrar el dashboard individual si estamos en vista consolidada
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
        # ── CORRECCIÓN RECURRENTE ──────────────────────────────────────────────
        # Solo propagar desde el mes INMEDIATAMENTE anterior (p_actual - 1),
        # no desde el último mes con datos. Así, si en el mes anterior se desactivó
        # un recurrente, no vuelve a aparecer en el mes actual.
        p_anterior = p_actual - 1
        foto_anterior = gastos_hist[gastos_hist["lt"] == p_anterior]
        if not foto_anterior.empty:
            # Solo los que tienen Movimiento Recurrente = True en ese mes exacto
            activos = foto_anterior[foto_anterior["Movimiento Recurrente"] == True].copy()
            if not activos.empty:
                df_mes_g = activos.reindex(columns=["Categoría","Descripción","Monto","Valor Referencia","Pagado","Movimiento Recurrente","Es Proyectado","Presupuesto Asociado","Es Referencia"])
                df_mes_g["Pagado"]               = False
                df_mes_g["Fecha Pago"]           = pd.NaT
                df_mes_g["Es Proyectado"]        = df_mes_g["Es Proyectado"].fillna(False)
                df_mes_g["Presupuesto Asociado"] = df_mes_g["Presupuesto Asociado"].where(
                    df_mes_g["Presupuesto Asociado"].notna(), other=None
                )
                df_mes_g = df_mes_g.sort_values(["Categoría","Descripción"], ascending=[True,True]).reset_index(drop=True)
        # Si no hay datos en el mes anterior inmediato, el mes queda vacío (sin propagar)

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
if "Es Referencia" not in df_mes_g.columns:
    df_mes_g["Es Referencia"] = False
else:
    df_mes_g["Es Referencia"] = df_mes_g["Es Referencia"].fillna(False).astype(bool)

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
if "Es Referencia" not in df_proy_rows.columns:
    df_proy_rows["Es Referencia"] = False

config_proy = {
    "Categoría":             st.column_config.SelectboxColumn("Categoría", options=LISTA_CATEGORIAS, width="medium"),
    "Descripción":           st.column_config.TextColumn("Descripción", width="large"),
    "Valor Referencia":      st.column_config.NumberColumn("Valor Proyectado", format="$ %,.0f", width="small",
                                 help="Monto que proyectas gastar en este ítem"),
    "Es Referencia":         st.column_config.CheckboxColumn("📌 Referencia", default=False, width="small",
                                 help="Activa para hacer seguimiento de este ítem: aparecerá en Pendientes y en Seguimiento de Proyectados"),
    "📋":                    st.column_config.CheckboxColumn("📋 Copiar al registrar", default=False, width="small",
                                 help="Copia automáticamente el valor proyectado como monto al registrar el movimiento"),
    "Movimiento Recurrente": st.column_config.CheckboxColumn("🔁 Recurrente", default=False, width="small",
                                 help="Se repite todos los meses automáticamente"),
}

df_base_proy = df_proy_rows.reindex(
    columns=["Categoría", "Descripción", "Valor Referencia", "Es Referencia", "📋", "Movimiento Recurrente"]
).sort_values(["Categoría", "Descripción"], ascending=[True, True]).reset_index(drop=True)

df_ed_proy = st.data_editor(
    df_base_proy,
    use_container_width=True,
    num_rows="dynamic",
    column_config=config_proy,
    key="proy_ed",
    on_change=lambda: st.session_state.update({"datos_modificados": True})
)

# Limpiar columna 📋 (es de uso visual solamente — la lógica se aplica al registrar el movimiento)
df_ed_proy_clean = df_ed_proy.copy()
df_ed_proy_clean["📋"] = df_ed_proy_clean.get("📋", False)
if "Es Referencia" not in df_ed_proy_clean.columns:
    df_ed_proy_clean["Es Referencia"] = False
df_ed_proy_clean["Es Referencia"] = df_ed_proy_clean["Es Referencia"].fillna(False).astype(bool)

# ── Solo los ítems con 📌 Referencia activo aparecen en el dropdown de movimientos ──
items_referencia = df_ed_proy_clean[
    df_ed_proy_clean["Es Referencia"] == True
]["Descripción"].dropna().tolist()
# También incluir los ya guardados en BD con referencia activa
if "Es Referencia" in df_mes_g.columns:
    items_ref_bd = df_mes_g[
        (df_mes_g["Es Proyectado"] == True) & (df_mes_g["Es Referencia"] == True)
    ]["Descripción"].dropna().tolist()
    items_referencia = sorted(set(items_referencia + items_ref_bd))
else:
    items_referencia = sorted(set(items_referencia))

# (mantener lista completa para compatibilidad interna)
items_proyectados = items_referencia

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
if not df_ed_proy_clean.empty:
    proy_con_copia = df_ed_proy_clean[df_ed_proy_clean["📋"] == True].copy()
    if not proy_con_copia.empty:
        filas_nuevas = []
        descripciones_existentes = df_base_mov["Descripción"].str.strip().str.upper().tolist()
        for _, proy_row in proy_con_copia.iterrows():
            desc_proy  = str(proy_row.get("Descripción", "")).strip()
            cat_proy   = str(proy_row.get("Categoría", ""))
            val_proy   = float(proy_row.get("Valor Referencia", 0) or 0)
            if desc_proy.upper() not in descripciones_existentes:
                filas_nuevas.append({
                    "Categoría":            cat_proy,
                    "Descripción":          desc_proy,
                    "Monto":                val_proy,
                    "Presupuesto Asociado": desc_proy,
                    "Pagado":               False,
                    "Fecha Pago":           pd.NaT,
                })
            else:
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
    key="mov_ed",
    on_change=lambda: st.session_state.update({"datos_modificados": True})
)

# ══════════════════════════════════════════════════════════
# RECONSTRUIR df_ed_g unificado para toda la lógica downstream
# (KPIs, gráficas, presupuesto vs ejecución, guardar)
# ══════════════════════════════════════════════════════════

# Preparar tabla proyectada con todas las columnas necesarias
df_proy_final = df_ed_proy_clean.copy()
df_proy_final["Es Proyectado"]        = True
df_proy_final["Pagado"]               = False
df_proy_final["Monto"]                = 0.0
df_proy_final["Presupuesto Asociado"] = None
df_proy_final["Fecha Pago"]           = pd.NaT
if "Es Referencia" not in df_proy_final.columns:
    df_proy_final["Es Referencia"] = False
df_proy_final["Es Referencia"] = df_proy_final["Es Referencia"].fillna(False).astype(bool)
if "Movimiento Recurrente" not in df_proy_final.columns:
    df_proy_final["Movimiento Recurrente"] = False

# Preparar tabla de movimientos con todas las columnas necesarias
df_mov_final = df_ed_mov.copy()
df_mov_final["Es Proyectado"]         = False
df_mov_final["Valor Referencia"]      = 0.0
df_mov_final["Movimiento Recurrente"] = False
df_mov_final["Es Referencia"]         = False

# Unificar en df_ed_g
df_ed_g = pd.concat([df_proy_final, df_mov_final], ignore_index=True)

# Asegurar tipos
df_ed_g["Monto"]             = pd.to_numeric(df_ed_g["Monto"],           errors="coerce").fillna(0)
df_ed_g["Valor Referencia"]  = pd.to_numeric(df_ed_g["Valor Referencia"],errors="coerce").fillna(0)
df_ed_g["Pagado"]            = df_ed_g["Pagado"].fillna(False).astype(bool)
df_ed_g["Es Proyectado"]     = df_ed_g["Es Proyectado"].fillna(False).astype(bool)
df_ed_g["Movimiento Recurrente"] = df_ed_g["Movimiento Recurrente"].fillna(False).astype(bool)

# ── ANTI-DUPLICACIÓN EN KPIs ──────────────────────────────────────────────────
# Ítems proyectados con Referencia activa que ya tienen movimientos asociados pagados
# se marcan como pagados para que calcular_metricas no los cuente como pendientes dobles.
if "Es Referencia" in df_ed_g.columns and "Presupuesto Asociado" in df_ed_g.columns:
    _proy_con_pago_kpi = set(
        df_ed_g[df_ed_g["Pagado"] == True]["Presupuesto Asociado"]
        .dropna().astype(str).str.strip().str.upper().tolist()
    )
    for _idx, _row in df_ed_g.iterrows():
        if (bool(_row.get("Es Proyectado", False)) and
            bool(_row.get("Es Referencia", False)) and
            not bool(_row.get("Pagado", False))):
            _desc     = str(_row.get("Descripción","")).strip().upper()
            _vref     = float(_row.get("Valor Referencia", 0) or 0)
            # Calcular ejecutado para este ítem
            _movs_k   = df_ed_g[
                df_ed_g["Presupuesto Asociado"].astype(str).str.strip().str.upper() == _desc
            ]
            _ejecutado = float(pd.to_numeric(_movs_k["Monto"], errors="coerce").fillna(0).sum())
            _pag_comp  = bool(_movs_k["Pagado"].fillna(False).all()) if not _movs_k.empty else False
            if _pag_comp and _ejecutado >= _vref:
                df_ed_g.loc[_idx, "Pagado"] = True

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

# Métricas base
it, vp, _vpy_old, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_v, s_in)

# ── vpy desde calcular_pendientes → mismo número que la tabla visual ──
_df_pend_kpi = calcular_pendientes(df_ed_g)
if not _df_pend_kpi.empty:
    _df_pend_kpi["_val"] = _df_pend_kpi.apply(
        lambda r: float(r.get("Monto", 0) or 0) if float(r.get("Monto", 0) or 0) > 0
                  else float(r.get("Valor Referencia", 0) or 0),
        axis=1
    )
    vpy = float(_df_pend_kpi["_val"].sum())
else:
    vpy = 0.0

# Recalcular fact y bf con el vpy correcto
it_total = float(s_in) + float(n_in) + float(otr_v)
fact     = it_total - vp
bf       = fact - vpy
ahorro_p = (bf / it_total * 100) if it_total > 0 else 0.0
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

    df_pagados_t = df[df["Pagado"].fillna(False).astype(bool) == True].copy()
    df_pend_adj  = calcular_pendientes(df)  # ← usa la función unificada

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div style="color:#2ecc71;font-weight:800;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px">✅ Obligaciones Pagadas</div>', unsafe_allow_html=True)
        html_p = make_tabla(df_pagados_t, "PAGADO", "#2ecc71", "Fecha Pago", True)
        if html_p: st.markdown(html_p, unsafe_allow_html=True)
        else: st.info("Sin pagos registrados.")
    with col2:
        st.markdown('<div style="color:#e74c3c;font-weight:800;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px">⏳ Obligaciones Pendientes</div>', unsafe_allow_html=True)
        html_n = make_tabla(df_pend_adj, "PENDIENTE", "#fca311", "Disponible", False)
        if html_n: st.markdown(html_n, unsafe_allow_html=True)
        else: st.success("¡Sin obligaciones pendientes!")


render_resumen_gastos(df_ed_g)

# ══════════════════════════════════════════════
# PRESUPUESTO VS EJECUCIÓN POR CATEGORÍA
# ══════════════════════════════════════════════
st.markdown('<div class="section-header"><span>📊 Presupuesto vs Ejecución por Categoría</span></div>', unsafe_allow_html=True)

df_mes_bd = df_g_full[
    (df_g_full["Periodo"] == mes_s) &
    (df_g_full["Año"] == anio_s)
].copy()

# Solo ítems proyectados con 📌 Referencia activa
if "Es Referencia" not in df_mes_bd.columns:
    df_mes_bd["Es Referencia"] = False
df_proyectados = df_mes_bd[
    (df_mes_bd.get("Es Proyectado", pd.Series(False, index=df_mes_bd.index)).fillna(False).astype(bool)) &
    (df_mes_bd.get("Es Referencia", pd.Series(False, index=df_mes_bd.index)).fillna(False).astype(bool))
].copy() if not df_mes_bd.empty else pd.DataFrame()

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

# ══════════════════════════════════════════════════════════
# 🤖 ASESOR IA DE FINANZAS PERSONALES (Google Gemini)
# ══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span>🤖 Asesor IA de Finanzas</span></div>', unsafe_allow_html=True)

with st.expander("💡 Obtener diagnóstico y recomendaciones personalizadas", expanded=False):
    st.caption("Gemini analiza tus flujos del mes y actúa como tu asesor de finanzas personales.")

    # ── Construir contexto financiero ─────────────────────
    resumen_cats = ""
    if not df_ed_g.empty:
        t_df = df_ed_g.copy()
        t_df["_v"] = t_df.apply(lambda r: float(r.get("Monto",0) or 0) if float(r.get("Monto",0) or 0) > 0 else float(r.get("Valor Referencia",0) or 0), axis=1)
        por_cat = t_df.groupby("Categoría")["_v"].sum().sort_values(ascending=False)
        for cat, val in por_cat.items():
            if val > 0:
                resumen_cats += f"  - {cat}: ${val:,.0f}\n"

    resumen_proyectados = ""
    df_proy_ia = df_ed_g[df_ed_g["Es Proyectado"] == True].copy()
    if not df_proy_ia.empty:
        for _, pr in df_proy_ia.iterrows():
            desc_p = str(pr.get("Descripción",""))
            vref_p = float(pr.get("Valor Referencia", 0) or 0)
            key_p  = desc_p.strip().upper()
            ejec_p = 0.0
            if "Presupuesto Asociado" in df_ed_g.columns:
                movs_p = df_ed_g[df_ed_g["Presupuesto Asociado"].astype(str).str.strip().str.upper() == key_p]
                ejec_p = float(pd.to_numeric(movs_p["Monto"], errors="coerce").fillna(0).sum())
            pct_p = (ejec_p / vref_p * 100) if vref_p > 0 else 0
            resumen_proyectados += f"  - {desc_p}: proyectado ${vref_p:,.0f} / ejecutado ${ejec_p:,.0f} ({pct_p:.0f}%)\n"

    prompt_contexto = f"""Eres un asesor experto en finanzas personales. Analiza los datos financieros del mes de {mes_s} {anio_s} y genera un diagnóstico claro, directo y útil en español. Sé específico con los números.

DATOS DEL MES:
- Ingresos totales: ${it:,.0f}
- Saldo anterior: ${s_in:,.0f}
- Nómina: ${n_in:,.0f}
- Otros ingresos: ${otr_v:,.0f}
- Obligaciones pagadas: ${vp:,.0f}
- Obligaciones pendientes: ${vpy:,.0f}
- Dinero disponible: ${fact:,.0f}
- {label_ahorro}: ${bf:,.0f}
- Eficiencia de ahorro: {ahorro_p:.1f}% (meta recomendada: 20%)

GASTOS POR CATEGORÍA:
{resumen_cats if resumen_cats else "  Sin datos"}

ÍTEMS PROYECTADOS VS EJECUCIÓN:
{resumen_proyectados if resumen_proyectados else "  Sin proyectados definidos"}

Genera un diagnóstico con estas secciones (usa emojis):
1. 📊 Estado General del Mes (2-3 frases sobre la salud financiera)
2. ⚠️ Alertas y Riesgos (identifica gastos problemáticos o riesgos concretos)
3. ✅ Puntos Positivos (qué está funcionando bien)
4. 💡 Recomendaciones (3-5 acciones concretas y priorizadas)
5. 🎯 Meta del Próximo Mes (1 objetivo específico y alcanzable)

Sé directo, usa los números reales, habla como asesor financiero de confianza."""

    # ── Botón ─────────────────────────────────────────────
    btn_diagnostico = st.button("🔍 Generar Diagnóstico IA", key="btn_ia", use_container_width=True)

    if btn_diagnostico:
        try:
            import requests as _req
            _groq_key = st.secrets.get("groq", {}).get("api_key", "")
            if not _groq_key:
                st.error("❌ API Key no configurada. Contacta al administrador.")
            else:
                _url = "https://api.groq.com/openai/v1/chat/completions"
                _headers = {
                    "Authorization": f"Bearer {_groq_key}",
                    "Content-Type": "application/json"
                }
                _body = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt_contexto}],
                    "max_tokens": 1200,
                    "temperature": 0.7
                }
                with st.spinner("🤖 Analizando tus finanzas..."):
                    _r = _req.post(_url, headers=_headers, json=_body, timeout=30)
                if _r.status_code == 200:
                    _txt = _r.json()["choices"][0]["message"]["content"]
                    st.session_state["ia_diagnostico"] = _txt
                else:
                    _msg = _r.json().get("error", {}).get("message", _r.text)
                    st.error(f"❌ Error: {_msg}")
        except Exception as e_ia:
            st.error(f"❌ Error: {str(e_ia)[:200]}")

    # ── Resultado ─────────────────────────────────────────
    if st.session_state.get("ia_diagnostico"):
        st.markdown("---")
        st.markdown(
            f'<div style="background:#2d3238;border-radius:12px;padding:20px 24px;'
            f'border-left:4px solid #fca311;line-height:1.8;font-size:0.92rem;color:#f8f9fa">'
            f'{st.session_state["ia_diagnostico"].replace(chr(10), "<br>")}'
            f'</div>',
            unsafe_allow_html=True
        )
        if st.button("🗑️ Limpiar diagnóstico", key="btn_limpiar_ia"):
            st.session_state["ia_diagnostico"] = ""
            st.rerun()




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
