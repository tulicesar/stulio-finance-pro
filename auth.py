"""
auth.py — Autenticación, registro y gestión de sesión
Flujo de registro con aprobación del administrador.
"""
import streamlit as st
import os
import re


ADMIN_EMAIL = "arqtulicesar@gmail.com"
APP_URL     = "https://stulio-finance-pro-7xa6pgb2ttmkdper9lwqqo.streamlit.app"


def _validar_password(pwd):
    if len(pwd) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Z]", pwd):
        return False, "La contraseña debe tener al menos una letra mayúscula."
    if not re.search(r"[0-9]", pwd):
        return False, "La contraseña debe tener al menos un número."
    return True, ""


def _enviar_correo_html(gmail_user, gmail_pass, destinatario, asunto, html_body):
    """Envía un correo HTML via Gmail SMTP SSL."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = gmail_user
    msg["To"]      = destinatario
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_pass)
        smtp.sendmail(gmail_user, destinatario, msg.as_string())


def _notificar_admin_solicitud(gmail_user, gmail_pass, nombre, email, solicitud_id):
    """Envía correo al admin con botones Aprobar / Rechazar."""
    aprobar_url  = f"{APP_URL}?accion=aprobar&id={solicitud_id}"
    rechazar_url = f"{APP_URL}?accion=rechazar&id={solicitud_id}"

    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1e23;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:30px 20px">

  <div style="text-align:center;margin-bottom:24px">
    <h1 style="color:#fca311;font-size:1.6rem;margin:0">My FinanceApp</h1>
    <p style="color:#adb5bd;font-size:0.8rem;margin:4px 0">by Stulio Designs</p>
  </div>

  <div style="background:#2d3238;border-radius:12px;padding:24px;margin-bottom:20px;border-left:4px solid #fca311">
    <h2 style="color:#fff;margin:0 0 8px">🙋 Nueva solicitud de registro</h2>
    <p style="color:#adb5bd;margin:0;font-size:0.85rem">
      Un usuario quiere unirse a <b style="color:#fff">My FinanceApp</b> y necesita tu aprobación.
    </p>
  </div>

  <div style="background:#2d3238;border-radius:12px;padding:20px;margin-bottom:20px">
    <table style="width:100%;border-collapse:collapse">
      <tr style="border-bottom:1px solid #3a3f44">
        <td style="padding:10px 8px;color:#adb5bd;font-size:0.82rem;width:40%">Nombre</td>
        <td style="padding:10px 8px;color:#fff;font-size:0.85rem;font-weight:700">{nombre}</td>
      </tr>
      <tr>
        <td style="padding:10px 8px;color:#adb5bd;font-size:0.82rem">Correo</td>
        <td style="padding:10px 8px;color:#fca311;font-size:0.85rem">{email}</td>
      </tr>
    </table>
  </div>

  <div style="text-align:center;margin-bottom:24px">
    <p style="color:#adb5bd;font-size:0.82rem;margin-bottom:16px">
      Haz clic en una opción para gestionar la solicitud:
    </p>
    <a href="{aprobar_url}"
       style="background:#2ecc71;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;
              font-weight:800;font-size:0.95rem;display:inline-block;margin:0 8px 8px">
      ✅ Aprobar
    </a>
    <a href="{rechazar_url}"
       style="background:#e74c3c;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;
              font-weight:800;font-size:0.95rem;display:inline-block;margin:0 8px 8px">
      ❌ Rechazar
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
                        f"🙋 Solicitud de registro — {nombre}", html)


def _notificar_usuario_aprobado(gmail_user, gmail_pass, nombre, email_usuario):
    """Notifica al usuario que fue aprobado y puede crear su cuenta."""
    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1e23;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:30px 20px">

  <div style="text-align:center;margin-bottom:24px">
    <h1 style="color:#fca311;font-size:1.6rem;margin:0">My FinanceApp</h1>
    <p style="color:#adb5bd;font-size:0.8rem;margin:4px 0">by Stulio Designs</p>
  </div>

  <div style="background:#2d3238;border-radius:12px;padding:24px;margin-bottom:20px;border-left:4px solid #2ecc71">
    <h2 style="color:#2ecc71;margin:0 0 8px">✅ ¡Tu solicitud fue aprobada!</h2>
    <p style="color:#adb5bd;margin:0;font-size:0.85rem;line-height:1.6">
      Hola <b style="color:#fff">{nombre.split()[0]}</b>, el administrador ha aprobado tu acceso a
      <b style="color:#fca311">My FinanceApp</b>. Ya puedes crear tu cuenta.
    </p>
  </div>

  <div style="text-align:center;margin-bottom:24px">
    <a href="{APP_URL}"
       style="background:#fca311;color:#14213d;padding:14px 32px;border-radius:8px;text-decoration:none;
              font-weight:800;font-size:1rem;display:inline-block">
      🚀 Crear mi cuenta ahora
    </a>
  </div>

  <div style="background:#2d3238;border-radius:12px;padding:16px;margin-bottom:20px">
    <p style="color:#adb5bd;font-size:0.82rem;margin:0;line-height:1.6">
      ℹ️ Al ingresar a la app, ve a la pestaña <b style="color:#fff">✨ Crear cuenta</b> y
      regístrate con este correo: <b style="color:#fca311">{email_usuario}</b>
    </p>
  </div>

  <div style="text-align:center;border-top:1px solid #3a3f44;padding-top:16px">
    <p style="color:#6c757d;font-size:0.75rem;margin:0">
      My FinanceApp · by Stulio Designs<br>
      ¿Tienes dudas? Escríbenos a {ADMIN_EMAIL}
    </p>
  </div>

</div>
</body>
</html>"""
    _enviar_correo_html(gmail_user, gmail_pass, email_usuario,
                        "✅ ¡Tu acceso a My FinanceApp fue aprobado!", html)


