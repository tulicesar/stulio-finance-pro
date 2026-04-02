import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Page Config ---
st.set_page_config(layout="wide", page_title="My FinanceApp - Modo Claro")

# --- Custom CSS for Theme and Component Styling ---
# Based on instructions: Light theme (light gray background, black text), 
# light green sidebar background, light gray input backgrounds, light gray button backgrounds.
# Reinstall the category color bars and values.
st.markdown("""
<style>
    /* Global App Background and Text */
    .stApp {
        background-color: #F0F2F6 !important;
        color: #000000 !important;
    }

    /* Sidebar Background and Text */
    [data-testid="stSidebar"] {
        background-color: #D1EAE0 !important; /* Settled light green */
        color: #000000 !important;
    }
    
    /* Input backgrounds in Sidebar (Año, Mes, Nomina, etc.) */
    [data-testid="stSidebar"] [data-testid="stNumberInputContainer"],
    [data-testid="stSidebar"] [data-testid="stTextInputContainer"],
    [data-testid="stSidebar"] div[class*="stSelectbox"] div[role="combobox"] {
        background-color: #E0E0E0 !important; /* Light gray input */
        color: #000000 !important;
        border-color: #B0B0B0 !important;
    }
    [data-testid="stSidebar"] input {
        color: #000000 !important;
    }
    [data-testid="stSidebar"] label {
        color: #000000 !important;
    }

    /* Titles, headings, and markdown text */
    h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #000000 !important;
    }

    /* Sidebar Button styling (Gris claro background, black text) */
    [data-testid="stSidebar"] div.stButton button {
        background-color: #E0E0E0 !important; /* Light gray button */
        color: #000000 !important;
        border: 1px solid #A0A0A0 !important;
        width: 100% !important;
        margin-top: 5px !important;
    }

    /* Sidebar Button hover effect */
    [data-testid="stSidebar"] div.stButton button:hover {
        background-color: #D0D0D0 !important;
    }

    /* Summary Card Styling */
    .summary-card-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 20px;
    }
    .summary-card {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 10px;
        padding: 20px;
        flex: 1;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .summary-card h4 {
        margin: 0;
        color: #333333 !important;
        font-size: 14px;
        text-transform: uppercase;
    }
    .summary-card p {
        margin: 5px 0 0 0;
        font-size: 24px;
        font-weight: bold;
    }

    /* Info Legend Styling */
    .info-legend-container {
        margin-top: 20px;
        color: #000000 !important;
    }
    .info-legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        background-color: #F8F9FA;
        padding: 5px 10px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .color-bar {
        width: 120px;
        height: 25px;
        border-radius: 15px;
        margin-right: 15px;
    }
    .category-text {
        font-weight: bold;
        flex: 1;
    }
    .value-text {
        font-weight: bold;
    }

    /* Main Area Table Styling (Theme overrides might be enough, but here's CSS) */
    .stDataFrame, div[data-testid="stTable"] table {
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }
    div[data-testid="stTable"] th {
        background-color: #E0E0E0 !important;
        color: #000000 !important;
    }
    div[data-testid="stTable"] td {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-bottom: 1px solid #D0D0D0 !important;
    }

</style>
""", unsafe_allow_html=True)

# --- Define Color Map ---
CATEGORY_COLORS = {
    'Ahorro (Saldo)': '#DAA520', # Goldenrod for savings
    'Pendiente': '#DC143C',     # Crimson for pending
    'Pagado': '#00FA9A'         # Medium Spring Green for paid
}

