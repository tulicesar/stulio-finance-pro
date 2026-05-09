"""
data.py — Carga de datos desde Supabase y cálculo de métricas financieras
"""
import pandas as pd
import streamlit as st


# --- CARGAR BASE DE DATOS ---
def cargar_bd(supabase, u_id, token):
    try:
        supabase.postgrest.auth(token)
        r_g  = supabase.table("gastos").select("*").eq("usuario_id", u_id).execute()
        r_i  = supabase.table("ingresos_base").select("*").eq("usuario_id", u_id).execute()
        r_oi = supabase.table("otros_ingresos").select("*").eq("usuario_id", u_id).execute()

        df_g  = pd.DataFrame(r_g.data)  if r_g.data  else pd.DataFrame(columns=["anio","periodo","categoria","descripcion","monto","valor_referencia","pagado","recurrente","usuario_id","fecha_pago","es_proyectado","presupuesto_asociado","es_referencia"])
        df_i  = pd.DataFrame(r_i.data)  if r_i.data  else pd.DataFrame(columns=["anio","periodo","saldo_anterior","nomina","otros","usuario_id"])
        df_oi = pd.DataFrame(r_oi.data) if r_oi.data else pd.DataFrame(columns=["anio","periodo","descripcion","monto","usuario_id"])

        df_g  = df_g.rename(columns={
            "anio":"Año","periodo":"Periodo","categoria":"Categoría",
            "descripcion":"Descripción","monto":"Monto",
            "valor_referencia":"Valor Referencia","pagado":"Pagado",
            "recurrente":"Movimiento Recurrente","usuario_id":"Usuario",
            "fecha_pago":"Fecha Pago","es_proyectado":"Es Proyectado",
            "presupuesto_asociado":"Presupuesto Asociado",
            "es_referencia":"Es Referencia"
        })
        df_i  = df_i.rename(columns={
            "anio":"Año","periodo":"Periodo","saldo_anterior":"SaldoAnterior",
            "nomina":"Nomina","otros":"Otros","usuario_id":"Usuario"
        })
        df_oi = df_oi.rename(columns={
            "anio":"Año","periodo":"Periodo","descripcion":"Descripción",
            "monto":"Monto","usuario_id":"Usuario"
        })

        for df in [df_g, df_i, df_oi]:
            if "Año" in df.columns:
                df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(0).astype(int)

        if "Fecha Pago" in df_g.columns:
            df_g["Fecha Pago"] = pd.to_datetime(df_g["Fecha Pago"], errors="coerce")

        return df_g, df_i, df_oi

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# --- CALCULAR MÉTRICAS (vectorizado con pandas) ---
def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)

    if df_g.empty:
        return it, 0.0, 0.0, it, it, 100.0

    df = df_g.copy()
    df["Monto"]            = pd.to_numeric(df["Monto"],            errors="coerce").fillna(0)
    df["Valor Referencia"] = pd.to_numeric(df["Valor Referencia"], errors="coerce").fillna(0)
    df["Pagado"]           = df["Pagado"].fillna(False).astype(bool)

    # Pagado
    vp = float(df.loc[df["Pagado"], "Monto"].sum())

    # Pendiente
    df_pend = df[~df["Pagado"]].copy()

    if df_pend.empty:
        vpy = 0.0
    else:
        df_pend["_base"] = df_pend["Monto"].where(
            df_pend["Monto"] > 0, df_pend["Valor Referencia"]
        )

        tiene_proyectados = (
            "Es Proyectado" in df.columns and
            "Presupuesto Asociado" in df.columns and
            df_pend.get("Es Proyectado", pd.Series(False)).any()
        )

        if tiene_proyectados:
            _pa    = df["Presupuesto Asociado"].astype(str).str.strip()
            validos = ~_pa.isin(["nan", "None", "NaN", ""])
            # ✅ Usar Monto si > 0, sino Valor Referencia para los asociados
            df_asoc = df[validos].copy()
            df_asoc["_val"] = df_asoc["Monto"].where(
                df_asoc["Monto"] > 0, df_asoc["Valor Referencia"]
            )
            asociados_map = (
                df_asoc
                .groupby(_pa[validos])["_val"]
                .sum()
                .to_dict()
            )

            def pendiente_proyectado(row):
                nombre    = str(row.get("Descripción", "")).strip()
                vref      = float(row["Valor Referencia"])
                asociados = float(asociados_map.get(nombre, 0))
                return max(vref - asociados, 0)

            es_proy = df_pend.get("Es Proyectado", pd.Series(False)).fillna(False).astype(bool)
            df_pend["_base"] = df_pend.apply(
                lambda r: pendiente_proyectado(r) if bool(r.get("Es Proyectado", False)) else r["_base"],
                axis=1
            )

        vpy = float(df_pend["_base"].sum())

    bf       = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0.0
    return it, vp, vpy, float(it - vp), bf, ahorro_p



