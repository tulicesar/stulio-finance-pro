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
                                    }).execute()
                                except:
                                    pass

                                # ── Correo tutorial detallado ─────────────
                                try:
                                    import smtplib
                                    from email.mime.text import MIMEText
                                    from email.mime.multipart import MIMEMultipart
                                    _gmail_user = st.secrets.get("gmail", {}).get("email", "")
                                    _gmail_pass = st.secrets.get("gmail", {}).get("app_password", "")
                                    if _gmail_user and _gmail_pass:
                                        _msg = MIMEMultipart("alternative")
                                        _msg["Subject"] = f"📚 Tu guía completa de My FinanceApp, {nombre_completo.split()[0]}"
                                        _msg["From"]    = _gmail_user
                                        _msg["To"]      = email_reg.strip()
                                        _html_tutorial = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1e23;font-family:Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:30px 20px">

  <div style="text-align:center;margin-bottom:24px">
    <h1 style="color:#fca311;font-size:1.8rem;margin:0">My FinanceApp</h1>
    <p style="color:#adb5bd;font-size:0.85rem;margin:4px 0">by Stulio Designs</p>
  </div>

  <div style="background:#2d3238;border-radius:12px;padding:24px;margin-bottom:20px;border-left:4px solid #fca311">
    <h2 style="color:#fff;margin:0 0 8px">📚 Tu guía paso a paso</h2>
    <p style="color:#adb5bd;margin:0;font-size:0.85rem;line-height:1.6">
      Hola <b style="color:#fff">{nombre_completo.split()[0]}</b>, aquí tienes todo lo que necesitas saber para sacarle el máximo provecho a My FinanceApp.
    </p>
  </div>

  <!-- Pasos -->
  <div style="background:#2d3238;border-radius:12px;padding:24px;margin-bottom:16px">

    <div style="margin-bottom:16px;padding:14px;background:#3a3f44;border-radius:8px;border-left:3px solid #fca311">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:6px">1️⃣ Configura tu mes</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.6">
        En el <b>panel izquierdo</b> selecciona el año y mes. Luego ingresa tu <b>Saldo Anterior</b> (lo que tenías del mes pasado) y tu <b>Nómina</b>. Si tienes otros ingresos, agrégalos en la sección de Ingresos Adicionales. Presiona <b>💾 Guardar</b>.
      </div>
    </div>

    <div style="margin-bottom:16px;padding:14px;background:#3a3f44;border-radius:8px;border-left:3px solid #fca311">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:6px">2️⃣ Define tus Gastos Proyectados</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.6">
        En la tabla <b>"Gastos / Egresos Proyectados"</b> registra todos los gastos que planeas tener: servicios, arriendos, seguros, etc. con su valor estimado.<br><br>
        • Activa <b>📌 Referencia</b> en los ítems que quieres hacer seguimiento de ejecución.<br>
        • Activa <b>🔁 Recurrente</b> en los que se repiten cada mes — aparecerán automáticamente el próximo mes.<br>
        • Usa <b>📋 Copiar al registrar</b> para que el valor proyectado se copie automáticamente al registrar el movimiento.
      </div>
    </div>

    <div style="margin-bottom:16px;padding:14px;background:#3a3f44;border-radius:8px;border-left:3px solid #fca311">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:6px">3️⃣ Registra tus movimientos diarios</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.6">
        En <b>"Editar / Agregar Movimientos"</b> registra cada gasto del día a día con su monto real.<br><br>
        • Asocia cada gasto a un <b>Ítem Proyectado</b> para hacer seguimiento del presupuesto.<br>
        • Marca <b>✅ Pagado</b> cuando hayas cancelado la obligación.<br>
        • Agrega la <b>Fecha</b> para llevar un historial detallado.
      </div>
    </div>

    <div style="margin-bottom:16px;padding:14px;background:#3a3f44;border-radius:8px;border-left:3px solid #fca311">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:6px">4️⃣ Analiza tus métricas</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.6">
        El dashboard muestra automáticamente:<br>
        • <b>Obligaciones Pagadas</b> — lo que ya cancelaste<br>
        • <b>Obligaciones Pendientes</b> — lo que aún debes con saldo disponible<br>
        • <b>Dinero Disponible</b> — ingresos menos pagado<br>
        • <b>Saldo a Favor</b> — lo que te queda después de cubrir todo<br>
        • Gráficas de distribución por categoría y seguimiento de proyectados
      </div>
    </div>

    <div style="margin-bottom:16px;padding:14px;background:#3a3f44;border-radius:8px;border-left:3px solid #fca311">
      <div style="color:#fca311;font-weight:800;font-size:0.85rem;margin-bottom:6px">5️⃣ Descarga tus extractos</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.6">
        Desde el sidebar descarga tu resumen en <b>📄 PDF</b> o <b>📊 Excel</b>. También puedes generar <b>proyecciones semestrales</b> para planear con anticipación.
      </div>
    </div>

    <div style="padding:14px;background:#3a3f44;border-radius:8px;border-left:3px solid #2ecc71">
      <div style="color:#2ecc71;font-weight:800;font-size:0.85rem;margin-bottom:6px">💡 Funciones avanzadas</div>
      <div style="color:#dee2e6;font-size:0.82rem;line-height:1.6">
        • <b>🤖 Asesor IA</b> — obtén un diagnóstico financiero personalizado al final del dashboard.<br>
        • <b>👥 Finanzas Grupales</b> — vincula tu cuenta con otra persona (pareja, socio, familiar) para ver un dashboard consolidado con extractos compartidos.
      </div>
    </div>
  </div>

  <div style="text-align:center;margin-bottom:24px">
    <a href="https://stulio-finance-pro-7xa6pgb2ttmkdper9lwqqo.streamlit.app"
       style="background:#fca311;color:#14213d;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:800;font-size:1rem;display:inline-block">
      🚀 Ir a My FinanceApp
    </a>
  </div>

  <div style="text-align:center;border-top:1px solid #3a3f44;padding-top:16px">
    <p style="color:#6c757d;font-size:0.75rem;margin:0">
      My FinanceApp · by Stulio Designs<br>
      ¿Tienes dudas? Escríbenos a arqtulicesar@gmail.com
    </p>
  </div>

</div>
</body>
</html>"""
                                        _msg.attach(MIMEText(_html_tutorial, "html"))
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
