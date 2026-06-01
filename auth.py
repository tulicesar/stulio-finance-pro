"""
auth.py — Autenticación, registro y gestión de sesión
Registro con aprobación manual del administrador.
"""
import streamlit as st
import os
import re


ADMIN_EMAIL = "arqtulicesar@gmail.com"
APP_URL = "https://stulio-finance-pro-7xa6pgb2ttmkdper9lwqqo.streamlit.app"


def _validar_password(pwd):
    if len(pwd) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Z]", pwd):
        return False, "La contraseña debe tener al menos una letra mayúscula."
    if not re.search(r"[0-9]", pwd):
        return False, "La contraseña debe tener al menos un número."
    return True, ""


def _enviar_correo_html(gmail_user, gmail_pass, destinatario, asunto, html):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = gmail_user
    msg["To"] = destinatario
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_pass)
        smtp.sendmail(gmail_user, destinatario, msg.as_string())


def _notificar_admin_nuevo_registro(gmail_user, gmail_pass, nombre, email, token_aprobacion):
    """Envía correo al admin con botones Aprobar / Rechazar."""
    aprobar_url  = f"{APP_URL}/?accion=aprobar&token={token_aprobacion}"
    rechazar_url = f"{APP_URL}/?accion=rechazar&token={token_aprobacion}"

    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1e23;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:30px 20px">

  <div style="text-align:center;margin-bottom:24px">
    <h1 style="color:#fca311;font-size:1.8rem;margin:0">My FinanceApp</h1>
    <p style="color:#adb5bd;font-size:0.85rem;margin:4px 0">by Stulio Designs</p>
  </div>

  <div style="background:#2d3238;border-radius:12px;padding:24px;margin-bottom:20px;border-left:4px solid #fca311">
    <h2 style="color:#fff;margin:0 0 12px">🔔 Nueva solicitud de registro</h2>
    <table style="width:100%;border-collapse:collapse">
      <tr>
        <td style="padding:8px 0;color:#adb5bd;font-size:0.85rem;width:140px">Nombre:</td>
        <td style="padding:8px 0;color:#fff;font-size:0.85rem"><b>{nombre}</b></td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#adb5bd;font-size:0.85rem">Correo:</td>
        <td style="padding:8px 0;color:#fff;font-size:0.85rem"><b>{email}</b></td>
      </tr>
    </table>
  </div>

  <div style="text-align:center;margin-bottom:16px">
    <a href="{aprobar_url}"
       style="background:#27ae60;color:#fff;padding:14px 40px;border-radius:8px;
              text-decoration:none;font-weight:800;font-size:1rem;display:inline-block">
      ✅ Aprobar registro
    </a>
  </div>
  <div style="text-align:center;margin-bottom:24px">
    <a href="{rechazar_url}"
       style="background:#e74c3c;color:#fff;padding:10px 28px;border-radius:8px;
              text-decoration:none;font-weight:700;font-size:0.9rem;display:inline-block">
      ❌ Rechazar solicitud
    </a>
  </div>

  <div style="text-align:center;border-top:1px solid #3a3f44;padding-top:16px">
    <p style="color:#6c757d;font-size:0.75rem;margin:0">
      My FinanceApp · by Stulio Designs<br>
      Este correo fue generado automáticamente.
    </p>
  </div>
</div>
</body>
</html>"""
    _enviar_correo_html(gmail_user, gmail_pass, ADMIN_EMAIL,
                        f"🔔 Solicitud de registro — {nombre}", html)


def _notificar_usuario_pendiente(gmail_user, gmail_pass, nombre, email):
    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1e23;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:30px 20px">
  <div style="text-align:center;margin-bottom:24px">
    <h1 style="color:#fca311;font-size:1.8rem;margin:0">My FinanceApp</h1>
    <p style="color:#adb5bd;font-size:0.85rem;margin:4px 0">by Stulio Designs</p>
  </div>
  <div style="background:#2d3238;border-radius:12px;padding:24px;border-left:4px solid #fca311">
    <h2 style="color:#fff;margin:0 0 10px">⏳ Solicitud recibida</h2>
    <p style="color:#dee2e6;font-size:0.85rem;line-height:1.7;margin:0">
      Hola <b>{nombre.split()[0]}</b>, recibimos tu solicitud para unirte a <b>My FinanceApp</b>.<br><br>
      El administrador revisará tu solicitud y te notificará por este correo
      cuando tu cuenta esté lista.<br><br>
      Gracias por tu paciencia 🙏
    </p>
  </div>
  <div style="text-align:center;border-top:1px solid #3a3f44;padding-top:16px;margin-top:24px">
    <p style="color:#6c757d;font-size:0.75rem;margin:0">
      ¿Tienes dudas? Escríbenos a {ADMIN_EMAIL}
    </p>
  </div>
</div>
</body>
</html>"""
    _enviar_correo_html(gmail_user, gmail_pass, email,
                        "⏳ Tu solicitud está en revisión — My FinanceApp", html)


