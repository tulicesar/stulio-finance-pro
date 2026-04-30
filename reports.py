"""
reports.py — Generación de reportes PDF y Excel
"""
import os
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
import pytz

def generar_pdf_reporte(df_g_full, df_i_full, df_oi_full, meses, titulo, anio, u_id):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    import math

    nombre_usuario = st.session_state.get("u_nombre_completo", u_id)
    buf = BytesIO()
    c   = canvas.Canvas(buf, pagesize=letter)

    C_AZUL   = HexColor("#14213d")
    C_NARANJA= HexColor("#fca311")
    C_GRIS   = HexColor("#e5e5e5")
    C_NEGRO  = HexColor("#000000")
    C_VERDE  = HexColor("#2ecc71")
    C_ROJO   = HexColor("#e74c3c")
    C_OSCURO = HexColor("#2d3238")

    total_periodo_nomina = total_periodo_otros = total_periodo_gastos = 0

    # Guardamos datos del último mes para la página 2
    ultimo_g_m  = None
    ultimo_it   = ultimo_vp = ultimo_vpy = ultimo_bf = ultimo_ahorro_p = 0

    def head(canvas_obj, t, a, user_name):
        canvas_obj.setFillColor(colors.white)
        canvas_obj.rect(0, 0, 612, 792, fill=1)
        if os.path.exists(LOGO_APP_H):
            canvas_obj.drawImage(LOGO_APP_H, 55, 670, width=500, height=100, preserveAspectRatio=True, anchor='c')
        canvas_obj.setFont("Helvetica-BoldOblique", 9)
        canvas_obj.setFillColor(C_AZUL)
        canvas_obj.drawString(50, 650, f"Usuario: {user_name}")
        canvas_obj.drawRightString(560, 650, f"{t} {a}")
        canvas_obj.setStrokeColor(C_NARANJA); canvas_obj.setLineWidth(2); canvas_obj.line(50, 645, 560, 645)
        tz = pytz.timezone('America/Bogota')
        fecha_gen = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
        canvas_obj.setFont("Helvetica", 7); canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(50, 30, f"Documento generado el: {fecha_gen}")
        return 620

    y = head(c, titulo, anio, nombre_usuario)

    for m in meses:
        i_m  = df_i_full[(df_i_full["Periodo"]==m) & (df_i_full["Año"]==anio) & (df_i_full["Usuario"]==u_id)]
        g_m  = df_g_full[(df_g_full["Periodo"]==m) & (df_g_full["Año"]==anio) & (df_g_full["Usuario"]==u_id)]
        oi_m = df_oi_full[(df_oi_full["Periodo"]==m) & (df_oi_full["Año"]==anio) & (df_oi_full["Usuario"]==u_id)]

        s_ant   = float(i_m["SaldoAnterior"].iloc[0]) if not i_m.empty else 0
        nom     = float(i_m["Nomina"].iloc[0])        if not i_m.empty else 0
        otr_sum = float(oi_m["Monto"].sum())          if not oi_m.empty else 0

        it, vp, vpy, _, bf, ahorro_p = calcular_metricas(g_m, nom, otr_sum, s_ant)
        total_periodo_nomina  += nom
        total_periodo_otros   += otr_sum
        total_periodo_gastos  += (vp + vpy)

        # Guardamos el último mes para página 2
        ultimo_g_m = g_m; ultimo_it = it; ultimo_vp = vp
        ultimo_vpy = vpy; ultimo_bf = bf; ultimo_ahorro_p = ahorro_p

        if y < 250: c.showPage(); y = head(c, titulo, anio, nombre_usuario)

        c.setFillColor(C_GRIS); c.rect(50, y-55, 510, 60, fill=1, stroke=0)
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 11); c.drawString(60, y-15, f"MES: {m}")
        c.setFont("Helvetica", 9)
        c.drawString(60, y-30, f"Ingresos: $ {it:,.0f} | Pagadas: $ {vp:,.0f} | Pendientes: $ {vpy:,.0f}")
        c.setFillColor(C_NARANJA); c.setFont("Helvetica-Bold", 9)
        c.drawString(60, y-45, f"SALDO A FAVOR FINAL: $ {bf:,.0f}"); y -= 80

        c.setFont("Helvetica-Bold", 9); c.setFillColor(C_AZUL); c.drawString(60, y, "RELACIÓN DE INGRESOS"); y -= 15
        c.setFont("Helvetica", 8); c.setFillColor(C_NEGRO)
        c.drawString(60, y, "Saldo Anterior"); c.drawRightString(480, y, f"$ {s_ant:,.0f}"); y -= 10
        c.drawString(60, y, "Nómina");         c.drawRightString(480, y, f"$ {nom:,.0f}"); y -= 5

        if not oi_m.empty:
            c.setStrokeColor(colors.lightgrey); c.line(60, y, 480, y); y -= 12
            c.setFont("Helvetica-BoldOblique", 7); c.setFillColor(colors.darkgrey)
            c.drawString(60, y, "Ingresos Variables"); y -= 10
            for _, r_oi in oi_m.iterrows():
                c.setFont("Helvetica", 8); c.setFillColor(C_NEGRO)
                c.drawString(65, y, f"● {r_oi['Descripción']}"); c.drawRightString(480, y, f"$ {r_oi['Monto']:,.0f}"); y -= 10
            c.setFont("Helvetica-Bold", 8); c.line(60, y+5, 480, y+5)
            c.drawRightString(480, y-5, f"Total Otros Ingresos: $ {otr_sum:,.0f}"); y -= 25
        else:
            y -= 15

        # ✅ MEJORA: $ en montos de gastos + total al pie
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9); c.drawString(60, y, "RELACIÓN DE GASTOS"); y -= 15
        c.setFont("Helvetica-Bold", 8)
        c.drawString(60, y, "CATEGORÍA - DESCRIPCIÓN"); c.drawRightString(490, y, "MONTO"); c.drawRightString(545, y, "PAGADO"); y -= 12
        c.setStrokeColor(C_GRIS); c.setLineWidth(0.5); c.line(60, y+8, 545, y+8)
        c.setFont("Helvetica", 8); c.setFillColor(C_NEGRO)
        total_gastos_mes = 0
        for _, row in g_m.iterrows():
            if y < 80: c.showPage(); y = head(c, titulo, anio, nombre_usuario); c.setFont("Helvetica", 8)
            monto_fila = float(row['Monto'])
            # ✅ Solo sumar al total los gastos pagados
            if bool(row.get("Pagado", False)):
                total_gastos_mes += monto_fila
            c.drawString(60, y, f"{row['Categoría']} - {row['Descripción']}"[:65])
            c.drawRightString(490, y, f"$ {monto_fila:,.0f}")
            c.drawRightString(545, y, "SI" if row["Pagado"] else "NO"); y -= 12

        # ✅ TOTAL AL PIE DE LA TABLA
        c.setStrokeColor(C_AZUL); c.setLineWidth(1); c.line(60, y+8, 545, y+8)
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9)
        c.drawString(60, y-2, "TOTAL GASTOS DEL MES:")
        c.drawRightString(490, y-2, f"$ {total_gastos_mes:,.0f}")
        y -= 25

    if len(meses) > 1:
        if y < 150: c.showPage(); y = head(c, titulo, anio, nombre_usuario)
        y -= 20
        c.setFillColor(C_NARANJA); c.setStrokeColor(C_AZUL); c.setLineWidth(2)
        c.rect(50, y-100, 510, 110, fill=1, stroke=1)
        c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 12)
        c.drawString(70, y-5, f"RESUMEN: {titulo.upper()}")
        ing_totales         = total_periodo_nomina + total_periodo_otros
        saldo_final_periodo = ing_totales - total_periodo_gastos
        c.setFont("Helvetica", 10)
        c.drawString(70, y-25, f"Total Nómina Percibida:       $ {total_periodo_nomina:,.0f}")
        c.drawString(70, y-40, f"Total Ingresos Adicionales:   $ {total_periodo_otros:,.0f}")
        c.drawString(70, y-55, f"Total Gastos del Periodo:     $ {total_periodo_gastos:,.0f}")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, y-85, f"SALDO TOTAL AL CIERRE: $ {abs(saldo_final_periodo):,.0f}"); y -= 150

    # ============================================================
    # PÁGINA VISUAL: ANÁLISIS (siempre página nueva)
    # ============================================================
    c.showPage()
    y = head(c, titulo, anio, nombre_usuario)

    import math

    def draw_arc_filled(canvas_obj, cx, cy, r_out, r_in, angle_start, angle_end, fill_color):
        steps = max(int(abs(angle_end - angle_start) / 2), 1)
        points_out, points_in = [], []
        for i in range(steps + 1):
            angle = math.radians(angle_start + (angle_end - angle_start) * i / steps)
            points_out.append((cx + r_out * math.cos(angle), cy + r_out * math.sin(angle)))
            points_in.append( (cx + r_in  * math.cos(angle), cy + r_in  * math.sin(angle)))
        path = canvas_obj.beginPath()
        path.moveTo(*points_out[0])
        for pt in points_out[1:]: path.lineTo(*pt)
        for pt in reversed(points_in): path.lineTo(*pt)
        path.close()
        canvas_obj.setFillColor(fill_color)
        canvas_obj.drawPath(path, fill=1, stroke=0)

    # --- TÍTULO ---
    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "ANÁLISIS VISUAL DEL MES"); y -= 8
    c.setStrokeColor(C_NARANJA); c.setLineWidth(2); c.line(50, y, 560, y)

    # ── COORDENADAS FIJAS DE LAS DOS COLUMNAS ──────────────────
    # Columna izquierda:  x 50  → 290  (ancho 240)
    # Columna derecha:    x 320 → 560  (ancho 240)
    # Fila superior:      y 560 → 420
    # Fila inferior tend: y 200 → 100
    # ───────────────────────────────────────────────────────────

    TOP_Y   = y - 20   # 587 aprox
    BAR_X   = 50
    BAR_W   = 170      # ancho máximo de la barra (cabe en 240px)
    ROW_H   = 17
    COL2_X  = 330      # inicio columna derecha

    # ============================================================
    # COL IZQ — DESGLOSE POR CATEGORÍA
    # ============================================================
    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9)
    c.drawString(BAR_X, TOP_Y, "DESGLOSE POR CATEGORÍA")
    y_cat = TOP_Y - 16

    if ultimo_g_m is not None and not ultimo_g_m.empty:
        t_pdf   = ultimo_g_m.copy()
        t_pdf['V'] = t_pdf.apply(lambda r: r['Monto'] if r['Pagado'] else r['Valor Referencia'], axis=1)
        total_v = t_pdf['V'].sum()
        if total_v > 0:
            res_cat = t_pdf.groupby("Categoría")['V'].sum().reset_index()
            res_cat['pct'] = res_cat['V'] / total_v * 100
            res_cat = res_cat.sort_values('V', ascending=False)

            for _, r in res_cat.iterrows():
                if y_cat < 220: break
                color_hex = COLOR_MAP.get(r['Categoría'], "#6c757d")
                pct   = r['pct']
                monto = r['V']
                bar_len = max((pct / 100) * BAR_W, 3)

                # ✅ Fondo gris claro (visible en PDF blanco)
                c.setFillColor(HexColor("#e0e0e0"))
                c.roundRect(BAR_X, y_cat - ROW_H + 5, BAR_W, ROW_H - 7, 3, fill=1, stroke=0)
                # Barra color
                c.setFillColor(HexColor(color_hex))
                c.roundRect(BAR_X, y_cat - ROW_H + 5, bar_len, ROW_H - 7, 3, fill=1, stroke=0)
                # ✅ Etiqueta dentro de la barra en negro (visible sobre colores claros)
                c.setFillColor(C_NEGRO); c.setFont("Helvetica-Bold", 6)
                c.drawString(BAR_X + 3, y_cat - 8, r['Categoría'][:18])
                # ✅ Monto + % FUERA a la derecha en negro (sobre fondo blanco del PDF)
                c.setFont("Helvetica", 6); c.setFillColor(C_NEGRO)
                c.drawString(BAR_X + BAR_W + 4, y_cat - 8, f"${monto:,.0f}  {pct:.1f}%")
                y_cat -= ROW_H

    # ============================================================
    # COL DER ARRIBA — GAUGE EFICIENCIA DE AHORRO
    # ============================================================
    META  = 20
    v_cl  = max(0, min(ultimo_ahorro_p, 100))
    CX    = COL2_X + 100    # centro del gauge en la columna derecha
    CY    = TOP_Y - 75
    R_OUT = 65
    R_IN  = 46

    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(CX, TOP_Y, "EFICIENCIA DE AHORRO")

    ang_meta = 180 - (META / 100 * 180)
    draw_arc_filled(c, CX, CY, R_OUT, R_IN, ang_meta, 180, HexColor("#f8d7da"))
    draw_arc_filled(c, CX, CY, R_OUT, R_IN, 0, ang_meta, HexColor("#d4edda"))
    ang_val = 180 - (v_cl / 100 * 180)
    draw_arc_filled(c, CX, CY, R_OUT, R_IN, ang_val, 180, HexColor("#fca311"))

    ang_meta_r = math.radians(ang_meta)
    c.setStrokeColor(C_VERDE); c.setLineWidth(2)
    c.line(CX + R_IN  * math.cos(ang_meta_r), CY + R_IN  * math.sin(ang_meta_r),
           CX + (R_OUT+6) * math.cos(ang_meta_r), CY + (R_OUT+6) * math.sin(ang_meta_r))

    c.setFillColor(C_NARANJA); c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(CX, CY - 12, f"{v_cl:.0f}%")
    c.setFont("Helvetica", 7); c.setFillColor(C_NEGRO)
    c.drawCentredString(CX, CY - 24, f"Meta: {META}%")
    if v_cl >= META:
        c.setFillColor(C_VERDE); c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(CX, CY - 36, "¡Meta alcanzada!")
    else:
        c.setFillColor(C_ROJO); c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(CX, CY - 36, f"Falta {META - v_cl:.0f}% para la meta")

    # ============================================================
    # COL DER ABAJO — ESTADO REAL DEL DINERO
    # ============================================================
    y_est = CY - 60
    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(CX, y_est, "ESTADO REAL DEL DINERO"); y_est -= 14

    total_est = ultimo_vp + ultimo_vpy + (ultimo_bf if ultimo_bf > 0 else 0)
    if total_est > 0:
        items_estado = [
            ("Oblig. Pagadas",  ultimo_vp,                              "#2ecc71"),
            ("Oblig. Pendient", ultimo_vpy,                             "#e74c3c"),
            ("Saldo a Favor",   ultimo_bf if ultimo_bf > 0 else 0,      "#fca311"),
        ]
        BAR_EST_X = COL2_X
        BAR_EST_W = 190
        for label, val, hex_col in items_estado:
            pct_e = (val / total_est * 100) if total_est > 0 else 0
            bar_e = max((pct_e / 100) * BAR_EST_W, 2)
            # ✅ Fondo gris claro
            c.setFillColor(HexColor("#e0e0e0"))
            c.roundRect(BAR_EST_X, y_est - 13, BAR_EST_W, 13, 3, fill=1, stroke=0)
            # Barra color
            c.setFillColor(HexColor(hex_col))
            c.roundRect(BAR_EST_X, y_est - 13, bar_e, 13, 3, fill=1, stroke=0)
            # ✅ Texto negro visible
            c.setFillColor(C_NEGRO); c.setFont("Helvetica-Bold", 7)
            c.drawString(BAR_EST_X + 3, y_est - 10, label)
            c.setFont("Helvetica", 7)
            c.drawRightString(BAR_EST_X + BAR_EST_W - 3, y_est - 10, f"$ {val:,.0f} ({pct_e:.1f}%)")
            y_est -= 22

    # ============================================================
    # PARTE INFERIOR — TENDENCIA DE AHORRO (ancho completo)
    # ============================================================
    Y_TEND_TOP = 210
    c.setStrokeColor(C_AZUL); c.setLineWidth(1)
    c.line(50, Y_TEND_TOP, 560, Y_TEND_TOP)
    c.setFillColor(C_AZUL); c.setFont("Helvetica-Bold", 10)
    c.drawString(50, Y_TEND_TOP - 14, "TENDENCIA DE AHORRO (Últimos 6 meses)")

    meses_lista_h = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    hist_pdf = []; m_idx_ref = meses_lista_h.index(meses[-1])
    for i in range(5, -1, -1):
        idx = m_idx_ref - i; a_h = anio
        if idx < 0: idx += 12; a_h -= 1
        m_n = meses_lista_h[idx]
        i_h = df_i_full[(df_i_full["Periodo"]==m_n) & (df_i_full["Año"]==a_h) & (df_i_full["Usuario"]==u_id)]
        if not i_h.empty:
            g_h  = df_g_full[(df_g_full["Periodo"]==m_n)  & (df_g_full["Año"]==a_h)  & (df_g_full["Usuario"]==u_id)]
            oi_h = df_oi_full[(df_oi_full["Periodo"]==m_n) & (df_oi_full["Año"]==a_h) & (df_oi_full["Usuario"]==u_id)]
            _, _, _, _, bf_h, _ = calcular_metricas(g_h, i_h["Nomina"].iloc[0], oi_h["Monto"].sum() if not oi_h.empty else 0, i_h["SaldoAnterior"].iloc[0])
            hist_pdf.append((f"{m_n[:3]}", bf_h))

    if hist_pdf:
        max_val   = max([abs(v[1]) for v in hist_pdf] + [1])
        BAR_H_MAX = 65
        # ✅ BAR_BASE es la línea del suelo — las barras crecen HACIA ARRIBA desde aquí
        BAR_BASE  = Y_TEND_TOP - 100
        bar_w     = 60
        x_bar     = 80
        # Línea base
        c.setStrokeColor(HexColor("#cccccc")); c.setLineWidth(0.5)
        c.line(60, BAR_BASE, 500, BAR_BASE)
        for m_n, val in hist_pdf:
            h_bar   = max((abs(val) / max_val) * BAR_H_MAX, 3)
            color_b = C_NARANJA if val >= 0 else C_ROJO
            c.setFillColor(color_b)
            # ✅ La barra arranca desde BAR_BASE y sube h_bar puntos
            c.roundRect(x_bar, BAR_BASE, bar_w - 10, h_bar, 3, fill=1, stroke=0)
            # Mes debajo de la línea base
            c.setFillColor(C_NEGRO); c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_bar + (bar_w-10)//2, BAR_BASE - 12, m_n)
            # Valor encima de la barra
            c.setFont("Helvetica", 6)
            c.drawCentredString(x_bar + (bar_w-10)//2, BAR_BASE + h_bar + 3, f"${val:,.0f}")
            x_bar += bar_w

    c.showPage(); c.save(); buf.seek(0)
    return buf

# ============================================================


def generar_excel_reporte(df_g_full, df_i_full, df_oi_full, mes, anio, u_id, nomina, otros, saldo_ant):
    buf = BytesIO()

    # Filtrar datos del mes/año/usuario
    df_g  = df_g_full[(df_g_full["Periodo"]==mes) & (df_g_full["Año"]==anio)].copy()
    df_i  = df_i_full[(df_i_full["Periodo"]==mes) & (df_i_full["Año"]==anio)].copy()
    df_oi = df_oi_full[(df_oi_full["Periodo"]==mes) & (df_oi_full["Año"]==anio)].copy()

    # Calcular métricas
    it, vp, vpy, fact, bf, ahorro_p = calcular_metricas(df_g, nomina, otros, saldo_ant)

    # Traducir TRUE/FALSE → SI/NO
    if not df_g.empty:
        df_g["Pagado"]               = df_g["Pagado"].map({True:"SI", False:"NO"})
        df_g["Movimiento Recurrente"]= df_g["Movimiento Recurrente"].map({True:"SI", False:"NO"})

    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        wb = writer.book

        # ── COLORES Y FORMATOS ──────────────────────────────────
        AZUL    = "#14213d"
        NARANJA = "#fca311"
        GRIS1   = "#f2f2f2"
        GRIS2   = "#ffffff"
        VERDE   = "#2ecc71"
        ROJO    = "#e74c3c"

        def fmt(bg, font_color="#000000", bold=False, num_fmt=None, border=False, align="left"):
            d = {"bg_color": bg, "font_color": font_color, "bold": bold,
                 "valign": "vcenter", "align": align}
            if num_fmt: d["num_format"] = num_fmt
            if border:  d.update({"border": 1, "border_color": "#cccccc"})
            return wb.add_format(d)

        f_title      = fmt(AZUL,    "#ffffff", bold=True,  align="center")
        f_subtitle   = fmt(NARANJA, AZUL,      bold=True,  align="center")
        f_header     = fmt(AZUL,    "#ffffff", bold=True,  border=True, align="center")
        f_row1       = fmt(GRIS1,   "#000000", border=True)
        f_row2       = fmt(GRIS2,   "#000000", border=True)
        f_row1_money = fmt(GRIS1,   "#000000", border=True, num_fmt='$ #,##0', align="right")
        f_row2_money = fmt(GRIS2,   "#000000", border=True, num_fmt='$ #,##0', align="right")
        f_total      = fmt(NARANJA, AZUL,      bold=True,  num_fmt='$ #,##0', border=True, align="right")
        f_total_lbl  = fmt(NARANJA, AZUL,      bold=True,  border=True)
        f_kpi_lbl    = fmt(AZUL,    "#ffffff", bold=True,  align="center")
        f_kpi_val    = fmt(NARANJA, AZUL,      bold=True,  num_fmt='$ #,##0', align="center")
        f_kpi_verde  = fmt(VERDE,   "#ffffff", bold=True,  num_fmt='$ #,##0', align="center")
        f_kpi_rojo   = fmt(ROJO,    "#ffffff", bold=True,  num_fmt='$ #,##0', align="center")
        f_si         = fmt(GRIS1,   VERDE,     bold=True,  border=True, align="center")
        f_no         = fmt(GRIS1,   ROJO,      bold=True,  border=True, align="center")
        f_si2        = fmt(GRIS2,   VERDE,     bold=True,  border=True, align="center")
        f_no2        = fmt(GRIS2,   ROJO,      bold=True,  border=True, align="center")

        nombre_usuario = st.session_state.get("u_nombre_completo", u_id)

        # ══════════════════════════════════════════════════════
        # HOJA 1 — GASTOS
        # ══════════════════════════════════════════════════════
        ws_g = wb.add_worksheet("📋 Gastos")
        writer.sheets["📋 Gastos"] = ws_g
        ws_g.set_zoom(85)
        ws_g.hide_gridlines(2)

        # Anchos de columna
        ws_g.set_column("A:A", 22)
        ws_g.set_column("B:B", 30)
        ws_g.set_column("C:C", 16)
        ws_g.set_column("D:D", 16)
        ws_g.set_column("E:E", 10)
        ws_g.set_column("F:F", 12)

        # Header limpio sin imagen
        ws_g.set_row(0, 28); ws_g.set_row(1, 22)
        ws_g.merge_range("A1:F1", "MY FINANCEAPP — REPORTE DE GASTOS", f_title)
        ws_g.merge_range("A2:F2", f"{mes.upper()} {anio}  |  {nombre_usuario}", f_subtitle)

        # Encabezados tabla
        headers_g = ["CATEGORÍA", "DESCRIPCIÓN", "MONTO", "VALOR REF.", "PAGADO", "RECURRENTE"]
        for col, h in enumerate(headers_g):
            ws_g.write(3, col, h, f_header)
        ws_g.set_row(3, 20)

        # Filas de datos
        for i, (_, row) in enumerate(df_g.iterrows()):
            r = i + 4
            is_odd = i % 2 == 0
            fm      = f_row1       if is_odd else f_row2
            fm_mon  = f_row1_money if is_odd else f_row2_money
            ws_g.set_row(r, 16)

            ws_g.write(r, 0, str(row.get("Categoría","")),    fm)
            ws_g.write(r, 1, str(row.get("Descripción","")),  fm)
            ws_g.write(r, 2, float(row.get("Monto", 0)),      fm_mon)
            ws_g.write(r, 3, float(row.get("Valor Referencia", 0)), fm_mon)

            # Pagado con color
            pag = str(row.get("Pagado","NO"))
            ws_g.write(r, 4, pag, (f_si if is_odd else f_si2) if pag=="SI" else (f_no if is_odd else f_no2))

            rec = str(row.get("Movimiento Recurrente","NO"))
            ws_g.write(r, 5, rec, (f_si if is_odd else f_si2) if rec=="SI" else (f_no if is_odd else f_no2))

        # Fila total
        last = len(df_g) + 4
        ws_g.set_row(last, 20)
        ws_g.merge_range(last, 0, last, 1, "TOTAL GASTOS DEL MES", f_total_lbl)
        ws_g.write(last, 2, float(df_g["Monto"].apply(pd.to_numeric, errors="coerce").fillna(0).sum()), f_total)
        ws_g.write(last, 3, "", f_total)
        ws_g.write(last, 4, "", f_total)
        ws_g.write(last, 5, "", f_total)

        # ══════════════════════════════════════════════════════
        # HOJA 2 — INGRESOS
        # ══════════════════════════════════════════════════════
        ws_i = wb.add_worksheet("💰 Ingresos")
        writer.sheets["💰 Ingresos"] = ws_i
        ws_i.set_zoom(85)
        ws_i.hide_gridlines(2)
        ws_i.set_column("A:A", 30)
        ws_i.set_column("B:B", 20)

        ws_i.set_row(0, 28); ws_i.set_row(1, 22)
        ws_i.merge_range("A1:B1", "MY FINANCEAPP — INGRESOS DEL MES", f_title)
        ws_i.merge_range("A2:B2", f"{mes.upper()} {anio}  |  {nombre_usuario}", f_subtitle)

        ws_i.write(3, 0, "CONCEPTO",  f_header)
        ws_i.write(3, 1, "MONTO",     f_header)
        ws_i.set_row(3, 20)

        ingresos_base = [
            ("Saldo Anterior",  saldo_ant),
            ("Nómina / Ingreso Fijo", nomina),
        ]
        for i, (label, val) in enumerate(ingresos_base):
            r = i + 4
            fm = f_row1 if i % 2 == 0 else f_row2
            fm_m = f_row1_money if i % 2 == 0 else f_row2_money
            ws_i.write(r, 0, label, fm)
            ws_i.write(r, 1, float(val), fm_m)
            ws_i.set_row(r, 16)

        # Otros ingresos
        row_start = 7
        if not df_oi.empty:
            ws_i.merge_range(row_start, 0, row_start, 1, "INGRESOS ADICIONALES", f_header)
            ws_i.set_row(row_start, 18); row_start += 1
            for i, (_, row) in enumerate(df_oi.iterrows()):
                r = row_start + i
                fm = f_row1 if i % 2 == 0 else f_row2
                fm_m = f_row1_money if i % 2 == 0 else f_row2_money
                ws_i.write(r, 0, str(row.get("Descripción","")), fm)
                ws_i.write(r, 1, float(row.get("Monto", 0)),     fm_m)
                ws_i.set_row(r, 16)
            row_start += len(df_oi) + 1
        else:
            row_start += 1

        # Total ingresos
        ws_i.set_row(row_start, 20)
        ws_i.write(row_start, 0, "TOTAL INGRESOS", f_total_lbl)
        ws_i.write(row_start, 1, float(it),         f_total)

        # ══════════════════════════════════════════════════════
        # HOJA 3 — RESUMEN
        # ══════════════════════════════════════════════════════
        ws_r = wb.add_worksheet("📊 Resumen")
        writer.sheets["📊 Resumen"] = ws_r
        ws_r.set_zoom(85)
        ws_r.hide_gridlines(2)
        ws_r.set_column("A:A", 28)
        ws_r.set_column("B:B", 20)
        ws_r.set_column("C:C", 5)
        ws_r.set_column("D:D", 28)
        ws_r.set_column("E:E", 20)

        ws_r.set_row(0, 28); ws_r.set_row(1, 22)
        ws_r.merge_range("A1:E1", "MY FINANCEAPP — RESUMEN FINANCIERO", f_title)
        ws_r.merge_range("A2:E2", f"{mes.upper()} {anio}  |  {nombre_usuario}", f_subtitle)

        # KPIs en 2 columnas
        kpis = [
            ("INGRESOS TOTALES",       it,   f_kpi_val),
            ("OBLIGACIONES PAGADAS",   vp,   f_kpi_verde),
            ("OBLIGACIONES PENDIENTES",vpy,  f_kpi_rojo),
            ("DINERO DISPONIBLE",      fact, f_kpi_val),
            ("SALDO A FAVOR" if bf >= 0 else "DÉFICIT", bf, f_kpi_verde if bf >= 0 else f_kpi_rojo),
            ("EFICIENCIA DE AHORRO",   ahorro_p, fmt(NARANJA, AZUL, bold=True, num_fmt='0.0"%"', align="center")),
        ]

        row = 4
        for i, (label, val, fmt_val) in enumerate(kpis):
            col_l = 0 if i % 2 == 0 else 3
            col_v = 1 if i % 2 == 0 else 4
            if i % 2 == 0 and i > 0: row += 3
            ws_r.set_row(row,   18)
            ws_r.set_row(row+1, 22)
            ws_r.write(row,   col_l, label, f_kpi_lbl)
            ws_r.write(row,   col_v, "",    f_kpi_lbl)
            ws_r.write(row+1, col_l, "",    fmt_val)
            ws_r.write(row+1, col_v, val,   fmt_val)

        # Tabla resumen categorías
        row_cat = row + 6
        ws_r.merge_range(row_cat, 0, row_cat, 4, "DESGLOSE POR CATEGORÍA", f_header)
        ws_r.set_row(row_cat, 20); row_cat += 1

        ws_r.write(row_cat, 0, "CATEGORÍA",  f_header)
        ws_r.write(row_cat, 1, "MONTO",      f_header)
        ws_r.write(row_cat, 2, "%",          f_header)
        ws_r.write(row_cat, 3, "PAGADO",     f_header)
        ws_r.write(row_cat, 4, "PENDIENTE",  f_header)
        ws_r.set_row(row_cat, 18); row_cat += 1

        if not df_g.empty:
            df_g_num = df_g_full[(df_g_full["Periodo"]==mes) & (df_g_full["Año"]==anio)].copy()
            df_g_num["Monto"] = pd.to_numeric(df_g_num["Monto"], errors="coerce").fillna(0)
            df_g_num["Pagado"] = df_g_num["Pagado"].astype(bool) if df_g_num["Pagado"].dtype != bool else df_g_num["Pagado"]
            total_g = df_g_num["Monto"].sum()
            cat_res = df_g_num.groupby("Categoría").agg(
                Monto=("Monto","sum"),
                Pagado=("Monto", lambda x: x[df_g_num.loc[x.index,"Pagado"]==True].sum()),
            ).reset_index()
            cat_res["Pendiente"] = cat_res["Monto"] - cat_res["Pagado"]
            cat_res["Pct"] = cat_res["Monto"] / total_g * 100 if total_g > 0 else 0
            cat_res = cat_res.sort_values("Monto", ascending=False)

            f_pct = wb.add_format({"num_format": "0.0%", "align":"center", "border":1,
                                   "border_color":"#cccccc", "valign":"vcenter"})
            for i, (_, row_d) in enumerate(cat_res.iterrows()):
                r = row_cat + i
                fm = f_row1 if i % 2 == 0 else f_row2
                fm_m = f_row1_money if i % 2 == 0 else f_row2_money
                ws_r.set_row(r, 16)
                ws_r.write(r, 0, str(row_d["Categoría"]),     fm)
                ws_r.write(r, 1, float(row_d["Monto"]),       fm_m)
                ws_r.write(r, 2, float(row_d["Pct"]/100),     f_pct)
                ws_r.write(r, 3, float(row_d["Pagado"]),      fm_m)
                ws_r.write(r, 4, float(row_d["Pendiente"]),   fm_m)

            # Total categorías
            last_cat = row_cat + len(cat_res)
            ws_r.set_row(last_cat, 20)
            ws_r.write(last_cat, 0, "TOTAL", f_total_lbl)
            ws_r.write(last_cat, 1, float(total_g), f_total)
            ws_r.write(last_cat, 2, "",  f_total)
            ws_r.write(last_cat, 3, float(vp),  f_total)
            ws_r.write(last_cat, 4, float(vpy), f_total)

    buf.seek(0)
    return buf.getvalue()


