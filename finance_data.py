"""
data.py — Carga de datos desde Supabase y cálculo de métricas financieras
"""
import pandas as pd
import streamlit as st


# ── CARGAR BASE DE DATOS ──────────────────────────────────────────────────────
def cargar_bd(supabase, u_id, token):
    try:
        supabase.postgrest.auth(token)
        r_g   = supabase.table("gastos").select("*").eq("usuario_id", u_id).execute()
        r_i   = supabase.table("ingresos_base").select("*").eq("usuario_id", u_id).execute()
        r_oi  = supabase.table("otros_ingresos").select("*").eq("usuario_id", u_id).execute()
        r_b   = supabase.table("billeteras").select("*").eq("usuario_id", u_id).order("created_at").execute()
        r_sab = supabase.table("saldo_anterior_billetera").select("*").eq("usuario_id", u_id).execute()
        r_ip  = supabase.table("ingresos_proyectados").select("*").eq("usuario_id", u_id).execute()

        df_g = pd.DataFrame(r_g.data) if r_g.data else pd.DataFrame(columns=[
            "anio","periodo","categoria","descripcion","monto","valor_referencia",
            "pagado","recurrente","usuario_id","fecha_pago","es_proyectado",
            "presupuesto_asociado","es_referencia","billetera_pago"
        ])
        df_i = pd.DataFrame(r_i.data) if r_i.data else pd.DataFrame(columns=[
            "anio","periodo","saldo_anterior","nomina","otros","usuario_id","billetera"
        ])
        df_oi = pd.DataFrame(r_oi.data) if r_oi.data else pd.DataFrame(columns=[
            "anio","periodo","descripcion","monto","usuario_id","billetera"
        ])
        df_b = pd.DataFrame(r_b.data) if r_b.data else pd.DataFrame(columns=[
            "id","usuario_id","nombre","created_at"
        ])
        df_sab = pd.DataFrame(r_sab.data) if r_sab.data else pd.DataFrame(columns=[
            "id","usuario_id","periodo","anio","billetera","monto"
        ])
        df_ip = pd.DataFrame(r_ip.data) if r_ip.data else pd.DataFrame(columns=[
            "anio","periodo","descripcion","valor_referencia","destino_copia",
            "recurrente","usuario_id"
        ])

        df_g = df_g.rename(columns={
            "anio":"Año", "periodo":"Periodo", "categoria":"Categoría",
            "descripcion":"Descripción", "monto":"Monto",
            "valor_referencia":"Valor Referencia", "pagado":"Pagado",
            "recurrente":"Movimiento Recurrente", "usuario_id":"Usuario",
            "fecha_pago":"Fecha Pago", "es_proyectado":"Es Proyectado",
            "presupuesto_asociado":"Presupuesto Asociado",
            "es_referencia":"Es Referencia",
            "billetera_pago":"Billetera Pago"
        })
        df_i = df_i.rename(columns={
            "anio":"Año", "periodo":"Periodo", "saldo_anterior":"SaldoAnterior",
            "nomina":"Nomina", "otros":"Otros", "usuario_id":"Usuario",
            "billetera":"Billetera"
        })
        df_oi = df_oi.rename(columns={
            "anio":"Año", "periodo":"Periodo", "descripcion":"Descripción",
            "monto":"Monto", "usuario_id":"Usuario", "billetera":"Billetera"
        })
        if "anio" in df_sab.columns:
            df_sab = df_sab.rename(columns={"anio":"Año","periodo":"Periodo"})
        df_ip = df_ip.rename(columns={
            "anio":"Año", "periodo":"Periodo", "descripcion":"Descripción",
            "valor_referencia":"Valor Proyectado", "destino_copia":"Destino Copia",
            "recurrente":"Movimiento Recurrente", "usuario_id":"Usuario"
        })

        for df in [df_g, df_i, df_oi, df_sab, df_ip]:
            if "Año" in df.columns:
                df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(0).astype(int)

        if "Fecha Pago" in df_g.columns:
            df_g["Fecha Pago"] = pd.to_datetime(df_g["Fecha Pago"], errors="coerce")

        return df_g, df_i, df_oi, df_b, df_sab, df_ip

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# ── CARGAR / GUARDAR CONFIG DE USUARIO ───────────────────────────────────────
def cargar_config(supabase, u_id, token):
    """Retorna dict con configuración del usuario. Claves: billeteras_desde_periodo, billeteras_desde_anio."""
    try:
        supabase.postgrest.auth(token)
        r = supabase.table("config_usuario").select("*").eq("usuario_id", str(u_id)).execute()
        if r.data:
            return r.data[0]
        return {}
    except:
        return {}