def _notificar_usuario_aprobado(gmail_user, gmail_pass, nombre, email):
    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1e23;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:30px 20px">
  <div style="text-align:center;margin-bottom:24px">
    <h1 style="color:#fca311;font-size:1.8rem;margin:0">My FinanceApp</h1>
    <p style="color:#adb5bd;font-size:0.85rem;margin:4px 0">by Stulio Designs</p>
  </div>
  <div style="background:#2d3238;border-radius:12px;padding:24px;border-left:4px solid #27ae60;margin-bottom:20px">
    <h2 style="color:#fff;margin:0 0 10px">🎉 ¡Tu cuenta fue aprobada!</h2>
    <p style="color:#dee2e6;font-size:0.85rem;line-height:1.7;margin:0">
      Hola <b>{nombre.split()[0]}</b>, el administrador aprobó tu acceso a <b>My FinanceApp</b>.<br><br>
      Revisa tu bandeja de entrada — te enviamos un correo de confirmación de Supabase.
      Haz clic en ese enlace para activar tu cuenta, luego usa la opción
      <b>"🔓 Recuperar contraseña"</b> en la app para crear tu contraseña personal.
    </p>
  </div>
  <div style="text-align:center;margin-bottom:24px">
    <a href="{APP_URL}"
       style="background:#fca311;color:#14213d;padding:14px 32px;border-radius:8px;
              text-decoration:none;font-weight:800;font-size:1rem;display:inline-block">
      🚀 Ir a My FinanceApp
    </a>
  </div>
  <div style="text-align:center;border-top:1px solid #3a3f44;padding-top:16px">
    <p style="color:#6c757d;font-size:0.75rem;margin:0">
      ¿Tienes dudas? Escríbenos a {ADMIN_EMAIL}
    </p>
  </div>
</div>
</body>
</html>"""
    _enviar_correo_html(gmail_user, gmail_pass, email,
                        "🎉 ¡Tu cuenta en My FinanceApp fue aprobada!", html)


def _notificar_usuario_rechazado(gmail_user, gmail_pass, nombre, email):
    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1e23;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:30px 20px">
  <div style="text-align:center;margin-bottom:24px">
    <h1 style="color:#fca311;font-size:1.8rem;margin:0">My FinanceApp</h1>
    <p style="color:#adb5bd;font-size:0.85rem;margin:4px 0">by Stulio Designs</p>
  </div>
  <div style="background:#2d3238;border-radius:12px;padding:24px;border-left:4px solid #e74c3c">
    <h2 style="color:#fff;margin:0 0 10px">❌ Solicitud no aprobada</h2>
    <p style="color:#dee2e6;font-size:0.85rem;line-height:1.7;margin:0">
      Hola <b>{nombre.split()[0]}</b>, lamentablemente tu solicitud de acceso a
      <b>My FinanceApp</b> no fue aprobada en este momento.<br><br>
      Si crees que es un error, puedes escribirnos directamente a {ADMIN_EMAIL}.
    </p>
  </div>
  <div style="text-align:center;border-top:1px solid #3a3f44;padding-top:16px;margin-top:24px">
    <p style="color:#6c757d;font-size:0.75rem;margin:0">My FinanceApp · by Stulio Designs</p>
  </div>
</div>
</body>
</html>"""
    _enviar_correo_html(gmail_user, gmail_pass, email,
                        "Actualización sobre tu solicitud — My FinanceApp", html)


