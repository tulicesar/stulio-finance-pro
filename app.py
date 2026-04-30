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

# --- 7. CARGAR BASE DE DATOS ---
# ⚠️ IMPORTANTE: No usamos @st.cache_data aquí porque necesitamos
# el token de sesión en cada llamada para que RLS funcione correctamente.
def cargar_bd(u_id, token):
    try:
        # Inyectamos el token ANTES de cada consulta
        supabase.postgrest.auth(token)

        r_g  = supabase.table("gastos").select("*").eq("usuario_id", u_id).execute()
        r_i  = supabase.table("ingresos_base").select("*").eq("usuario_id", u_id).execute()
        r_oi = supabase.table("otros_ingresos").select("*").eq("usuario_id", u_id).execute()

        df_g = pd.DataFrame(r_g.data)   if r_g.data  else pd.DataFrame(columns=["anio","periodo","categoria","descripcion","monto","valor_referencia","pagado","recurrente","usuario_id"])
        df_i = pd.DataFrame(r_i.data)   if r_i.data  else pd.DataFrame(columns=["anio","periodo","saldo_anterior","nomina","otros","usuario_id"])
        df_oi= pd.DataFrame(r_oi.data)  if r_oi.data else pd.DataFrame(columns=["anio","periodo","descripcion","monto","usuario_id"])

        # Renombrar columnas para la interfaz
        df_g  = df_g.rename(columns={"anio":"Año","periodo":"Periodo","categoria":"Categoría","descripcion":"Descripción","monto":"Monto","valor_referencia":"Valor Referencia","pagado":"Pagado","recurrente":"Movimiento Recurrente","usuario_id":"Usuario","fecha_pago":"Fecha Pago"})
        df_i  = df_i.rename(columns={"anio":"Año","periodo":"Periodo","saldo_anterior":"SaldoAnterior","nomina":"Nomina","otros":"Otros","usuario_id":"Usuario"})
        df_oi = df_oi.rename(columns={"anio":"Año","periodo":"Periodo","descripcion":"Descripción","monto":"Monto","usuario_id":"Usuario"})

        for df in [df_g, df_i, df_oi]:
            if "Año" in df.columns:
                df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(0).astype(int)

        # ✅ Forzar Fecha Pago a datetime (evita que aparezca "None" como texto)
        if "Fecha Pago" in df_g.columns:
            df_g["Fecha Pago"] = pd.to_datetime(df_g["Fecha Pago"], errors="coerce")

        return df_g, df_i, df_oi

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# --- 8. CALCULAR MÉTRICAS ---
def calcular_metricas(df_g, nom, otr, s_ant):
    it   = float(s_ant) + float(nom) + float(otr)
    vp   = df_g[df_g["Pagado"] == True]["Monto"].sum() if not df_g.empty else 0
    vpy  = df_g[df_g["Pagado"] == False].apply(
        lambda x: x["Monto"] if x["Monto"] > 0 else x["Valor Referencia"], axis=1
    ).sum() if not df_g.empty else 0
    bf   = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0
    return it, vp, vpy, (it - vp), bf, ahorro_p

