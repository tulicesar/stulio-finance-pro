import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from supabase import create_client, Client
import io

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Stulio Finance Pro", page_icon="💰", layout="wide")

# Configuración de Supabase
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Error conectando a Supabase. Revisa los Secrets. Detalles: {e}")
    st.stop()

# Constantes
USER_DB = "usuarios.json"
LOGO_LOGIN = "logo_login.png" 
LOGO_SIDEBAR = "logo_sidebar.png"
LOGO_APP_H = "logo_app.png"
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
LISTA_CATEGORIAS = ["Vivienda", "Transporte", "Alimentación", "Salud", "Educación", "Entretenimiento", "Ropa", "Ahorro", "Deudas", "Otros"]

# Estilos CSS
st.markdown("""
    <style>
    .card { border-radius: 10px; padding: 15px; background-color: #f9f9f9; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; }
    .card-label { font-size: 14px; font-weight: bold; color: #555; }
    .card-value { font-size: 20px; font-weight: bold; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)


# --- 2. FUNCIONES AUXILIARES ---
def cargar_usuarios():
    if not os.path.exists(USER_DB):
        return {}
    with open(USER_DB, "r") as f:
        return json.load(f)

def format_moneda(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except ValueError:
        return "0"

def parse_moneda(texto):
    try:
        return float(str(texto).replace(".", "").replace(",", "").replace("$", "").strip())
    except ValueError:
        return 0.0

@st.cache_data(ttl=10) # Caché de 10 segundos para no saturar la base de datos
def cargar_bd(u_id):
    # Descargamos solo la info del usuario logueado
    r_g = supabase.table("gastos").select("*").eq("usuario_id", u_id).execute()
    r_i = supabase.table("ingresos_base").select("*").eq("usuario_id", u_id).execute()
    r_oi = supabase.table("otros_ingresos").select("*").eq("usuario_id", u_id).execute()
    
    df_g = pd.DataFrame(r_g.data) if r_g.data else pd.DataFrame(columns=["categoria", "descripcion", "monto", "valor_referencia", "pagado", "recurrente", "periodo", "anio", "usuario_id"])
    df_i = pd.DataFrame(r_i.data) if r_i.data else pd.DataFrame(columns=["anio", "periodo", "saldo_anterior", "nomina", "otros", "usuario_id"])
    df_oi = pd.DataFrame(r_oi.data) if r_oi.data else pd.DataFrame(columns=["descripcion", "monto", "periodo", "anio", "usuario_id"])
    
    # Capitalizamos columnas para la UI
    df_g = df_g.rename(columns={"categoria":"Categoria", "descripcion":"Descripcion", "monto":"Monto", "valor_referencia":"Referencia", "pagado":"Pagado", "recurrente":"Recurrente", "periodo":"Periodo", "anio":"Anio", "usuario_id":"Usuario"})
    df_i = df_i.rename(columns={"anio":"Anio", "periodo":"Periodo", "saldo_anterior":"SaldoAnterior", "nomina":"Nomina", "otros":"Otros", "usuario_id":"Usuario"})
    df_oi = df_oi.rename(columns={"descripcion":"Descripcion", "monto":"Monto", "periodo":"Periodo", "anio":"Anio", "usuario_id":"Usuario"})
    
    return df_g, df_i, df_oi


# --- 3. ACCESO (LOGIN/REGISTRO) ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists(LOGO_LOGIN): st.image(LOGO_LOGIN, use_container_width=True)
        
        t_in, t_reg = st.tabs(["🔑 Login", "📝 Registro"])
        db_u = cargar_usuarios()
        
        with t_in:
            u = st.text_input("Usuario", key="login_u")
            p = st.text_input("Pass", type="password", key="login_p")
            if st.button("Ingresar", use_container_width=True):
                if u in db_u:
                    u_data = db_u[u]
                    if isinstance(u_data, dict):
                        pw_ok = (u_data.get("pass") == p)
                        nom = u_data.get("nombre", u)
                    else:
                        pw_ok = (u_data == p)
                        nom = u
                    
                    if pw_ok:
                        st.session_state.autenticado = True
                        st.session_state.usuario_id = u
                        st.session_state.u_nombre_completo = nom
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta")
                else:
                    st.error("❌ Usuario no encontrado")
        
        with t_reg:
            st.markdown("### Crear o Actualizar cuenta")
            rn = st.text_input("Nombre Completo", key="reg_n")
            ru = st.text_input("ID Usuario", key="reg_u")
            rp = st.text_input("Pass", type="password", key="reg_p")
            if st.button("Procesar Registro"):
                if not ru or not rp:
                    st.warning("⚠️ Completa usuario y contraseña")
                else:
                    if ru in db_u and isinstance(db_u[ru], dict) and db_u[ru].get("pass") != rp:
                        st.error("❌ El usuario existe y la contraseña no coincide")
                    else:
                        db_u[ru] = {"pass": rp, "nombre": rn}
                        with open(USER_DB, "w") as f:
                            json.dump(db_u, f, indent=4)
                        st.success(f"✅ ¡Hecho! Datos guardados. Ve al Login.")
    st.stop()


# --- 4. LÓGICA DASHBOARD ---
u_id = st.session_state.usuario_id
df_g_full, df_i_full, df_oi_full = cargar_bd(u_id)

with st.sidebar:
    if os.path.exists(LOGO_SIDEBAR): st.image(LOGO_SIDEBAR, use_container_width=True)
    st.markdown(f"### 👤 {st.session_state.u_nombre_completo}")
    
    # 5 y 6. Cambio a 'Año' y actualización de lista de años
    anio_s = st.selectbox("Año", [2026, 2027, 2028], index=0)
    mes_s = st.selectbox("Mes Actual", MESES, index=datetime.now().month-1)
    
    # Filtro del mes
    i_m_act = df_i_full[(df_i_full["Periodo"]==mes_s) & (df_i_full["Anio"]==anio_s)]
    val_s_init = i_m_act["SaldoAnterior"].iloc[0] if not i_m_act.empty else 0.0
    val_n_init = i_m_act["Nomina"].iloc[0] if not i_m_act.empty else 0.0
    
    st.markdown("---")
    # 2. Restauración campos de ingreso fijos
    s_in = parse_moneda(st.text_input("Saldo Anterior", value=format_moneda(val_s_init)))
    n_in = parse_moneda(st.text_input("Ingreso Fijo", value=format_moneda(val_n_init)))
    
    # 4. Caja para el total de ingresos adicionales
    caja_sumatoria_oi = st.empty()
    
    st.markdown("---")
    if st.button("Salir"): st.session_state.autenticado = False; st.rerun()

if os.path.exists(LOGO_APP_H): st.image(LOGO_APP_H, use_container_width=True)


# --- 5. CUERPO PRINCIPAL ---
# 9. Infografía Financiera
st.markdown("---")
st.markdown("### 📊 Infografía Financiera y Resumen")
col_info1, col_info2, col_info3 = st.columns(3)
col_info1.metric("Fondo Fijo (Nómina + Saldo)", f"$ {format_moneda(n_in + s_in)}")
caja_infografia_gastos = col_info2.empty()
caja_infografia_disp = col_info3.empty()
st.markdown("---")

st.markdown(f"## Gestión de {mes_s} {anio_s}")

st.markdown("#### 📝 Registro de Gastos")
df_g_mes = df_g_full[(df_g_full["Periodo"] == mes_s) & (df_g_full["Anio"] == anio_s)]

# 1. Editor de gastos con checkboxes en False por defecto
df_ed_g = st.data_editor(
    df_g_mes.reindex(columns=["Categoria", "Descripcion", "Monto", "Referencia", "Pagado", "Recurrente"]).reset_index(drop=True), 
    use_container_width=True, 
    num_rows="dynamic", 
    column_config={
        "Categoria": st.column_config.SelectboxColumn("Categoria", options=LISTA_CATEGORIAS),
        "Pagado": st.column_config.CheckboxColumn("Pagado", default=False),
        "Recurrente": st.column_config.CheckboxColumn("Recurrente", default=False)
    }
)

# 3. Restauración de título de variables
st.markdown("#### 💸 Ingresos Adicionales (Variables)")
df_oi_mes = df_oi_full[(df_oi_full["Periodo"] == mes_s) & (df_oi_full["Anio"] == anio_s)]

df_ed_oi = st.data_editor(
    df_oi_mes.reindex(columns=["Descripcion", "Monto"]).reset_index(drop=True), 
    use_container_width=True, 
    num_rows="dynamic"
)

# Cálculos Matemáticos
otr_v = float(df_ed_oi["Monto"].sum()) if not df_ed_oi.empty else 0.0
# Actualizamos métrica del Sidebar (Punto 4)
caja_sumatoria_oi.metric("Total Ingresos Adic.", f"$ {format_moneda(otr_v)}")

g_pagado = float(df_ed_g[df_ed_g["Pagado"]==True]["Monto"].sum()) if not df_ed_g.empty else 0.0
g_pend = float(df_ed_g[df_ed_g["Pagado"]==False]["Monto"].sum()) if not df_ed_g.empty else 0.0
it = s_in + n_in + otr_v
bf = it - g_pagado - g_pend

# Llenar la infografía superior dinámicamente
caja_infografia_gastos.metric("Total Gastos (Pagado + Pendiente)", f"$ {format_moneda(g_pagado + g_pend)}")
caja_infografia_disp.metric("Disponible Teórico", f"$ {format_moneda(it - (g_pagado + g_pend))}")

# Tarjetas KPI
st.divider()
c1, c2, c3, c4, c5 = st.columns(5)
tarj = [("INGRESOS", it, "black"), ("PAGADO", g_pagado, "green"), ("PENDIENTE", g_pend, "red"), ("DISPONIBLE", it-g_pagado, "blue"), ("SALDO FINAL", bf, "#d4af37")]
for i, (l, v, color) in enumerate(tarj): 
    with [c1, c2, c3, c4, c5][i]:
        st.markdown(f'<div class="card"><div class="card-label">{l}</div><div class="card-value" style="color:{color}">$ {v:,.0f}</div></div>', unsafe_allow_html=True)


# --- 6. GUARDAR DATOS EN NUBE ---
st.markdown("---")
if st.button("💾 GUARDAR CAMBIOS DEFINITIVOS", use_container_width=True):
    try:
        # Borrar datos previos
        supabase.table("gastos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
        supabase.table("otros_ingresos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
        supabase.table("ingresos_base").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()

        # Preparar y limpiar vacíos
        g_save = df_ed_g.dropna(subset=["Descripcion"]).assign(periodo=mes_s, anio=anio_s, usuario_id=u_id).rename(columns={"Categoria":"categoria","Descripcion":"descripcion","Monto":"monto","Referencia":"valor_referencia","Pagado":"pagado","Recurrente":"recurrente"}).to_dict(orient="records")
        oi_save = df_ed_oi.dropna(subset=["Descripcion"]).assign(periodo=mes_s, anio=anio_s, usuario_id=u_id).rename(columns={"Descripcion":"descripcion","Monto":"monto"}).to_dict(orient="records")
        i_save = {"anio": anio_s, "periodo": mes_s, "saldo_anterior": s_in, "nomina": n_in, "otros": otr_v, "usuario_id": u_id}

        # Insertar
        if g_save: supabase.table("gastos").insert(g_save).execute()
        if oi_save: supabase.table("otros_ingresos").insert(oi_save).execute()
        supabase.table("ingresos_base").insert(i_save).execute()

        st.balloons()
        st.success("✅ ¡Sincronizado con Supabase!")
        st.cache_data.clear() # Limpia caché para forzar lectura de lo nuevo
        st.rerun()

    except Exception as e: 
        st.error(f"❌ Error real de Supabase: {e}")


# --- 7. MÓDULO DE REPORTES Y PROYECCIONES ---
# 7 y 8. Restauración de Reportes y Proyecciones Semestrales
st.markdown("---")
st.markdown("## 📑 Generación de Extractos y Proyecciones")

col_rep1, col_rep2 = st.columns(2)

with col_rep1:
    st.markdown("#### 📅 Extracto Mensual")
    
    # Generador Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_ed_g.to_excel(writer, sheet_name='Gastos', index=False)
        df_ed_oi.to_excel(writer, sheet_name='Ingresos Adic', index=False)
    
    st.download_button(
        label="📥 Descargar Extracto (Excel)",
        data=buffer.getvalue(),
        file_name=f"Extracto_{mes_s}_{anio_s}_{u_id}.xlsx",
        mime="application/vnd.ms-excel",
        use_container_width=True
    )
    
    # Botón PDF
    if st.button("📄 Generar Extracto (PDF)", use_container_width=True):
        st.info("💡 PDF Activo: Puedes integrar aquí tu librería fpdf conectando las variables actuales.")

with col_rep2:
    st.markdown("#### 🔮 Proyección Semestral")
    semestre_sel = st.selectbox("Selecciona el semestre", ["Semestre 1 (Ene - Jun)", "Semestre 2 (Jul - Dic)"])
    if st.button("📊 Generar Proyección", use_container_width=True):
        meses_filtro = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"] if "1" in semestre_sel else ["Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        # Filtramos la base de datos completa por el semestre seleccionado
        df_proy = df_g_full[(df_g_full["Anio"] == anio_s) & (df_g_full["Periodo"].isin(meses_filtro))]
        total_proy = df_proy["Monto"].sum() if not df_proy.empty else 0
        
        st.success(f"Gasto acumulado proyectado para {semestre_sel}: **$ {format_moneda(total_proy)}**")
        if not df_proy.empty:
            st.dataframe(df_proy.groupby("Categoria")["Monto"].sum().reset_index(), use_container_width=True)
        else:
            st.warning("No hay datos registrados en este semestre para proyectar.")
