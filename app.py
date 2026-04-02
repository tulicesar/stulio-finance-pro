# --- ANÁLISIS ---
st.markdown("### 📊 Análisis")
c1, c2, c3 = st.columns([1.5, 1, 1.2])

with c1:
    st.markdown("#### Desglose de Gastos") # Título añadido
    t_df = df_ed.copy()
    t_df['V'] = t_df.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
    
    if not t_df.empty and t_df['V'].sum() > 0:
        # Sincronización de colores usando el COLOR_MAP
        fig = px.pie(
            t_df, 
            values='V', 
            names='Categoría', 
            hole=0.6, 
            color='Categoría', # Se indica la columna para asignar color
            color_discrete_map=COLOR_MAP # Se aplica el mapa de colores definido
        )
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Barras de leyenda (Sincronizadas por color)
        res = t_df.groupby("Categoría")['V'].sum().reset_index()
        for _, r in res.iterrows():
            color_hex = COLOR_MAP.get(r["Categoría"], "#eee")
            st.markdown(f'<div class="legend-bar" style="background:{color_hex}">{r["Categoría"]} <span>$ {r["V"]:,.0f}</span></div>', unsafe_allow_html=True)

with c2:
    st.markdown("#### Eficiencia de Ahorro") # Título añadido
    gauge = go.Figure(go.Indicator(
        mode="gauge+number", 
        value=ahorro_p, 
        number={'suffix': "%", 'font':{'color':'#d4af37'}}, 
        gauge={
            'axis':{'range':[0,100]},
            'bar':{'color':"white"},
            'bgcolor':"#1f2630",
            'steps':[
                {'range':[0,20],'color':'#ff4b4b'},
                {'range':[50,100],'color':'#00d26a'}
            ],
            'threshold':{'line':{'color':"#d4af37",'width':6},'thickness':0.85,'value':ahorro_p}
        }
    ))
    gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=50,b=0,l=0,r=0))
    st.plotly_chart(gauge, use_container_width=True)

with c3:
    st.markdown("#### Estado Real del Dinero") # Título añadido
    pie = go.Figure(data=[go.Pie(
        labels=['Pagado', 'Pendiente', 'Ahorro'], 
        values=[vp, vpy, saldo_fin], 
        hole=.65, 
        marker_colors=['#2ecc71', '#e74c3c', '#d4af37'], # Colores fijos para el estado del dinero
        textinfo='percent+label'
    )])
    pie.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=380, margin=dict(t=0,b=0,l=0,r=0))
    st.plotly_chart(pie, use_container_width=True)