# --- CARGAR DATOS DE OTRO USUARIO (para vista consolidada) ---
def cargar_bd_usuario(supabase, u_id, token):
    """Igual que cargar_bd pero sin mostrar errores en UI — para uso interno."""
    try:
        supabase.postgrest.auth(token)
        r_g  = supabase.table("gastos").select("*").eq("usuario_id", u_id).execute()
        r_i  = supabase.table("ingresos_base").select("*").eq("usuario_id", u_id).execute()
        r_oi = supabase.table("otros_ingresos").select("*").eq("usuario_id", u_id).execute()

        df_g  = pd.DataFrame(r_g.data)  if r_g.data  else pd.DataFrame(columns=["anio","periodo","categoria","descripcion","monto","valor_referencia","pagado","recurrente","usuario_id","fecha_pago","es_proyectado","presupuesto_asociado","es_referencia"])
        df_i  = pd.DataFrame(r_i.data)  if r_i.data  else pd.DataFrame(columns=["anio","periodo","saldo_anterior","nomina","otros","usuario_id"])
        df_oi = pd.DataFrame(r_oi.data) if r_oi.data else pd.DataFrame(columns=["anio","periodo","descripcion","monto","usuario_id"])

        df_g  = df_g.rename(columns={"anio":"Año","periodo":"Periodo","categoria":"Categoría","descripcion":"Descripción","monto":"Monto","valor_referencia":"Valor Referencia","pagado":"Pagado","recurrente":"Movimiento Recurrente","usuario_id":"Usuario","fecha_pago":"Fecha Pago","es_proyectado":"Es Proyectado","presupuesto_asociado":"Presupuesto Asociado","es_referencia":"Es Referencia"})
        df_i  = df_i.rename(columns={"anio":"Año","periodo":"Periodo","saldo_anterior":"SaldoAnterior","nomina":"Nomina","otros":"Otros","usuario_id":"Usuario"})
        df_oi = df_oi.rename(columns={"anio":"Año","periodo":"Periodo","descripcion":"Descripción","monto":"Monto","usuario_id":"Usuario"})

        for df in [df_g, df_i, df_oi]:
            if "Año" in df.columns:
                df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(0).astype(int)
        if "Fecha Pago" in df_g.columns:
            df_g["Fecha Pago"] = pd.to_datetime(df_g["Fecha Pago"], errors="coerce")

        return df_g, df_i, df_oi
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# --- CARGAR VÍNCULOS DEL USUARIO ---
def cargar_vinculos(supabase, u_id, token):
    """Retorna lista de vínculos activos del usuario (como A o como B)."""
    try:
        supabase.postgrest.auth(token)
        r = supabase.table("vinculos_usuarios").select("*").execute()
        if not r.data:
            return []
        vinculos = []
        for v in r.data:
            if (str(v.get("usuario_id_a","")) == str(u_id) or
                str(v.get("usuario_id_b","")) == str(u_id)):
                vinculos.append(v)
        return vinculos
    except:
        return []


# --- BUSCAR USUARIO POR EMAIL ---
def buscar_usuario_por_email(supabase, email, token):
    """Busca un usuario en la tabla usuarios por su email."""
    try:
        supabase.postgrest.auth(token)
        r = supabase.table("usuarios").select("usuario_id,nombre_completo,email").eq("email", email.strip().lower()).execute()
        if r.data:
            return r.data[0]
        return None
    except:
        return None
def guardar_bd(supabase, token, u_id, mes_s, anio_s, df_g_limpio, df_oi_limpio, s_in, n_in, otr_v):
    supabase.postgrest.auth(token)

    # Borrar registros anteriores del mes
    supabase.table("gastos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
    supabase.table("otros_ingresos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
    supabase.table("ingresos_base").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()

    # Insertar gastos
    if not df_g_limpio.empty:
        gastos_db = []
        for _, row in df_g_limpio.iterrows():
            fecha_p = None
            if bool(row["Pagado"]):
                fp = row.get("Fecha Pago", None)
                if fp is not None and str(fp) not in ["None","NaT",""]:
                    try: fecha_p = str(fp)[:10]
                    except: fecha_p = None
            gastos_db.append({
                "anio": int(anio_s), "periodo": str(mes_s),
                "categoria": str(row["Categoría"]), "descripcion": str(row["Descripción"]),
                "monto": float(row["Monto"]), "valor_referencia": float(row["Valor Referencia"]),
                "pagado": bool(row["Pagado"]), "recurrente": bool(row["Movimiento Recurrente"]),
                "fecha_pago": fecha_p,
                "es_proyectado": bool(row.get("Es Proyectado", False)),
                "es_referencia": bool(row.get("Es Referencia", False)),
                "presupuesto_asociado": str(row["Presupuesto Asociado"]) if row.get("Presupuesto Asociado") not in [None,"None",""] else None,
                "usuario_id": str(u_id)
            })
        supabase.table("gastos").insert(gastos_db).execute()

    # Insertar otros ingresos
    if not df_oi_limpio.empty:
        otros_db = [{
            "anio": int(anio_s), "periodo": str(mes_s),
            "descripcion": str(row["Descripción"]), "monto": float(row["Monto"]),
            "usuario_id": str(u_id)
        } for _, row in df_oi_limpio.iterrows()]
        supabase.table("otros_ingresos").insert(otros_db).execute()

    # Insertar ingreso base
    supabase.table("ingresos_base").insert({
        "anio": int(anio_s), "periodo": str(mes_s),
        "saldo_anterior": float(s_in), "nomina": float(n_in),
        "otros": float(otr_v), "usuario_id": str(u_id)
    }).execute()