# --- 9. GENERADOR DE PDF ---
def generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses, titulo, anio, u_id):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    import math

    nombre_usuario = st.session_state.get("u_nombre_completo", u_id)
    buf = BytesIO()
    c   = canvas.Canvas(buf, pagesize=letter)

    C_AZUL   = HexColor("#14213d")
    C_NARANJA= HexColor("#fca311")
    C_GRIS   = HexColor("#e5e5e5")
    C_NEGRO  = HexColor("#000000")
    C_VERDE  = HexColor("#2ecc71")
    C_ROJO   = HexColor("#e74c3c")
    C_OSCURO = HexColor("#2d3238")

    total_periodo_nomina = total_periodo_otros = total_periodo_gastos = 0

    # Guardamos datos del último mes para la página 2
    ultimo_g_m  = None
    ultimo_it   = ultimo_vp = ultimo_vpy = ultimo_bf = ultimo_ahorro_p = 0

    def head(canvas_obj, t, a, user_name):
        canvas_obj.setFillColor(colors.white)
        canvas_obj.rect(0, 0, 612, 792, fill=1)
        if os.path.exists(LOGO_APP_H):
            canvas_obj.drawImage(LOGO_APP_H, 55, 670, width=500, height=100, preserveAspectRatio=True, anchor='c')
        canvas_obj.setFont("Helvetica-BoldOblique", 9)
        canvas_obj.setFillColor(C_AZUL)
        canvas_obj.drawString(50, 650, f"Usuario: {user_name}")
        canvas_obj.drawRightString(560, 650, f"{t} {a}")
        canvas_obj.setStrokeColor(C_NARANJA); canvas_obj.setLineWidth(2); canvas_obj.line(50, 645, 560, 645)
        tz = pytz.timezone('America/Bogota')
        fecha_gen = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
        canvas_obj.setFont("Helvetica", 7); canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(50, 30, f"Documento generado el: {fecha_gen}")
        return 620

    y = head(c, titulo, anio, nombre_usuario)

    for m in meses:
        i_m  = df_i_full[(df_i_full["Periodo"]==m) & (df_i_full["Año"]==anio) & (df_i_full["Usuario"]==u_id)]
        g_m  = df_g_full[(df_g_full["Periodo"]==m) & (df_g_full["Año"]==anio) & (df_g_full["Usuario"]==u_id)]
        oi_m = df_oi_full[(df_oi_full["Periodo"]==m) & (df_oi_full["Año"]==anio) & (df_oi_full["Usuario"]==u_id)]

        s_ant   = float(i_m["SaldoAnterior"].iloc[0]) if not i_m.empty else 0
        nom     = float(i_m["Nomina"].iloc[0])        if not i_m.empty else 0
        otr_sum = float(oi_m["Monto"].sum())          if not oi_m.empty else 0

        it, vp, vpy, _, bf, ahorro_p = calcular_metricas(g_m, nom, otr_sum, s_ant)
        total_periodo_nomina  += nom
        total_periodo_otros   += otr_sum
        total_periodo_gastos  += (vp + vpy)

        # Guardamos el último mes para página 2
        ultimo_g_m = g_m; ultimo_it = it; ultimo_vp = vp
        ultimo_vpy = vpy; ultimo_bf = bf; ultimo_ahorro_p = ahorro_p

        if y < 250: c.showPage(); y = head(c, titulo, anio, nombre_usuario)

        c.setFillColor(C_GRIS); c.rect(50, y-55, 510, 60, fill=1, stroke=0)
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 11); c.drawString(60, y-15, f"MES: {m}")
        c.setFont("Helvetica", 9)
        c.drawString(60, y-30, f"Ingresos: $ {it:,.0f} | Pagadas: $ {vp:,.0f} | Pendientes: $ {vpy:,.0f}")
        c.setFillColor(C_NARANJA); c.setFont("Helvetica-Bold", 9)
        c.drawString(60, y-45, f"SALDO A FAVOR FINAL: $ {bf:,.0f}"); y -= 80

        c.setFont("Helvetica-Bold", 9); c.setFillColor(C_AZUL); c.drawString(60, y, "RELACIÓN DE INGRESOS"); y -= 15
        c.setFont("Helvetica", 8); c.setFillColor(C_NEGRO)
        c.drawString(60, y, "Saldo Anterior"); c.drawRightString(480, y, f"$ {s_ant:,.0f}"); y -= 10
        c.drawString(60, y, "Nómina");         c.drawRightString(480, y, f"$ {nom:,.0f}"); y -= 5

        if not oi_m.empty:
            c.setStrokeColor(colors.lightgrey); c.line(60, y, 480, y); y -= 12
            c.setFont("Helvetica-BoldOblique", 7); c.setFillColor(colors.darkgrey)
            c.drawString(60, y, "Ingresos Variables"); y -= 10
            for _, r_oi in oi_m.iterrows():
                c.setFont("Helvetica", 8); c.setFillColor(C_NEGRO)
                c.drawString(65, y, f"● {r_oi['Descripción']}"); c.drawRightString(480, y, f"$ {r_oi['Monto']:,.0f}"); y -= 10
            c.setFont("Helvetica-Bold", 8); c.line(60, y+5, 480, y+5)
            c.drawRightString(480, y-5, f"Total Otros Ingresos: $ {otr_sum:,.0f}"); y -= 25
        else:
            y -= 15

        # ✅ MEJORA: $ en montos de gastos + total al pie
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "RELACIÓN DE GASTOS"); y -= 15
        c.setFont("Helvetica-Bold", 8)
        c.drawString(60, y, "CATEGORÍA - DESCRIPCIÓN"); c.drawRightString(490, y, "MONTO"); c.drawRightString(545, y, "PAGADO"); y -= 12
        c.setStrokeColor(C_GRIS); c.setLineWidth(0.5); c.line(60, y+8, 545, y+8)
        c.setFont("Helvetica", 8); c.setFillColor(C_NEGRO)
        total_gastos_mes = 0
        for _, row in g_m.iterrows():
            if y < 80: c.showPage(); y = head(c, titulo, anio, nombre_usuario); c.setFont("Helvetica", 8)
            monto_fila = float(row['Monto'])
            total_gastos_mes += monto_fila
            c.drawString(60, y, f"{row['Categoría']} - {row['Descripción']}"[:65])
            c.drawRightString(490, y, f"$ {monto_fila:,.0f}")
            c.drawRightString(545, y, "SI" if row["Pagado"] else "NO"); y -= 12

        # ✅ TOTAL AL PIE DE LA TABLA
        c.setStrokeColor(C_AZUL); c.setLineWidth(1); c.line(60, y+8, 545, y+8)
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9)
        c.drawString(60, y-2, "TOTAL GASTOS DEL MES:")
        c.drawRightString(490, y-2, f"$ {total_gastos_mes:,.0f}")
        y -= 25

    if len(meses) > 1:
        if y < 150: c.showPage(); y = head(c, titulo, anio, nombre_usuario)
        y -= 20
        c.setFillColor(C_NARANJA); c.setStrokeColor(C_AZUL); c.setLineWidth(2)
        c.rect(50, y-100, 510, 110, fill=1, stroke=1)
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 12)
        c.drawString(70, y-5, f"RESUMEN: {titulo.upper()}")
        ing_totales         = total_periodo_nomina + total_periodo_otros
        saldo_final_periodo = ing_totales - total_periodo_gastos
        c.setFont("Helvetica", 10)
        c.drawString(70, y-25, f"Total Nómina Percibida:       $ {total_periodo_nomina:,.0f}")
        c.drawString(70, y-40, f"Total Ingresos Adicionales:   $ {total_periodo_otros:,.0f}")
        c.drawString(70, y-55, f"Total Gastos del Periodo:     $ {total_periodo_gastos:,.0f}")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, y-85, f"SALDO TOTAL AL CIERRE: $ {abs(saldo_final_periodo):,.0f}"); y -= 150

    # ============================================================
    # PÁGINA VISUAL: ANÁLISIS (siempre página nueva)
    # ============================================================
    c.showPage()
    y = head(c, titulo, anio, nombre_usuario)

    import math

    def draw_arc_filled(canvas_obj, cx, cy, r_out, r_in, angle_start, angle_end, fill_color):
        steps = max(int(abs(angle_end - angle_start) / 2), 1)
        points_out, points_in = [], []
        for i in range(steps + 1):
            angle = math.radians(angle_start + (angle_end - angle_start) * i / steps)
            points_out.append((cx + r_out * math.cos(angle), cy + r_out * math.sin(angle)))
            points_in.append( (cx + r_in  * math.cos(angle), cy + r_in  * math.sin(angle)))
        path = canvas_obj.beginPath()
        path.moveTo(*points_out[0])
        for pt in points_out[1:]: path.lineTo(*pt)
        for pt in reversed(points_in): path.lineTo(*pt)
        path.close()
        canvas_obj.setFillColor(fill_color)
        canvas_obj.drawPath(path, fill=1, stroke=0)

    # --- TÍTULO ---
    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "ANÁLISIS VISUAL DEL MES"); y -= 8
    c.setStrokeColor(C_NARANJA); c.setLineWidth(2); c.line(50, y, 560, y)

    # ── COORDENADAS FIJAS DE LAS DOS COLUMNAS ──────────────────
    # Columna izquierda:  x 50  → 290  (ancho 240)
    # Columna derecha:    x 320 → 560  (ancho 240)
    # Fila superior:      y 560 → 420
    # Fila inferior tend: y 200 → 100
    # ───────────────────────────────────────────────────────────

    TOP_Y   = y - 20   # 587 aprox
    BAR_X   = 50
    BAR_W   = 170      # ancho máximo de la barra (cabe en 240px)
    ROW_H   = 17
    COL2_X  = 330      # inicio columna derecha

    # ============================================================
    # COL IZQ — DESGLOSE POR CATEGORÍA
    # ============================================================
    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9)
    c.drawString(BAR_X, TOP_Y, "DESGLOSE POR CATEGORÍA")
    y_cat = TOP_Y - 16

    if ultimo_g_m is not None and not ultimo_g_m.empty:
        t_pdf   = ultimo_g_m.copy()
        t_pdf['V'] = t_pdf.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
        total_v = t_pdf['V'].sum()
        if total_v > 0:
            res_cat = t_pdf.groupby("Categoría")['V'].sum().reset_index()
            res_cat['pct'] = res_cat['V'] / total_v * 100
            res_cat = res_cat.sort_values('V', ascending=False)

            for _, r in res_cat.iterrows():
                if y_cat < 220: break
                color_hex = COLOR_MAP.get(r['Categoría'], "#6c757d")
                pct   = r['pct']
                monto = r['V']
                bar_len = max((pct / 100) * BAR_W, 3)

                # ✅ Fondo gris claro (visible en PDF blanco)
                c.setFillColor(HexColor("#e0e0e0"))
                c.roundRect(BAR_X, y_cat - ROW_H + 5, BAR_W, ROW_H - 7, 3, fill=1, stroke=0)
                # Barra color
                c.setFillColor(HexColor(color_hex))
                c.roundRect(BAR_X, y_cat - ROW_H + 5, bar_len, ROW_H - 7, 3, fill=1, stroke=0)
                # ✅ Etiqueta dentro de la barra en negro (visible sobre colores claros)
                c.setFillColor(C_NEGRO); c.setFont("Helvetica-Bold", 6)
                c.drawString(BAR_X + 3, y_cat - 8, r['Categoría'][:18])
                # ✅ Monto + % FUERA a la derecha en negro (sobre fondo blanco del PDF)
                c.setFont("Helvetica", 6); c.setFillColor(C_NEGRO)
                c.drawString(BAR_X + BAR_W + 4, y_cat - 8, f"${monto:,.0f}  {pct:.1f}%")
                y_cat -= ROW_H

    # ============================================================
    # COL DER ARRIBA — GAUGE EFICIENCIA DE AHORRO
    # ============================================================
    META  = 20
    v_cl  = max(0, min(ultimo_ahorro_p, 100))
    CX    = COL2_X + 100    # centro del gauge en la columna derecha
    CY    = TOP_Y - 75
    R_OUT = 65
    R_IN  = 46

    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(CX, TOP_Y, "EFICIENCIA DE AHORRO")

    ang_meta = 180 - (META / 100 * 180)
    draw_arc_filled(c, CX, CY, R_OUT, R_IN, ang_meta, 180, HexColor("#f8d7da"))
    draw_arc_filled(c, CX, CY, R_OUT, R_IN, 0, ang_meta, HexColor("#d4edda"))
    ang_val = 180 - (v_cl / 100 * 180)
    draw_arc_filled(c, CX, CY, R_OUT, R_IN, ang_val, 180, HexColor("#fca311"))

    ang_meta_r = math.radians(ang_meta)
    c.setStrokeColor(C_VERDE); c.setLineWidth(2)
    c.line(CX + R_IN  * math.cos(ang_meta_r), CY + R_IN  * math.sin(ang_meta_r),
           CX + (R_OUT+6) * math.cos(ang_meta_r), CY + (R_OUT+6) * math.sin(ang_meta_r))

    c.setFillColor(C_NARANJA); c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(CX, CY - 12, f"{v_cl:.0f}%")
    c.setFont("Helvetica", 7); c.setFillColor(C_NEGRO)
    c.drawCentredString(CX, CY - 24, f"Meta: {META}%")
    if v_cl >= META:
        c.setFillColor(C_VERDE); c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(CX, CY - 36, "¡Meta alcanzada!")
    else:
        c.setFillColor(C_ROJO); c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(CX, CY - 36, f"Falta {META - v_cl:.0f}% para la meta")

    # ============================================================
    # COL DER ABAJO — ESTADO REAL DEL DINERO
    # ============================================================
    y_est = CY - 60
    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(CX, y_est, "ESTADO REAL DEL DINERO"); y_est -= 14

    total_est = ultimo_vp + ultimo_vpy + (ultimo_bf if ultimo_bf > 0 else 0)
    if total_est > 0:
        items_estado = [
            ("Oblig. Pagadas",  ultimo_vp,                              "#2ecc71"),
            ("Oblig. Pendient", ultimo_vpy,                             "#e74c3c"),
            ("Saldo a Favor",   ultimo_bf if ultimo_bf > 0 else 0,      "#fca311"),
        ]
        BAR_EST_X = COL2_X
        BAR_EST_W = 190
        for label, val, hex_col in items_estado:
            pct_e = (val / total_est * 100) if total_est > 0 else 0
            bar_e = max((pct_e / 100) * BAR_EST_W, 2)
            # ✅ Fondo gris claro
            c.setFillColor(HexColor("#e0e0e0"))
            c.roundRect(BAR_EST_X, y_est - 13, BAR_EST_W, 13, 3, fill=1, stroke=0)
            # Barra color
            c.setFillColor(HexColor(hex_col))
            c.roundRect(BAR_EST_X, y_est - 13, bar_e, 13, 3, fill=1, stroke=0)
            # ✅ Texto negro visible
            c.setFillColor(C_NEGRO); c.setFont("Helvetica-Bold", 7)
            c.drawString(BAR_EST_X + 3, y_est - 10, label)
            c.setFont("Helvetica", 7)
            c.drawRightString(BAR_EST_X + BAR_EST_W - 3, y_est - 10, f"$ {val:,.0f} ({pct_e:.1f}%)")
            y_est -= 22

    # ============================================================
    # PARTE INFERIOR — TENDENCIA DE AHORRO (ancho completo)
    # ============================================================
    Y_TEND_TOP = 210
    c.setStrokeColor(C_AZUL); c.setLineWidth(1)
    c.line(50, Y_TEND_TOP, 560, Y_TEND_TOP)
    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 10)
    c.drawString(50, Y_TEND_TOP - 14, "TENDENCIA DE AHORRO (Últimos 6 meses)")

    meses_lista_h = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    hist_pdf = []; m_idx_ref = meses_lista_h.index(meses[-1])
    for i in range(5, -1, -1):
        idx = m_idx_ref - i; a_h = anio
        if idx < 0: idx += 12; a_h -= 1
        m_n = meses_lista_h[idx]
        i_h = df_i_full[(df_i_full["Periodo"]==m_n) & (df_i_full["Año"]==a_h) & (df_i_full["Usuario"]==u_id)]
        if not i_h.empty:
            g_h  = df_g_full[(df_g_full["Periodo"]==m_n)  & (df_g_full["Año"]==a_h)  & (df_g_full["Usuario"]==u_id)]
            oi_h = df_oi_full[(df_oi_full["Periodo"]==m_n) & (df_oi_full["Año"]==a_h) & (df_oi_full["Usuario"]==u_id)]
            _, _, _, _, bf_h, _ = calcular_metricas(g_h, i_h["Nomina"].iloc[0], oi_h["Monto"].sum() if not oi_h.empty else 0, i_h["SaldoAnterior"].iloc[0])
            hist_pdf.append((f"{m_n[:3]}", bf_h))

    if hist_pdf:
        max_val   = max([abs(v[1]) for v in hist_pdf] + [1])
        BAR_H_MAX = 65
        # ✅ BAR_BASE es la línea del suelo — las barras crecen HACIA ARRIBA desde aquí
        BAR_BASE  = Y_TEND_TOP - 100
        bar_w     = 60
        x_bar     = 80
        # Línea base
        c.setStrokeColor(HexColor("#cccccc")); c.setLineWidth(0.5)
        c.line(60, BAR_BASE, 500, BAR_BASE)
        for m_n, val in hist_pdf:
            h_bar   = max((abs(val) / max_val) * BAR_H_MAX, 3)
            color_b = C_NARANJA if val >= 0 else C_ROJO
            c.setFillColor(color_b)
            # ✅ La barra arranca desde BAR_BASE y sube h_bar puntos
            c.roundRect(x_bar, BAR_BASE, bar_w - 10, h_bar, 3, fill=1, stroke=0)
            # Mes debajo de la línea base
            c.setFillColor(C_NEGRO); c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_bar + (bar_w-10)//2, BAR_BASE - 12, m_n)
            # Valor encima de la barra
            c.setFont("Helvetica", 6)
            c.drawCentredString(x_bar + (bar_w-10)//2, BAR_BASE + h_bar + 3, f"${val:,.0f}")
            x_bar += bar_w

    c.showPage(); c.save(); buf.seek(0)
    return buf

# ============================================================
# --- 10. GENERADOR DE EXCEL ESTILIZADO ---
def generar_excel_reporte(df_g_full, df_i_full, df_oi_full, mes, anio, u_id, nomina, otros, saldo_ant):
    buf = BytesIO()

    # Filtrar datos del mes/año/usuario
    df_g  = df_g_full[(df_g_full["Periodo"]==mes) & (df_g_full["Año"]==anio)].copy()
    df_i  = df_i_full[(df_i_full["Periodo"]==mes) & (df_i_full["Año"]==anio)].copy()
    df_oi = df_oi_full[(df_oi_full["Periodo"]==mes) & (df_oi_full["Año"]==anio)].copy()

    # Calcular métricas
    it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_g, nomina, otros, saldo_ant)

    # Traducir TRUE/FALSE → SI/NO
    if not df_g.empty:
        df_g["Pagado"]               = df_g["Pagado"].map({True:"SI", False:"NO"})
        df_g["Movimiento Recurrente"]= df_g["Movimiento Recurrente"].map({True:"SI", False:"NO"})

    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        wb = writer.book

        # ── COLORES Y FORMATOS ──────────────────────────────────
        AZUL    = "#14213d"
        NARANJA = "#fca311"
        GRIS1   = "#f2f2f2"
        GRIS2   = "#ffffff"
        VERDE   = "#2ecc71"
        ROJO    = "#e74c3c"

        def fmt(bg, font_color="#000000", bold=False, num_fmt=None, border=False, align="left"):
            d = {"bg_color": bg, "font_color": font_color, "bold": bold,
                 "valign": "vcenter", "align": align}
            if num_fmt: d["num_format"] = num_fmt
            if border:  d.update({"border": 1, "border_color": "#cccccc"})
            return wb.add_format(d)

        f_title      = fmt(AZUL,    "#ffffff", bold=True,  align="center")
        f_subtitle   = fmt(NARANJA, AZUL,      bold=True,  align="center")
        f_header     = fmt(AZUL,    "#ffffff", bold=True,  border=True, align="center")
        f_row1       = fmt(GRIS1,   "#000000", border=True)
        f_row2       = fmt(GRIS2,   "#000000", border=True)
        f_row1_money = fmt(GRIS1,   "#000000", border=True, num_fmt='$ #,##0', align="right")
        f_row2_money = fmt(GRIS2,   "#000000", border=True, num_fmt='$ #,##0', align="right")
        f_total      = fmt(NARANJA, AZUL,      bold=True,  num_fmt='$ #,##0', border=True, align="right")
        f_total_lbl  = fmt(NARANJA, AZUL,      bold=True,  border=True)
        f_kpi_lbl    = fmt(AZUL,    "#ffffff", bold=True,  align="center")
        f_kpi_val    = fmt(NARANJA, AZUL,      bold=True,  num_fmt='$ #,##0', align="center")
        f_kpi_verde  = fmt(VERDE,   "#ffffff", bold=True,  num_fmt='$ #,##0', align="center")
        f_kpi_rojo   = fmt(ROJO,    "#ffffff", bold=True,  num_fmt='$ #,##0', align="center")
        f_si         = fmt(GRIS1,   VERDE,     bold=True,  border=True, align="center")
        f_no         = fmt(GRIS1,   ROJO,      bold=True,  border=True, align="center")
        f_si2        = fmt(GRIS2,   VERDE,     bold=True,  border=True, align="center")
        f_no2        = fmt(GRIS2,   ROJO,      bold=True,  border=True, align="center")

        nombre_usuario = st.session_state.get("u_nombre_completo", u_id)

        # ══════════════════════════════════════════════════════
        # HOJA 1 — GASTOS
        # ══════════════════════════════════════════════════════
        ws_g = wb.add_worksheet("📋 Gastos")
        writer.sheets["📋 Gastos"] = ws_g
        ws_g.set_zoom(85)
        ws_g.hide_gridlines(2)

        # Anchos de columna
        ws_g.set_column("A:A", 22)
        ws_g.set_column("B:B", 30)
        ws_g.set_column("C:C", 16)
        ws_g.set_column("D:D", 16)
        ws_g.set_column("E:E", 10)
        ws_g.set_column("F:F", 12)

        # Header limpio sin imagen
        ws_g.set_row(0, 28); ws_g.set_row(1, 22)
        ws_g.merge_range("A1:F1", "MY FINANCEAPP — REPORTE DE GASTOS", f_title)
        ws_g.merge_range("A2:F2", f"{mes.upper()} {anio}  |  {nombre_usuario}", f_subtitle)

        # Encabezados tabla
        headers_g = ["CATEGORÍA", "DESCRIPCIÓN", "MONTO", "VALOR REF.", "PAGADO", "RECURRENTE"]
        for col, h in enumerate(headers_g):
            ws_g.write(3, col, h, f_header)
        ws_g.set_row(3, 20)

        # Filas de datos
        for i, (_, row) in enumerate(df_g.iterrows()):
            r = i + 4
            is_odd = i % 2 == 0
            fm      = f_row1       if is_odd else f_row2
            fm_mon  = f_row1_money if is_odd else f_row2_money
            ws_g.set_row(r, 16)

            ws_g.write(r, 0, str(row.get("Categoría","")),    fm)
            ws_g.write(r, 1, str(row.get("Descripción","")),  fm)
            ws_g.write(r, 2, float(row.get("Monto", 0)),      fm_mon)
            ws_g.write(r, 3, float(row.get("Valor Referencia", 0)), fm_mon)

            # Pagado con color
            pag = str(row.get("Pagado","NO"))
            ws_g.write(r, 4, pag, (f_si if is_odd else f_si2) if pag=="SI" else (f_no if is_odd else f_no2))

            rec = str(row.get("Movimiento Recurrente","NO"))
            ws_g.write(r, 5, rec, (f_si if is_odd else f_si2) if rec=="SI" else (f_no if is_odd else f_no2))

        # Fila total
        last = len(df_g) + 4
        ws_g.set_row(last, 20)
        ws_g.merge_range(last, 0, last, 1, "TOTAL GASTOS DEL MES", f_total_lbl)
        ws_g.write(last, 2, float(df_g["Monto"].apply(pd.to_numeric, errors="coerce").fillna(0).sum()), f_total)
        ws_g.write(last, 3, "", f_total)
        ws_g.write(last, 4, "", f_total)
        ws_g.write(last, 5, "", f_total)

        # ══════════════════════════════════════════════════════
        # HOJA 2 — INGRESOS
        # ══════════════════════════════════════════════════════
        ws_i = wb.add_worksheet("💰 Ingresos")
        writer.sheets["💰 Ingresos"] = ws_i
        ws_i.set_zoom(85)
        ws_i.hide_gridlines(2)
        ws_i.set_column("A:A", 30)
        ws_i.set_column("B:B", 20)

        ws_i.set_row(0, 28); ws_i.set_row(1, 22)
        ws_i.merge_range("A1:B1", "MY FINANCEAPP — INGRESOS DEL MES", f_title)
        ws_i.merge_range("A2:B2", f"{mes.upper()} {anio}  |  {nombre_usuario}", f_subtitle)

        ws_i.write(3, 0, "CONCEPTO",  f_header)
        ws_i.write(3, 1, "MONTO",     f_header)
        ws_i.set_row(3, 20)

        ingresos_base = [
            ("Saldo Anterior",  saldo_ant),
            ("Nómina / Ingreso Fijo", nomina),
        ]
        for i, (label, val) in enumerate(ingresos_base):
            r = i + 4
            fm = f_row1 if i % 2 == 0 else f_row2
            fm_m = f_row1_money if i % 2 == 0 else f_row2_money
            ws_i.write(r, 0, label, fm)
            ws_i.write(r, 1, float(val), fm_m)
            ws_i.set_row(r, 16)

        # Otros ingresos
        row_start = 7
        if not df_oi.empty:
            ws_i.merge_range(row_start, 0, row_start, 1, "INGRESOS ADICIONALES", f_header)
            ws_i.set_row(row_start, 18); row_start += 1
            for i, (_, row) in enumerate(df_oi.iterrows()):
                r = row_start + i
                fm = f_row1 if i % 2 == 0 else f_row2
                fm_m = f_row1_money if i % 2 == 0 else f_row2_money
                ws_i.write(r, 0, str(row.get("Descripción","")), fm)
                ws_i.write(r, 1, float(row.get("Monto", 0)),     fm_m)
                ws_i.set_row(r, 16)
            row_start += len(df_oi) + 1
        else:
            row_start += 1

        # Total ingresos
        ws_i.set_row(row_start, 20)
        ws_i.write(row_start, 0, "TOTAL INGRESOS", f_total_lbl)
        ws_i.write(row_start, 1, float(it),         f_total)

        # ══════════════════════════════════════════════════════
        # HOJA 3 — RESUMEN
        # ══════════════════════════════════════════════════════
        ws_r = wb.add_worksheet("📊 Resumen")
        writer.sheets["📊 Resumen"] = ws_r
        ws_r.set_zoom(85)
        ws_r.hide_gridlines(2)
        ws_r.set_column("A:A", 28)
        ws_r.set_column("B:B", 20)
        ws_r.set_column("C:C", 5)
        ws_r.set_column("D:D", 28)
        ws_r.set_column("E:E", 20)

        ws_r.set_row(0, 28); ws_r.set_row(1, 22)
        ws_r.merge_range("A1:E1", "MY FINANCEAPP — RESUMEN FINANCIERO", f_title)
        ws_r.merge_range("A2:E2", f"{mes.upper()} {anio}  |  {nombre_usuario}", f_subtitle)

        # KPIs en 2 columnas
        kpis = [
            ("INGRESOS TOTALES",       it,   f_kpi_val),
            ("OBLIGACIONES PAGADAS",   vp,   f_kpi_verde),
            ("OBLIGACIONES PENDIENTES",vpy,  f_kpi_rojo),
            ("DINERO DISPONIBLE",      fact, f_kpi_val),
            ("SALDO A FAVOR" if bf >= 0 else "DÉFICIT", bf, f_kpi_verde if bf >= 0 else f_kpi_rojo),
            ("EFICIENCIA DE AHORRO",   ahorro_p, fmt(NARANJA, AZUL, bold=True, num_fmt='0.0"%"', align="center")),
        ]

        row = 4
        for i, (label, val, fmt_val) in enumerate(kpis):
            col_l = 0 if i % 2 == 0 else 3
            col_v = 1 if i % 2 == 0 else 4
            if i % 2 == 0 and i > 0: row += 3
            ws_r.set_row(row,   18)
            ws_r.set_row(row+1, 22)
            ws_r.write(row,   col_l, label, f_kpi_lbl)
            ws_r.write(row,   col_v, "",    f_kpi_lbl)
            ws_r.write(row+1, col_l, "",    fmt_val)
            ws_r.write(row+1, col_v, val,   fmt_val)

        # Tabla resumen categorías
        row_cat = row + 6
        ws_r.merge_range(row_cat, 0, row_cat, 4, "DESGLOSE POR CATEGORÍA", f_header)
        ws_r.set_row(row_cat, 20); row_cat += 1

        ws_r.write(row_cat, 0, "CATEGORÍA",  f_header)
        ws_r.write(row_cat, 1, "MONTO",      f_header)
        ws_r.write(row_cat, 2, "%",          f_header)
        ws_r.write(row_cat, 3, "PAGADO",     f_header)
        ws_r.write(row_cat, 4, "PENDIENTE",  f_header)
        ws_r.set_row(row_cat, 18); row_cat += 1

        if not df_g.empty:
            df_g_num = df_g_full[(df_g_full["Periodo"]==mes) & (df_g_full["Año"]==anio)].copy()
            df_g_num["Monto"] = pd.to_numeric(df_g_num["Monto"], errors="coerce").fillna(0)
            df_g_num["Pagado"] = df_g_num["Pagado"].astype(bool) if df_g_num["Pagado"].dtype != bool else df_g_num["Pagado"]
            total_g = df_g_num["Monto"].sum()
            cat_res = df_g_num.groupby("Categoría").agg(
                Monto=("Monto","sum"),
                Pagado=("Monto", lambda x: x[df_g_num.loc[x.index,"Pagado"]==True].sum()),
            ).reset_index()
            cat_res["Pendiente"] = cat_res["Monto"] - cat_res["Pagado"]
            cat_res["Pct"] = cat_res["Monto"] / total_g * 100 if total_g > 0 else 0
            cat_res = cat_res.sort_values("Monto", ascending=False)

            f_pct = wb.add_format({"num_format": "0.0%", "align":"center", "border":1,
                                   "border_color":"#cccccc", "valign":"vcenter"})
            for i, (_, row_d) in enumerate(cat_res.iterrows()):
                r = row_cat + i
                fm = f_row1 if i % 2 == 0 else f_row2
                fm_m = f_row1_money if i % 2 == 0 else f_row2_money
                ws_r.set_row(r, 16)
                ws_r.write(r, 0, str(row_d["Categoría"]),     fm)
                ws_r.write(r, 1, float(row_d["Monto"]),       fm_m)
                ws_r.write(r, 2, float(row_d["Pct"]/100),     f_pct)
                ws_r.write(r, 3, float(row_d["Pagado"]),      fm_m)
                ws_r.write(r, 4, float(row_d["Pendiente"]),   fm_m)

            # Total categorías
            last_cat = row_cat + len(cat_res)
            ws_r.set_row(last_cat, 20)
            ws_r.write(last_cat, 0, "TOTAL", f_total_lbl)
            ws_r.write(last_cat, 1, float(total_g), f_total)
            ws_r.write(last_cat, 2, "",  f_total)
            ws_r.write(last_cat, 3, float(vp),  f_total)
            ws_r.write(last_cat, 4, float(vpy), f_total)

    buf.seek(0)
    return buf.getvalue()


