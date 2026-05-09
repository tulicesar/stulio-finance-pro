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

        tab_login, tab_registro, tab_recuperar = st.tabs(["🔑 Ingresar", "✨ Crear cuenta", "🔓 Recuperar contraseña"])

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
                            if r_user.data and r_user.data[0]["nombre_completo"]:
                                nombre = r_user.data[0]["nombre_completo"]
                            else:
                                # Intentar desde metadatos de Supabase Auth
                                meta = res.user.user_metadata or {}
                                nombre = meta.get("nombre_completo") or email.split("@")[0].title()
                        except:
                            try:
                                meta = res.user.user_metadata or {}
                                nombre = meta.get("nombre_completo") or email.split("@")[0].title()
                            except:
                                nombre = email.split("@")[0].title()
                        st.session_state.u_nombre_completo = nombre
                        st.session_state.autenticado       = True
                        st.session_state.u_email           = email.strip()
                        st.success(f"✅ ¡Hola, {nombre}!")
                        st.rerun()
                    except Exception as e:
                        err = str(e).lower()
                        if "email not confirmed" in err:
                            st.warning("📧 Tu correo aún no está confirmado. Revisa tu bandeja de entrada.")
                        elif "invalid" in err:
                            st.error("❌ Correo o contraseña incorrectos.")
                        else:
                            # 🔴 AQUÍ ESTÁ EL CAMBIO CLAVE 🔴
                            st.error(f"❌ Error técnico de Supabase: {e}")

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

        # ── RECUPERAR CONTRASEÑA ───────────────────────────────
        with tab_recuperar:
            st.markdown("##### ¿Olvidaste tu contraseña?")
            st.caption("Te enviaremos un enlace a tu correo para que puedas restablecerla.")

            email_rec = st.text_input(
                "Correo electrónico",
                key="rec_email",
                placeholder="tucorreo@ejemplo.com"
            )

            if st.button("📧 Enviar enlace de recuperación", use_container_width=True, key="btn_recuperar"):
                if not email_rec or not re.match(r"[^@]+@[^@]+\.[^@]+", email_rec):
                    st.error("❌ Ingresa un correo válido.")
                else:
                    try:
                        supabase.auth.reset_password_for_email(
                            email_rec.strip(),
                            options={"redirect_to": "https://stulio-finance-pro-7xa6pgb2ttmkdper9lwqqo.streamlit.app"}
                        )
                        st.success(f"✅ Enlace enviado a **{email_rec}**")
                        st.info("Revisa tu bandeja de entrada y sigue el enlace para crear una nueva contraseña. Si no lo ves, revisa la carpeta de spam.")
                    except Exception as e:
                        err = str(e).lower()
                        if "user not found" in err or "not found" in err:
                            # Por seguridad, no revelamos si el correo existe o no
                            st.success(f"✅ Si ese correo está registrado, recibirás el enlace en unos minutos.")
                        else:
                            st.error(f"❌ Error: {e}")


def cerrar_sesion():
    for key in ["autenticado", "token", "usuario_id", "u_nombre_completo"]:
        st.session_state[key] = False if key == "autenticado" else (None if key != "u_nombre_completo" else "")
    st.rerun()


