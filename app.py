import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import re
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

# --- 2. INICIALIZACIÓN DE SESSION STATE (una sola vez, al inicio) ---
for key, default in {
    "autenticado": False,
    "token": None,
    "usuario_id": None,        # Ahora guarda el UUID real de Supabase
    "u_nombre_completo": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- 3. CONEXIÓN A SUPABASE ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)

    # Si ya hay sesión activa, reinyectamos el token en cada recarga
    if st.session_state.autenticado and st.session_state.token:
        supabase.postgrest.auth(st.session_state.token)

except Exception:
    st.error("Error conectando a Supabase. Revisa los Secrets.")
    st.stop()


# --- 4. CONSTANTES ---
LOGO_LOGIN   = "logoapp 1.png"
LOGO_SIDEBAR = "logoapp 2.png"
LOGO_APP_H   = "LOGOapp horizontal.png"

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

# --- 5. ESTILOS ---
st.markdown("""
    <style>
    header { background-color: rgba(0,0,0,0) !important; }
    .stApp { background: #495057; color: #ffffff; }

    /* ── TABLAS — filas alternas forzadas ── */
    [data-testid="stDataEditor"] { border-radius: 10px; overflow: hidden; }
    [data-testid="stDataEditor"] div { font-size: 0.85rem !important; }
    [data-testid="stDataEditor"] tr:nth-child(even) td { background-color: #3a3f44 !important; }
    [data-testid="stDataEditor"] tr:nth-child(odd)  td { background-color: #2d3238 !important; }
    [data-testid="stDataEditor"] th { background-color: #14213d !important; color: #fca311 !important; font-weight: 700 !important; }

    /* ── TABS ── */
    .stTabs [aria-selected="true"] { color: #fca311 !important; border-bottom-color: #fca311 !important; font-weight: bold; }

    /* ── KPI CARDS ── */
    .card {
        background-color: #ffffff; border-radius: 12px; padding: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-bottom: 10px;
        color: #495057; text-align: center; border-bottom: 5px solid #fca311;
        min-height: 100px; display: flex; flex-direction: column; justify-content: center;
    }
    .card-label { font-size: 0.8rem; color: #495057; font-weight: 800; text-transform: uppercase; line-height: 1.1; opacity: 0.7; }
    .card-value { font-size: 1.6rem; font-weight: 800; color: #495057; margin: 3px 0; }

    /* ── LEGEND BARS ── */
    .legend-bar {
        padding: 8px 12px; border-radius: 6px; margin-bottom: 4px;
        font-size: 0.9rem; font-weight: bold; color: #1a1d21;
        display: flex; justify-content: space-between; align-items: center;
    }

    /* ── CHART CARDS — envuelven cada gráfica ── */
    .chart-card {
        background-color: #3a3f44; border-radius: 14px; padding: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.35); margin-bottom: 8px;
        border-top: 3px solid #fca311;
    }
    .chart-title {
        font-size: 0.85rem; font-weight: 800; text-transform: uppercase;
        color: #fca311; letter-spacing: 0.05em; margin-bottom: 10px;
    }

    /* ── SECTION HEADERS ── */
    .section-header {
        display: flex; align-items: center; gap: 10px;
        background: linear-gradient(90deg, #212529 0%, rgba(33,37,41,0) 100%);
        border-left: 4px solid #fca311; border-radius: 4px;
        padding: 8px 14px; margin: 18px 0 10px 0;
    }
    .section-header span { font-size: 1.05rem; font-weight: 800;
        color: #ffffff; text-transform: uppercase; letter-spacing: 0.04em; }

    /* ── SIDEBAR ── */
    section[data-testid="stSidebar"] { background-color: #212529 !important; border-right: 1px solid #495057; }

    /* ── BOTÓN CERRAR SIDEBAR MÓVIL ── */
    #close-sidebar-btn {
        display: none;
        position: fixed;
        bottom: 24px;
        left: 16px;
        z-index: 99999;
        background: #fca311;
        color: #14213d;
        border: none;
        border-radius: 50px;
        padding: 12px 20px;
        font-weight: 800;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        box-shadow: 0 4px 0 #9a6c00;
        cursor: pointer;
    }
    @media (max-width: 768px) {
        #close-sidebar-btn { display: block; }
    }

    /* ── BOTONES sidebar — Pill azul oscuro / sombra naranja ── */
    .stButton>button {
        border-radius: 50px !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
        width: 100% !important;
        border: none !important;
        background: #14213d !important;
        color: #fca311 !important;
        box-shadow: 0 4px 0 #fca311 !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
        padding: 10px 20px !important;
    }
    .stButton>button:hover {
        background: #1e3260 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 0 #fca311 !important;
    }
    .stButton>button:active {
        transform: translateY(4px) !important;
        box-shadow: none !important;
    }

    /* ── BOTÓN GUARDAR — Pill naranja / sombra azul oscuro ── */
    .save-btn button {
        border-radius: 50px !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        background: #fca311 !important;
        color: #14213d !important;
        border: none !important;
        box-shadow: 0 6px 0 #14213d !important;
        padding: 16px !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
    }
    .save-btn button:hover {
        filter: brightness(1.06) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 7px 0 #14213d !important;
    }
    .save-btn button:active {
        transform: translateY(5px) !important;
        box-shadow: none !important;
    }

    /* ── JERARQUÍA DE TÍTULOS ── */
    h2 { color: #ffffff !important; font-weight: 800 !important;
         border-bottom: 2px solid #fca311; padding-bottom: 6px; }
    h3 { color: #fca311 !important; font-weight: bold !important; }
    h4 { color: #adb5bd !important; font-weight: 600 !important; font-size: 0.9rem !important; text-transform: uppercase; }

    /* ── DIVIDER ── */
    hr { border-color: rgba(252,163,17,0.3) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5b. BOTÓN CERRAR SIDEBAR MÓVIL ---
st.markdown("""
<button id="close-sidebar-btn" onclick="closeSidebar()">✕ Cerrar menú</button>
<script>
function closeSidebar() {
    // Busca el botón de colapsar el sidebar de Streamlit y lo clickea
    var btns = window.parent.document.querySelectorAll('[data-testid="collapsedControl"], button[kind="header"]');
    btns.forEach(function(btn){ btn.click(); });
    // Alternativa: busca el botón «
    var chevron = window.parent.document.querySelector('button[aria-label="Close sidebar"], [data-testid="baseButton-header"]');
    if (chevron) chevron.click();
}
// Mostrar solo cuando el sidebar está abierto
var observer = new MutationObserver(function() {
    var sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
    var btn = document.getElementById("close-sidebar-btn");
    if (sidebar && btn) {
        var isOpen = window.parent.innerWidth <= 768 && 
                     sidebar.getBoundingClientRect().left >= 0;
        btn.style.display = isOpen ? "block" : "none";
    }
});
observer.observe(window.parent.document.body, { attributes: true, subtree: true, attributeFilter: ["class", "style"] });
</script>
""", unsafe_allow_html=True)

# --- 6. FUNCIONES DE FORMATO ---

# --- FUNCIONES DE FORMATO ---
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


# --- 11. PANTALLA DE LOGIN ---
# ============================================================
if not st.session_state.autenticado:
    mostrar_login(supabase, LOGO_LOGIN)
    st.stop()

# ============================================================

# --- 12. APP PRINCIPAL (solo si está autenticado) ---
# ============================================================
u_id  = st.session_state.usuario_id
token = st.session_state.token

# Reinyectamos token y cargamos datos
supabase.postgrest.auth(token)
df_g_full, df_i_full, df_oi_full = cargar_bd(supabase, u_id, token)

meses_lista = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR):
        st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")

    anio_s = st.selectbox("Año", [2026, 2027, 2028], index=0)
    mes_s  = st.selectbox("Mes Actual", meses_lista, index=datetime.now().month - 1)

    i_m_act = df_i_full[(df_i_full["Periodo"] == mes_s) & (df_i_full["Año"] == anio_s)]

    # Mes anterior
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

    # Extractos
    st.divider(); st.subheader("📑 Extractos")
    c_pdf, c_xls = st.columns(2)
    with c_pdf:
        if st.button("📄 PDF"):
            pdf = generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, [mes_s], f"Extracto {mes_s}", anio_s, u_id)
            st.download_button("Descargar PDF", pdf, f"Extracto_{mes_s}.pdf")
    with c_xls:
        if st.button("📊 Excel"):
            # Tomamos valores de ingresos directo de la BD para evitar variables no definidas
            i_m_xls  = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Año"]==anio_s)]
            oi_m_xls = df_oi_full[(df_oi_full["Periodo"]==mes_s) & (df_oi_full["Año"]==anio_s)]
            n_xls = float(i_m_xls["Nomina"].iloc[0])        if not i_m_xls.empty else 0.0
            s_xls = float(i_m_xls["SaldoAnterior"].iloc[0]) if not i_m_xls.empty else 0.0
            o_xls = float(oi_m_xls["Monto"].sum())          if not oi_m_xls.empty else 0.0
            buf_xls = generar_excel_reporte(
                df_g_full, df_i_full, df_oi_full,
                mes_s, anio_s, u_id,
                n_xls, o_xls, s_xls
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

    if st.button("🚪 Salir"):
        cerrar_sesion()

# Eliminar cuenta (fuera del sidebar, en la parte inferior)
mostrar_eliminar_cuenta(supabase, token, u_id,
    st.session_state.get("u_email", ""))

# --- CUERPO PRINCIPAL ---
if os.path.exists(LOGO_APP_H):
    st.image(LOGO_APP_H, use_container_width=True)
st.markdown(f"## Gestión de {mes_s} {anio_s}")

# Cargar gastos del mes
df_mes_g = df_g_full[(df_g_full["Periodo"]==mes_s) & (df_g_full["Año"]==anio_s)].copy()

# Copia inteligente desde el mes anterior si está vacío
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

# Tabla de gastos
# ✅ Fecha Pago: siempre como datetime, NaT para vacíos
if "Fecha Pago" not in df_mes_g.columns:
    df_mes_g["Fecha Pago"] = pd.NaT
else:
    df_mes_g["Fecha Pago"] = pd.to_datetime(df_mes_g["Fecha Pago"], errors="coerce")
df_mes_g["Fecha Pago"] = df_mes_g["Fecha Pago"].where(df_mes_g["Fecha Pago"].notna(), other=pd.NaT)

# ✅ Nuevas columnas de presupuesto proyectado
if "Es Proyectado" not in df_mes_g.columns:
    df_mes_g["Es Proyectado"] = False
else:
    df_mes_g["Es Proyectado"] = df_mes_g["Es Proyectado"].fillna(False).astype(bool)
if "Presupuesto Asociado" not in df_mes_g.columns:
    df_mes_g["Presupuesto Asociado"] = None

# ✅ Columna temporal para copiar Ref → Monto por fila
df_mes_g["📋"] = False

# ✅ Autocompletado: todas las descripciones usadas históricamente por este usuario
descripciones_históricas = sorted(df_g_full["Descripción"].dropna().unique().tolist()) if not df_g_full.empty else []

# ── EDITOR SIEMPRE VISIBLE ──────────────────────────────
st.markdown('<div class="section-header"><span>✏️ Editar / Agregar Movimientos</span></div>', unsafe_allow_html=True)
st.caption("Los cambios se aplican al presionar 💾 GUARDAR CAMBIOS DEFINITIVOS")
if True:  # bloque siempre activo (reemplaza el expander)
    # Items proyectados disponibles para asociar
    items_proyectados = df_mes_g[df_mes_g["Es Proyectado"]==True]["Descripción"].dropna().tolist() if not df_mes_g.empty else []

    config_g = {
        "Categoría":             st.column_config.SelectboxColumn("Categoría", options=LISTA_CATEGORIAS, width="medium"),
        "Descripción":           st.column_config.TextColumn("Descripción", width="medium"),
        "Monto":                 st.column_config.NumberColumn("Monto", format="$ %,.0f", width="small"),
        "Valor Referencia":      st.column_config.NumberColumn("Val.Ref", format="$ %,.0f", width="small"),
        "📋":                    st.column_config.CheckboxColumn("📋", default=False, width="small",
                                     help="Copia Valor Referencia → Monto"),
        "Es Proyectado":         st.column_config.CheckboxColumn("Proy.", default=False, width="small",
                                     help="Ítem proyectado"),
        "Presupuesto Asociado":  st.column_config.SelectboxColumn("Asociado a", options=items_proyectados, width="small",
                                     help="Ítem proyectado al que pertenece este gasto"),
        "Pagado":                st.column_config.CheckboxColumn("✅", default=False, width="small"),
        "Movimiento Recurrente": st.column_config.CheckboxColumn("🔁", default=False, width="small"),
        "Fecha Pago":            st.column_config.DateColumn("Fecha", format="DD/MM/YY", width="small"),
    }
    # Preparar df base — sin rerun, sin session_state complejo
    df_base = df_mes_g.reindex(columns=["Categoría","Descripción","Monto","Valor Referencia","📋","Es Proyectado","Presupuesto Asociado","Pagado","Movimiento Recurrente","Fecha Pago"]).reset_index(drop=True)

    df_ed_g = st.data_editor(
        df_base,
        use_container_width=True, num_rows="dynamic", column_config=config_g, key="g_ed"
    )

    # ✅ Aplicar copia silenciosa: si 📋 está marcado, copiar Ref → Monto
    # Esto ocurre DESPUÉS de leer df_ed_g, sin rerun, preservando todos los demás valores
    if "📋" in df_ed_g.columns:
        mask_copy = df_ed_g["📋"] == True
        if mask_copy.any():
            df_ed_g.loc[mask_copy, "Monto"] = pd.to_numeric(
                df_ed_g.loc[mask_copy, "Valor Referencia"], errors="coerce"
            ).fillna(0)
            # Desmarcar el check después de copiar
            df_ed_g.loc[mask_copy, "📋"] = False



# Tabla de ingresos adicionales
st.markdown('<div class="section-header"><span>💰 Ingresos Adicionales</span></div>', unsafe_allow_html=True)
df_mes_oi = df_oi_full[(df_oi_full["Periodo"]==mes_s) & (df_oi_full["Año"]==anio_s)].copy()
df_ed_oi  = st.data_editor(
    df_mes_oi.reindex(columns=["Descripción","Monto"]).reset_index(drop=True),
    use_container_width=True, num_rows="dynamic",
    column_config={"Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f")},
    key="oi_ed"
)


st.markdown('<div class="section-header"><span>📝 Movimiento de Gastos</span></div>', unsafe_allow_html=True)

# ✅ Ordenar A-Z por Categoría y Descripción
if not df_mes_g.empty:
    df_mes_g = df_mes_g.sort_values(["Categoría","Descripción"], ascending=[True,True]).reset_index(drop=True)


# ── TABLA VISUAL con colores por categoría ──────────────────
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
        html  = '<div style="border-radius:10px;overflow:hidden;margin-bottom:12px"><table style="width:100%;border-collapse:collapse;font-family:sans-serif"><thead><tr style="background:#14213d">'
        html += th + ';text-align:left">Categoría</th>'
        html += th + ';text-align:left">Descripción</th>'
        html += th + ';text-align:right">Monto</th>'
        html += th + f';text-align:right">{col_extra_label}</th>'
        html += f'</tr></thead><tbody>{filas}</tbody></table></div>'
        return html

    df_pagados    = df[df["Pagado"] == True].copy()
    df_pendientes = df[df["Pagado"] == False].copy()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div style="color:#2ecc71;font-weight:800;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px">✅ Obligaciones Pagadas</div>', unsafe_allow_html=True)
        html_p = make_tabla(df_pagados, "PAGADO", "#2ecc71", "Fecha Pago", True)
        if html_p: st.markdown(html_p, unsafe_allow_html=True)
        else: st.info("Sin pagos registrados.")
    with col2:
        st.markdown('<div style="color:#e74c3c;font-weight:800;font-size:0.9rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px">⏳ Obligaciones Pendientes</div>', unsafe_allow_html=True)
        # ✅ Para ítems proyectados, ajustar Val.Ref descontando asociados pagados
        df_pend_adj = df_pendientes.copy()
        if "Es Proyectado" in df_pend_adj.columns and "Presupuesto Asociado" in df.columns:
            for idx, row in df_pend_adj.iterrows():
                if bool(row.get("Es Proyectado", False)):
                    nombre = str(row.get("Descripción",""))
                    _pa = df["Presupuesto Asociado"].astype(str).str.strip()
                    asociados_monto = df[
                        (_pa == nombre.strip()) &
                        (_pa != "nan") & (_pa != "None") & (_pa != "")
                    ]["Monto"].apply(pd.to_numeric, errors="coerce").fillna(0).sum()
                    vref_orig = float(row.get("Valor Referencia", 0) or 0)
                    df_pend_adj.loc[idx, "Valor Referencia"] = max(vref_orig - asociados_monto, 0)
        html_n = make_tabla(df_pend_adj, "PENDIENTE", "#fca311", "Val.Ref", False)
        if html_n: st.markdown(html_n, unsafe_allow_html=True)
        else: st.success("¡Sin obligaciones pendientes!")


render_resumen_gastos(df_mes_g)


# Cálculos
df_ed_g["Monto"]            = pd.to_numeric(df_ed_g["Monto"],           errors="coerce").fillna(0)
df_ed_g["Valor Referencia"] = pd.to_numeric(df_ed_g["Valor Referencia"],errors="coerce").fillna(0)
df_ed_oi["Monto"]           = pd.to_numeric(df_ed_oi["Monto"],          errors="coerce").fillna(0)

otr_v = float(df_ed_oi["Monto"].sum())
placeholder_otros.text_input("Otros Ingresos (Total)", value=f"$ {otr_v:,.0f}", disabled=True)

it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_ed_g, n_in, otr_v, s_in)
label_ahorro = "SALDO A FAVOR" if bf >= 0 else "DÉFICIT"

# ══════════════════════════════════════════════
# PRESUPUESTO VS EJECUCIÓN POR CATEGORÍA
# ══════════════════════════════════════════════
st.markdown('<div class="section-header"><span>📊 Presupuesto vs Ejecución por Categoría</span></div>', unsafe_allow_html=True)

# ✅ Usar datos de BD para seguimiento (más confiable que el editor)
df_mes_bd = df_g_full[
    (df_g_full["Periodo"] == mes_s) &
    (df_g_full["Año"] == anio_s)
].copy()

# Items proyectados desde BD
df_proyectados = df_mes_bd[df_mes_bd["Es Proyectado"] == True].copy() if "Es Proyectado" in df_mes_bd.columns else pd.DataFrame()

# Gastos asociados desde BD
if "Presupuesto Asociado" in df_mes_bd.columns:
    _pa = df_mes_bd["Presupuesto Asociado"].astype(str).str.strip()
    df_asociados = df_mes_bd[
        _pa.notna() &
        (_pa != "") &
        (_pa != "None") &
        (_pa != "nan") &
        (_pa != "NaN")
    ].copy()
else:
    df_asociados = pd.DataFrame()


# Para la vista por categoría: presupuesto = suma Valor Referencia de proyectados
# ✅ Presupuesto = suma de TODOS los Valor Referencia por categoría
cats_con_ref   = df_ed_g[df_ed_g["Valor Referencia"] > 0].groupby("Categoría")["Valor Referencia"].sum()
# ✅ Ejecutado = suma de Monto donde Pagado = True
df_pagados     = df_ed_g[df_ed_g["Pagado"] == True] if "Pagado" in df_ed_g.columns else pd.DataFrame()
cats_ejecutado = df_pagados.groupby("Categoría")["Monto"].sum() if not df_pagados.empty else pd.Series(dtype=float)
# ✅ Todas las categorías con al menos un valor de referencia
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
            disp_label = "Excedido"  if excedido else "Disponible"
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

        # Gastos reales asociados a este ítem
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

        # Lista de gastos asociados
        gastos_lista = ""
        if not df_asociados.empty and "Presupuesto Asociado" in df_asociados.columns:
            assoc = df_asociados[df_asociados["Presupuesto Asociado"] == nombre_proy]
            for _, ag in assoc.iterrows():
                gastos_lista += f'<div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #495057"><span style="font-size:10px;color:#adb5bd">{ag["Descripción"]}</span><span style="font-size:10px;color:#fff">$ {float(ag["Monto"]):,.0f}</span></div>'

        # Construir tarjeta sin f-strings anidados
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

# KPIs
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

# Gráficas
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
    META = 20  # Meta recomendada de ahorro

    # ✅ MEJORA 2: Gauge con zona de meta y mensaje contextual
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=v_cl,
        number={'suffix': "%", 'font': {'color': '#fca311', 'size': 50}, 'valueformat': '.0f'},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#fca311"},
            'bgcolor': "white",
            'steps': [
                {'range': [0, META],  'color': '#f8d7da'},   # Zona roja: bajo la meta
                {'range': [META, 100],'color': '#d4edda'},   # Zona verde: sobre la meta
            ],
            'threshold': {
                'line': {'color': "#2ecc71", 'width': 3},
                'thickness': 0.85,
                'value': META
            }
        }
    ))
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(t=50,b=0,l=25,r=25))
    st.plotly_chart(fig2, use_container_width=True)

    # Mensaje contextual debajo del gauge
    if v_cl >= META:
        st.markdown(f'<div style="text-align:center;color:#2ecc71;font-weight:bold;font-size:0.85rem">✅ ¡Meta alcanzada! Ahorraste {v_cl:.0f}% (Meta: {META}%)</div>', unsafe_allow_html=True)
    else:
        falta = META - v_cl
        st.markdown(f'<div style="text-align:center;color:#e74c3c;font-weight:bold;font-size:0.85rem">⚠️ Te falta {falta:.0f}% para la meta recomendada del {META}%</div>', unsafe_allow_html=True)

with inf3:
    st.markdown('<div class="chart-card"><div class="chart-title">Estado Real del Dinero</div>', unsafe_allow_html=True)

    # ✅ MEJORA 3: Dona con saldo a favor en el centro en lugar de solo "Estado"
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
        showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=250,
        margin=dict(t=0,b=0,l=0,r=0),
        annotations=[
            dict(text=centro_label,  x=0.5, y=0.58, font_size=13, showarrow=False, font_color="#495057", font=dict(family="Arial Black")),
            dict(text=centro_valor,  x=0.5, y=0.42, font_size=15, showarrow=False, font_color=centro_color, font=dict(family="Arial Black")),
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
    df_g_limpio  = df_ed_g.dropna(subset=["Categoría","Descripción","Monto"], how="all")
    df_oi_limpio = df_ed_oi.dropna(subset=["Descripción","Monto"], how="all")

    if df_g_limpio.empty and df_oi_limpio.empty and n_in == 0:
        st.error("🛑 No hay datos suficientes para guardar.")
    else:
        try:
            with st.spinner("Sincronizando con Supabase..."):
                guardar_bd(supabase, token, u_id, mes_s, anio_s,
                           df_g_limpio, df_oi_limpio, s_in, n_in, otr_v)
                st.balloons()
                st.success("✅ ¡Todo guardado y sincronizado de forma segura!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")