def guardar_config(supabase, u_id, token, **kwargs):
    """Upsert de configuración del usuario. Pasar como kwargs los campos a actualizar."""
    try:
        supabase.postgrest.auth(token)
        payload = {"usuario_id": str(u_id), **kwargs}
        supabase.table("config_usuario").upsert(payload, on_conflict="usuario_id").execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar configuración: {e}")
        return False


# ── CARGAR DATOS DE OTRO USUARIO (vista consolidada) ─────────────────────────
def cargar_bd_usuario(supabase, u_id, token):
    try:
        supabase.postgrest.auth(token)
        r_g  = supabase.table("gastos").select("*").eq("usuario_id", u_id).execute()
        r_i  = supabase.table("ingresos_base").select("*").eq("usuario_id", u_id).execute()
        r_oi = supabase.table("otros_ingresos").select("*").eq("usuario_id", u_id).execute()

        df_g  = pd.DataFrame(r_g.data)  if r_g.data  else pd.DataFrame()
        df_i  = pd.DataFrame(r_i.data)  if r_i.data  else pd.DataFrame()
        df_oi = pd.DataFrame(r_oi.data) if r_oi.data else pd.DataFrame()

        df_g  = df_g.rename(columns={"anio":"Año","periodo":"Periodo","categoria":"Categoría",
            "descripcion":"Descripción","monto":"Monto","valor_referencia":"Valor Referencia",
            "pagado":"Pagado","recurrente":"Movimiento Recurrente","usuario_id":"Usuario",
            "fecha_pago":"Fecha Pago","es_proyectado":"Es Proyectado",
            "presupuesto_asociado":"Presupuesto Asociado","es_referencia":"Es Referencia",
            "billetera_pago":"Billetera Pago"})
        df_i  = df_i.rename(columns={"anio":"Año","periodo":"Periodo","saldo_anterior":"SaldoAnterior",
            "nomina":"Nomina","otros":"Otros","usuario_id":"Usuario","billetera":"Billetera"})
        df_oi = df_oi.rename(columns={"anio":"Año","periodo":"Periodo","descripcion":"Descripción",
            "monto":"Monto","usuario_id":"Usuario","billetera":"Billetera"})

        for df in [df_g, df_i, df_oi]:
            if "Año" in df.columns:
                df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(0).astype(int)
        if "Fecha Pago" in df_g.columns:
            df_g["Fecha Pago"] = pd.to_datetime(df_g["Fecha Pago"], errors="coerce")

        return df_g, df_i, df_oi
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()


# ── CALCULAR SALDO REAL POR BILLETERA ────────────────────────────────────────
def calcular_saldo_billeteras(df_g, df_i, df_oi, df_sab, lista_billeteras, mes_s, anio_s, df_transferencias=None):
    """
    Retorna dict {nombre_billetera: saldo_real} para el periodo dado.
    Saldo real = saldo_anterior + ingresos_recibidos - gastos_pagados +/- transferencias
    Solo cuenta movimientos PAGADOS en gastos.
    """
    saldos = {b: 0.0 for b in lista_billeteras}
    if not lista_billeteras:
        return saldos

    # 1. Saldo anterior distribuido por billetera
    if not df_sab.empty:
        # df_sab puede venir como tabla completa de BD (con Periodo/Año)
        # o como df_sab_input local (solo columnas billetera/monto sin filtrar)
        if "Periodo" in df_sab.columns and "Año" in df_sab.columns:
            filtro = (df_sab["Periodo"] == mes_s) & (df_sab["Año"] == anio_s)
            _df_sab_iter = df_sab[filtro]
        else:
            _df_sab_iter = df_sab  # ya viene filtrado por periodo desde el sidebar
        for _, row in _df_sab_iter.iterrows():
            b = str(row.get("billetera") or row.get("Billetera", "")).strip()
            if b in saldos:
                saldos[b] += float(row.get("monto") or row.get("Monto", 0) or 0)

    # 2. Ingreso fijo (nómina) del mes
    if not df_i.empty:
        filtro_i = (df_i["Periodo"] == mes_s) & (df_i["Año"] == anio_s)
        for _, row in df_i[filtro_i].iterrows():
            b = str(row.get("Billetera", "") or "").strip()
            if b in saldos:
                saldos[b] += float(row.get("Nomina", 0) or 0)

    # 3. Otros ingresos del mes
    if not df_oi.empty:
        filtro_oi = (df_oi["Periodo"] == mes_s) & (df_oi["Año"] == anio_s)
        for _, row in df_oi[filtro_oi].iterrows():
            b = str(row.get("Billetera", "") or "").strip()
            if b in saldos:
                saldos[b] += float(row.get("Monto", 0) or 0)

    # 4. Gastos PAGADOS del mes (restan)
    if not df_g.empty:
        filtro_g = (
            (df_g["Periodo"] == mes_s) &
            (df_g["Año"] == anio_s) &
            (df_g["Pagado"].fillna(False).astype(bool)) &
            (df_g["Es Proyectado"].fillna(False).astype(bool) == False)
        )
        for _, row in df_g[filtro_g].iterrows():
            b = str(row.get("Billetera Pago", "") or "").strip()
            if b in saldos:
                saldos[b] -= float(row.get("Monto", 0) or 0)

    # 5. Transferencias entre billeteras (neutrales para ingresos/egresos)
    if df_transferencias is not None and not df_transferencias.empty:
        for _, row in df_transferencias.iterrows():
            origen  = str(row.get("billetera_origen",  "")).strip()
            destino = str(row.get("billetera_destino", "")).strip()
            monto_t = float(row.get("monto", 0) or 0)
            if origen in saldos:
                saldos[origen]  -= monto_t
            if destino in saldos:
                saldos[destino] += monto_t

    return saldos


