"""Póster editorial de una pantalla, parametrizado por JSON.

Uso: python build_editorial_poster.py configs/geonorm_editorial.json
El texto y las rutas de evidencia se leen íntegramente desde el JSON.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

W,H,DPI=1080,1920,144
NAVY="092D45"; BLUE="126C8F"; TURQ="35B9BF"; GOLD="F2B950"; PAPER="F4F1EA"; INK="18232B"; WHITE="FFFFFF"; GREY="5F6B72"
def I(px): return Inches(px/DPI)
def C(h): return RGBColor.from_string(h)
def rect(s,x,y,w,h,fill,line=None,round=False):
    z=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if round else MSO_SHAPE.RECTANGLE,I(x),I(y),I(w),I(h));z.fill.solid();z.fill.fore_color.rgb=C(fill);z.line.color.rgb=C(line or fill);return z
def text(s,value,x,y,w,h,size=14,color=INK,bold=False,align=PP_ALIGN.LEFT,margin=0):
    b=s.shapes.add_textbox(I(x),I(y),I(w),I(h));t=b.text_frame;t.clear();t.word_wrap=True;t.margin_left=t.margin_right=t.margin_top=t.margin_bottom=I(margin)
    p=t.paragraphs[0];p.text=value;p.alignment=align
    for r in p.runs:r.font.name="Arial";r.font.size=Pt(size);r.font.bold=bold;r.font.color.rgb=C(color)
    return b
def fit_image(s,path,x,y,w,h):
    p=Path(path)
    if not p.exists():
        rect(s,x,y,w,h,WHITE,TURQ,True);text(s,"EVIDENCIA\nPENDIENTE",x,y+40,w,h-80,14,GOLD,True,PP_ALIGN.CENTER);return
    with Image.open(p) as im: iw,ih=im.size
    scale=min(w/iw,h/ih); dw,dh=iw*scale,ih*scale
    # Preserve the complete scientific figure without distortion.
    pic=s.shapes.add_picture(str(p),I(x+(w-dw)/2),I(y+(h-dh)/2),I(dw),I(dh))
    return pic
def label(s,value,x,y,w): text(s,value.upper(),x,y,w,26,12,TURQ,True)
def metric(s,value,label,x,y):
    rect(s,x,y,135,88,NAVY,NAVY,True);text(s,value,x+8,y+13,119,32,20,WHITE,True,PP_ALIGN.CENTER);text(s,label,x+8,y+52,119,21,12,WHITE,False,PP_ALIGN.CENTER)
def bullet_list(s,items,x,y,w,line_h=49):
    for i,item in enumerate(items):
        rect(s,x,y+i*line_h+7,10,10,GOLD,GOLD,True);text(s,item,x+26,y+i*line_h,w-26,line_h,14,INK)
def main(path):
    cfg=json.loads(Path(path).read_text(encoding="utf-8")); p=cfg["poster"]
    prs=Presentation();prs.slide_width=I(W);prs.slide_height=I(H);s=prs.slides.add_slide(prs.slide_layouts[6]);rect(s,0,0,W,H,PAPER)
    # Hero
    rect(s,0,0,W,480,NAVY);rect(s,0,464,W,16,GOLD);text(s,p["event"],60,48,650,25,12,TURQ,True);text(s,p["title"],60,95,610,160,21,WHITE,True);text(s,p["authors"],60,282,600,25,14,WHITE,True);text(s,p["affiliation"],60,315,600,42,12,"D6E5EA")
    rect(s,735,55,135,52,WHITE,WHITE,True);text(s,"LOGO\nUNI",748,62,110,37,12,NAVY,True,PP_ALIGN.CENTER);rect(s,885,55,135,52,WHITE,WHITE,True);text(s,"LOGO\nSGP/CPG",895,62,115,37,12,NAVY,True,PP_ALIGN.CENTER)
    rect(s,720,155,300,245,BLUE,BLUE,True);fit_image(s,p["hero_visual"],735,170,270,215)
    for i,m in enumerate(p["hero_metrics"]):metric(s,m["value"],m["label"],60+i*155,382)
    # Context and method
    label(s,"Reto y propuesta",60,525,300);text(s,p["intro"],60,558,400,176,14,INK);label(s,"Método reproducible",510,525,420)
    for i,step in enumerate(p["method_steps"]):
        x=510+i*132;rect(s,x,570,112,126,WHITE,"D5DBDC",True);text(s,f"0{i+1}",x+16,588,80,20,12,BLUE,True);text(s,step,x+13,620,86,51,12,NAVY,True,PP_ALIGN.CENTER)
        if i<3:text(s,"→",x+111,616,22,26,16,GOLD,True,PP_ALIGN.CENTER)
    text(s,p["method_note"],510,720,500,40,12,GREY)
    # Results zone
    rect(s,0,825,W,665,"E7EEF0");label(s,"Resultados: evidencia que sostiene la propuesta",60,860,750)
    text(s,p["results_intro"],60,895,960,46,14,INK)
    for i,r in enumerate(p["results"]):
        x=60+i*490;rect(s,x,970,460,430,WHITE,WHITE,True);rect(s,x,970,460,44,BLUE,BLUE,True);text(s,r["domain"],x+18,982,400,22,12,WHITE,True);metric(s,r["metrics"][0]["value"],r["metrics"][0]["label"],x+22,1033);metric(s,r["metrics"][1]["value"],r["metrics"][1]["label"],x+172,1033);metric(s,r["metrics"][2]["value"],r["metrics"][2]["label"],x+322,1033);fit_image(s,r["visual"],x+22,1140,225,180);text(s,r["finding"],x+270,1160,150,90,13,INK,True);text(s,r["caption"],x+22,1330,415,42,12,GREY)
    # impact + conclusion
    label(s,"Aplicabilidad y conclusiones",60,1540,460);text(s,p["deploy"],60,1580,435,55,14,NAVY,True);bullet_list(s,p["conclusions"],60,1660,440,45)
    rect(s,550,1540,470,300,NAVY,NAVY,True);text(s,p["closing_title"],582,1570,400,60,17,WHITE,True);text(s,p["closing_text"],582,1645,390,90,12,"D6E5EA");text(s,p["contact"],582,1780,390,25,12,TURQ,True)
    rect(s,60,1873,960,2,TURQ);text(s,p["footer"],60,1889,960,18,12,GREY)
    out=Path(path).with_suffix(".pptx");prs.save(out);print(out)
if __name__=="__main__":main(sys.argv[1])
