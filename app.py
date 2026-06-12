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
from finance_data import cargar_bd, calcular_metricas, guardar_bd, guardar_billeteras, calcular_saldo_billeteras, cargar_config, guardar_config, cargar_bd_usuario, cargar_vinculos, buscar_usuario_por_email, cargar_transferencias, guardar_transferencia, eliminar_transferencia, guardar_ingresos_proyectados
from reportes_v2 import generar_pdf_reporte, generar_excel_reporte, generar_pdf_proyeccion

# --- HELPERS DE FORMATO DE MONTOS (separador de miles estilo CO) ---
def _fmt_miles(x):
    """Convierte un número a texto '$ 400.000' con separador de miles '.'."""
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        v = float(x)
    except (TypeError, ValueError):
        return ""
    return f"$ {v:,.0f}".replace(",", ".")

def _money_column(label, help=None, width=None):
    """Crea una TextColumn alineada a la derecha para mostrar montos formateados."""
    cfg = st.column_config.TextColumn(label, help=help, width=width)
    cfg["alignment"] = "right"
    return cfg

def _parse_miles(x):
    """Convierte texto con separador de miles '.' de vuelta a número (ej: '400.000' -> 400000.0)."""
    if x is None:
        return 0.0
    if isinstance(x, (int, float)):
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0
    s = str(x).strip()
    if s == "" or s.lower() in ("none", "nan"):
        return 0.0
    s = s.replace("$", "").replace(" ", "").replace(".", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="My FinanceApp by Stulio Designs", layout="wide", page_icon="💰")

# --- 2. INICIALIZACIÓN DE SESSION STATE ---
for key, default in {
    "autenticado": False,
    "token": None,
    "usuario_id": None,
    "u_nombre_completo": "",
    "mostrar_eliminar": False,
    "cierre_mes_por_periodo": {},
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
    "Gastos Estacionamientos",
    "Obligaciones Financieras", "Salud", "Educación",
    "Cuidado Personal", "Mascotas", "Viajes y Recreación", "Suscripciones",
    "Seguros", "Ahorro e Inversión", "Impuestos", "Imprevistos", "Otros"
]

COLOR_MAP = {
    "Hogar": "#fca311", "Servicios": "#77B5FE", "Alimentación": "#77DD77",
    "Transporte": "#FF6961", "Gasto Vehiculos": "#FDFD96",
    "Obligaciones Financieras": "#84b6f4", "Salud": "#fdcae1",
    "Educación": "#B39EB5", "Cuidado Personal": "#FFD1DC",
    "Mascotas": "#CFCFCF", "Viajes y Recreación": "#AEC6CF",
    "Suscripciones": "#cfcfc4",
    "Gastos Estacionamientos": "#8ecae6",
    "Seguros": "#836953", "Ahorro e Inversión": "#d4af37",
    "Impuestos": "#ffda9e", "Imprevistos": "#ff6b6b", "Otros": "#b2e2f2"
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
    if df.empty:
        return pd.DataFrame(columns=df.columns)

    col_pa = "Presupuesto Asociado"

    items_con_referencia = set()
    if "Es Referencia" in df.columns and "Es Proyectado" in df.columns:
        items_con_referencia = set(
            df[
                (df["Es Proyectado"].fillna(False).astype(bool)) &
                (df["Es Referencia"].fillna(False).astype(bool))
            ]["Descripción"].dropna().str.strip().str.upper().tolist()
        )

    df_movs_reales = df[df["Es Proyectado"].fillna(False).astype(bool) == False]
    descripciones_pagadas = set(
        df_movs_reales[df_movs_reales["Pagado"].fillna(False).astype(bool)]
        ["Descripción"].dropna().str.strip().str.upper().tolist()
    )
    if col_pa in df.columns:
        items_proy_pagados = set(
            df[df["Pagado"].fillna(False).astype(bool)][col_pa]
            .dropna().astype(str).str.strip().str.upper().tolist()
        ) - {"", "NAN", "NONE", "NAN"}
        descripciones_pagadas = descripciones_pagadas | items_proy_pagados

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
        es_proy  = bool(row.get("Es Proyectado", False))
        es_ref   = bool(row.get("Es Referencia", False))
        col_pa_v = str(row.get(col_pa, "")).strip() if col_pa in df.columns else ""
        tiene_asociado = col_pa_v not in ("", "nan", "None", "NaN")
        desc_key = str(row.get("Descripción", "")).strip().upper()

        if es_proy:
            if es_ref:
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
                if desc_key in descripciones_pagadas:
                    continue
                filas_pendientes.append(row)
        elif tiene_asociado:
            key_pa = col_pa_v.upper()
            if key_pa in items_con_referencia:
                continue
            else:
                filas_pendientes.append(row)
        else:
            filas_pendientes.append(row)

    return pd.DataFrame(filas_pendientes).reset_index(drop=True) if filas_pendientes else pd.DataFrame(columns=df.columns)

# --- 7. LAYOUT BASE PLOTLY ---
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family=SF_FONT, color="#ffffff"),
)

# --- 11. PANTALLA DE LOGIN ---
if not st.session_state.autenticado:

    _recovery_token = st.query_params.get("recovery_token", "")

    if not _recovery_token:
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
    df_g_full, df_i_full, df_oi_full, df_b_full, df_sab_full, df_ip_full = cargar_bd(supabase, u_id, token)
    cfg_usuario = cargar_config(supabase, u_id, token)
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
if "Periodo" not in df_ip_full.columns:
    df_ip_full = pd.DataFrame(columns=["Periodo","Año","Descripción","Valor Proyectado","Destino Copia","Movimiento Recurrente"])

meses_lista = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

_hoy = datetime.now()
_mes_real  = meses_lista[_hoy.month - 1]
_anio_real = _hoy.year