# ── FUENTE ÚNICA DE VERDAD: DINERO DISPONIBLE REAL ───────────────────────────
def calcular_fact_billeteras(df_g, df_i, df_oi, df_sab, lista_billeteras, mes_s, anio_s, df_transferencias=None):
    """
    Envuelve calcular_saldo_billeteras() y devuelve (saldos_dict, total).
    `total` es el Dinero Disponible REAL del periodo cuando el módulo de
    billeteras está activo: la suma de los saldos de cada billetera.
    Esta es la única fuente de verdad para "Dinero Disponible" y para el
    "Saldo Anterior sugerido" del mes siguiente — evita que ambos cálculos
    diverjan entre sí (bug histórico: Saldo Anterior se recalculaba en vivo
    mientras Total Billeteras dependía de un snapshot guardado).
    """
    saldos = calcular_saldo_billeteras(
        df_g, df_i, df_oi, df_sab, lista_billeteras, mes_s, anio_s,
        df_transferencias=df_transferencias
    )
    return saldos, sum(saldos.values())


# ── CALCULAR MÉTRICAS ─────────────────────────────────────────────────────────
def calcular_metricas(df_g, nom, otr, s_ant):
    it = float(s_ant) + float(nom) + float(otr)

    if df_g.empty:
        return it, 0.0, 0.0, it, it, 100.0

    df = df_g.copy()
    df["Monto"]            = pd.to_numeric(df["Monto"],            errors="coerce").fillna(0)
    df["Valor Referencia"] = pd.to_numeric(df["Valor Referencia"], errors="coerce").fillna(0)
    df["Pagado"]           = df["Pagado"].fillna(False).astype(bool)

    vp = float(df.loc[df["Pagado"], "Monto"].sum())

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
            df_asoc = df[validos].copy()
            df_asoc["_val"] = df_asoc["Monto"].where(df_asoc["Monto"] > 0, df_asoc["Valor Referencia"])
            asociados_map = df_asoc.groupby(_pa[validos])["_val"].sum().to_dict()

            def pendiente_proyectado(row):
                nombre    = str(row.get("Descripción", "")).strip()
                vref      = float(row["Valor Referencia"])
                asociados = float(asociados_map.get(nombre, 0))
                return max(vref - asociados, 0)

            df_pend["_base"] = df_pend.apply(
                lambda r: pendiente_proyectado(r) if bool(r.get("Es Proyectado", False)) else r["_base"],
                axis=1
            )
        vpy = float(df_pend["_base"].sum())

    bf       = it - vp - vpy
    ahorro_p = (bf / it * 100) if it > 0 else 0.0
    return it, vp, vpy, float(it - vp), bf, ahorro_p


# ── CARGAR VÍNCULOS ───────────────────────────────────────────────────────────
def cargar_vinculos(supabase, u_id, token):
    try:
        supabase.postgrest.auth(token)
        _uid = str(u_id)
        r_a = supabase.table("vinculos_usuarios").select("*").eq("usuario_id_a", _uid).execute()
        r_b = supabase.table("vinculos_usuarios").select("*").eq("usuario_id_b", _uid).execute()
        vinculos = []
        if r_a.data: vinculos.extend(r_a.data)
        if r_b.data: vinculos.extend(r_b.data)
        return vinculos
    except:
        return []


