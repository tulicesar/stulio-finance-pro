"""
auth.py — Autenticación y gestión de sesión
"""
import streamlit as st
import os


def mostrar_login(supabase, LOGO_LOGIN):
    """Muestra la pantalla de login y maneja la autenticación."""
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN):
            st.image(LOGO_LOGIN, use_container_width=True)

        email = st.text_input("Correo electrónico", key="login_email")
        pwd   = st.text_input("Contraseña", type="password", key="login_pwd")

        if st.button("Ingresar", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({
                    "email": email.strip(), "password": pwd
                })

                st.session_state.token      = res.session.access_token
                st.session_state.usuario_id = res.user.id
                supabase.postgrest.auth(st.session_state.token)

                # Buscar nombre real en la tabla usuarios
                try:
                    r_user = supabase.table("usuarios").select("nombre_completo").eq("usuario_id", res.user.id).execute()
                    nombre = r_user.data[0]["nombre_completo"] if r_user.data else email.split("@")[0].title()
                except:
                    nombre = email.split("@")[0].title()

                st.session_state.u_nombre_completo = nombre
                st.session_state.autenticado       = True

                st.success(f"✅ ¡Hola, {nombre}!")
                st.rerun()

            except Exception:
                st.error("❌ Correo o contraseña incorrectos.")


def cerrar_sesion():
    """Limpia el session state y cierra la sesión."""
    for key in ["autenticado", "token", "usuario_id", "u_nombre_completo"]:
        st.session_state[key] = False if key == "autenticado" else (None if key != "u_nombre_completo" else "")
    st.rerun()
