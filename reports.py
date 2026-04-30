"""
reports.py — Generación de reportes PDF y Excel
Funciones pequeñas y bien separadas por responsabilidad.
"""
import os
import math
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
import pytz
from data import calcular_metricas

LOGO_APP_H = "LOGOapp horizontal.png"
COLOR_MAP = {
    "Hogar": "#fca311", "Servicios": "#77B5FE", "Alimentación": "#77DD77",
    "Transporte": "#FF6961", "Gasto Vehiculos": "#FDFD96",
    "Obligaciones Financieras": "#84b6f4", "Salud": "#fdcae1",
    "Educación": "#B39EB5", "Cuidado Personal": "#FFD1DC",
    "Mascotas": "#CFCFCF", "Viajes y Recreación": "#AEC6CF",
    "Servicios de Streaming": "#cfcfc4", "Seguros": "#836953",
    "Ahorro e Inversión": "#d4af37", "Impuestos": "#ffda9e", "Otros": "#b2e2f2"
}

def _C():
    from reportlab.lib.colors import HexColor
    return {"az":HexColor("#14213d"),"na":HexColor("#fca311"),
            "gr":HexColor("#e5e5e5"),"ne":HexColor("#000000"),
            "ve":HexColor("#2ecc71"),"ro":HexColor("#e74c3c")}

def _head(c, t, a, u):
    from reportlab.lib import colors
    C=_C()
    c.setFillColor(colors.white); c.rect(0,0,612,792,fill=1)
    if os.path.exists(LOGO_APP_H):
        c.drawImage(LOGO_APP_H,55,670,width=500,height=100,preserveAspectRatio=True,anchor='c')
    c.setFont("Helvetica-BoldOblique",9); c.setFillColor(C["az"])
    c.drawString(50,650,f"Usuario: {u}"); c.drawRightString(560,650,f"{t} {a}")
    c.setStrokeColor(C["na"]); c.setLineWidth(2); c.line(50,645,560,645)
    tz=pytz.timezone('America/Bogota')
    c.setFont("Helvetica",7); c.setFillColor(colors.grey)
    c.drawString(50,30,f"Documento generado el: {datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')}")
    return 620

def _mes_header(c,m,it,vp,vpy,bf,y,t,a,u):
    C=_C()
    if y<250: c.showPage(); y=_head(c,t,a,u)
    c.setFillColor(C["gr"]); c.rect(50,y-55,510,60,fill=1,stroke=0)
    c.setFillColor(C["az"]); c.setFont("Helvetica-Bold",11); c.drawString(60,y-15,f"MES: {m}")
    c.setFont("Helvetica",9)
    c.drawString(60,y-30,f"Ingresos: $ {it:,.0f} | Pagadas: $ {vp:,.0f} | Pendientes: $ {vpy:,.0f}")
    c.setFillColor(C["na"]); c.setFont("Helvetica-Bold",9)
    c.drawString(60,y-45,f"SALDO A FAVOR FINAL: $ {bf:,.0f}")
    return y-80

def _ingresos(c,y,s,n,oi,os_,t,a,u):
    from reportlab.lib import colors
    C=_C()
    c.setFont("Helvetica-Bold",9); c.setFillColor(C["az"]); c.drawString(60,y,"RELACIÓN DE INGRESOS"); y-=15
    c.setFont("Helvetica",8); c.setFillColor(C["ne"])
    c.drawString(60,y,"Saldo Anterior"); c.drawRightString(480,y,f"$ {s:,.0f}"); y-=10
    c.drawString(60,y,"Nómina"); c.drawRightString(480,y,f"$ {n:,.0f}"); y-=5
    if not oi.empty:
        c.setStrokeColor(colors.lightgrey); c.line(60,y,480,y); y-=12
        c.setFont("Helvetica-BoldOblique",7); c.setFillColor(colors.darkgrey)
        c.drawString(60,y,"Ingresos Variables"); y-=10
        for _,r in oi.iterrows():
            c.setFont("Helvetica",8); c.setFillColor(C["ne"])
            c.drawString(65,y,f"● {r['Descripción']}"); c.drawRightString(480,y,f"$ {r['Monto']:,.0f}"); y-=10
        c.setFont("Helvetica-Bold",8); c.line(60,y+5,480,y+5)
        c.drawRightString(480,y-5,f"Total Otros Ingresos: $ {os_:,.0f}"); y-=25
    else: y-=15
    return y