# ── FUNCIÓN REUTILIZABLE: enviar extracto + proyección por correo ──
def enviar_correo_extracto_proyeccion(dest_email, nombre_user, mes_s, anio_s,
                                       df_g_full, df_i_full, df_oi_full, u_id):
    """Envía al correo del usuario el extracto del mes (mes_s/anio_s) y la
    proyección simple del mes siguiente. Devuelve (ok: bool, mensaje: str)."""
    try:
        import smtplib, os as _os
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        from email.mime.image import MIMEImage

        _idx_actual = meses_lista.index(mes_s)
        _mes_sig  = meses_lista[_idx_actual + 1] if _idx_actual < 11 else "Enero"
        _anio_sig = anio_s if _idx_actual < 11 else anio_s + 1

        _gmail_user = st.secrets.get("gmail", {}).get("email", "")
        _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")
        if not _gmail_user or not _gmail_pass:
            return False, "Credenciales de Gmail no configuradas en secrets."
        if not dest_email:
            return False, "El usuario no tiene email registrado."

        _pdf_actual = generar_pdf_reporte(
            df_g_full, df_i_full, df_oi_full, [mes_s], f"Extracto {mes_s}", anio_s, u_id
        )
        _pdf_proy = generar_pdf_proyeccion(
            df_g_full, df_i_full, df_oi_full, _mes_sig, _anio_sig, u_id
        )

        _nombre_user = (nombre_user or "").split(" ")[0] or "amig@"

        _msg = MIMEMultipart("mixed")
        _msg["Subject"] = f"📄 Tu extracto de {mes_s} {anio_s} ya está listo — My FinanceApp"
        _msg["From"]    = _gmail_user
        _msg["To"]      = dest_email

        _msg_alt = MIMEMultipart("related")
        _html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
            <div style="text-align:center;margin-bottom:20px">
                <img src="cid:logo_finance" alt="My FinanceApp" style="max-width:280px;width:100%;height:auto">
            </div>
            <h2 style="color:#fca311">¡Hola {_nombre_user}! 👋</h2>
            <p>Aquí tienes tu resumen financiero del mes 🎉</p>
            <p>Te dejamos adjuntos:</p>
            <ul>
                <li>📄 <b>Extracto de {mes_s} {anio_s}</b> — todo lo que pasó con tus finanzas este mes.</li>
                <li>🔮 <b>Proyección de {_mes_sig} {_anio_sig}</b> — para que llegues preparad@ al siguiente mes.</li>
            </ul>
            <p>Recuerda registrar tus movimientos a tiempo para que tus proyecciones sean cada vez más
            precisas. ¡Tú puedes! 💪</p>
            <p style="color:#adb5bd;font-size:0.8rem;margin-top:30px">
            Recibes este correo porque activaste el envío automático mensual en
            "Configuración de cuenta" de My FinanceApp. Puedes desactivarlo cuando quieras.</p>
        </div>
        """
        _msg_alt.attach(MIMEText(_html, "html"))

        _logo_path = _os.path.join(_os.path.dirname(__file__), LOGO_APP_H)
        if _os.path.exists(_logo_path):
            with open(_logo_path, "rb") as _f:
                _img = MIMEImage(_f.read())
                _img.add_header("Content-ID", "<logo_finance>")
                _img.add_header("Content-Disposition", "inline", filename=LOGO_APP_H)
                _msg_alt.attach(_img)

        _msg.attach(_msg_alt)

        for _pdf_obj, _fname in [
            (_pdf_actual, f"Extracto_{mes_s}_{anio_s}.pdf"),
            (_pdf_proy,   f"Proyeccion_{_mes_sig}_{_anio_sig}.pdf"),
        ]:
            _pdf_bytes = _pdf_obj.getvalue() if hasattr(_pdf_obj, "getvalue") else _pdf_obj
            _adj = MIMEApplication(_pdf_bytes, _subtype="pdf")
            _adj.add_header("Content-Disposition", "attachment", filename=_fname)
            _msg.attach(_adj)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as _smtp:
            _smtp.login(_gmail_user, _gmail_pass)
            _smtp.sendmail(_gmail_user, dest_email, _msg.as_string())

        return True, f"Correo enviado a {dest_email}"
    except Exception as e:
        return False, str(e)


# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR):
        st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")

    anio_s = st.selectbox("Año", [2026, 2027, 2028], index=0)
    mes_s  = st.selectbox("Mes Actual", meses_lista, index=datetime.now().month - 1)

    _periodo_key = f"{mes_s}_{anio_s}"
    df_transferencias_full = cargar_transferencias(supabase, u_id, token, mes_s, anio_s)

    i_m_act = df_i_full[(df_i_full["Periodo"] == mes_s) & (df_i_full["Año"] == anio_s)]

    idx   = meses_lista.index(mes_s)
    m_ant = meses_lista[idx-1] if idx > 0 else "Diciembre"
    a_ant = anio_s if idx > 0 else anio_s - 1

    i_ant  = df_i_full[(df_i_full["Periodo"]==m_ant) & (df_i_full["Año"]==a_ant)]
    g_ant  = df_g_full[(df_g_full["Periodo"]==m_ant) & (df_g_full["Año"]==a_ant)]
    oi_ant = df_oi_full[(df_oi_full["Periodo"]==m_ant) & (df_oi_full["Año"]==a_ant)]

    s_sug = 0.0
    if not i_ant.empty:
        _nom_ant = float(i_ant["Nomina"].sum())
        _otr_ant = float(oi_ant["Monto"].sum()) if not oi_ant.empty else 0.0
        _sal_ant = float(i_ant["SaldoAnterior"].iloc[0])
        # Ingresos proyectados del mes anterior que aún no fueron migrados
        _ip_ant = df_ip_full[
            (df_ip_full["Periodo"] == m_ant) & (df_ip_full["Año"] == a_ant)
        ] if not df_ip_full.empty else pd.DataFrame()
        _total_ip_ant = float(_ip_ant["Valor Proyectado"].sum()) if not _ip_ant.empty else 0.0
        _it_ant  = _sal_ant + _nom_ant + _otr_ant  # Ingresos Proyectados ya NO suman al Saldo a Favor
        _vp_ant  = float(g_ant[g_ant["Pagado"].fillna(False).astype(bool)]["Monto"].sum()) if not g_ant.empty else 0.0
        _pend_ant = calcular_pendientes(g_ant)
        if not _pend_ant.empty:
            _pend_ant["_v"] = _pend_ant.apply(
                lambda r: float(r.get("Monto",0) or 0) if float(r.get("Monto",0) or 0) > 0
                          else float(r.get("Valor Referencia",0) or 0), axis=1
            )
            _vpy_ant = float(_pend_ant["_v"].sum())
        else:
            _vpy_ant = 0.0
        s_sug = _it_ant - _vp_ant - _vpy_ant

    st.divider()
    arr_on = st.toggle(f"Arrastrar saldo de {m_ant} {a_ant}", value=True)

    val_s_init = s_sug if arr_on else float(i_m_act["SaldoAnterior"].iloc[0] if not i_m_act.empty else 0.0)
    s_txt = st.text_input("Saldo Anterior", value=format_moneda(val_s_init))
    s_in  = parse_moneda(s_txt)

    val_n_init = float(i_m_act["Nomina"].iloc[0] if not i_m_act.empty else 0.0)
    n_txt = st.text_input("Ingreso Fijo (Sueldo o Nomina)", value=format_moneda(val_n_init))
    n_in  = parse_moneda(n_txt)

    # ── Lista de billeteras del usuario ───────────────────
    lista_billeteras = df_b_full["nombre"].tolist() if not df_b_full.empty else []
    opciones_bill    = [""] + lista_billeteras

    # ── Determinar si billeteras están activas para este periodo ──
    _bill_desde_p = cfg_usuario.get("billeteras_desde_periodo", None)
    _bill_desde_a = cfg_usuario.get("billeteras_desde_anio", None)
    if _bill_desde_p and _bill_desde_a:
        _idx_act  = meses_lista.index(mes_s)   if mes_s   in meses_lista else 0
        _idx_desd = meses_lista.index(_bill_desde_p) if _bill_desde_p in meses_lista else 0
        modulo_billeteras_activo = (
            int(anio_s) > int(_bill_desde_a) or
            (int(anio_s) == int(_bill_desde_a) and _idx_act >= _idx_desd)
        )
    else:
        modulo_billeteras_activo = False

    bill_nomina  = ""
    df_sab_input = pd.DataFrame(columns=["billetera","monto"])

    if modulo_billeteras_activo and lista_billeteras:
        # Billetera del ingreso fijo
        _bill_nom_saved = ""
        if not i_m_act.empty and "Billetera" in i_m_act.columns:
            _bill_nom_saved = str(i_m_act["Billetera"].iloc[0] or "")
        _bill_nom_idx = opciones_bill.index(_bill_nom_saved) if _bill_nom_saved in opciones_bill else 0
        bill_nomina = st.selectbox(
            "💳 Billetera del ingreso fijo",
            options=opciones_bill,
            index=_bill_nom_idx,
            key="sel_bill_nomina"
        )

        # ── Saldo inicial por billetera ───────────────────
        with st.expander("💳 Saldo por billetera", expanded=True):
            st.caption("Digita el saldo actual de cada billetera.")

            # Leer saldos guardados para el mes actual
            _sab_mes = df_sab_full[
                (df_sab_full["Periodo"] == mes_s) & (df_sab_full["Año"] == anio_s)
            ] if not df_sab_full.empty else pd.DataFrame()
            _sab_dict = {}
            if not _sab_mes.empty:
                for _, _r in _sab_mes.iterrows():
                    _b = str(_r.get("billetera") or _r.get("Billetera","")).strip()
                    _sab_dict[_b] = float(_r.get("monto") or _r.get("Monto", 0) or 0)

            # ── FIX: Si el mes actual no tiene saldos guardados y "Arrastrar"
            #    está ON, calcular saldos finales del mes anterior como sugerencia ──
            if not _sab_dict and arr_on and lista_billeteras:
                _sab_ant_mes = df_sab_full[
                    (df_sab_full["Periodo"] == m_ant) & (df_sab_full["Año"] == a_ant)
                ] if not df_sab_full.empty else pd.DataFrame()
                _sab_ant_existe = not _sab_ant_mes.empty

                if _sab_ant_existe:
                    # Calcular saldo real final del mes anterior por billetera
                    _saldos_fin_ant = calcular_saldo_billeteras(
                        df_g_full, df_i_full, df_oi_full,
                        df_sab_full, lista_billeteras, m_ant, a_ant
                    )
                    if any(v != 0 for v in _saldos_fin_ant.values()):
                        _sab_dict = {b: _saldos_fin_ant.get(b, 0.0) for b in lista_billeteras}
                        st.caption(f"💡 Saldos calculados de {m_ant} {a_ant} — edita si es necesario.")

            sab_rows = []
            _total_dist = 0.0
            for _b in lista_billeteras:
                _m = _sab_dict.get(_b, 0.0)
                _m_new = st.number_input(
                    f"{_b}", value=_m, step=1000.0,
                    format="%.0f", key=f"sab_{_b}_{mes_s}_{anio_s}"
                )
                sab_rows.append({"billetera": _b, "monto": _m_new})
                _total_dist += _m_new
            df_sab_input = pd.DataFrame(sab_rows)

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
        st.markdown('<p style="color:#adb5bd;font-size:0.78rem;margin-bottom:6px">Notificaciones</p>', unsafe_allow_html=True)
        _notif_actual = bool(cfg_usuario.get("notif_email_mensual", False))
        _notif_nuevo = st.checkbox(
            "📧 Enviarme mi extracto y proyección por correo cada fin de mes",
            value=_notif_actual, key="chk_notif_mensual"
        )
        if _notif_nuevo != _notif_actual:
            if guardar_config(supabase, u_id, token, notif_email_mensual=_notif_nuevo):
                st.success("✅ Preferencia actualizada.")
                st.rerun()

        mostrar_eliminar_cuenta(
            supabase, token, u_id,
            st.session_state.get("u_email", "")
        )

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
                col_vk1, col_vk2 = st.columns([3, 1])
                with col_vk1:
                    st.caption(f"👥 **{_nombre_g}**  \n{_nombre_otro}")
                with col_vk2:
                    if st.button("🔗", key=f"btn_desvincular_{_v['id']}", help="Desvincular", use_container_width=True):
                        st.session_state[f"confirmar_desvincular_{_v['id']}"] = True
                        st.rerun()
                if st.session_state.get(f"confirmar_desvincular_{_v['id']}"):
                    st.warning(f"⚠️ ¿Seguro que quieres desvincular **{_nombre_g}**?")
                    if st.button("✅ Sí, desvincular", key=f"btn_ok_desv_{_v['id']}", use_container_width=True):
                        try:
                            supabase.postgrest.auth(token)
                            supabase.table("vinculos_usuarios").delete().eq("id", _v["id"]).execute()
                            st.session_state.pop(f"confirmar_desvincular_{_v['id']}", None)
                            st.session_state["vista_consolidada"] = False
                            st.success("✅ Vínculo eliminado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                    if st.button("✗ Cancelar", key=f"btn_cancel_desv_{_v['id']}", use_container_width=True):
                        st.session_state.pop(f"confirmar_desvincular_{_v['id']}", None)
                        st.rerun()

    # ── 👥 VISTA CONSOLIDADA ───────────────────────────────
    vinculos_activos   = cargar_vinculos(supabase, u_id, token)
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

    # ── 💳 GESTIÓN DE BILLETERAS ──────────────────────────
    with st.expander("💳 Mis Billeteras"):
        _nombres_actuales = df_b_full["nombre"].tolist() if not df_b_full.empty else []

        st.markdown(
            '<p style="color:#fca311;font-weight:800;font-size:0.78rem;'
            'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px">'
            'Módulo Billeteras</p>', unsafe_allow_html=True
        )
        if modulo_billeteras_activo:
            st.caption(f"✅ Activo desde {_bill_desde_p} {_bill_desde_a}")
            if st.button("🔴 Desactivar billeteras", key="btn_desact_bill", use_container_width=True):
                guardar_config(supabase, u_id, token,
                               billeteras_desde_periodo=None,
                               billeteras_desde_anio=None)
                st.rerun()
        else:
            st.caption(f"Inactivo para {mes_s} {anio_s}. Al activar, aplica a este mes y los siguientes.")
            if _nombres_actuales:
                if st.button(f"🟢 Activar desde {mes_s} {anio_s}", key="btn_act_bill", use_container_width=True):
                    guardar_config(supabase, u_id, token,
                                   billeteras_desde_periodo=mes_s,
                                   billeteras_desde_anio=int(anio_s))
                    st.rerun()
            else:
                st.warning("Primero crea al menos una billetera.")

        st.markdown("---")

        if _nombres_actuales:
            st.markdown("**Billeteras registradas:**")
            for _bn in _nombres_actuales:
                _col_n, _col_x = st.columns([5, 1])
                _col_n.markdown(f"💳 {_bn}")
                if _col_x.button("🗑", key=f"del_bill_{_bn}", help=f"Eliminar {_bn}"):
                    _lista_nueva = [x for x in _nombres_actuales if x != _bn]
                    if guardar_billeteras(supabase, token, u_id, _lista_nueva):
                        st.rerun()
            st.markdown("---")
        else:
            st.caption("Aún no tienes billeteras.")

        _nueva_bill = st.text_input(
            "Nueva billetera",
            key="input_nueva_bill",
            placeholder="Ej: Cuenta Ahorros, Nequi, Efectivo"
        )
        if st.button("➕ Agregar", key="btn_add_bill", use_container_width=True):
            _nueva_bill = _nueva_bill.strip()
            if not _nueva_bill:
                st.error("❌ Escribe un nombre.")
            elif _nueva_bill in _nombres_actuales:
                st.error(f"❌ Ya existe una billetera llamada **{_nueva_bill}**.")
            else:
                _lista_nueva = _nombres_actuales + [_nueva_bill]
                if guardar_billeteras(supabase, token, u_id, _lista_nueva):
                    st.success(f"✅ '{_nueva_bill}' agregada.")
                    st.rerun()

    # ── 🔒 CIERRE DE MES ──────────────────────────────────
    st.markdown(
        '<p style="color:#fca311;font-weight:800;font-size:0.78rem;'
        'text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px">'
        '🔒 Cierre de Mes</p>',
        unsafe_allow_html=True
    )

    st.session_state["toggle_cierre_mes"] = st.session_state["cierre_mes_por_periodo"].get(_periodo_key, False)

    def _on_cierre_change():
        st.session_state["cierre_mes_por_periodo"][_periodo_key] = st.session_state["toggle_cierre_mes"]

    st.toggle(
        "Activar cierre de mes",
        key="toggle_cierre_mes",
        on_change=_on_cierre_change,
        help="Nivela los ítems proyectados con remanente al final del mes."
    )
    if st.session_state["cierre_mes_por_periodo"].get(_periodo_key, False):
        st.caption("✅ Remanentes proyectados excluidos de pendientes.")

    st.divider()
    if st.button("🚪 Salir"):
        cerrar_sesion()

# --- CUERPO PRINCIPAL ---

# ══════════════════════════════════════════════════════════
# VISTA CONSOLIDADA
# ══════════════════════════════════════════════════════════
if st.session_state.get("vista_consolidada") and vinculos_aceptados:
    if os.path.exists(LOGO_APP_H):
        st.image(LOGO_APP_H, use_container_width=True)

    st.markdown(f"## 👥 Dashboard Consolidado — {mes_s} {anio_s}")
    st.caption("Vista combinada de todos los usuarios vinculados.")

    if st.button("◀ Volver a mi dashboard personal", key="btn_salir_consolidado"):
        st.session_state["vista_consolidada"] = False
        st.rerun()

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
            try:
                r_n = supabase.table("usuarios").select("nombre_completo").eq("usuario_id", otro_id).execute()
                nombres_usuarios.append(r_n.data[0]["nombre_completo"] if r_n.data else "Usuario vinculado")
            except:
                nombres_usuarios.append("Usuario vinculado")

    df_g_cons  = pd.concat([g[(g["Periodo"]==mes_s) & (g["Año"]==anio_s)] for g in todos_g if not g.empty], ignore_index=True) if todos_g else pd.DataFrame()
    df_i_cons  = pd.concat([i[(i["Periodo"]==mes_s) & (i["Año"]==anio_s)] for i in todos_i if not i.empty], ignore_index=True) if todos_i else pd.DataFrame()
    df_oi_cons = pd.concat([oi[(oi["Periodo"]==mes_s) & (oi["Año"]==anio_s)] for oi in todos_oi if not oi.empty], ignore_index=True) if todos_oi else pd.DataFrame()

    nom_cons = float(df_i_cons["Nomina"].sum()) if not df_i_cons.empty and "Nomina" in df_i_cons.columns else 0.0
    sal_cons = float(df_i_cons["SaldoAnterior"].sum()) if not df_i_cons.empty else 0.0
    otr_cons = float(df_oi_cons["Monto"].sum()) if not df_oi_cons.empty else 0.0
    it_c, vp_c, vpy_c, fact_c, bf_c, aho_c = calcular_metricas(df_g_cons, nom_cons, otr_cons, sal_cons)
    label_bf_c = "SALDO A FAVOR" if bf_c >= 0 else "DÉFICIT"

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

    st.stop()

if os.path.exists(LOGO_APP_H):
    st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s} {anio_s}")

df_mes_g = df_g_full[(df_g_full["Periodo"]==mes_s) & (df_g_full["Año"]==anio_s)].copy()

meses_map_r = {m: i for i, m in enumerate(meses_lista)}
gastos_hist = df_g_full.copy()
if not gastos_hist.empty:
    p_actual = (anio_s * 12) + meses_lista.index(mes_s)
    gastos_hist["lt"] = (gastos_hist["Año"] * 12) + gastos_hist["Periodo"].map(meses_map_r)
    p_anterior    = p_actual - 1
    foto_anterior = gastos_hist[gastos_hist["lt"] == p_anterior]
    if not foto_anterior.empty:
        activos = foto_anterior[foto_anterior["Movimiento Recurrente"] == True].copy()
        if not activos.empty:
            if df_mes_g.empty:
                # Mes vacío: cargar todos los recurrentes
                df_mes_g = activos.reindex(columns=[
                    "Categoría","Descripción","Monto","Valor Referencia",
                    "Pagado","Movimiento Recurrente","Es Proyectado",
                    "Presupuesto Asociado","Es Referencia"
                ])
                df_mes_g["Pagado"]     = False
                df_mes_g["Fecha Pago"] = pd.NaT
                df_mes_g["Monto"]      = 0.0
                df_mes_g["Es Proyectado"] = df_mes_g.apply(
                    lambda r: True if float(r.get("Valor Referencia", 0) or 0) > 0
                              else bool(r.get("Es Proyectado", False)),
                    axis=1
                )
                df_mes_g["Es Referencia"] = df_mes_g["Es Referencia"].fillna(False).astype(bool)
                df_mes_g["Presupuesto Asociado"] = df_mes_g["Presupuesto Asociado"].where(
                    df_mes_g["Presupuesto Asociado"].notna(), other=None
                )
                df_mes_g = df_mes_g.sort_values(
                    ["Es Proyectado","Categoría","Descripción"],
                    ascending=[False, True, True]
                ).reset_index(drop=True)
            else:
                # Mes con datos: agregar solo recurrentes que NO existen aún
                _desc_actuales = set(
                    df_mes_g["Descripción"].str.strip().str.upper().tolist()
                )
                _nuevos = activos[
                    ~activos["Descripción"].str.strip().str.upper().isin(_desc_actuales)
                ].copy()
                if not _nuevos.empty:
                    _nuevos = _nuevos.reindex(columns=[
                        "Categoría","Descripción","Monto","Valor Referencia",
                        "Pagado","Movimiento Recurrente","Es Proyectado",
                        "Presupuesto Asociado","Es Referencia"
                    ])
                    _nuevos["Pagado"]     = False
                    _nuevos["Fecha Pago"] = pd.NaT
                    _nuevos["Monto"]      = 0.0
                    _nuevos["Es Proyectado"] = _nuevos.apply(
                        lambda r: True if float(r.get("Valor Referencia", 0) or 0) > 0
                                  else bool(r.get("Es Proyectado", False)),
                        axis=1
                    )
                    _nuevos["Es Referencia"] = _nuevos["Es Referencia"].fillna(False).astype(bool)
                    _nuevos["Presupuesto Asociado"] = _nuevos["Presupuesto Asociado"].where(
                        _nuevos["Presupuesto Asociado"].notna(), other=None
                    )
                    df_mes_g = pd.concat([df_mes_g, _nuevos], ignore_index=True)
                    df_mes_g = df_mes_g.sort_values(
                        ["Es Proyectado","Categoría","Descripción"],
                        ascending=[False, True, True]
                    ).reset_index(drop=True)

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
# ══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span>📅 Gastos / Egresos Proyectados</span></div>', unsafe_allow_html=True)
st.caption("Define aquí los gastos que proyectas para el mes. Estos sirven como presupuesto de referencia.")

df_proy_rows = df_mes_g[df_mes_g["Es Proyectado"] == True].copy()
df_proy_rows["📋"] = False
if "Es Referencia" not in df_proy_rows.columns:
    df_proy_rows["Es Referencia"] = False

config_proy = {
    "Categoría":             st.column_config.SelectboxColumn("Categoría", options=LISTA_CATEGORIAS, width="medium"),
    "Descripción":           st.column_config.TextColumn("Descripción", width="large"),
    "Valor Referencia":      _money_column("Valor Proyectado", width="small",
                                 help="Monto que proyectas gastar en este ítem (ej: 400.000)"),
    "Es Referencia":         st.column_config.CheckboxColumn("📌 Referencia", default=False, width="small",
                                 help="Activa para hacer seguimiento de este ítem"),
    "📋":                    st.column_config.CheckboxColumn("📋 Copiar al registrar", default=False, width="small",
                                 help="Copia automáticamente el valor proyectado como monto al registrar el movimiento"),
    "Movimiento Recurrente": st.column_config.CheckboxColumn("🔁 Recurrente", default=False, width="small",
                                 help="Se repite todos los meses automáticamente"),
}

df_base_proy = df_proy_rows.reindex(
    columns=["Categoría", "Descripción", "Valor Referencia", "Es Referencia", "📋", "Movimiento Recurrente"]
).sort_values(["Categoría", "Descripción"], ascending=[True, True]).reset_index(drop=True)
df_base_proy["Valor Referencia"] = df_base_proy["Valor Referencia"].apply(_fmt_miles)

df_ed_proy = st.data_editor(
    df_base_proy,
    use_container_width=True,
    num_rows="dynamic",
    column_config=config_proy,
    key="proy_ed",
    on_change=lambda: st.session_state.update({"datos_modificados": True})
)

df_ed_proy_clean = df_ed_proy.copy()
df_ed_proy_clean["Valor Referencia"] = df_ed_proy_clean["Valor Referencia"].apply(_parse_miles)
df_ed_proy_clean["📋"] = df_ed_proy_clean.get("📋", False)
if "Es Referencia" not in df_ed_proy_clean.columns:
    df_ed_proy_clean["Es Referencia"] = False
df_ed_proy_clean["Es Referencia"] = df_ed_proy_clean["Es Referencia"].fillna(False).astype(bool)

items_referencia = df_ed_proy_clean[
    df_ed_proy_clean["Es Referencia"] == True
]["Descripción"].dropna().tolist()
if "Es Referencia" in df_mes_g.columns:
    items_ref_bd = df_mes_g[
        (df_mes_g["Es Proyectado"] == True) & (df_mes_g["Es Referencia"] == True)
    ]["Descripción"].dropna().tolist()
    items_referencia = sorted(set(items_referencia + items_ref_bd))
else:
    items_referencia = sorted(set(items_referencia))

items_proyectados = items_referencia

# ══════════════════════════════════════════════════════════
# TABLA 2: EDITAR / AGREGAR MOVIMIENTOS
# ══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span>✏️ Editar / Agregar Movimientos</span></div>', unsafe_allow_html=True)
st.caption("Registra aquí los gastos del día a día. Asocia cada uno a su ítem proyectado si aplica.")

df_mov_rows = df_mes_g[df_mes_g["Es Proyectado"] == False].copy()

config_mov = {
    "Categoría":            st.column_config.SelectboxColumn("Categoría", options=LISTA_CATEGORIAS, width="medium"),
    "Descripción":          st.column_config.TextColumn("Descripción", width="large"),
    "Monto":                _money_column("Monto", width="small",
                                help="Valor del gasto (ej: 50.000)"),
    "Presupuesto Asociado": st.column_config.SelectboxColumn("Ítem Proyectado", options=items_proyectados, width="medium",
                                help="Ítem proyectado al que pertenece este gasto"),
    "Pagado":               st.column_config.CheckboxColumn("✅ Pagado", default=False, width="small"),
    "Fecha Pago":           st.column_config.DateColumn("Fecha", format="DD/MM/YY", width="small"),
}
if modulo_billeteras_activo and lista_billeteras:
    config_mov["Billetera Pago"] = st.column_config.SelectboxColumn(
        "💳 Billetera", options=opciones_bill, width="medium",
        help="Billetera con la que pagas este gasto"
    )

_cols_mov = ["Categoría", "Descripción", "Monto", "Presupuesto Asociado"]
if modulo_billeteras_activo and lista_billeteras:
    _cols_mov.append("Billetera Pago")
_cols_mov += ["Pagado", "Fecha Pago"]

df_base_mov = df_mov_rows.reindex(
    columns=_cols_mov
).sort_values(["Categoría", "Descripción"], ascending=[True, True]).reset_index(drop=True)

# ── 📋 COPIAR AL REGISTRAR ────────────────────────────────
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

df_base_mov["Monto"] = df_base_mov["Monto"].apply(_fmt_miles)

df_ed_mov = st.data_editor(
    df_base_mov,
    use_container_width=True,
    num_rows="dynamic",
    column_config=config_mov,
    key="mov_ed",
    on_change=lambda: st.session_state.update({"datos_modificados": True})
)
df_ed_mov["Monto"] = df_ed_mov["Monto"].apply(_parse_miles)

# ══════════════════════════════════════════════════════════
# RECONSTRUIR df_ed_g unificado
# ══════════════════════════════════════════════════════════
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

df_mov_final = df_ed_mov.copy()
df_mov_final["Es Proyectado"]         = False
df_mov_final["Valor Referencia"]      = 0.0
df_mov_final["Movimiento Recurrente"] = False
df_mov_final["Es Referencia"]         = False

df_ed_g = pd.concat([df_proy_final, df_mov_final], ignore_index=True)

df_ed_g["Monto"]             = pd.to_numeric(df_ed_g["Monto"],           errors="coerce").fillna(0)
df_ed_g["Valor Referencia"]  = pd.to_numeric(df_ed_g["Valor Referencia"],errors="coerce").fillna(0)
df_ed_g["Pagado"]            = df_ed_g["Pagado"].fillna(False).astype(bool)
df_ed_g["Es Proyectado"]     = df_ed_g["Es Proyectado"].fillna(False).astype(bool)
df_ed_g["Movimiento Recurrente"] = df_ed_g["Movimiento Recurrente"].fillna(False).astype(bool)

# ── ANTI-DUPLICACIÓN EN KPIs ──────────────────────────────
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
            _movs_k   = df_ed_g[
                df_ed_g["Presupuesto Asociado"].astype(str).str.strip().str.upper() == _desc
            ]
            _ejecutado = float(pd.to_numeric(_movs_k["Monto"], errors="coerce").fillna(0).sum())
            _pag_comp  = bool(_movs_k["Pagado"].fillna(False).all()) if not _movs_k.empty else False
            if _pag_comp and _ejecutado >= _vref:
                df_ed_g.loc[_idx, "Pagado"] = True

df_base = df_ed_g.copy()

# ══════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════
# 📈 INGRESOS PROYECTADOS
# ══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span>📈 Ingresos Proyectados</span></div>', unsafe_allow_html=True)
st.caption("Define aquí los ingresos que proyectas recibir este mes. Al copiar, la fila migra a su destino y deja de ser proyección.")

# ── Base de datos del periodo ─────────────────────────────
df_mes_ip = df_ip_full[(df_ip_full["Periodo"]==mes_s) & (df_ip_full["Año"]==anio_s)].copy()

# Propagar recurrentes de mes anterior si el mes actual está vacío
if df_mes_ip.empty:
    _p_actual_ip = (anio_s * 12) + meses_lista.index(mes_s)
    _ip_hist = df_ip_full.copy()
    if not _ip_hist.empty and "Periodo" in _ip_hist.columns:
        _meses_map_ip = {m: i for i, m in enumerate(meses_lista)}
        _ip_hist["_lt"] = (_ip_hist["Año"] * 12) + _ip_hist["Periodo"].map(_meses_map_ip)
        _ip_ant = _ip_hist[_ip_hist["_lt"] == _p_actual_ip - 1]
        if not _ip_ant.empty:
            _activos_ip = _ip_ant[_ip_ant["Movimiento Recurrente"] == True].copy()
            if not _activos_ip.empty:
                df_mes_ip = _activos_ip.reindex(columns=["Descripción","Valor Proyectado","Destino Copia","Movimiento Recurrente"])
                df_mes_ip["Destino Copia"] = None   # recurrentes sin destino predeterminado
                df_mes_ip = df_mes_ip.reset_index(drop=True)

_OPCIONES_DESTINO = ["Ingresos Adicionales", "Ingreso Fijo (Sueldo/Nómina)"]

_ip_cols = ["Descripción", "Valor Proyectado", "Destino Copia", "Movimiento Recurrente"]
_ip_base = df_mes_ip.reindex(columns=_ip_cols).reset_index(drop=True)
# Destino Copia vacío por defecto (None), NO se fuerza valor predeterminado
if "Destino Copia" not in _ip_base.columns:
    _ip_base["Destino Copia"] = None
# Normalizar: cualquier valor que no sea de la lista → None
_ip_base["Destino Copia"] = _ip_base["Destino Copia"].apply(
    lambda v: v if v in _OPCIONES_DESTINO else None
)

_ip_config = {
    "Descripción":           st.column_config.TextColumn("Descripción", width="large"),
    "Valor Proyectado":      _money_column("💵 Valor Proyectado", width="small",
                                 help="Monto que proyectas recibir (ej: 400.000)"),
    "Destino Copia":         st.column_config.SelectboxColumn("📋 Copiar a", options=_OPCIONES_DESTINO, width="medium",
                                 help="Elige a dónde migrar este ingreso al presionar Copiar. Vacío = solo suma al Saldo a Favor."),
    "Movimiento Recurrente": st.column_config.CheckboxColumn("🔁 Recurrente", default=False, width="small",
                                 help="Se propaga automáticamente al mes siguiente"),
}

_ip_base["Valor Proyectado"] = _ip_base["Valor Proyectado"].apply(_fmt_miles)

df_ed_ip = st.data_editor(
    _ip_base,
    use_container_width=True,
    num_rows="dynamic",
    column_config=_ip_config,
    key="ip_ed",
    on_change=lambda: st.session_state.update({"datos_modificados": True})
)
df_ed_ip["Valor Proyectado"] = df_ed_ip["Valor Proyectado"].apply(_parse_miles)

# Calcular total proyectado — TODAS las filas suman al Saldo a Favor
# (solo dejan de sumar cuando se copian y desaparecen de la tabla)
_ip_df_calc = df_ed_ip.copy()
_ip_df_calc["Valor Proyectado"] = pd.to_numeric(_ip_df_calc["Valor Proyectado"], errors="coerce").fillna(0)
_total_ip = float(_ip_df_calc["Valor Proyectado"].sum())
_total_ip_con_destino = float(_ip_df_calc[
    _ip_df_calc["Destino Copia"].isin(_OPCIONES_DESTINO)
]["Valor Proyectado"].sum())

# Redefinir _ip_sin_destino solo para referencia visual (no afecta cálculo)
_ip_sin_destino = _ip_df_calc[~_ip_df_calc["Destino Copia"].isin(_OPCIONES_DESTINO)]

if _total_ip > 0:
    _msg_ip = f"📊 Total Ingresos Proyectados: $ {_total_ip:,.0f}"
    if _total_ip_con_destino > 0:
        _msg_ip += f"&nbsp;&nbsp;|&nbsp;&nbsp;⏳ Listo para copiar: $ {_total_ip_con_destino:,.0f}"
    st.markdown(
        f'<p style="color:#ffffff; font-size:0.85rem; margin-top:-8px;">{_msg_ip}</p>',
        unsafe_allow_html=True
    )

# ── BOTÓN COPIAR ──────────────────────────────────────────
if st.button("📋 Ejecutar copia a destinos", key="btn_copiar_ip"):
    _ip_con_destino = _ip_df_calc[
        (_ip_df_calc["Destino Copia"].isin(_OPCIONES_DESTINO)) &
        (_ip_df_calc["Valor Proyectado"] > 0) &
        (_ip_df_calc["Descripción"].notna()) &
        (_ip_df_calc["Descripción"].str.strip() != "")
    ].copy()

    if _ip_con_destino.empty:
        st.warning("⚠️ No hay filas con destino seleccionado y valor > 0 para copiar.")
    else:
        _a_oi   = _ip_con_destino[_ip_con_destino["Destino Copia"] == "Ingresos Adicionales"]
        _a_fijo = _ip_con_destino[_ip_con_destino["Destino Copia"] == "Ingreso Fijo (Sueldo/Nómina)"]

        # ── Persistir migración a Otros Ingresos en Supabase ──
        if not _a_oi.empty:
            _oi_bd = df_oi_full[(df_oi_full["Periodo"]==mes_s) & (df_oi_full["Año"]==anio_s)].copy()
            _oi_existentes_bd = set(_oi_bd["Descripción"].str.strip().str.upper().tolist()) if not _oi_bd.empty else set()
            _filas_oi_nuevas = []
            for _, _r in _a_oi.iterrows():
                _d = str(_r["Descripción"]).strip()
                if _d.upper() not in _oi_existentes_bd:
                    _filas_oi_nuevas.append({"Descripción": _d, "Monto": float(_r["Valor Proyectado"])})
                else:
                    _mask = _oi_bd["Descripción"].str.strip().str.upper() == _d.upper()
                    _oi_bd.loc[_mask & (_oi_bd["Monto"].fillna(0) == 0), "Monto"] = float(_r["Valor Proyectado"])
            if _filas_oi_nuevas:
                _oi_bd = pd.concat([_oi_bd, pd.DataFrame(_filas_oi_nuevas)], ignore_index=True)
            # Guardar otros_ingresos actualizados en BD
            try:
                supabase.postgrest.auth(token)
                supabase.table("otros_ingresos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
                for _, _row_oi in _oi_bd.iterrows():
                    _desc_oi = str(_row_oi.get("Descripción","")).strip()
                    _monto_oi = float(_row_oi.get("Monto", 0) or 0)
                    if _desc_oi:
                        supabase.table("otros_ingresos").insert({
                            "anio": int(anio_s), "periodo": str(mes_s),
                            "descripcion": _desc_oi, "monto": _monto_oi,
                            "billetera": str(_row_oi.get("Billetera","") or "") or None,
                            "usuario_id": str(u_id)
                        }).execute()
            except Exception as _e:
                st.error(f"Error al guardar ingresos adicionales: {_e}")

        # ── Persistir migración a Ingreso Fijo en Supabase ──
        if not _a_fijo.empty:
            _suma_fijo_migrada = float(_a_fijo["Valor Proyectado"].sum())
            try:
                supabase.postgrest.auth(token)
                _i_bd = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s)]
                _n_actual = float(_i_bd["Nomina"].iloc[0]) if not _i_bd.empty else 0.0
                _s_actual = float(_i_bd["SaldoAnterior"].iloc[0]) if not _i_bd.empty else s_in
                _o_actual = float(_i_bd["Otros"].iloc[0]) if not _i_bd.empty and "Otros" in _i_bd.columns else 0.0
                _bill_act = str(_i_bd["Billetera"].iloc[0]) if not _i_bd.empty and "Billetera" in _i_bd.columns else ""
                _n_nueva  = _n_actual + _suma_fijo_migrada
                supabase.table("ingresos_base").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
                supabase.table("ingresos_base").insert({
                    "anio": int(anio_s), "periodo": str(mes_s),
                    "saldo_anterior": _s_actual, "nomina": _n_nueva,
                    "otros": _o_actual, "billetera": _bill_act or None,
                    "usuario_id": str(u_id)
                }).execute()
            except Exception as _e:
                st.error(f"Error al guardar ingreso fijo: {_e}")

        # ── Eliminar filas migradas de ingresos_proyectados en BD ──
        _descripciones_migradas = set(_ip_con_destino["Descripción"].str.strip().str.upper().tolist())
        _ip_restantes = _ip_df_calc[
            ~_ip_df_calc["Descripción"].str.strip().str.upper().isin(_descripciones_migradas)
        ].copy()
        guardar_ingresos_proyectados(supabase, token, u_id, mes_s, anio_s, _ip_restantes)
        st.rerun()


# ══════════════════════════════════════════════════════════
# 💰 INGRESOS ADICIONALES
# ══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span>💰 Ingresos Adicionales</span></div>', unsafe_allow_html=True)
df_mes_oi = df_oi_full[(df_oi_full["Periodo"]==mes_s) & (df_oi_full["Año"]==anio_s)].copy()
_oi_cols   = ["Descripción","Monto"] + (["Billetera"] if modulo_billeteras_activo and lista_billeteras else [])
_oi_config = {"Monto": _money_column("Monto", help="Valor del ingreso (ej: 400.000)")}
if modulo_billeteras_activo and lista_billeteras:
    _oi_config["Billetera"] = st.column_config.SelectboxColumn(
        "💳 Billetera", options=opciones_bill, width="medium",
        help="Cuenta donde recibes este ingreso"
    )
_oi_base = df_mes_oi.reindex(columns=_oi_cols).reset_index(drop=True)
_oi_base["Monto"] = _oi_base["Monto"].apply(_fmt_miles)
df_ed_oi = st.data_editor(
    _oi_base,
    use_container_width=True, num_rows="dynamic",
    column_config=_oi_config,
    key="oi_ed"
)
df_ed_oi["Monto"] = df_ed_oi["Monto"].apply(_parse_miles)

# ══════════════════════════════════════════════════════════
# 🔄 TRANSFERENCIAS ENTRE BILLETERAS
# ══════════════════════════════════════════════════════════
if modulo_billeteras_activo and len(lista_billeteras) >= 2:
    st.markdown('<div class="section-header"><span>🔄 Transferencias entre Billeteras</span></div>', unsafe_allow_html=True)
    st.caption("Registra movimientos entre tus propias billeteras. No afectan ingresos ni egresos.")

    with st.container():
        _col_t1, _col_t2, _col_t3, _col_t4, _col_t5 = st.columns([2, 2, 2, 3, 1.5])
        with _col_t1:
            _origen = st.selectbox("Desde", lista_billeteras, key="tr_origen")
        with _col_t2:
            _destinos_disponibles = [b for b in lista_billeteras if b != _origen]
            _destino = st.selectbox("Hacia", _destinos_disponibles, key="tr_destino")
        with _col_t3:
            _monto_tr = st.number_input("Monto", min_value=0.0, step=10000.0, format="%.0f", key="tr_monto")
        with _col_t4:
            _desc_tr = st.text_input("Descripción (opcional)", placeholder="Ej: Recarga Nequi", key="tr_desc")
        with _col_t5:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Registrar", key="btn_registrar_tr", use_container_width=True):
                if _monto_tr <= 0:
                    st.error("❌ El monto debe ser mayor a cero.")
                elif _origen == _destino:
                    st.error("❌ Origen y destino deben ser diferentes.")
                else:
                    if guardar_transferencia(supabase, u_id, token, mes_s, anio_s,
                                            _origen, _destino, _monto_tr, _desc_tr):
                        st.success(f"✅ Transferencia registrada: {_origen} → {_destino} por $ {_monto_tr:,.0f}")
                        st.rerun()

    # Historial del mes (solo para eliminar si el usuario se equivocó)
    if not df_transferencias_full.empty:
        st.markdown("**Transferencias del mes:**")
        for _, _tr in df_transferencias_full.iterrows():
            _col_h1, _col_h2 = st.columns([8, 1])
            with _col_h1:
                _desc_show = f" — {_tr['descripcion']}" if _tr.get('descripcion') else ""
                st.markdown(
                    f'<div style="background:#3a3f44;border-radius:8px;padding:8px 14px;margin-bottom:4px;'
                    f'font-size:0.85rem;color:#fff">'
                    f'<span style="color:#4361ee;font-weight:700">{_tr["billetera_origen"]}</span>'
                    f' → <span style="color:#2ecc71;font-weight:700">{_tr["billetera_destino"]}</span>'
                    f' &nbsp;|&nbsp; <span style="color:#fca311;font-weight:700">$ {float(_tr["monto"]):,.0f}</span>'
                    f'{_desc_show}</div>',
                    unsafe_allow_html=True
                )
            with _col_h2:
                if st.button("🗑", key=f"del_tr_{_tr['id']}", help="Eliminar", use_container_width=True):
                    eliminar_transferencia(supabase, u_id, token, _tr["id"])
                    st.rerun()

    # Recargar para el cálculo de saldos
    df_transferencias_full = cargar_transferencias(supabase, u_id, token, mes_s, anio_s)

# ── CALCULAR MÉTRICAS ─────────────────────────────────────
df_ed_oi["Monto"] = pd.to_numeric(df_ed_oi["Monto"], errors="coerce").fillna(0)
otr_v = float(df_ed_oi["Monto"].sum())
placeholder_otros.text_input("Otros Ingresos (Total)", value=f"$ {otr_v:,.0f}", disabled=True)

it, vp, _vpy_old, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_v, s_in)
# Los Ingresos Proyectados ya NO suman al Saldo a Favor (solo se muestran como proyección aparte)

_df_pend_kpi = calcular_pendientes(df_ed_g)

if st.session_state["cierre_mes_por_periodo"].get(_periodo_key, False) and not _df_pend_kpi.empty:
    _df_pend_kpi = _df_pend_kpi[~(
        (_df_pend_kpi["Es Proyectado"].fillna(False).astype(bool)) &
        (pd.to_numeric(_df_pend_kpi["Monto"], errors="coerce").fillna(0) == 0)
    )].copy()

if not _df_pend_kpi.empty:
    _df_pend_kpi["_val"] = _df_pend_kpi.apply(
        lambda r: float(r.get("Monto", 0) or 0) if float(r.get("Monto", 0) or 0) > 0
                  else float(r.get("Valor Referencia", 0) or 0),
        axis=1
    )
    vpy = float(_df_pend_kpi["_val"].sum())
else:
    vpy = 0.0

it_total = float(s_in) + float(n_in) + float(otr_v)
fact     = it_total - vp
bf       = fact - vpy
ahorro_p = (bf / it_total * 100) if it_total > 0 else 0.0
label_ahorro = "SALDO A FAVOR" if bf >= 0 else "DÉFICIT"

# ── SALDO PROYECTADO (incluye Ingresos Proyectados aún no migrados) ──
saldo_proyectado = bf + float(_total_ip)
label_saldo_proy = "SALDO PROYECTADO" if saldo_proyectado >= 0 else "DÉFICIT PROYECTADO"

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

if _total_ip > 0:
    st.markdown(
        f'<div class="card" style="border:1px dashed #999; opacity:0.85;">'
        f'<div class="card-label">{label_saldo_proy} <span style="font-weight:normal;">(si se cumplen los Ingresos Proyectados)</span></div>'
        f'<div class="card-value" style="color:#9b59b6">$ {saldo_proyectado:,.0f}</div></div>',
        unsafe_allow_html=True
    )

st.divider()

# ══════════════════════════════════════════════════════════
# 💳 SECCIÓN BILLETERAS
# ══════════════════════════════════════════════════════════
if modulo_billeteras_activo and lista_billeteras:
    _fecha_hoy_str = _hoy.strftime("%d/%m/%Y")

    st.markdown(
        f'<div class="section-header"><span>💳 Estado de Billeteras — {_fecha_hoy_str}</span></div>',
        unsafe_allow_html=True
    )

    if _mes_real == mes_s and _anio_real == anio_s:
        # Estamos viendo el mes real → usar los datos en edición (incluye cambios sin guardar)
        _df_i_calc  = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s)].copy()
        _df_g_calc  = df_ed_g.copy()
        _df_g_calc["Periodo"] = mes_s
        _df_g_calc["Año"]     = anio_s
        if not _df_i_calc.empty:
            _df_i_calc.loc[_df_i_calc.index[0], "Nomina"]    = n_in
            _df_i_calc.loc[_df_i_calc.index[0], "Billetera"] = bill_nomina
        else:
            _df_i_calc = pd.DataFrame([{
                "Año": anio_s, "Periodo": mes_s, "Nomina": n_in,
                "Billetera": bill_nomina, "SaldoAnterior": s_in
            }])
        _df_oi_calc = df_ed_oi.copy()
        _df_oi_calc["Periodo"] = mes_s
        _df_oi_calc["Año"]     = anio_s
        _df_sab_real = df_sab_input
        _df_transf_real = df_transferencias_full
    else:
        # Estamos proyectando otro mes → el estado de billeteras siempre refleja el mes real (hoy)
        _df_i_calc  = df_i_full[(df_i_full["Periodo"]==_mes_real) & (df_i_full["Año"]==_anio_real)].copy()
        _df_g_calc  = df_g_full[(df_g_full["Periodo"]==_mes_real) & (df_g_full["Año"]==_anio_real)].copy()
        _df_oi_calc = df_oi_full[(df_oi_full["Periodo"]==_mes_real) & (df_oi_full["Año"]==_anio_real)].copy()
        _df_sab_real = df_sab_full
        _df_transf_real = cargar_transferencias(supabase, u_id, token, _mes_real, _anio_real)

    saldos_bill = calcular_saldo_billeteras(
        _df_g_calc, _df_i_calc, _df_oi_calc,
        _df_sab_real, lista_billeteras, _mes_real, _anio_real,
        df_transferencias=_df_transf_real
    )

    total_bill = sum(saldos_bill.values())

    _ncols = min(len(lista_billeteras), 4)
    _cols_bill = st.columns(_ncols)
    _colores_bill = ["#4361ee","#fca311","#2ecc71","#e74c3c","#9b5de5","#00b4d8"]
    for _i, _b in enumerate(lista_billeteras):
        _saldo = saldos_bill.get(_b, 0.0)
        _col   = _colores_bill[_i % len(_colores_bill)]
        _col_idx = _i % _ncols
        _cols_bill[_col_idx].markdown(
            f'<div class="card" style="border-bottom: 5px solid {_col}">'
            f'<div class="card-label">💳 {_b}</div>'
            f'<div class="card-value" style="color:{_col}; font-size:1.3rem">$ {_saldo:,.0f}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    if total_bill != 0:
        import plotly.graph_objects as _go
        _fig_bill = _go.Figure()
        _colores_usados = [_colores_bill[i % len(_colores_bill)] for i in range(len(lista_billeteras))]
        _saldos_vals = [saldos_bill.get(b, 0) for b in lista_billeteras]
        _fig_bill.add_trace(_go.Bar(
            x=lista_billeteras,
            y=_saldos_vals,
            marker_color=_colores_usados,
            text=[f"$ {v:,.0f}" for v in _saldos_vals],
            textposition="outside",
            textfont=dict(color="#ffffff", size=12),
        ))
        _fig_bill.update_layout(
            **PLOTLY_LAYOUT,
            height=220,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            showlegend=False,
        )
        st.markdown('<div class="chart-card"><div class="chart-title">Distribución de fondos por billetera</div>', unsafe_allow_html=True)
        st.plotly_chart(_fig_bill, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        _diff_bill = fact - total_bill
        if abs(_diff_bill) < 1:
            st.success(f"✅ Total billeteras coincide con Dinero Disponible: **$ {total_bill:,.0f}**")
        else:
            st.warning(f"⚠️ Total billeteras **$ {total_bill:,.0f}** vs Dinero Disponible **$ {fact:,.0f}** — diferencia: **$ {_diff_bill:,.0f}**")

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
    df_pend_adj  = calcular_pendientes(df)

    if st.session_state["cierre_mes_por_periodo"].get(_periodo_key, False) and not df_pend_adj.empty:
        df_pend_adj = df_pend_adj[~(
            (df_pend_adj["Es Proyectado"].fillna(False).astype(bool)) &
            (pd.to_numeric(df_pend_adj["Monto"], errors="coerce").fillna(0) == 0)
        )].copy()

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
    t_df = df_ed_g[df_ed_g["Es Proyectado"].fillna(False).astype(bool) == False].copy()
    t_df['V'] = pd.to_numeric(t_df['Monto'], errors='coerce').fillna(0)
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

# ── TENDENCIA DE AHORRO (Últimos 6 meses) ─────────────────
if mes_s == _mes_real and anio_s == _anio_real:
    st.markdown('<div class="chart-card"><div class="chart-title">Tendencia de Ahorro (Últimos 6 meses)</div>', unsafe_allow_html=True)
    _ref_idx = meses_lista.index(mes_s)
    _hist_meses, _hist_vals = [], []
    for _i in range(5, -1, -1):
        _idx = _ref_idx - _i
        _ah  = anio_s
        if _idx < 0:
            _idx += 12
            _ah -= 1
        _mn = meses_lista[_idx]
        _ih = df_i_full[(df_i_full["Periodo"]==_mn) & (df_i_full["Año"]==_ah)]
        if not _ih.empty:
            _gh = df_g_full[(df_g_full["Periodo"]==_mn) & (df_g_full["Año"]==_ah)]
            _oh = df_oi_full[(df_oi_full["Periodo"]==_mn) & (df_oi_full["Año"]==_ah)]
            _, _, _, _, _bfh, _ = calcular_metricas(
                _gh, _ih["Nomina"].iloc[0],
                _oh["Monto"].sum() if not _oh.empty else 0,
                _ih["SaldoAnterior"].iloc[0]
            )
            _hist_meses.append(_mn[:3])
            _hist_vals.append(_bfh)

    if _hist_vals:
        fig_tend = go.Figure(go.Bar(
            x=_hist_meses,
            y=_hist_vals,
            marker_color=["#fca311" if v >= 0 else "#e74c3c" for v in _hist_vals],
            text=[f"$ {v:,.0f}" for v in _hist_vals],
            textposition="outside",
            textfont=dict(color="#ffffff", size=11),
        ))
        fig_tend.update_layout(
            **PLOTLY_LAYOUT,
            height=240,
            margin=dict(t=30,b=10,l=10,r=10),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            showlegend=False,
        )
        st.plotly_chart(fig_tend, use_container_width=True)
    else:
        st.caption("No hay suficientes datos históricos para mostrar la tendencia.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# 🤖 ASESOR IA
# ══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span>🤖 Asesor IA de Finanzas</span></div>', unsafe_allow_html=True)

with st.expander("💡 Obtener diagnóstico y recomendaciones personalizadas", expanded=False):
    st.caption("Gemini analiza tus flujos del mes y actúa como tu asesor de finanzas personales.")

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
    df_g_limpio = df_ed_g.dropna(subset=["Categoría", "Descripción"], how="all")
    df_g_limpio = df_g_limpio[
        (df_g_limpio["Valor Referencia"] > 0) | (df_g_limpio["Monto"] > 0) |
        (df_g_limpio["Descripción"].notna() & (df_g_limpio["Descripción"].str.strip() != ""))
    ].copy()
    df_oi_limpio = df_ed_oi.dropna(subset=["Descripción","Monto"], how="all")

    _errores_bill = []
    if modulo_billeteras_activo and lista_billeteras:
        if not bill_nomina:
            _errores_bill.append("❌ El **Ingreso Fijo** no tiene billetera asignada.")
        _mov_pagados_sin_bill = df_g_limpio[
            (df_g_limpio["Pagado"].fillna(False).astype(bool)) &
            (df_g_limpio["Es Proyectado"].fillna(False).astype(bool) == False) &
            (df_g_limpio["Billetera Pago"].fillna("").astype(str).str.strip() == "")
        ] if "Billetera Pago" in df_g_limpio.columns else pd.DataFrame()
        if not _mov_pagados_sin_bill.empty:
            _errores_bill.append(f"❌ **{len(_mov_pagados_sin_bill)} gasto(s) pagado(s)** sin billetera asignada.")

    if _errores_bill:
        for _e in _errores_bill:
            st.error(_e)
    elif df_g_limpio.empty and df_oi_limpio.empty and n_in == 0:
        st.error("🛑 No hay datos suficientes para guardar.")
    else:
        try:
            with st.spinner("Sincronizando con Supabase..."):
                guardar_bd(supabase, token, u_id, mes_s, anio_s,
                           df_g_limpio, df_oi_limpio, s_in, n_in, otr_v,
                           bill_nomina=bill_nomina,
                           df_sab_nuevo=df_sab_input)
                # Guardar ingresos proyectados
                _df_ip_guardar = df_ed_ip.dropna(subset=["Descripción","Valor Proyectado"], how="all").copy()
                _df_ip_guardar["Valor Proyectado"] = pd.to_numeric(_df_ip_guardar["Valor Proyectado"], errors="coerce").fillna(0)
                _df_ip_guardar = _df_ip_guardar[
                    (_df_ip_guardar["Descripción"].notna()) &
                    (_df_ip_guardar["Descripción"].str.strip() != "")
                ]
                guardar_ingresos_proyectados(supabase, token, u_id, mes_s, anio_s, _df_ip_guardar)
                st.session_state.datos_modificados = False
                st.balloons()
                st.success("✅ ¡Todo guardado y sincronizado de forma segura!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")

# ══════════════════════════════════════════════════════════════
# 📧 CENTRO DE NOTIFICACIONES (solo admin)
# ══════════════════════════════════════════════════════════════
ADMIN_EMAIL = "arqtulicesar@gmail.com"
APP_URL = "https://stulio-finance-pro.streamlit.app"

if st.session_state.get("u_email", "").lower() == ADMIN_EMAIL:
    st.divider()
    st.markdown('<div class="section-header"><span>📧 Centro de Notificaciones (Admin)</span></div>', unsafe_allow_html=True)

    try:
        _sb_admin_key = st.secrets["supabase"]["service_role_key"]
        _sb_admin = create_client(st.secrets["supabase"]["url"], _sb_admin_key)
    except Exception as _e:
        _sb_admin = None
        st.error(f"No se pudo crear cliente admin: {_e}")

    with st.expander("📤 Extractos automáticos de fin de mes"):
        st.caption(
            f"Envía el extracto de **{_mes_real} {_anio_real}** y la proyección del "
            f"siguiente mes a todos los usuarios que activaron la opción "
            f"'Enviarme mi extracto y proyección por correo' en su Configuración de cuenta."
        )
        if _sb_admin and st.button("📤 Enviar extractos a usuarios suscritos", key="btn_envio_masivo_extractos"):
            try:
                _r_cfg = _sb_admin.table("config_usuario").select("usuario_id").eq("notif_email_mensual", True).execute()
                _ids_suscritos = [r["usuario_id"] for r in (_r_cfg.data or [])]
            except Exception as _e:
                _ids_suscritos = []
                st.error(f"Error consultando suscriptores: {_e}")

            if not _ids_suscritos:
                st.info("Ningún usuario tiene activada esta opción todavía.")
            else:
                _enviados, _fallidos = 0, []
                with st.spinner(f"Enviando a {len(_ids_suscritos)} usuario(s)..."):
                    for _uid_s in _ids_suscritos:
                        try:
                            _r_u = _sb_admin.table("usuarios").select("email,nombre_completo").eq("usuario_id", _uid_s).execute()
                            if not _r_u.data:
                                continue
                            _email_u  = _r_u.data[0].get("email", "")
                            _nombre_u = _r_u.data[0].get("nombre_completo", "")

                            _g, _i, _oi, _, _, _ = cargar_bd(_sb_admin, _uid_s, _sb_admin_key)

                            _ok, _msgr = enviar_correo_extracto_proyeccion(
                                dest_email=_email_u, nombre_user=_nombre_u,
                                mes_s=_mes_real, anio_s=_anio_real,
                                df_g_full=_g, df_i_full=_i, df_oi_full=_oi,
                                u_id=_uid_s
                            )
                            if _ok: _enviados += 1
                            else: _fallidos.append(f"{_email_u}: {_msgr}")
                        except Exception as _e:
                            _fallidos.append(f"{_uid_s}: {_e}")

                st.success(f"✅ Enviados: {_enviados} de {len(_ids_suscritos)}")
                for _f in _fallidos:
                    st.warning(f"⚠️ {_f}")

    with st.expander("📰 Newsletter de actualizaciones"):
        st.caption("Envía un correo a TODOS los usuarios registrados anunciando novedades y/o el nuevo link de acceso.")
        _nl_asunto = st.text_input(
            "Asunto", value="🚀 ¡My FinanceApp tiene novedades!", key="nl_asunto"
        )
        _nl_titulo = st.text_input(
            "Título principal", value="¡Hola de nuevo! 👋", key="nl_titulo"
        )
        _nl_cuerpo = st.text_area(
            "Mensaje (puedes usar HTML simple)",
            value=(
                f"Tenemos novedades en <b>My FinanceApp</b>:<br><br>"
                f"✅ Nuevo cálculo de <b>Saldo Proyectado</b> separado del Saldo a Favor<br>"
                f"✅ <b>Estado de Billeteras</b> siempre sincronizado con el día de hoy<br>"
                f"✅ Nueva sección de <b>Tendencia de Ahorro</b> en tu dashboard<br>"
                f"✅ Reportes mejorados (PDF / Excel)<br><br>"
                f"📌 <b>Importante:</b> nuestro link de acceso cambió. A partir de ahora "
                f"entra siempre desde:<br>"
                f"<a href='{APP_URL}' style='color:#fca311'>{APP_URL}</a>"
            ),
            height=200, key="nl_cuerpo"
        )
        _nl_test_first = st.checkbox("Enviarme primero solo a mí como prueba", value=True, key="nl_test_first")

        if _sb_admin and st.button("📨 Enviar Newsletter", key="btn_enviar_newsletter"):
            try:
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                from email.mime.image import MIMEImage

                _gmail_user = st.secrets.get("gmail", {}).get("email", "")
                _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")

                if _nl_test_first:
                    _r_dest = [{"email": st.session_state.get("u_email",""), "nombre_completo": st.session_state.get("u_nombre_completo","")}]
                else:
                    _r_all = _sb_admin.table("usuarios").select("email,nombre_completo").execute()
                    _r_dest = _r_all.data or []

                _enviados_nl, _fallidos_nl = 0, []
                for _u in _r_dest:
                    _email_u = _u.get("email","")
                    if not _email_u:
                        continue
                    _nombre_u = (_u.get("nombre_completo") or "").split(" ")[0] or "amig@"
                    try:
                        _msg = MIMEMultipart("related")
                        _msg["Subject"] = _nl_asunto
                        _msg["From"]    = _gmail_user
                        _msg["To"]      = _email_u
                        _html = f"""
                        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
                            <div style="text-align:center;margin-bottom:20px">
                                <img src="cid:logo_finance" alt="My FinanceApp" style="max-width:280px;width:100%;height:auto">
                            </div>
                            <h2 style="color:#fca311">{_nl_titulo}</h2>
                            <p>Hola {_nombre_u},</p>
                            <p>{_nl_cuerpo}</p>
                            <p style="margin-top:25px;text-align:center">
                                <a href="{APP_URL}" style="background:#fca311;color:#14213d;padding:12px 24px;
                                border-radius:8px;text-decoration:none;font-weight:bold">Ir a My FinanceApp</a>
                            </p>
                        </div>
                        """
                        _msg.attach(MIMEText(_html, "html"))
                        _logo_path = os.path.join(os.path.dirname(__file__), LOGO_APP_H)
                        if os.path.exists(_logo_path):
                            with open(_logo_path, "rb") as _f:
                                _img = MIMEImage(_f.read())
                                _img.add_header("Content-ID", "<logo_finance>")
                                _img.add_header("Content-Disposition", "inline", filename=LOGO_APP_H)
                                _msg.attach(_img)

                        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as _smtp:
                            _smtp.login(_gmail_user, _gmail_pass)
                            _smtp.sendmail(_gmail_user, _email_u, _msg.as_string())
                        _enviados_nl += 1
                    except Exception as _e:
                        _fallidos_nl.append(f"{_email_u}: {_e}")

                st.success(f"✅ Newsletter enviado a {_enviados_nl} destinatario(s).")
                for _f in _fallidos_nl:
                    st.warning(f"⚠️ {_f}")
            except Exception as _e:
                st.error(f"❌ Error: {_e}")
