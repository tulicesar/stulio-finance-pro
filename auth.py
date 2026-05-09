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

            if st.button("Crear cuenta", use_container_width=True, key="btn_registro", disabled=not acepta_terminos):
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

                                # ── Correo de bienvenida ───────────────────
                                try:
                                    import smtplib
                                    from email.mime.text import MIMEText
                                    from email.mime.multipart import MIMEMultipart
                                    _gmail_user = st.secrets.get("gmail", {}).get("email", "")
                                    _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")
                                    if _gmail_user and _gmail_pass:
                                        _msg = MIMEMultipart("alternative")
                                        _msg["Subject"] = f"🎉 ¡Bienvenido a My FinanceApp, {nombre_completo.split()[0]}!"
                                        _msg["From"]    = _gmail_user
                                        _msg["To"]      = email_reg.strip()
                                        _html_bienvenida = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1e23;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:30px 20px">

  <!-- Header -->
  <div style="text-align:center;margin-bottom:30px">
    <h1 style="color:#fca311;font-size:1.8rem;margin:0">My FinanceApp</h1>
    <p style="color:#adb5bd;font-size:0.85rem;margin:4px 0">by Stulio Designs</p>
  </div>

  <!-- Saludo -->
  <div style="background:#2d3238;border-radius:12px;padding:24px;margin-bottom:20px;border-left:4px solid #fca311">
    <h2 style="color:#fff;margin:0 0 10px">¡Hola, {nombre_completo.split()[0]}! 👋</h2>
    <p style="color:#adb5bd;margin:0;line-height:1.6">
      Tu cuenta ha sido creada exitosamente. Estamos emocionados de acompañarte en el control de tus finanzas personales.
      <br><br>Primero debes confirmar tu correo haciendo clic en el enlace que Supabase te envió por separado.
    </p>
  </div>

  <!-- Tutorial -->
  <div style="background:#2d3238;border-radius:12px;padding:24px;margin-bottom:20px">
    <h3 style="color:#fca311;margin:0 0 16px">🚀 Cómo empezar — Guía rápida</h3>

    <div style="margin-bottom:16px;padding:12px;background:#3a3f44;border-radius:8px">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:4px">PASO 1 — Configura tu mes</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.5">
        En el panel izquierdo selecciona el <b>año y mes</b> que quieres gestionar. Ingresa tu <b>saldo anterior</b> y tu <b>nómina</b> del mes.
      </div>
    </div>

    <div style="margin-bottom:16px;padding:12px;background:#3a3f44;border-radius:8px">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:4px">PASO 2 — Define tus gastos proyectados</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.5">
        En la tabla <b>"Gastos / Egresos Proyectados"</b> registra los gastos que planeas tener este mes (servicios, arriendo, etc.) con su valor estimado. Activa el check <b>📌 Referencia</b> en los ítems que quieres hacer seguimiento.
      </div>
    </div>

    <div style="margin-bottom:16px;padding:12px;background:#3a3f44;border-radius:8px">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:4px">PASO 3 — Registra tus movimientos diarios</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.5">
        En <b>"Editar / Agregar Movimientos"</b> registra cada gasto del día a día. Puedes asociarlo a un ítem proyectado para hacer seguimiento del presupuesto. Marca el check <b>✅ Pagado</b> cuando lo hayas cancelado.
      </div>
    </div>

    <div style="margin-bottom:16px;padding:12px;background:#3a3f44;border-radius:8px">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:4px">PASO 4 — Revisa tus métricas</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.5">
        El dashboard muestra automáticamente tus <b>KPIs financieros</b>: ingresos, obligaciones pagadas, pendientes, dinero disponible y saldo a favor. También verás gráficas de distribución por categoría.
      </div>
    </div>

    <div style="margin-bottom:16px;padding:12px;background:#3a3f44;border-radius:8px">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:4px">PASO 5 — Genera extractos</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.5">
        Descarga tu resumen mensual en <b>PDF o Excel</b> desde el sidebar. También puedes generar proyecciones semestrales.
      </div>
    </div>

    <div style="padding:12px;background:#3a3f44;border-radius:8px">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:4px">💡 EXTRA — Asesor IA y Finanzas Grupales</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.5">
        Usa el <b>🤖 Asesor IA</b> para obtener un diagnóstico personalizado de tu situación financiera. Y con <b>👥 Finanzas Grupales</b> puedes vincular tu cuenta con otra persona para ver un dashboard consolidado.
      </div>
    </div>
  </div>

  <!-- CTA -->
  <div style="text-align:center;margin-bottom:24px">
    <a href="https://stulio-finance-pro-7xa6pgb2ttmkdper9lwqqo.streamlit.app"
       style="background:#fca311;color:#14213d;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:800;font-size:1rem;display:inline-block">
      🚀 Ir a My FinanceApp
    </a>
  </div>

  <!-- Footer -->
  <div style="text-align:center;border-top:1px solid #3a3f44;padding-top:16px">
    <p style="color:#6c757d;font-size:0.75rem;margin:0">
      My FinanceApp · by Stulio Designs<br>
      Si tienes dudas escríbenos a arqtulicesar@gmail.com
    </p>
  </div>

</div>
</body>
</html>
                                        """
                                        _msg.attach(MIMEText(_html_bienvenida, "html"))
                                        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as _smtp:
                                            _smtp.login(_gmail_user, _gmail_pass)
                                            _smtp.sendmail(_gmail_user, email_reg.strip(), _msg.as_string())
                                except:
                                    pass  # Si falla el correo, no bloquear el registro

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
                            options={"redirect_to": "https://tulicesar.github.io/stulio-finance-pro/redirect.html"}
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

        if st.button("✅ Confirmar solicitud", key="btn_confirmar_solicitud", disabled=not confirmar, use_container_width=True):
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

    # ── CONFIRMACIÓN FINAL ────────────────────────────────
    if st.session_state.get("solicitud_eliminar_enviada"):
        st.success("✅ Solicitud enviada correctamente.")
        st.info("El administrador procesará tu solicitud en las próximas 24-48 horas. Puedes seguir usando la app hasta entonces.")
        if st.button("Cerrar", key="btn_cerrar_solicitud"):
            st.session_state["solicitud_eliminar_enviada"] = False
            st.rerun()