# --- 11. PANTALLA DE LOGIN ---
# ============================================================
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN):
            st.image(LOGO_LOGIN, use_container_width=True)

        # ✅ Ahora pedimos el correo completo, sin mapeo hardcodeado
        email = st.text_input("Correo electrónico", key="login_email")
        pwd   = st.text_input("Contraseña", type="password", key="login_pwd")

        if st.button("Ingresar", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email.strip(), "password": pwd})

                # Guardamos el UUID real y el token
                st.session_state.token      = res.session.access_token
                st.session_state.usuario_id = res.user.id          # ✅ UUID real de Supabase
                supabase.postgrest.auth(st.session_state.token)

                # Buscamos el nombre real en la tabla usuarios
                try:
                    r_user = supabase.table("usuarios").select("nombre_completo").eq("usuario_id", res.user.id).execute()
                    nombre = r_user.data[0]["nombre_completo"] if r_user.data else email.split("@")[0].title()
                except:
                    nombre = email.split("@")[0].title()

                st.session_state.u_nombre_completo = nombre
                st.session_state.autenticado       = True

                st.success(f"✅ ¡Hola, {nombre}!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Correo o contraseña incorrectos.")
    st.stop()

# ============================================================
# --- 12. APP PRINCIPAL (solo si está autenticado) ---
# ============================================================
u_id  = st.session_state.usuario_id
token = st.session_state.token

