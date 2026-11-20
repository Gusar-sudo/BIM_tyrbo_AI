# -*- coding: utf-8 -*-
# Межстекольный профиль FS.C-156 (FS.G-06), альбом М1 табл. 3 и рис. 18: Н-образный, 10 мм поперёк стекла,
# зазор между торцами стёкол gap_mm (4). Контур профиля = ширина импоста для Revit, поэтому панели
# обрезаются на gap/2 с каждой стороны — зазор есть в геометрии, а не только в формуле.
# Контур: полки у граней стекла (x ±gap/2, толщина flange_mm, выступ за грань стекла over_mm),
#         стенка между торцами (x ±web_mm/2).
# Аргументы: base_profile, out_dir, gap_mm 4, web_mm 2.4, flange_mm 1, over_mm 1,
#            items [{save_as, glass_outer_mm (наружная грань стекла, знак = сторона фасада), glass_mm}]
# Сохраняет КОПИИ .rfa в out_dir; проект не меняется.
import json, io, os
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    args = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read())
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MM = lambda v: v / FT
fams = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
G = float(args.get("gap_mm", 4)) / 2; Wb = float(args.get("web_mm", 2.4)) / 2
Fl = float(args.get("flange_mm", 1)); Ov = float(args.get("over_mm", 1))
rows = []
for it in args["items"]:
    r = {"save_as": it["save_as"]}
    bd = doc.EditFamily(fams[args["base_profile"]])
    try:
        own = [ce for ce in FilteredElementCollector(bd).OfClass(CurveElement) if ce.GeometryCurve is not None]
        view = bd.GetElement(own[0].OwnerViewId)
        outers = it["glass_outer_mm"] if isinstance(it["glass_outer_mm"], list) else [it["glass_outer_mm"]]
        t = float(it["glass_mm"]); Ps = []
        for o in outers:   # по одному Н-контуру на каждое стекло
            o = float(o); s = 1 if o > 0 else -1
            ylo, yhi = sorted([o + s * Ov, o - s * (t + Ov)])   # полки: за гранями стекла на over_mm, всего t + 2·over
            lo1, hi0 = ylo + Fl, yhi - Fl
            if args.get("chamfer_flange"):   # полка 4,7 у грани, скосом в стенку 4 (ложится в фаску стекла, рис. 18); отрезки >= 0,8 мм
                a = ylo + 0.8; b = ylo + 1.6; c = yhi - 0.8; d = yhi - 1.6
                Ps.append([(-G, ylo), (G, ylo), (G, a), (Wb, b), (Wb, d), (G, c), (G, yhi), (-G, yhi), (-G, c), (-Wb, d), (-Wb, b), (-G, a)])
                continue
            Ps.append([(-G, ylo), (G, ylo), (G, lo1), (Wb, lo1), (Wb, hi0), (G, hi0), (G, yhi), (-G, yhi), (-G, hi0), (-Wb, hi0), (-Wb, lo1), (-G, lo1)])
        if it.get("origin_on_first"):   # первое Н-сечение на оси семейства (Revit берёт ширину импоста по оси); к стеклу — «Смещение» типа
            c0 = sum(y for _, y in Ps[0]) / len(Ps[0]); r["shift_mm"] = round(c0, 2)
            Ps = [[(x, y - c0) for x, y in P] for P in Ps]
        if it.get("axis_tab_mm"):   # проба: маленький контур на оси (y=0) — ширина импоста для Revit
            h = float(it["axis_tab_mm"]) / 2
            Ps.append([(-G, -h), (G, -h), (G, h), (-G, h)])

        def mk():
            ids = [ce.Id for ce in own] + [fi.Id for fi in FilteredElementCollector(bd).OfClass(FamilyInstance)]
            bd.Delete(List[ElementId](ids))
            for P in Ps:
                for i in range(len(P)):
                    p, q = P[i], P[(i + 1) % len(P)]
                    bd.FamilyCreate.NewDetailCurve(view, Line.CreateBound(XYZ(MM(p[0]), MM(p[1]), 0), XYZ(MM(q[0]), MM(q[1]), 0)))
            return len(ids)
        tr = Transaction(bd, u"FT: FS.C-156"); tr.Start()
        try:
            r["deleted"] = mk(); tr.Commit()
        except Exception:
            tr.RollBack(); raise
        r["outline_mm"] = [[[round(x, 2), round(y, 2)] for x, y in P] for P in Ps]
        so = SaveAsOptions(); so.OverwriteExistingFile = True
        r["rfa"] = os.path.join(OUT, it["save_as"] + u".rfa"); bd.SaveAs(r["rfa"], so); r["ok"] = True
    except Exception as ex:
        import traceback
        r["error"] = traceback.format_exc()[-400:]
    finally:
        bd.Close(False)
    rows.append(r)
__output__ = {"status": "completed_unverified" if all(x.get("ok") for x in rows) else "partial",
              "summary": u"копий FS.C-156: %d из %d; проект не менялся" % (sum(1 for x in rows if x.get("ok")), len(rows)), "rows": rows}