def _gastos(c,y,gm,t,a,u):
    C=_C()
    c.setFillColor(C["az"]); c.setFont("Helvetica-Bold",9); c.drawString(60,y,"RELACIÓN DE GASTOS"); y-=15
    c.setFont("Helvetica-Bold",8)
    c.drawString(60,y,"CATEGORÍA - DESCRIPCIÓN"); c.drawRightString(490,y,"MONTO"); c.drawRightString(545,y,"PAGADO"); y-=12
    c.setStrokeColor(C["gr"]); c.setLineWidth(0.5); c.line(60,y+8,545,y+8)
    c.setFont("Helvetica",8); c.setFillColor(C["ne"]); total=0
    for _,row in gm.iterrows():
        if y<80: c.showPage(); y=_head(c,t,a,u); c.setFont("Helvetica",8)
        m=float(row['Monto'])
        if bool(row.get("Pagado",False)): total+=m
        c.drawString(60,y,f"{row['Categoría']} - {row['Descripción']}"[:65])
        c.drawRightString(490,y,f"$ {m:,.0f}"); c.drawRightString(545,y,"SI" if row["Pagado"] else "NO"); y-=12
    c.setStrokeColor(C["az"]); c.setLineWidth(1); c.line(60,y+8,545,y+8)
    c.setFillColor(C["az"]); c.setFont("Helvetica-Bold",9)
    c.drawString(60,y-2,"TOTAL GASTOS PAGADOS:"); c.drawRightString(490,y-2,f"$ {total:,.0f}")
    return y-25, total

def _resumen_periodo(c,y,titulo,nom,otr,gas):
    C=_C()
    if y<150: c.showPage(); y=620
    y-=20
    c.setFillColor(C["na"]); c.setStrokeColor(C["az"]); c.setLineWidth(2)
    c.rect(50,y-100,510,110,fill=1,stroke=1)
    c.setFillColor(C["az"]); c.setFont("Helvetica-Bold",12); c.drawString(70,y-5,f"RESUMEN: {titulo.upper()}")
    saldo=nom+otr-gas
    c.setFont("Helvetica",10)
    c.drawString(70,y-25,f"Total Nómina Percibida:       $ {nom:,.0f}")
    c.drawString(70,y-40,f"Total Ingresos Adicionales:   $ {otr:,.0f}")
    c.drawString(70,y-55,f"Total Gastos del Periodo:     $ {gas:,.0f}")
    c.setFont("Helvetica-Bold",12); c.drawString(70,y-85,f"SALDO TOTAL AL CIERRE: $ {abs(saldo):,.0f}")
    return y-150

def _draw_arc(c,cx,cy,ro,ri,a0,a1,col):
    steps=max(int(abs(a1-a0)/2),1)
    po,pi=[],[]
    for i in range(steps+1):
        ang=math.radians(a0+(a1-a0)*i/steps)
        po.append((cx+ro*math.cos(ang),cy+ro*math.sin(ang)))
        pi.append((cx+ri*math.cos(ang),cy+ri*math.sin(ang)))
    path=c.beginPath(); path.moveTo(*po[0])
    for pt in po[1:]: path.lineTo(*pt)
    for pt in reversed(pi): path.lineTo(*pt)
    path.close(); c.setFillColor(col); c.drawPath(path,fill=1,stroke=0)