def _procesar_accion_url(supabase):
    """
    Lee ?accion=aprobar|rechazar&token=... de la URL y actúa.
    Se llama al inicio de mostrar_login().
    """
    params = st.query_params
    accion = params.get("accion", "")
    token  = params.get("token", "")

    if accion not in ("aprobar", "rechazar") or not token:
        return

    st.query_params.clear()

    try:
        res = supabase.table("solicitudes_registro") \
            .select("*").eq("token_aprobacion", token).execute()
    except Exception as e:
        st.error(f"❌ Error consultando la solicitud: {e}")
        return

    if not res.data:
        st.warning("⚠️ Token inválido o solicitud no encontrada.")
        return

    solicitud = res.data[0]

    if solicitud["estado"] != "pendiente":
        st.info(f"ℹ️ Esta solicitud ya fue procesada (estado: {solicitud['estado']}).")
        return

    nombre = solicitud["nombre_completo"]
    email  = solicitud["email"]

    _gmail_user = st.secrets.get("gmail", {}).get("email", "")
    _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")

    if accion == "aprobar":
        try:
            # Usar service_role para crear usuario con permisos de admin
            from supabase import create_client
            _service_key = st.secrets.get("supabase", {}).get("service_role_key", "")
            _url          = st.secrets.get("supabase", {}).get("url", "")
            supabase_admin = create_client(_url, _service_key)

            sign_res = supabase_admin.auth.admin.invite_user_by_email(
                email,
                options={"data": {"nombre_completo": nombre}}
            )

            if sign_res.user:
                try:
                    supabase.table("usuarios").upsert({
                        "usuario_id":      sign_res.user.id,
                        "nombre_completo": nombre,
                    }).execute()
                except:
                    pass

                supabase.table("solicitudes_registro") \
                    .update({"estado": "aprobado"}) \
                    .eq("token_aprobacion", token).execute()

                if _gmail_user and _gmail_pass:
                    try:
                        _notificar_usuario_aprobado(_gmail_user, _gmail_pass, nombre, email)
                    except Exception as e_mail:
                        st.error(f"❌ Error enviando correo al usuario: {e_mail}")

                st.success(f"✅ Cuenta de **{nombre}** ({email}) aprobada.")
                st.info("Se le envió un correo de invitación para que cree su contraseña e ingrese.")
            else:
                st.error("❌ No se pudo crear la cuenta en Supabase Auth.")
        except Exception as e:
            err = str(e).lower()
            if "already registered" in err or "already exists" in err:
                st.warning(f"⚠️ El correo {email} ya tiene una cuenta registrada.")
                supabase.table("solicitudes_registro") \
                    .update({"estado": "aprobado"}) \
                    .eq("token_aprobacion", token).execute()
            else:
                st.error(f"❌ Error al crear la cuenta: {e}")

    elif accion == "rechazar":
        try:
            supabase.table("solicitudes_registro") \
                .update({"estado": "rechazado"}) \
                .eq("token_aprobacion", token).execute()

            if _gmail_user and _gmail_pass:
                try:
                    _notificar_usuario_rechazado(_gmail_user, _gmail_pass, nombre, email)
                except:
                    pass

            st.info(f"🚫 Solicitud de **{nombre}** ({email}) rechazada. Se le notificó por correo.")
        except Exception as e:
            st.error(f"❌ Error al rechazar: {e}")


# ══════════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════

