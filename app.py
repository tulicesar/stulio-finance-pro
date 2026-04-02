# --- 4. ACCESO ---
if 'autenticado' not in st.session_state: 
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # Carga del nuevo logo desde el repositorio
        NUEVO_LOGO = "logoapp 2.jpg"
        if os.path.exists(NUEVO_LOGO):
            st.image(NUEVO_LOGO, use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center; color: #d4af37;'>My FinanceApp</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; margin-top: -20px;'>by Stulio Designs</p>", unsafe_allow_html=True)
        
        tab_log, tab_reg = st.tabs(["🔑 Entrar", "📝 Registro"])
        usuarios = cargar_usuarios()
        
        with tab_log:
            u_in = st.text_input("Usuario", key="l_u").strip()
            p_in = st.text_input("Contraseña", type="password", key="l_p").strip()
            if st.button("Iniciar Sesión", use_container_width=True):
                if u_in in usuarios and usuarios[u_in]["pass"] == p_in:
                    st.session_state.autenticado = True
                    st.session_state.usuario_id = u_in
                    st.session_state.u_nombre_completo = usuarios[u_in].get("nombre", u_in)
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
                    
        with tab_reg:
            rn_full = st.text_input("Nombre Completo")
            rn_user = st.text_input("Nuevo Usuario")
            rn_pass = st.text_input("Nueva Contraseña", type="password")
            if st.button("Crear Cuenta", use_container_width=True):
                if rn_user and rn_pass:
                    usuarios[rn_user] = {"pass": rn_pass, "nombre": rn_full}
                    guardar_usuarios(usuarios)
                    st.success("✅ Cuenta creada. Ya puedes entrar.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()
