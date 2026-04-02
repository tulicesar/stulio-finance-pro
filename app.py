# --- 4. ACCESO (CORREGIDO CON REGISTRO) ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        # Contenedor visual para el Login
        st.markdown('<div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; border: 1px solid #d4af37;">', unsafe_allow_html=True)
        
        if os.path.exists(LOGO_LOGIN): 
            st.image(LOGO_LOGIN, use_container_width=True)
        else:
            st.markdown("<h2 style='text-align: center; color: #d4af37;'>My FinanceApp</h2>", unsafe_allow_html=True)
        
        # Pestañas para elegir entre entrar o registrarse
        tab_entrar, tab_registrar = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
        
        usuarios = cargar_usuarios()
        
        with tab_entrar:
            u_in = st.text_input("Usuario", key="login_user")
            p_in = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("Entrar", use_container_width=True):
                if u_in in usuarios and usuarios[u_in]["pass"] == p_in:
                    st.session_state.autenticado = True
                    st.session_state.usuario_id = u_in
                    st.session_state.u_nombre_completo = usuarios[u_in].get("nombre", u_in)
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
        
        with tab_registrar:
            nuevo_nombre = st.text_input("Nombre Completo")
            nuevo_usuario = st.text_input("Nombre de Usuario (ID)")
            nueva_pass = st.text_input("Crear Contraseña", type="password")
            
            if st.button("Crear Cuenta", use_container_width=True):
                if nuevo_usuario in usuarios:
                    st.warning("⚠️ El usuario ya existe")
                elif nuevo_usuario and nueva_pass:
                    usuarios[nuevo_usuario] = {"pass": nueva_pass, "nombre": nuevo_nombre}
                    guardar_usuarios(usuarios)
                    st.success("✅ Registro exitoso. Ahora puedes iniciar sesión.")
                else:
                    st.error("❌ Por favor completa los campos")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()