def mostrar_login(supabase, LOGO_LOGIN):

    _procesar_accion_url(supabase)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN):
            st.image(LOGO_LOGIN, use_container_width=True)

        tab_login, tab_registro, tab_recuperar = st.tabs(["🔑 Ingresar", "✨ Solicitar acceso", "🔓 Recuperar contraseña"])

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
                            st.error(f"❌ Error técnico: {e}")

        # ── SOLICITUD DE REGISTRO ──────────────────────────────
        with tab_registro:
            st.markdown("##### Solicita tu acceso a My FinanceApp")
            st.info("📋 El acceso a la app es por invitación. Completa el formulario y el administrador revisará tu solicitud.")

            nombre_completo = st.text_input("Nombre completo", key="reg_nombre", placeholder="Ej: Juan Pérez")
            email_reg       = st.text_input("Correo electrónico", key="reg_email", placeholder="tucorreo@ejemplo.com")

            with st.expander("📋 Términos y Condiciones de uso"):
                st.markdown("""
**My FinanceApp — Términos y Condiciones**

**1. Uso de la aplicación**
My FinanceApp es una herramienta de gestión financiera personal. El usuario es el único responsable de la veracidad y exactitud de los datos que registra.

**2. Privacidad y datos**
Los datos financieros registrados son de uso exclusivo del usuario. My FinanceApp no comparte, vende ni cede información personal a terceros. Los datos se almacenan de forma segura en servidores cifrados.

**3. Limitación de responsabilidad**
My FinanceApp es una herramienta de apoyo informativo. No constituye asesoría financiera, legal ni fiscal profesional. El desarrollador no se hace responsable de decisiones financieras tomadas con base en la información registrada en la app.

**4. Seguridad**
El usuario es responsable de mantener seguras sus credenciales de acceso. My FinanceApp no almacena contraseñas en texto plano.

**5. Módulo Grupal**
Al vincular su cuenta con otro usuario, el usuario acepta que cierta información financiera consolidada será visible para el usuario vinculado.

**6. Modificaciones**
My FinanceApp se reserva el derecho de modificar estos términos. Los cambios serán notificados por correo electrónico.

**7. Contacto**
Para dudas o solicitudes: arqtulicesar@gmail.com
                """)

            acepta_terminos = st.checkbox(
                "He leído y acepto los Términos y Condiciones de uso",
                key="check_terminos"
            )

            if st.button("📨 Enviar solicitud", use_container_width=True, key="btn_registro", disabled=not acepta_terminos):
                if not nombre_completo or not email_reg:
                    st.error("❌ Por favor completa todos los campos.")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", email_reg):
                    st.error("❌ El correo no tiene un formato válido.")
                else:
                    try:
                        existe = supabase.table("solicitudes_registro") \
                            .select("estado") \
                            .eq("email", email_reg.strip()) \
                            .in_("estado", ["pendiente", "aprobado"]) \
                            .execute()

                        if existe.data:
                            estado_actual = existe.data[0]["estado"]
                            if estado_actual == "pendiente":
                                st.warning("⏳ Ya tienes una solicitud pendiente de revisión. Te avisaremos cuando sea procesada.")
                            elif estado_actual == "aprobado":
                                st.info("✅ Tu correo ya fue aprobado. Si aún no tienes contraseña, usa la pestaña '🔓 Recuperar contraseña'.")
                        else:
                            ins = supabase.table("solicitudes_registro").insert({
                                "nombre_completo": nombre_completo.strip(),
                                "email":           email_reg.strip(),
                                "estado":          "pendiente"
                            }).execute()

                            token_gen = ins.data[0]["token_aprobacion"] if ins.data else None

                            _gmail_user = st.secrets.get("gmail", {}).get("email", "")
                            _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")

                            if _gmail_user and _gmail_pass and token_gen:
                                try:
                                    _notificar_admin_nuevo_registro(
                                        _gmail_user, _gmail_pass,
                                        nombre_completo.strip(), email_reg.strip(), token_gen
                                    )
                                except Exception as e_mail:
                                    st.error(f"❌ Error enviando correo al admin: {e_mail}")
                                try:
                                    _notificar_usuario_pendiente(
                                        _gmail_user, _gmail_pass,
                                        nombre_completo.strip(), email_reg.strip()
                                    )
                                except Exception as e_mail2:
                                    st.error(f"❌ Error enviando correo al usuario: {e_mail2}")

                            st.success("✅ ¡Solicitud enviada! Recibirás un correo cuando el administrador la revise.")

                    except Exception as e:
                        st.error(f"❌ Error al enviar la solicitud: {e}")

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
                            options={"redirect_to": "https://tulicesar.github.io/stulio-finance-pro/redirect.html"}
                        )
                        st.success(f"✅ Enlace enviado a **{email_rec}**")
                        st.info("Revisa tu bandeja de entrada y sigue el enlace. Si no lo ves, revisa la carpeta de spam.")
                    except Exception as e:
                        err = str(e).lower()
                        if "user not found" in err or "not found" in err:
                            st.success("✅ Si ese correo está registrado, recibirás el enlace en unos minutos.")
                        else:
                            st.error(f"❌ Error: {e}")


# ══════════════════════════════════════════════════════════════

def cerrar_sesion():
    for key in ["autenticado", "token", "usuario_id", "u_nombre_completo"]:
        st.session_state[key] = False if key == "autenticado" else (None if key != "u_nombre_completo" else "")
    st.rerun()


def mostrar_eliminar_cuenta(supabase, token, u_id, email_usuario):
    """Solicitud de eliminación de cuenta — notifica al administrador por correo."""
    st.markdown(
        '<p style="color:#adb5bd;font-size:0.78rem;margin-bottom:10px">'
        'Opciones avanzadas de tu cuenta</p>',
        unsafe_allow_html=True
    )

    if not st.session_state.get("solicitud_eliminar_paso2"):
        if st.button("🗑️ Solicitar eliminar cuenta", key="btn_solicitar_eliminar_cuenta"):
            st.session_state["solicitud_eliminar_paso2"] = True
            st.rerun()
    else:
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

        if st.button("✅ Confirmar solicitud", key="btn_confirmar_solicitud", disabled=not confirmar, use_container_width=True):
            try:
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

                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart

                _gmail_user = st.secrets.get("gmail", {}).get("email", "")
                _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")

                if _gmail_user and _gmail_pass:
                    _msg = MIMEMultipart("alternative")
                    _msg["Subject"] = f"🗑️ Solicitud de eliminación de cuenta — {nombre_usuario}"
                    _msg["From"]    = _gmail_user
                    _msg["To"]      = _gmail_user

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

        if st.button("✗ Cancelar solicitud", key="btn_cancelar_solicitud", use_container_width=True):
            st.session_state["solicitud_eliminar_paso2"] = False
            st.rerun()

    if st.session_state.get("solicitud_eliminar_enviada"):
        st.success("✅ Solicitud enviada correctamente.")
        st.info("El administrador procesará tu solicitud en las próximas 24-48 horas.")
        if st.button("Cerrar", key="btn_cerrar_solicitud"):
            st.session_state["solicitud_eliminar_enviada"] = False
            st.rerun()
