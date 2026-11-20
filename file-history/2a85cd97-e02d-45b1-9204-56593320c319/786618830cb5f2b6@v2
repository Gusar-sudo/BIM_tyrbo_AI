"""Позиции текстов/выносок DXF, содержащих шаблон. py dxf_find_texts.py <dxf> <regex>"""
import re, sys, ezdxf
sys.stdout.reconfigure(encoding="utf-8")
doc = ezdxf.readfile(sys.argv[1]); rx = re.compile(sys.argv[2])
for e in doc.modelspace():
    t = e.dxftype(); s = None; p = None
    if t in ("TEXT", "MTEXT"):
        s = e.plain_text() if t == "MTEXT" else e.dxf.text; p = e.dxf.insert
    elif t == "MULTILEADER":
        try:
            ctx = e.context
            s = ctx.mtext.default_content if ctx.mtext else ""
            p = ctx.mtext.insert if ctx.mtext else None
            arrows = [(round(l.vertices[0].x, 1), round(l.vertices[0].y, 1)) for ld in ctx.leaders for l in ld.lines if l.vertices]
        except Exception as ex:
            s = "?" + str(ex)
    if s and rx.search(s):
        print(t, round(p.x, 1) if p else None, round(p.y, 1) if p else None, repr(s[:80]), arrows if t == "MULTILEADER" else "")