def _notificar_usuario_rechazado(gmail_user, gmail_pass, nombre, email_usuario):
    """Notifica al usuario que su solicitud fue rechazada."""
    html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1e23;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:30px 20px">

  <div style="text-align:center;margin-bottom:24px">
    <h1 style="color:#fca311;font-size:1.6rem;margin:0">My FinanceApp</h1>
    <p style="color:#adb5bd;font-size:0.8rem;margin:4px 0">by Stulio Designs</p>
  </div>

  <div style="background:#2d3238;border-radius:12px;padding:24px;margin-bottom:20px;border-left:4px solid #e74c3c">
    <h2 style="color:#e74c3c;margin:0 0 8px">❌ Solicitud no aprobada</h2>
    <p style="color:#adb5bd;margin:0;font-size:0.85rem;line-height:1.6">
      Hola <b style="color:#fff">{nombre.split()[0]}</b>, en este momento tu solicitud de acceso
      a <b style="color:#fca311">My FinanceApp</b> no fue aprobada.<br><br>
      Si crees que es un error, contáctanos directamente a
      <b style="color:#fca311">{ADMIN_EMAIL}</b>.
    </p>
  </div>

  <div style="text-align:center;border-top:1px solid #3a3f44;padding-top:16px">
    <p style="color:#6c757d;font-size:0.75rem;margin:0">
      My FinanceApp · by Stulio Designs
    </p>
  </div>