# --- Sidebar ---
with st.sidebar:
    # Top logo composition
    try:
        # Check if file exists, if not, use an alternative or placeholder
        if os.path.exists("logo_light.png"):
             st.image("logo_light.png", width=150)
        elif os.path.exists("logoapp3.jpg"):
             st.image("logoapp3.jpg", width=150)
        else:
             # Just in case, try all 
             files = ["logo_light.png", "logoapp3.jpg", "image_9.png", "image_10.png"]
             for f in files:
                if os.path.exists(f):
                    st.image(f, width=150)
                    break
             else:
                st.write("Logo Placeholder")
    except Exception as e:
        st.write("Logo Not Found")

    st.markdown("## 💰 My FinanceApp")
    st.markdown("*by Stulio Designs*", help="Personal Finance Dashboard")
    st.divider()
    
    # Financial Inputs
    year_col1, year_col2 = st.columns([1, 1])
    with year_col1:
        st.write("📊 Año")
    with year_col2:
        st.number_input("Año", value=2026, step=1, label_visibility="collapsed")
        
    mes_col1, mes_col2 = st.columns([1, 1])
    with mes_col1:
        st.write("🗓️ Mes Actual")
    with mes_col2:
        st.selectbox("Mes Actual", ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'], index=0, label_visibility="collapsed")
    
    st.divider()
    
    check_traer_saldo = st.checkbox("Traer saldo de Diciembre", value=True)
    
    input_list = [
        {"icon": "🏦", "label": "Saldo Anterior", "value": 0.00},
        {"icon": "💸", "label": "Nómina", "value": 1000000.00},
        {"icon": "➕", "label": "Otros", "value": 0.00},
    ]
    
    for item in input_list:
        label_col1, label_col2 = st.columns([1, 1.5])
        with label_col1:
            st.write(f"{item['icon']} {item['label']}")
        with label_col2:
            st.number_input(item['label'], value=item['value'], step=0.01, format="%.2f", label_visibility="collapsed")

    st.divider()
    
    # Secciones
    st.markdown("### 📄 Extractos")
    col_pdf, col_excel = st.columns(2)
    with col_pdf:
        st.button("PDF Ene", key="pdf_ene")
    with col_excel:
        st.button("Excel Ene", key="excel_ene")
        
    st.divider()
    st.markdown("### ⚖️ Balances Semestrales")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.button("🟢 Semestre 1", key="semestre_1")
    with col_s2:
        st.button("🟢 Semestre 2", key="semestre_2")
        
    # Salir button
    st.divider()
    st.button("🚪 Salir")

# --- Main Area ---
st.title("Enero 2026")

# Sample DataFrame
data = {
    'Icono': ['❤️', '💡', '📶'],
    'Categoría': ['Salud', 'Servicios', 'Servicios'],
    'Descripción': ['medicinas', 'luz', 'agua'],
    'Monto': [20000, 30000, 40000],
    'Valor Referencia': [40000, 0, 50000],
    'Pagado': [True, False, False],
    'Movimiento Recurrente': [True, False, False]
}
df = pd.DataFrame(data)

# Show DataEditor
st.markdown("### 📋 Ene Data")
st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True)

# --- Summary Cards (Custom HTML/CSS) ---
summary_data = [
    {"title": "INGRESOS", "value": "$ 1,000,000", "color": "#000000"},
    {"title": "PAGADO", "value": "$ 20,000", "color": "#00FF7F"}, # SpringGreen
    {"title": "PENDIENTE", "value": "$ 50,000", "color": "#DC143C"}, # Crimson
    {"title": "FONDOS ACTUALES", "value": "$ 980,000", "color": "#4169E1"}, # RoyalBlue
    {"title": "AHORRO FINAL", "value": "$ 930,000", "color": "#DAA520"} # Goldenrod
]

summary_cards_html = f'<div class="summary-card-container">'
for card in summary_data:
    summary_cards_html += f"""
        <div class="summary-card">
            <h4>{card['title']}</h4>
            <p style="color: {card['color']} !important;">{card['value']}</p>
        </div>
    """
summary_cards_html += '</div>'
st.markdown(summary_cards_html, unsafe_allow_html=True)

# --- Infographics and Info Legend ---
# Instructions: "reinstalar las barras de colores y valores en la leyenda"
# These are present in the mock info legend at the bottom of image_7.png.
# I will create a dedicated legend component below the charts.