# Reinyectamos token y cargamos datos
supabase.postgrest.auth(token)
df_g_full, df_i_full, df_oi_full = cargar_bd(u_id, token)

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
        for key in ["autenticado", "token", "usuario_id", "u_nombre_completo"]:
            st.session_state[key] = False if key == "autenticado" else None if key != "u_nombre_completo" else ""
        st.rerun()

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
                df_mes_g["Pagado"]     = False
                df_mes_g["Fecha Pago"] = pd.NaT
                df_mes_g = df_mes_g.sort_values(["Categoría","Descripción"], ascending=[True,True]).reset_index(drop=True)

# Tabla de gastos
st.markdown('<div class="section-header"><span>📝 Movimiento de Gastos</span></div>', unsafe_allow_html=True)

# ✅ Ordenar A-Z por Categoría y Descripción
if not df_mes_g.empty:
    df_mes_g = df_mes_g.sort_values(["Categoría","Descripción"], ascending=[True,True]).reset_index(drop=True)

# ✅ Fecha Pago: siempre como datetime, NaT para vacíos
if "Fecha Pago" not in df_mes_g.columns:
    df_mes_g["Fecha Pago"] = pd.NaT
else:
    df_mes_g["Fecha Pago"] = pd.to_datetime(df_mes_g["Fecha Pago"], errors="coerce")