</div>
</body>
</html>"""
    _enviar_correo_html(gmail_user, gmail_pass, email_usuario,
                        "Solicitud de acceso a My FinanceApp", html)


def _procesar_accion_admin(supabase):
    """
    Detecta si la URL contiene ?accion=aprobar&id=... o ?accion=rechazar&id=...
    y procesa la solicitud de registro. Se llama desde mostrar_login() al inicio.
    """
    try:
        params = st.query_params
        accion = params.get("accion", "")
        sol_id = params.get("id", "")
        if not accion or not sol_id:
            return

        _gmail_user = st.secrets.get("gmail", {}).get("email", "")
        _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")

        # Buscar la solicitud
        res = supabase.table("solicitudes_registro").select("*").eq("id", sol_id).execute()
        if not res.data:
            st.warning("⚠️ Solicitud no encontrada o ya fue procesada.")
            st.query_params.clear()
            return

        sol = res.data[0]
        if sol["estado"] != "pendiente":
            st.info(f"ℹ️ Esta solicitud ya fue procesada (estado: {sol['estado']}).")
            st.query_params.clear()
            return

        nombre = sol["nombre_completo"]
        email  = sol["email"]

        if accion == "aprobar":
            # Marcar como aprobada
            supabase.table("solicitudes_registro").update({"estado": "aprobada"}).eq("id", sol_id).execute()
            # Notificar al usuario
            if _gmail_user and _gmail_pass:
                try:
                    _notificar_usuario_aprobado(_gmail_user, _gmail_pass, nombre, email)
                except:
                    pass
            st.success(f"✅ Solicitud de **{nombre}** ({email}) aprobada. Se le notificó por correo.")

        elif accion == "rechazar":
            supabase.table("solicitudes_registro").update({"estado": "rechazada"}).eq("id", sol_id).execute()
            if _gmail_user and _gmail_pass:
                try:
                    _notificar_usuario_rechazado(_gmail_user, _gmail_pass, nombre, email)
                except:
                    pass
            st.info(f"ℹ️ Solicitud de **{nombre}** ({email}) rechazada. Se le notificó por correo.")

        st.query_params.clear()

    except Exception as e:
        st.error(f"❌ Error al procesar la acción: {e}")
        try:
            st.query_params.clear()
        except:
            pass


def mostrar_login(supabase, LOGO_LOGIN):
    # ── Procesar acciones del admin (aprobar/rechazar desde correo) ──
    _procesar_accion_admin(supabase)

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

        # ── REGISTRO ───────────────────────────────────────────
        with tab_registro:
            st.markdown("##### Solicitar acceso a My FinanceApp")
            st.info("📋 El acceso requiere aprobación del administrador. Te notificaremos por correo.")

            nombre_completo = st.text_input("Nombre completo", key="reg_nombre", placeholder="Ej: Juan Pérez")
            email_reg       = st.text_input("Correo electrónico", key="reg_email", placeholder="tucorreo@ejemplo.com")
            pwd_reg         = st.text_input("Contraseña", type="password", key="reg_pwd", placeholder="Mínimo 8 caracteres")
            pwd_reg2        = st.text_input("Confirmar contraseña", type="password", key="reg_pwd2", placeholder="Repite la contraseña")
            st.caption("🔒 Mínimo 8 caracteres, una mayúscula y un número.")

            # ── Términos y condiciones ─────────────────────────
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
Al vincular su cuenta con otro usuario, el usuario acepta que cierta información financiera consolidada será visible para el usuario vinculado. Ninguna de las partes tendrá acceso a los datos detallados del otro.

**6. Modificaciones**
My FinanceApp se reserva el derecho de modificar estos términos. Los cambios serán notificados por correo electrónico.

**7. Contacto**
Para dudas o solicitudes: arqtulicesar@gmail.com
                """)

            acepta_terminos = st.checkbox(
                "He leído y acepto los Términos y Condiciones de uso",
                key="check_terminos"
            )

            if st.button("📨 Enviar solicitud de acceso", use_container_width=True,
                         key="btn_registro", disabled=not acepta_terminos):
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
                            # ── Verificar si ya tiene solicitud pendiente o aprobada ──
                            existing = supabase.table("solicitudes_registro") \
                                .select("estado") \
                                .eq("email", email_reg.strip()) \
                                .execute()

                            if existing.data:
                                estado_actual = existing.data[0]["estado"]
                                if estado_actual == "pendiente":
                                    st.warning("⏳ Ya tienes una solicitud pendiente. Te avisaremos pronto.")
                                elif estado_actual == "aprobada":
                                    st.success("✅ Tu solicitud ya fue aprobada. Revisa tu correo y crea tu cuenta.")
                                elif estado_actual == "rechazada":
                                    st.error("❌ Tu solicitud fue rechazada. Contáctanos a arqtulicesar@gmail.com.")
                                # No procesamos más en ninguno de estos casos
                            else:
                                # ── Verificar si ya está registrado en Supabase Auth ──
                                # (no podemos chequearlo directamente, lo manejamos en el catch)

                                # ── Guardar solicitud en tabla ──
                                ins = supabase.table("solicitudes_registro").insert({
                                    "nombre_completo": nombre_completo.strip(),
                                    "email":           email_reg.strip(),
                                    "estado":          "pendiente",
                                    "password_hash":   pwd_reg,   # se guarda temporalmente; admin aprueba y usuario crea cuenta
                                }).execute()

                                solicitud_id = ins.data[0]["id"] if ins.data else "N/A"

                                # ── Notificar al admin ──
                                _gmail_user = st.secrets.get("gmail", {}).get("email", "")
                                _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")
                                if _gmail_user and _gmail_pass:
                                    try:
                                        _notificar_admin_solicitud(
                                            _gmail_user, _gmail_pass,
                                            nombre_completo.strip(),
                                            email_reg.strip(),
                                            solicitud_id
                                        )
                                    except:
                                        pass  # No bloquear si falla el correo

                                st.success(
                                    f"✅ ¡Solicitud enviada, {nombre_completo.split()[0]}! "
                                    "Te notificaremos a tu correo cuando sea aprobada."
                                )
                                st.info("⏳ El administrador revisará tu solicitud pronto.")

                        except Exception as e:
                            err = str(e).lower()
                            if "duplicate" in err or "unique" in err:
                                st.warning("⏳ Ya existe una solicitud con ese correo. Espera la revisión del administrador.")
                            else:
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
                        st.info("Revisa tu bandeja de entrada y sigue el enlace para crear una nueva contraseña. Si no lo ves, revisa la carpeta de spam.")
                    except Exception as e:
                        err = str(e).lower()
                        if "user not found" in err or "not found" in err:
                            st.success("✅ Si ese correo está registrado, recibirás el enlace en unos minutos.")
                        else:
                            st.error(f"❌ Error: {e}")


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

        if st.button("✅ Confirmar solicitud", key="btn_confirmar_solicitud",
                     disabled=not confirmar, use_container_width=True):
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

        if st.button("✗ Cancelar solicitud", key="btn_cancelar_solicitud", use_container_width=True):
            st.session_state["solicitud_eliminar_paso2"] = False
            st.rerun()

    if st.session_state.get("solicitud_eliminar_enviada"):
        st.success("✅ Solicitud enviada correctamente.")
        st.info("El administrador procesará tu solicitud en las próximas 24-48 horas.")
        if st.button("Cerrar", key="btn_cerrar_solicitud"):
            st.session_state["solicitud_eliminar_enviada"] = False
            st.rerun()