def mostrar_eliminar_cuenta(supabase, token, u_id, email_usuario):
    """Solicitud de eliminación de cuenta — notifica al administrador por correo."""
    import requests as _req

    st.markdown(
        '<p style="color:#adb5bd;font-size:0.78rem;margin-bottom:10px">'
        'Opciones avanzadas de tu cuenta</p>',
        unsafe_allow_html=True
    )

    if not st.session_state.get("solicitud_eliminar_paso2"):
        # ── PASO 1: botón inicial ─────────────────────────────
        if st.button("🗑️ Solicitar eliminar cuenta", key="btn_solicitar_eliminar_cuenta"):
            st.session_state["solicitud_eliminar_paso2"] = True
            st.rerun()
    else:
        # ── PASO 2: advertencia + confirmación ────────────────
        st.markdown("""
        <div style="background:#3a1a1a;border-radius:10px;padding:16px;border-left:4px solid #e74c3c;margin-bottom:12px">
            <div style="font-size:0.9rem;font-weight:800;color:#e74c3c;margin-bottom:8px">⚠️ ADVERTENCIA — Acción irreversible</div>
            <div style="font-size:0.82rem;color:#f8d7da;line-height:1.6">
                Al confirmar esta solicitud:<br>
                • Se enviará un aviso al administrador de la app<br>
                • El administrador procesará la eliminación en <b>24-48 horas</b><br>
                • Se borrarán <b>todos tus datos financieros</b> de forma permanente<br>
                • <b>No podrás recuperar</b> ningún historial ni extracto
            </div>
        </div>
        """, unsafe_allow_html=True)

        nombre_usuario = st.session_state.get("u_nombre_completo", "Usuario")
        confirmar = st.checkbox(
            "Entiendo que esta acción es irreversible y perderé todos mis datos.",
            key="check_solicitud_eliminar"
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Confirmar solicitud", key="btn_confirmar_solicitud", disabled=not confirmar):
                try:
                    # ── Guardar solicitud en Supabase ─────────
                    try:
                        supabase.postgrest.auth(token)
                        supabase.table("solicitudes_eliminacion").insert({
                            "usuario_id": str(u_id),
                            "nombre":     nombre_usuario,
                            "email":      email_usuario,
                            "estado":     "pendiente"
                        }).execute()
                    except:
                        pass

                    # ── Enviar correo al administrador via Gmail SMTP ──
                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart

                    _gmail_user = st.secrets.get("gmail", {}).get("email", "")
                    _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")

                    if _gmail_user and _gmail_pass:
                        _msg = MIMEMultipart("alternative")
                        _msg["Subject"] = f"🗑️ Solicitud de eliminación de cuenta — {nombre_usuario}"
                        _msg["From"]    = _gmail_user
                        _msg["To"]      = _gmail_user  # se envía a ti mismo

                        _cuerpo_html = f"""
                        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
                            <h2 style="color:#e74c3c">⚠️ Solicitud de eliminación de cuenta</h2>
                            <p>Un usuario ha solicitado eliminar su cuenta en <b>My FinanceApp</b>.</p>
                            <table style="width:100%;border-collapse:collapse;margin:20px 0">
                                <tr style="background:#f8f9fa">
                                    <td style="padding:10px;font-weight:bold">Nombre</td>
                                    <td style="padding:10px">{nombre_usuario}</td>
                                </tr>
                                <tr>
                                    <td style="padding:10px;font-weight:bold">Correo</td>
                                    <td style="padding:10px">{email_usuario}</td>
                                </tr>
                                <tr style="background:#f8f9fa">
                                    <td style="padding:10px;font-weight:bold">ID de usuario</td>
                                    <td style="padding:10px">{u_id}</td>
                                </tr>
                            </table>
                            <p>Para procesar la eliminación:</p>
                            <ol>
                                <li>Ve a <a href="https://supabase.com/dashboard/project/tfyrokxggpuxescvdrwf/auth/users">Supabase → Authentication → Users</a></li>
                                <li>Busca el usuario por correo: <b>{email_usuario}</b></li>
                                <li>Elimina el usuario y todos sus datos</li>
                            </ol>
                            <p style="color:#adb5bd;font-size:0.85rem">Este correo fue generado automáticamente por My FinanceApp.</p>
                        </div>
                        """
                        _msg.attach(MIMEText(_cuerpo_html, "html"))

                        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as _smtp:
                            _smtp.login(_gmail_user, _gmail_pass)
                            _smtp.sendmail(_gmail_user, _gmail_user, _msg.as_string())

                    st.session_state["solicitud_eliminar_enviada"] = True
                    st.session_state["solicitud_eliminar_paso2"]   = False
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al enviar la solicitud: {e}")

        with col_b:
            if st.button("✗ Cancelar", key="btn_cancelar_solicitud"):
                st.session_state["solicitud_eliminar_paso2"] = False
                st.rerun()

    # ── CONFIRMACIÓN FINAL ────────────────────────────────
    if st.session_state.get("solicitud_eliminar_enviada"):
        st.success("✅ Solicitud enviada correctamente.")
        st.info("El administrador procesará tu solicitud en las próximas 24-48 horas. Puedes seguir usando la app hasta entonces.")
        if st.button("Cerrar", key="btn_cerrar_solicitud"):
            st.session_state["solicitud_eliminar_enviada"] = False
            st.rerun()