# Reemplazar cualquier None/NaN residual por NaT
df_mes_g["Fecha Pago"] = df_mes_g["Fecha Pago"].where(
    df_mes_g["Fecha Pago"].notna(), other=pd.NaT
)

# ✅ Autocompletado: todas las descripciones usadas históricamente por este usuario
descripciones_históricas = sorted(df_g_full["Descripción"].dropna().unique().tolist()) if not df_g_full.empty else []

# ── TABLA VISUAL con colores por categoría ──────────────────
def render_tabla_gastos(df):
    if df.empty:
        st.info("No hay gastos registrados para este mes.")
        return

    filas_html = ""
    for i, (_, row) in enumerate(df.iterrows()):
        bg  = "#2d3238" if i % 2 == 0 else "#3a3f44"
        cat = str(row.get("Categoría", ""))
        col = COLOR_MAP.get(cat, "#aaaaaa")
        # Badge de categoría
        badge = f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;background:{col}22;color:{col}">{cat}</span>'
        # Monto
        monto = float(row.get("Monto", 0) or 0)
        vref  = float(row.get("Valor Referencia", 0) or 0)
        monto_str = f"$ {monto:,.0f}" if monto else f'<span style="color:#6c757d">$ {vref:,.0f}</span>'
        # Pagado / Recurrente
        pagado = row.get("Pagado", False)
        recur  = row.get("Movimiento Recurrente", False)
        chk_p  = '<span style="color:#2ecc71;font-size:16px">✓</span>' if pagado else '<span style="color:#6c757d">—</span>'
        chk_r  = '<span style="color:#2ecc71;font-size:16px">✓</span>' if recur  else '<span style="color:#6c757d">—</span>'
        # Fecha pago
        fp = row.get("Fecha Pago", None)
        if fp is not None and str(fp) not in ["NaT","None",""]:
            try:
                fecha_str = pd.to_datetime(fp).strftime("%d/%m/%Y")
            except:
                fecha_str = '<span style="color:#6c757d">—</span>'
        else:
            fecha_str = '<span style="color:#6c757d">—</span>'

        desc = str(row.get("Descripción",""))
        filas_html += f"""
        <tr style="background:{bg}">
            <td style="padding:7px 10px">{badge}</td>
            <td style="padding:7px 10px;color:#fff;font-size:12px">{desc}</td>
            <td style="padding:7px 10px;color:#fff;font-size:12px;text-align:right">{monto_str}</td>
            <td style="padding:7px 10px;text-align:center">{chk_p}</td>
            <td style="padding:7px 10px;text-align:center">{chk_r}</td>
            <td style="padding:7px 10px;color:#adb5bd;font-size:11px">{fecha_str}</td>
        </tr>"""

    tabla_html = f"""
    <div style="border-radius:10px;overflow:hidden;margin-bottom:8px">
    <table style="width:100%;border-collapse:collapse;font-family:sans-serif">
        <thead>
            <tr style="background:#14213d">
                <th style="padding:9px 10px;color:#fca311;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;text-align:left;font-weight:700">Categoría</th>
                <th style="padding:9px 10px;color:#fca311;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;text-align:left;font-weight:700">Descripción</th>
                <th style="padding:9px 10px;color:#fca311;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;text-align:right;font-weight:700">Monto</th>
                <th style="padding:9px 10px;color:#fca311;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;text-align:center;font-weight:700">Pagado</th>
                <th style="padding:9px 10px;color:#fca311;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;text-align:center;font-weight:700">Recurrente</th>
                <th style="padding:9px 10px;color:#fca311;font-size:11px;text-transform:uppercase;letter-spacing:0.04em;text-align:left;font-weight:700">Fecha Pago</th>
            </tr>
        </thead>
        <tbody>{filas_html}</tbody>
    </table>
    </div>"""
    st.markdown(tabla_html, unsafe_allow_html=True)