# ── BUSCAR USUARIO POR EMAIL ──────────────────────────────────────────────────
def buscar_usuario_por_email(supabase, email, token):
    try:
        supabase.postgrest.auth(token)
        r = supabase.table("usuarios").select("usuario_id,nombre_completo,email").eq("email", email.strip().lower()).execute()
        return r.data[0] if r.data else None
    except:
        return None


# ── GUARDAR BD ────────────────────────────────────────────────────────────────
def guardar_bd(supabase, token, u_id, mes_s, anio_s,
               df_g_limpio, df_oi_limpio, s_in, n_in, otr_v,
               bill_nomina="", df_sab_nuevo=None):
    """
    Parámetros nuevos:
      bill_nomina   — nombre de billetera asignada al ingreso fijo
      df_sab_nuevo  — DataFrame con columnas [billetera, monto] del saldo anterior
    """
    supabase.postgrest.auth(token)

    # Borrar registros anteriores del mes
    supabase.table("gastos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
    supabase.table("otros_ingresos").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
    supabase.table("ingresos_base").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
    supabase.table("saldo_anterior_billetera").delete().eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()

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
            bill_pago = str(row.get("Billetera Pago", "") or "").strip()
            gastos_db.append({
                "anio": int(anio_s), "periodo": str(mes_s),
                "categoria": str(row["Categoría"]), "descripcion": str(row["Descripción"]),
                "monto": float(row["Monto"]), "valor_referencia": float(row["Valor Referencia"]),
                "pagado": bool(row["Pagado"]), "recurrente": bool(row["Movimiento Recurrente"]),
                "fecha_pago": fecha_p,
                "es_proyectado": bool(row.get("Es Proyectado", False)),
                "es_referencia": bool(row.get("Es Referencia", False)),
                "presupuesto_asociado": str(row["Presupuesto Asociado"]) if row.get("Presupuesto Asociado") not in [None,"None",""] else None,
                "billetera_pago": bill_pago if bill_pago else None,
                "usuario_id": str(u_id)
            })
        supabase.table("gastos").insert(gastos_db).execute()

    # Insertar otros ingresos
    if not df_oi_limpio.empty:
        otros_db = []
        for _, row in df_oi_limpio.iterrows():
            bill_oi = str(row.get("Billetera", "") or "").strip()
            otros_db.append({
                "anio": int(anio_s), "periodo": str(mes_s),
                "descripcion": str(row["Descripción"]), "monto": float(row["Monto"]),
                "billetera": bill_oi if bill_oi else None,
                "usuario_id": str(u_id)
            })
        supabase.table("otros_ingresos").insert(otros_db).execute()

    # Insertar ingreso base
    supabase.table("ingresos_base").insert({
        "anio": int(anio_s), "periodo": str(mes_s),
        "saldo_anterior": float(s_in), "nomina": float(n_in),
        "otros": float(otr_v),
        "billetera": bill_nomina if bill_nomina else None,
        "usuario_id": str(u_id)
    }).execute()

    # Insertar saldo anterior por billetera
    if df_sab_nuevo is not None and not df_sab_nuevo.empty:
        sab_db = []
        for _, row in df_sab_nuevo.iterrows():
            b = str(row.get("billetera","")).strip()
            m = float(row.get("monto", 0) or 0)
            if b and m != 0:
                sab_db.append({
                    "usuario_id": str(u_id), "periodo": str(mes_s),
                    "anio": int(anio_s), "billetera": b, "monto": m
                })
        if sab_db:
            supabase.table("saldo_anterior_billetera").insert(sab_db).execute()


# ── GUARDAR BILLETERAS ────────────────────────────────────────────────────────
def guardar_billeteras(supabase, token, u_id, nombres_lista):
    """Sincroniza la lista completa de billeteras del usuario."""
    try:
        supabase.postgrest.auth(token)
        # Borrar todas las existentes
        supabase.table("billeteras").delete().eq("usuario_id", str(u_id)).execute()
        # Insertar una por una para evitar fallos silenciosos de RLS en batch
        for n in nombres_lista:
            n = n.strip()
            if n:
                supabase.table("billeteras").insert({
                    "usuario_id": str(u_id),
                    "nombre": n
                }).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar billeteras: {e}")
        return False


# ── TRANSFERENCIAS ENTRE BILLETERAS ──────────────────────────────────────────
def cargar_transferencias(supabase, u_id, token, mes_s, anio_s):
    """Retorna DataFrame con transferencias del periodo."""
    try:
        supabase.postgrest.auth(token)
        r = (supabase.table("transferencias_billeteras")
             .select("*")
             .eq("usuario_id", u_id)
             .eq("anio", anio_s)
             .eq("periodo", mes_s)
             .order("created_at")
             .execute())
        if r.data:
            df = pd.DataFrame(r.data)
            df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
            return df
        return pd.DataFrame(columns=["id","usuario_id","anio","periodo",
                                     "billetera_origen","billetera_destino",
                                     "monto","descripcion","created_at"])
    except Exception as e:
        import streamlit as st
        st.error(f"Error al cargar transferencias: {e}")
        return pd.DataFrame()


def guardar_transferencia(supabase, u_id, token, mes_s, anio_s,
                          origen, destino, monto, descripcion=""):
    """Inserta una transferencia entre billeteras."""
    try:
        supabase.postgrest.auth(token)
        supabase.table("transferencias_billeteras").insert({
            "usuario_id":        str(u_id),
            "anio":              int(anio_s),
            "periodo":           str(mes_s),
            "billetera_origen":  origen,
            "billetera_destino": destino,
            "monto":             float(monto),
            "descripcion":       descripcion or None,
        }).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Error al guardar transferencia: {e}")
        return False


def eliminar_transferencia(supabase, u_id, token, transfer_id):
    """Elimina una transferencia por ID."""
    try:
        supabase.postgrest.auth(token)
        supabase.table("transferencias_billeteras").delete().eq(
            "id", transfer_id).eq("usuario_id", str(u_id)).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Error al eliminar transferencia: {e}")
        return False
# ── TRANSFERENCIAS ENTRE BILLETERAS ──────────────────────────────────────────
def cargar_transferencias(supabase, u_id, token, mes_s, anio_s):
    """Retorna DataFrame con transferencias del periodo."""
    try:
        supabase.postgrest.auth(token)
        r = (supabase.table("transferencias_billeteras")
             .select("*")
             .eq("usuario_id", u_id)
             .eq("anio", anio_s)
             .eq("periodo", mes_s)
             .order("created_at")
             .execute())
        if r.data:
            df = pd.DataFrame(r.data)
            df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
            return df
        return pd.DataFrame(columns=["id","usuario_id","anio","periodo",
                                     "billetera_origen","billetera_destino",
                                     "monto","descripcion","created_at"])
    except Exception as e:
        import streamlit as st
        st.error(f"Error al cargar transferencias: {e}")
        return pd.DataFrame()


def guardar_transferencia(supabase, u_id, token, mes_s, anio_s,
                          origen, destino, monto, descripcion=""):
    """Inserta una transferencia entre billeteras."""
    try:
        supabase.postgrest.auth(token)
        supabase.table("transferencias_billeteras").insert({
            "usuario_id":        str(u_id),
            "anio":              int(anio_s),
            "periodo":           str(mes_s),
            "billetera_origen":  origen,
            "billetera_destino": destino,
            "monto":             float(monto),
            "descripcion":       descripcion or None,
        }).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Error al guardar transferencia: {e}")
        return False


def eliminar_transferencia(supabase, u_id, token, transfer_id):
    """Elimina una transferencia por ID."""
    try:
        supabase.postgrest.auth(token)
        supabase.table("transferencias_billeteras").delete().eq(
            "id", transfer_id).eq("usuario_id", str(u_id)).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Error al eliminar transferencia: {e}")
        return False


# ── INGRESOS PROYECTADOS ──────────────────────────────────────────────────────
def guardar_ingresos_proyectados(supabase, token, u_id, mes_s, anio_s, df_ip_limpio):
    """Guarda/actualiza los ingresos proyectados del periodo."""
    try:
        supabase.postgrest.auth(token)
        supabase.table("ingresos_proyectados").delete()\
            .eq("usuario_id", u_id).eq("anio", anio_s).eq("periodo", mes_s).execute()
        if not df_ip_limpio.empty:
            for _, row in df_ip_limpio.iterrows():
                desc = str(row.get("Descripción", "")).strip()
                if not desc:
                    continue
                supabase.table("ingresos_proyectados").insert({
                    "anio":             int(anio_s),
                    "periodo":          str(mes_s),
                    "descripcion":      desc,
                    "valor_referencia": float(row.get("Valor Proyectado", 0) or 0),
                    "destino_copia":    str(row.get("Destino Copia", "Ingresos Adicionales") or "Ingresos Adicionales"),
                    "recurrente":       bool(row.get("Movimiento Recurrente", False)),
                    "usuario_id":       str(u_id),
                }).execute()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Error al guardar ingresos proyectados: {e}")
        return False
