# --- 1b. FUENTE SF PRO DISPLAY ---
import base64

def embed_font(path, weight):
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"""
    @font-face {{
        font-family: 'SF Pro Display';
        src: url(data:font/otf;base64,{data}) format('opentype');
        font-weight: {weight};
    }}
    """

css_fonts = (
    embed_font("SFNSDisplay-Regular.otf",  "400") +
    embed_font("SFNSDisplay-Medium.otf",   "500") +
    embed_font("SFNSDisplay-Semibold.otf", "600") +
    embed_font("SFNSDisplay-Bold.otf",     "700")
)

# --- 5. ESTILOS ---
st.markdown(f"""
    <style>
    * {{
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}
    {css_fonts}
    header {{ background-color: rgba(0,0,0,0) !important; }}
    .stApp {{ background: #495057; color: #ffffff; }}

    /* ── TABLAS — filas alternas forzadas ── */
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
    #close-sidebar-btn {{
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
    }}
    @media (max-width: 768px) {{
        #close-sidebar-btn {{ display: block; }}
    }}

    /* ── BOTONES sidebar ── */
    .stButton>button {{
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
    }}
    .stButton>button:hover {{
        background: #1e3260 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 0 #fca311 !important;
    }}
    .stButton>button:active {{
        transform: translateY(4px) !important;
        box-shadow: none !important;
    }}

    /* ── BOTÓN GUARDAR ── */
    .save-btn button {{
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
    }}
    .save-btn button:hover {{
        filter: brightness(1.06) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 7px 0 #14213d !important;
    }}
    .save-btn button:active {{
        transform: translateY(5px) !important;
        box-shadow: none !important;
    }}

    /* ── JERARQUÍA DE TÍTULOS ── */
    h2 {{ color: #ffffff !important; font-weight: 800 !important;
         border-bottom: 2px solid #fca311; padding-bottom: 6px; }}
    h3 {{ color: #fca311 !important; font-weight: bold !important; }}
    h4 {{ color: #adb5bd !important; font-weight: 600 !important; font-size: 0.9rem !important; text-transform: uppercase; }}

    /* ── DIVIDER ── */
    hr {{ border-color: rgba(252,163,17,0.3) !important; }}
    </style>
    """, unsafe_allow_html=True)