# Mostrar tabla visual
render_tabla_gastos(df_mes_g)

# Editor: abierto por defecto si el mes está vacío, colapsado si ya tiene datos
editor_abierto = df_mes_g.empty
with st.expander("✏️ Editar / Agregar movimientos — los cambios se reflejan al GUARDAR", expanded=editor_abierto):
    config_g = {
        "Categoría":            st.column_config.SelectboxColumn("Categoría", options=LISTA_CATEGORIAS, width="medium"),
        "Descripción":          st.column_config.SelectboxColumn("Descripción", options=descripciones_históricas, width="large"),
        "Monto":                st.column_config.NumberColumn("Monto", format="$ %,.0f"),
        "Valor Referencia":     st.column_config.NumberColumn("Valor Referencia", format="$ %,.0f"),
        "Pagado":               st.column_config.CheckboxColumn("Pagado", default=False),
        "Movimiento Recurrente":st.column_config.CheckboxColumn("Recurrente", default=False),
        "Fecha Pago":           st.column_config.DateColumn("Fecha Pago", format="DD/MM/YYYY"),
    }
    df_ed_g = st.data_editor(
        df_mes_g.reindex(columns=["Categoría","Descripción","Monto","Valor Referencia","Pagado","Movimiento Recurrente","Fecha Pago"]).reset_index(drop=True),
        use_container_width=True, num_rows="dynamic", column_config=config_g, key="g_ed"
    )

