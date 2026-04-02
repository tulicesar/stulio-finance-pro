import streamlit as st
# ... tus otras importaciones ...

# --- INICIALIZACIÓN DE ESTADO ---
if 'modo_oscuro' not in st.session_state:
    st.session_state.modo_oscuro = True  # Predeterminado

# --- SIDEBAR: BOTÓN DE PREFERENCIA ---
with st.sidebar:
    # Usamos un toggle para un look moderno
    st.session_state.modo_oscuro = st.toggle('Modo Oscuro 🌙', value=st.session_state.modo_oscuro)
    st.divider()
    # ... resto de tu sidebar ...

# --- DEFINICIÓN DE VARIABLES DE COLOR ---
if st.session_state.modo_oscuro:
    # MODO OSCURO (Basado en logoapp 2.png)
    bg_app = "#10141D"
    bg_card = "#1A1F2B"
    text_main = "#FFFFFF"
    text_sec = "#A0AAB5"
    accent_vibrante = "#38EF7D" # Verde flecha
    accent_oro = "#F1C40F"      # Dorado monedas
    # Colores para gráficos (puedes reutilizar tu COLOR_MAP pero ajustando tonos)
    color_map_graficos = {
        "Hogar": "#5DADE2", "Servicios": "#F4D03F", "Salud": "#EC7063", 
        "Transporte": "#AF7AC5", "Obligaciones": "#EB984E", "Alimentación": "#A569BD", 
        "Otros": "#82E0AA", "Impuestos": "#F1948A"
    }
else:
    # MODO CLARO (Basado en logoapp 3.png)
    bg_app = "#F8F9FA"
    bg_card = "#FFFFFF"
    text_main = "#10141D"
    text_sec = "#5D6D7E"
    accent_vibrante = "#11998E" # Verde cian profundo
    accent_oro = "#E67E22"      # Ocre/Dorado
    # Colores para gráficos (tonos más saturados para fondo claro)
    color_map_graficos = {
        "Hogar": "#3498DB", "Servicios": "#F1C40F", "Salud": "#E74C3C", 
        "Transporte": "#8E44AD", "Obligaciones": "#E67E22", "Alimentación": "#884EA0", 
        "Otros": "#2ECC71", "Impuestos": "#E06666"
    }

# --- INYECCIÓN DE CSS DINÁMICO ---
st.markdown(f"""
    <style>
    /* Estilos globales */
    .stApp {{
        background-color: {bg_app} !important;
        color: {text_main} !important;
    }}
    
    /* Títulos y textos generales */
    h1, h2, h3, h4, p, span, label {{
        color: {text_main} !important;
    }}
    
    /* Textos secundarios (labels en formularios, etc.) */
    .stMarkdown p, .stCaption {{
        color: {text_sec} !important;
    }}

    /* Tarjetas de Métricas y Sidebar */
    [data-testid="stSidebar"], .card {{
        background-color: {bg_card} !important;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: {text_main} !important;
    }}
    
    /* Botones Principales (como Guardar) */
    .stButton>button {{
        background-color: {accent_vibrante} !important;
        color: {("#FFFFFF" if st.session_state.modo_oscuro else "#FFFFFF")} !important;
        border-radius: 8px;
        font-weight: bold;
    }}
    
    /* Botones Secundarios (como Salir, Excel, PDF) */
    [data-testid="stSidebar"] .stButton>button {{
        background-color: transparent !important;
        border: 2px solid {text_sec} !important;
        color: {text_sec} !important;
    }}
    [data-testid="stSidebar"] .stButton>button:hover {{
        border-color: {accent_vibrante} !important;
        color: {accent_vibrante} !important;
    }}

    /* Toggles y Radio buttons activos */
    .st-bj, .st-b8, .st-b9, .st-ba {{
        background-color: {accent_vibrante} !important;
    }
    
    /* Data Editor (Tabla) */
    [data-testid="stDataEditor"] {{
        background-color: {bg_card} !important;
        color: {text_main} !important;
    }}
    
    </style>
    """, unsafe_allow_html=True)