infographic_row = st.container()
with infographic_row:
    st.markdown("### 📊 Análisis de Gastos")
    col_donut1, col_gauge, col_donut2 = st.columns([1.5, 1, 1.2])

    with col_donut1:
        # Donut Chart 1 (Example Data)
        donut1_labels = ['Hogar', 'Servicios', 'Comida']
        donut1_values = [450000, 300000, 250000]
        fig_donut1 = go.Figure(data=[go.Pie(labels=donut1_labels, values=donut1_values, hole=.65, 
                                          marker=dict(colors=['#51446E', '#FBBF24', '#F45D48']))])
        fig_donut1.update_layout(title="Desglose Presupuestado", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                font_color="#000000", showlegend=False)
        st.plotly_chart(fig_donut1, use_container_width=True)

    with col_gauge:
        # Gauge Chart (Saving Efficiency)
        saving_efficiency = 93
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = saving_efficiency,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Eficiencia de Ahorro", 'font': {'color': '#000000', 'size': 16}},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#000000", 'tickmode': "array", 'tickvals': [0, 20, 40, 60, 80, 100]},
                'bar': {'color': "#000000"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#000000",
                'steps': [
                    {'range': [0, saving_efficiency/2], 'color': '#F45D48'}, # Red
                    {'range': [saving_efficiency/2, saving_efficiency], 'color': '#FBBF24'}, # Yellow
                    {'range': [saving_efficiency, 100], 'color': '#00FA9A'} # Green
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 93
                }
            }))
        
        fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              font={'color': "#000000"}, margin=dict(l=20, r=20, t=50, b=20))
        # Add flags for the medidor, just as a placeholder to match image
        st.plotly_chart(fig_gauge, use_container_width=True)
        # st.markdown(f'<div style="text-align:center; font-size:40px; font-weight:bold; color:#000000; margin-top:-70px;">{saving_efficiency}% <span style="font-size: 20px;">🏳️</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center; font-size:40px; font-weight:bold; color:#000000; margin-top:-70px;">{saving_efficiency}% <img src="https://flagcdn.com/w20/flag_white.png" width="20" style="vertical-align: middle;"></div>', unsafe_allow_html=True)

    with col_donut2:
        # Donut Chart 2 (Real Money State)
        donut2_data = {
            'Ahorro (Saldo)': [1000000, '90%'],
            'Pendiente': [100000, '9%'],
            'Pagado': [10000, '1%']
        }
        donut2_labels = list(donut2_data.keys())
        donut2_values = [v[0] for v in donut2_data.values()]
        donut2_percentages = [v[1] for v in donut2_data.values()]
        donut2_colors = [CATEGORY_COLORS[l] for l in donut2_labels]
        
        fig_donut2 = go.Figure(data=[go.Pie(labels=donut2_labels, values=donut2_values, hole=.75, 
                                          textinfo='label+percent', textposition='outside', textfont_color='#000000',
                                          marker=dict(colors=donut2_colors))])
        
        fig_donut2.update_layout(title="Estado Real del Dinero", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                font_color="#000000", showlegend=False)
        st.plotly_chart(fig_donut2, use_container_width=True)

# --- Info Legend Reinstallation ---
# Instructions: "reinstalar las barras de colores y valores en la leyenda"
# These are the actual colored bars with text and values.
st.divider()
st.markdown("### 📊 Leyenda de Categorías Presupuestadas")
legend_container = st.container()
with legend_container:
    info_legend_items = [
        {"color": CATEGORY_COLORS['Ahorro (Saldo)'], "category": "Ahorro (Saldo)", "value": "$ 20,000"},
        {"color": "#FBBF24", "category": "Servicios", "value": "$ 50,000"} # Mock from image
    ]
    
    legend_html = '<div class="info-legend-container">'
    for item in info_legend_items:
        legend_html += f"""
            <div class="info-legend-item">
                <div class="color-bar" style="background-color: {item['color']};"></div>
                <div class="category-text">{item['category']}</div>
                <div class="value-text">{item['value']}</div>
            </div>
        """
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)

st.divider()

# Boton guardar
col_final_1, col_final_2 = st.columns([1, 10])
with col_final_1:
    st.button("💾 GUARDAR CAMBIOS DEFINITIVOS")