# Tabla de ingresos adicionales
st.markdown('<div class="section-header"><span>💰 Ingresos Adicionales</span></div>', unsafe_allow_html=True)
df_mes_oi = df_oi_full[(df_oi_full["Periodo"]==mes_s) & (df_oi_full["Año"]==anio_s)].copy()
df_ed_oi  = st.data_editor(
    df_mes_oi.reindex(columns=["Descripción","Monto"]).reset_index(drop=True),
    use_container_width=True, num_rows="dynamic",
    column_config={"Monto": st.column_config.NumberColumn("Monto", format="$ %,.0f")},
    key="oi_ed"
)

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

cats_con_ref  = df_ed_g[df_ed_g["Valor Referencia"] > 0].groupby("Categoría")["Valor Referencia"].sum()
cats_ejecutado= df_ed_g.groupby("Categoría")["Monto"].sum()
todas_cats    = sorted(set(cats_con_ref.index.tolist() + cats_ejecutado.index.tolist()))

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
                supabase.postgrest.auth(token)

                # Borrar registros anteriores del mes
                supabase.table("gastos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
                supabase.table("otros_ingresos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
                supabase.table("ingresos_base").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()

                # Insertar gastos
                if not df_g_limpio.empty:
                    gastos_db = []
                    for _, row in df_g_limpio.iterrows():
                        # Fecha pago: solo si está marcado como pagado
                        fecha_p = None
                        if bool(row["Pagado"]):
                            fp = row.get("Fecha Pago", None)
                            if fp is not None and str(fp) not in ["None","NaT",""]:
                                try:
                                    fecha_p = str(fp)[:10]
                                except:
                                    fecha_p = None
                        gastos_db.append({
                            "anio": int(anio_s), "periodo": str(mes_s),
                            "categoria": str(row["Categoría"]), "descripcion": str(row["Descripción"]),
                            "monto": float(row["Monto"]), "valor_referencia": float(row["Valor Referencia"]),
                            "pagado": bool(row["Pagado"]), "recurrente": bool(row["Movimiento Recurrente"]),
                            "fecha_pago": fecha_p,
                            "usuario_id": str(u_id)
                        })
                    supabase.table("gastos").insert(gastos_db).execute()

                # Insertar otros ingresos
                if not df_oi_limpio.empty:
                    otros_db = [{
                        "anio": int(anio_s), "periodo": str(mes_s),
                        "descripcion": str(row["Descripción"]), "monto": float(row["Monto"]),
                        "usuario_id": str(u_id)
                    } for _, row in df_oi_limpio.iterrows()]
                    supabase.table("otros_ingresos").insert(otros_db).execute()

                # Insertar ingreso base
                supabase.table("ingresos_base").insert({
                    "anio": int(anio_s), "periodo": str(mes_s),
                    "saldo_anterior": float(s_in), "nomina": float(n_in),
                    "otros": float(otr_v), "usuario_id": str(u_id)
                }).execute()

                st.balloons()
                st.success("✅ ¡Todo guardado y sincronizado de forma segura!")
                st.rerun()

        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")