def _pagina_visual(c,t,a,u,ugm,uap,uvp,uvpy,ubf,dg,di,doi,meses,uid):
    from reportlab.lib.colors import HexColor
    C=_C()
    c.showPage(); y=_head(c,t,a,u)
    c.setFillColor(C["az"]); c.setFont("Helvetica-Bold",13); c.drawString(50,y,"ANÁLISIS VISUAL DEL MES"); y-=8
    c.setStrokeColor(C["na"]); c.setLineWidth(2); c.line(50,y,560,y)
    TOP=y-20; BX=50; BW=170; RH=17; C2=330
    c.setFillColor(C["az"]); c.setFont("Helvetica-Bold",9); c.drawString(BX,TOP,"DESGLOSE POR CATEGORÍA")
    yc=TOP-16
    if ugm is not None and not ugm.empty:
        tp=ugm.copy()
        tp['V']=tp.apply(lambda r:r['Monto'] if r['Pagado'] else r['Valor Referencia'],axis=1)
        tv=tp['V'].sum()
        if tv>0:
            rc=tp.groupby("Categoría")['V'].sum().reset_index()
            rc['pct']=rc['V']/tv*100; rc=rc.sort_values('V',ascending=False)
            for _,r in rc.iterrows():
                if yc<220: break
                ch=COLOR_MAP.get(r['Categoría'],"#6c757d"); p=r['pct']; m=r['V']
                bl=max((p/100)*BW,3)
                c.setFillColor(HexColor("#e0e0e0")); c.roundRect(BX,yc-RH+5,BW,RH-7,3,fill=1,stroke=0)
                c.setFillColor(HexColor(ch)); c.roundRect(BX,yc-RH+5,bl,RH-7,3,fill=1,stroke=0)
                c.setFillColor(C["ne"]); c.setFont("Helvetica-Bold",6); c.drawString(BX+3,yc-8,r['Categoría'][:18])
                c.setFont("Helvetica",6); c.drawString(BX+BW+4,yc-8,f"${m:,.0f}  {p:.1f}%")
                yc-=RH
    META=20; vcl=max(0,min(uap,100)); CX=C2+100; CY=TOP-75; RO=65; RI=46
    c.setFillColor(C["az"]); c.setFont("Helvetica-Bold",9); c.drawCentredString(CX,TOP,"EFICIENCIA DE AHORRO")
    am=180-(META/100*180)
    _draw_arc(c,CX,CY,RO,RI,am,180,HexColor("#f8d7da"))
    _draw_arc(c,CX,CY,RO,RI,0,am,HexColor("#d4edda"))
    _draw_arc(c,CX,CY,RO,RI,180-(vcl/100*180),180,HexColor("#fca311"))
    amr=math.radians(am); c.setStrokeColor(C["ve"]); c.setLineWidth(2)
    c.line(CX+RI*math.cos(amr),CY+RI*math.sin(amr),CX+(RO+6)*math.cos(amr),CY+(RO+6)*math.sin(amr))
    c.setFillColor(C["na"]); c.setFont("Helvetica-Bold",18); c.drawCentredString(CX,CY-12,f"{vcl:.0f}%")
    c.setFont("Helvetica",7); c.setFillColor(C["ne"]); c.drawCentredString(CX,CY-24,f"Meta: {META}%")
    if vcl>=META: c.setFillColor(C["ve"]); c.setFont("Helvetica-Bold",8); c.drawCentredString(CX,CY-36,"¡Meta alcanzada!")
    else: c.setFillColor(C["ro"]); c.setFont("Helvetica-Bold",8); c.drawCentredString(CX,CY-36,f"Falta {META-vcl:.0f}% para la meta")
    ye=CY-60; c.setFillColor(C["az"]); c.setFont("Helvetica-Bold",9); c.drawCentredString(CX,ye,"ESTADO REAL DEL DINERO"); ye-=14
    te=uvp+uvpy+max(ubf,0)
    if te>0:
        for lb,vl,hc in [("Oblig. Pagadas",uvp,"#2ecc71"),("Oblig. Pendient",uvpy,"#e74c3c"),("Saldo a Favor",max(ubf,0),"#fca311")]:
            pe=(vl/te*100) if te>0 else 0; be=max((pe/100)*190,2)
            c.setFillColor(HexColor("#e0e0e0")); c.roundRect(C2,ye-13,190,13,3,fill=1,stroke=0)
            c.setFillColor(HexColor(hc)); c.roundRect(C2,ye-13,be,13,3,fill=1,stroke=0)
            c.setFillColor(C["ne"]); c.setFont("Helvetica-Bold",7); c.drawString(C2+3,ye-10,lb)
            c.setFont("Helvetica",7); c.drawRightString(C2+187,ye-10,f"$ {vl:,.0f} ({pe:.1f}%)"); ye-=22
    YT=210; c.setStrokeColor(C["az"]); c.setLineWidth(1); c.line(50,YT,560,YT)
    c.setFillColor(C["az"]); c.setFont("Helvetica-Bold",10); c.drawString(50,YT-14,"TENDENCIA DE AHORRO (Últimos 6 meses)")
    mh=["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    hist=[]; ref=mh.index(meses[-1])
    for i in range(5,-1,-1):
        idx=ref-i; ah=a
        if idx<0: idx+=12; ah-=1
        mn=mh[idx]
        ih=di[(di["Periodo"]==mn)&(di["Año"]==ah)&(di["Usuario"]==uid)]
        if not ih.empty:
            gh=dg[(dg["Periodo"]==mn)&(dg["Año"]==ah)&(dg["Usuario"]==uid)]
            oh=doi[(doi["Periodo"]==mn)&(doi["Año"]==ah)&(doi["Usuario"]==uid)]
            _,_,_,_,bfh,_=calcular_metricas(gh,ih["Nomina"].iloc[0],oh["Monto"].sum() if not oh.empty else 0,ih["SaldoAnterior"].iloc[0])
            hist.append((mn[:3],bfh))
    if hist:
        mv=max([abs(v[1]) for v in hist]+[1]); BASE=YT-100; bw=60; xb=80
        c.setStrokeColor(HexColor("#cccccc")); c.setLineWidth(0.5); c.line(60,BASE,500,BASE)
        for mn,val in hist:
            hb=max((abs(val)/mv)*65,3); cb=C["na"] if val>=0 else C["ro"]
            c.setFillColor(cb); c.roundRect(xb,BASE,bw-10,hb,3,fill=1,stroke=0)
            c.setFillColor(C["ne"]); c.setFont("Helvetica-Bold",7); c.drawCentredString(xb+(bw-10)//2,BASE-12,mn)
            c.setFont("Helvetica",6); c.drawCentredString(xb+(bw-10)//2,BASE+hb+3,f"${val:,.0f}")
            xb+=bw

# ── FUNCIÓN PRINCIPAL PDF ─────────────────────────────────────
def generar_pdf_reporte(df_g_full,df_i_full,df_oi_full,meses,titulo,anio,u_id):
    from reportlab.pdfgen import canvas
    u=st.session_state.get("u_nombre_completo",u_id)
    buf=BytesIO(); c=canvas.Canvas(buf,pagesize=(612,792))
    y=_head(c,titulo,anio,u)
    tn=to=tg=0; ugm=None; uit=uvp=uvpy=ubf=uap=0
    for m in meses:
        im=df_i_full[(df_i_full["Periodo"]==m)&(df_i_full["Año"]==anio)&(df_i_full["Usuario"]==u_id)]
        gm=df_g_full[(df_g_full["Periodo"]==m)&(df_g_full["Año"]==anio)&(df_g_full["Usuario"]==u_id)]
        om=df_oi_full[(df_oi_full["Periodo"]==m)&(df_oi_full["Año"]==anio)&(df_oi_full["Usuario"]==u_id)]
        s=float(im["SaldoAnterior"].iloc[0]) if not im.empty else 0
        n=float(im["Nomina"].iloc[0]) if not im.empty else 0
        os_=float(om["Monto"].sum()) if not om.empty else 0
        it,vp,vpy,_,bf,ap=calcular_metricas(gm,n,os_,s)
        tn+=n; to+=os_; tg+=(vp+vpy)
        ugm=gm; uvp=vp; uvpy=vpy; ubf=bf; uap=ap
        y=_mes_header(c,m,it,vp,vpy,bf,y,titulo,anio,u)
        y=_ingresos(c,y,s,n,om,os_,titulo,anio,u)
        y,_=_gastos(c,y,gm,titulo,anio,u)
    if len(meses)>1: y=_resumen_periodo(c,y,titulo,tn,to,tg)
    _pagina_visual(c,titulo,anio,u,ugm,uap,uvp,uvpy,ubf,df_g_full,df_i_full,df_oi_full,meses,u_id)
    c.save(); buf.seek(0)
    return buf

# ── HELPERS EXCEL ─────────────────────────────────────────────
def _xfmt(wb,bg,fc="#000000",bold=False,nf=None,brd=False,al="left"):
    d={"bg_color":bg,"font_color":fc,"bold":bold,"valign":"vcenter","align":al}
    if nf: d["num_format"]=nf
    if brd: d.update({"border":1,"border_color":"#cccccc"})
    return wb.add_format(d)

def _xfmts(wb):
    AZ="#14213d"; NA="#fca311"; G1="#f2f2f2"; G2="#ffffff"
    f=_xfmt
    return {
        "ti":f(wb,AZ,"#ffffff",True,al="center"),
        "su":f(wb,NA,AZ,True,al="center"),
        "hd":f(wb,AZ,"#ffffff",True,brd=True,al="center"),
        "r1":f(wb,G1,brd=True), "r2":f(wb,G2,brd=True),
        "r1m":f(wb,G1,nf='$ #,##0',brd=True,al="right"),
        "r2m":f(wb,G2,nf='$ #,##0',brd=True,al="right"),
        "to":f(wb,NA,AZ,True,nf='$ #,##0',brd=True,al="right"),
        "tl":f(wb,NA,AZ,True,brd=True),
        "kl":f(wb,AZ,"#ffffff",True,al="center"),
        "kv":f(wb,NA,AZ,True,nf='$ #,##0',al="center"),
        "ko":f(wb,"#2ecc71","#ffffff",True,nf='$ #,##0',al="center"),
        "ke":f(wb,"#e74c3c","#ffffff",True,nf='$ #,##0',al="center"),
        "si":(f(wb,G1,"#2ecc71",True,brd=True,al="center"),f(wb,G2,"#2ecc71",True,brd=True,al="center")),
        "no":(f(wb,G1,"#e74c3c",True,brd=True,al="center"),f(wb,G2,"#e74c3c",True,brd=True,al="center")),
        "pc":wb.add_format({"num_format":"0.0%","align":"center","border":1,"border_color":"#cccccc","valign":"vcenter"}),
    }

# ── FUNCIÓN PRINCIPAL EXCEL ───────────────────────────────────
def generar_excel_reporte(df_g_full,df_i_full,df_oi_full,mes,anio,u_id,nomina,otros,saldo_ant):
    buf=BytesIO()
    dg=df_g_full[(df_g_full["Periodo"]==mes)&(df_g_full["Año"]==anio)].copy()
    di=df_i_full[(df_i_full["Periodo"]==mes)&(df_i_full["Año"]==anio)].copy()
    do=df_oi_full[(df_oi_full["Periodo"]==mes)&(df_oi_full["Año"]==anio)].copy()
    it,vp,vpy,fact,bf,ap=calcular_metricas(dg,nomina,otros,saldo_ant)
    nu=st.session_state.get("u_nombre_completo",u_id)
    with pd.ExcelWriter(buf,engine="xlsxwriter") as wr:
        wb=wr.book; F=_xfmts(wb)
        # ── Gastos ──
        wg=wb.add_worksheet("📋 Gastos"); wr.sheets["📋 Gastos"]=wg
        wg.set_zoom(85); wg.hide_gridlines(2)
        for col,w in [("A:A",22),("B:B",30),("C:C",16),("D:D",16),("E:E",10),("F:F",12)]: wg.set_column(col,w)
        wg.set_row(0,28); wg.set_row(1,22)
        wg.merge_range("A1:F1","MY FINANCEAPP — REPORTE DE GASTOS",F["ti"])
        wg.merge_range("A2:F2",f"{mes.upper()} {anio}  |  {nu}",F["su"])
        for ci,h in enumerate(["CATEGORÍA","DESCRIPCIÓN","MONTO","VALOR REF.","PAGADO","RECURRENTE"]):
            wg.write(3,ci,h,F["hd"])
        wg.set_row(3,20)
        dg2=dg.copy()
        if not dg2.empty:
            dg2["Pagado"]=dg2["Pagado"].map({True:"SI",False:"NO"})
            dg2["Movimiento Recurrente"]=dg2["Movimiento Recurrente"].map({True:"SI",False:"NO"})
        total=0
        for i,(_, row) in enumerate(dg2.iterrows()):
            r=i+4; odd=i%2==0
            fm=F["r1"] if odd else F["r2"]; fm_m=F["r1m"] if odd else F["r2m"]
            wg.set_row(r,16); wg.write(r,0,str(row.get("Categoría","")),fm)
            wg.write(r,1,str(row.get("Descripción","")),fm)
            m=float(row.get("Monto",0) or 0); wg.write(r,2,m,fm_m); total+=m
            wg.write(r,3,float(row.get("Valor Referencia",0) or 0),fm_m)
            p=str(row.get("Pagado","NO")); rc=str(row.get("Movimiento Recurrente","NO"))
            wg.write(r,4,p,(F["si"][0] if odd else F["si"][1]) if p=="SI" else (F["no"][0] if odd else F["no"][1]))
            wg.write(r,5,rc,(F["si"][0] if odd else F["si"][1]) if rc=="SI" else (F["no"][0] if odd else F["no"][1]))
        last=len(dg2)+4; wg.set_row(last,20)
        wg.merge_range(last,0,last,1,"TOTAL GASTOS DEL MES",F["tl"]); wg.write(last,2,total,F["to"])
        for ci in [3,4,5]: wg.write(last,ci,"",F["to"])
        # ── Ingresos ──
        wi=wb.add_worksheet("💰 Ingresos"); wr.sheets["💰 Ingresos"]=wi
        wi.set_zoom(85); wi.hide_gridlines(2); wi.set_column("A:A",30); wi.set_column("B:B",20)
        wi.set_row(0,28); wi.set_row(1,22)
        wi.merge_range("A1:B1","MY FINANCEAPP — INGRESOS DEL MES",F["ti"])
        wi.merge_range("A2:B2",f"{mes.upper()} {anio}  |  {nu}",F["su"])
        wi.write(3,0,"CONCEPTO",F["hd"]); wi.write(3,1,"MONTO",F["hd"]); wi.set_row(3,20)
        for i,(lb,vl) in enumerate([("Saldo Anterior",saldo_ant),("Nómina / Ingreso Fijo",nomina)]):
            r=i+4; fm=F["r1"] if i%2==0 else F["r2"]; fm_m=F["r1m"] if i%2==0 else F["r2m"]
            wi.write(r,0,lb,fm); wi.write(r,1,float(vl),fm_m); wi.set_row(r,16)
        rs=7
        if not do.empty:
            wi.merge_range(rs,0,rs,1,"INGRESOS ADICIONALES",F["hd"]); wi.set_row(rs,18); rs+=1
            for i,(_,row) in enumerate(do.iterrows()):
                r=rs+i; fm=F["r1"] if i%2==0 else F["r2"]; fm_m=F["r1m"] if i%2==0 else F["r2m"]
                wi.write(r,0,str(row.get("Descripción","")),fm); wi.write(r,1,float(row.get("Monto",0)),fm_m); wi.set_row(r,16)
            rs+=len(do)+1
        else: rs+=1
        wi.set_row(rs,20); wi.write(rs,0,"TOTAL INGRESOS",F["tl"]); wi.write(rs,1,float(it),F["to"])
        # ── Resumen ──
        wr_=wb.add_worksheet("📊 Resumen"); wr.sheets["📊 Resumen"]=wr_
        wr_.set_zoom(85); wr_.hide_gridlines(2)
        for col,w in [("A:A",28),("B:B",20),("C:C",5),("D:D",28),("E:E",20)]: wr_.set_column(col,w)
        wr_.set_row(0,28); wr_.set_row(1,22)
        wr_.merge_range("A1:E1","MY FINANCEAPP — RESUMEN FINANCIERO",F["ti"])
        wr_.merge_range("A2:E2",f"{mes.upper()} {anio}  |  {nu}",F["su"])
        kpis=[("INGRESOS TOTALES",it,F["kv"]),("OBLIGACIONES PAGADAS",vp,F["ko"]),
              ("OBLIGACIONES PENDIENTES",vpy,F["ke"]),("DINERO DISPONIBLE",fact,F["kv"]),
              ("SALDO A FAVOR" if bf>=0 else "DÉFICIT",bf,F["ko"] if bf>=0 else F["ke"]),
              ("EFICIENCIA DE AHORRO",ap,wb.add_format({"bg_color":"#fca311","font_color":"#14213d","bold":True,"num_format":'0.0"%"',"align":"center"}))]
        row=4
        for i,(lb,vl,fv) in enumerate(kpis):
            cl=0 if i%2==0 else 3; cv=1 if i%2==0 else 4
            if i%2==0 and i>0: row+=3
            wr_.set_row(row,18); wr_.set_row(row+1,22)
            wr_.write(row,cl,lb,F["kl"]); wr_.write(row,cv,"",F["kl"])
            wr_.write(row+1,cl,"",fv); wr_.write(row+1,cv,vl,fv)
        rc=row+6
        wr_.merge_range(rc,0,rc,4,"DESGLOSE POR CATEGORÍA",F["hd"]); wr_.set_row(rc,20); rc+=1
        for ci,h in enumerate(["CATEGORÍA","MONTO","%","PAGADO","PENDIENTE"]): wr_.write(rc,ci,h,F["hd"])
        wr_.set_row(rc,18); rc+=1
        dgn=dg.copy()
        dgn["Monto"]=pd.to_numeric(dgn["Monto"],errors="coerce").fillna(0)
        dgn["Pagado"]=dgn["Pagado"].astype(bool) if "Pagado" in dgn.columns else False
        if not dgn.empty:
            tg=dgn["Monto"].sum()
            cr=dgn.groupby("Categoría").agg(Monto=("Monto","sum"),Pagado=("Monto",lambda x:x[dgn.loc[x.index,"Pagado"]==True].sum())).reset_index()
            cr["Pendiente"]=cr["Monto"]-cr["Pagado"]; cr["Pct"]=cr["Monto"]/tg*100 if tg>0 else 0
            cr=cr.sort_values("Monto",ascending=False)
            for i,(_,rd) in enumerate(cr.iterrows()):
                r=rc+i; odd=i%2==0; fm=F["r1"] if odd else F["r2"]; fm_m=F["r1m"] if odd else F["r2m"]
                wr_.set_row(r,16); wr_.write(r,0,str(rd["Categoría"]),fm); wr_.write(r,1,float(rd["Monto"]),fm_m)
                wr_.write(r,2,float(rd["Pct"]/100),F["pc"]); wr_.write(r,3,float(rd["Pagado"]),fm_m); wr_.write(r,4,float(rd["Pendiente"]),fm_m)
            lc=rc+len(cr); wr_.set_row(lc,20); wr_.write(lc,0,"TOTAL",F["tl"]); wr_.write(lc,1,float(tg),F["to"])
            wr_.write(lc,2,"",F["to"]); wr_.write(lc,3,float(vp),F["to"]); wr_.write(lc,4,float(vpy),F["to"])
    buf.seek(0)
    return buf.getvalue()
