"""
auth.py — Autenticación, registro y gestión de sesión
"""
import streamlit as st
import os
import re


def _validar_password(pwd):
    if len(pwd) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Z]", pwd):
        return False, "La contraseña debe tener al menos una letra mayúscula."
    if not re.search(r"[0-9]", pwd):
        return False, "La contraseña debe tener al menos un número."
    return True, ""


def mostrar_login(supabase, LOGO_LOGIN):
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN):
            st.image(LOGO_LOGIN, use_container_width=True)

        tab_login, tab_registro = st.tabs(["🔑 Ingresar", "✨ Crear cuenta"])

        # ── LOGIN ──────────────────────────────────────────────
        with tab_login:
            email = st.text_input("Correo electrónico", key="login_email")
            pwd   = st.text_input("Contraseña", type="password", key="login_pwd")
            if st.button("Ingresar", use_container_width=True, key="btn_login"):
                if not email or not pwd:
                    st.error("❌ Por favor completa todos los campos.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email.strip(), "password": pwd})
                        st.session_state.token      = res.session.access_token
                        st.session_state.usuario_id = res.user.id
                        supabase.postgrest.auth(st.session_state.token)
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
                        err = str(e).lower()
                        if "email not confirmed" in err:
                            st.warning("📧 Tu correo aún no está confirmado. Revisa tu bandeja de entrada.")
                        elif "invalid" in err:
                            st.error("❌ Correo o contraseña incorrectos.")
                        else:
                            st.error("❌ Error al ingresar. Intenta de nuevo.")

        # ── REGISTRO ───────────────────────────────────────────
        with tab_registro:
            st.markdown("##### Crea tu cuenta en My FinanceApp")
            nombre_completo = st.text_input("Nombre completo", key="reg_nombre", placeholder="Ej: Juan Pérez")
            email_reg       = st.text_input("Correo electrónico", key="reg_email", placeholder="tucorreo@ejemplo.com")
            pwd_reg         = st.text_input("Contraseña", type="password", key="reg_pwd", placeholder="Mínimo 8 caracteres")
            pwd_reg2        = st.text_input("Confirmar contraseña", type="password", key="reg_pwd2", placeholder="Repite la contraseña")
            st.caption("🔒 Mínimo 8 caracteres, una mayúscula y un número.")

            if st.button("Crear cuenta", use_container_width=True, key="btn_registro"):
                if not nombre_completo or not email_reg or not pwd_reg or not pwd_reg2:
                    st.error("❌ Por favor completa todos los campos.")
                elif pwd_reg != pwd_reg2:
                    st.error("❌ Las contraseñas no coinciden.")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", email_reg):
                    st.error("❌ El correo no tiene un formato válido.")
                else:
                    valida, msg = _validar_password(pwd_reg)
                    if not valida:
                        st.error(f"❌ {msg}")
                    else:
                        try:
                            res = supabase.auth.sign_up({
                                "email": email_reg.strip(),
                                "password": pwd_reg,
                                "options": {"data": {"nombre_completo": nombre_completo.strip()}}
                            })
                            if res.user:
                                try:
                                    supabase.table("usuarios").upsert({
                                        "usuario_id":      res.user.id,
                                        "nombre_completo": nombre_completo.strip(),
                                        "password":        "—"
                                    }).execute()
                                except:
                                    pass
                                st.success(f"✅ ¡Cuenta creada! Revisa tu correo **{email_reg}** para confirmar tu cuenta.")
                                st.info("Una vez confirmado tu correo, ingresa desde la pestaña 🔑 Ingresar.")
                            else:
                                st.error("❌ No se pudo crear la cuenta. Intenta de nuevo.")
                        except Exception as e:
                            err = str(e).lower()
                            if "already registered" in err or "already exists" in err:
                                st.error("❌ Este correo ya está registrado. Intenta ingresar.")
                            else:
                                st.error(f"❌ Error al crear la cuenta: {e}")


def cerrar_sesion():
    for key in ["autenticado", "token", "usuario_id", "u_nombre_completo"]:
        st.session_state[key] = False if key == "autenticado" else (None if key != "u_nombre_completo" else "")
    st.rerun()
