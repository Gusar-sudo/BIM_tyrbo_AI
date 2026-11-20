# -*- coding: utf-8 -*-
# Проба семейства панели в проекте ЧЕРЕЗ ВИД (всё откатывается): загрузить rfa, поставить стены, задать параметры экземпляров
# панелей по стенам, построить 3D «Высокая» и «Низкая» на каждую стену и проверить геометрию так, как её рисует вид
# (Options.View): тела вне габарита панели (ADSK_Размер_Ширина/Высота ± tol) и число тел на панель. PNG видов -> out_dir.
# Причина: копии массива в семействе могут в проекте не слушать видимость и длину, хотя get_Geometry без вида чистый.
# Аргументы: rfa, out_dir, tol_mm (30), walls [{key, wall_type, length_mm, height_mm, grid_mm, transom_mm, panel_params{}}]
import json, os, clr
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
MM = lambda v: v / FT
OUT = args["out_dir"]
if not os.path.isdir(OUT):
    os.makedirs(OUT)
TOL = float(args.get("tol_mm", 30))
level = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
wtypes = dict((w.Name, w) for w in FilteredElementCollector(doc).OfClass(WallType))
vft = [t for t in FilteredElementCollector(doc).OfClass(ViewFamilyType) if t.ViewFamily == ViewFamily.ThreeDimensional][0]


OVR = bool(args.get("overwrite_values", False))   # True — значения параметров из семейства (сбрасывает и значения по умолчанию)


class _LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = OVR
        return True

    def OnSharedFamilyFound(self, a, b, src, c):
        src.Value = FamilySource.Family; c.Value = OVR
        return True


def solids(e, view):
    o = Options(); o.View = view
    T = e.GetTransform().Inverse if hasattr(e, "GetTransform") else Transform.Identity
    out = []

    def walk(ge, tr):
        for g in ge:
            if isinstance(g, GeometryInstance):
                walk(g.GetInstanceGeometry(), tr)
            elif isinstance(g, Solid) and g.Volume > 1e-9:
                pts = [T.OfPoint(p) for ed in g.Edges for p in ed.Tessellate()]
                out.append([min(p.X for p in pts) * FT, max(p.X for p in pts) * FT, min(p.Z for p in pts) * FT, max(p.Z for p in pts) * FT])
    walk(e.get_Geometry(o) or [], Transform.Identity)
    return out


res = {"walls": []}
tg = TransactionGroup(doc, u"проба панели через вид (откат)"); tg.Start()
try:
    t = Transaction(doc, u"загрузка"); t.Start()
    res["loaded"] = doc.LoadFamily(args["rfa"], _LO(), clr.Reference[Family]()) if args.get("rfa") else u"без загрузки (семейство проекта)"
    t.Commit()
    views = []
    for k, c in enumerate(args["walls"]):
        t = Transaction(doc, u"стена"); t.Start()
        P0 = XYZ(MM(60000), MM(800000 + 6000 * k), level.Elevation)
        L, H = float(c["length_mm"]), float(c["height_mm"])
        w = Wall.Create(doc, Line.CreateBound(P0, P0 + XYZ.BasisX * MM(L)), wtypes[c["wall_type"]].Id, level.Id, MM(H), 0, False, False)
        doc.Regenerate()
        g = float(c.get("grid_mm", 0) or 0)
        if g:
            for i in range(1, int(round(L / g))):
                w.CurtainGrid.AddGridLine(False, P0 + XYZ.BasisX * MM(g * i) + XYZ(0, 0, 1), False)
        if c.get("transom_mm"):
            w.CurtainGrid.AddGridLine(True, P0 + XYZ.BasisX * MM(min(g or L, L) / 2) + XYZ(0, 0, MM(c["transom_mm"])), False)
        doc.Regenerate()
        for pid in w.CurtainGrid.GetPanelIds():
            p = doc.GetElement(pid)
            for pn, pv in (c.get("panel_params") or {}).items():
                pp = p.LookupParameter(pn)
                if pp and not pp.IsReadOnly:
                    pp.Set(int(pv))
        vs = {}
        for dl, nm in ((ViewDetailLevel.Fine, u"высокая"), (ViewDetailLevel.Coarse, u"низкая")):
            v = View3D.CreateIsometric(doc, vft.Id); v.Name = u"FT проба %s %s" % (c["key"], nm)
            bb = BoundingBoxXYZ(); bb.Min = P0 - XYZ(MM(1500), MM(1500), MM(100)); bb.Max = P0 + XYZ(MM(L + 1500), MM(1500), MM(H + 200))
            v.IsSectionBoxActive = True; v.SetSectionBox(bb); v.DetailLevel = dl; v.DisplayStyle = DisplayStyle.ShadingWithEdges
            vs[nm] = v
        t.Commit()
        r = {"key": c["key"], "panels": []}
        for pid in w.CurtainGrid.GetPanelIds():
            p = doc.GetElement(pid)
            W = p.LookupParameter(u"ADSK_Размер_Ширина"); Hh = p.LookupParameter(u"ADSK_Размер_Высота")
            Wm = W.AsDouble() * FT if W else None; Hm = Hh.AsDouble() * FT if Hh else None
            row = {"type": p.Name, "W": round(Wm or 0), "H": round(Hm or 0)}
            for nm, v in vs.items():
                ss = solids(p, v)
                out_ = [s for s in ss if Wm and (s[0] < -Wm / 2 - TOL or s[1] > Wm / 2 + TOL or s[2] < -TOL - 30 or s[3] > Hm + TOL + 30)]
                row[nm] = {"solids": len(ss), "outside": len(out_), "x": [round(min(s[0] for s in ss)), round(max(s[1] for s in ss))] if ss else None,
                           "z": [round(min(s[2] for s in ss)), round(max(s[3] for s in ss))] if ss else None}
            for pn in (u"FT_Жалюзи", u"FT_Жалюзи_Видимость", u"FT_Жалюзи_Ламелей"):
                pp = p.LookupParameter(pn)
                row[pn] = pp.AsInteger() if pp else None
            r["panels"].append(row)
        res["walls"].append(r)
        views += [(vs[u"высокая"], u"%s_высокая" % c["key"]), (vs[u"низкая"], u"%s_низкая" % c["key"])]
    for v, key in views:
        o = ImageExportOptions(); o.ExportRange = ExportRange.SetOfViews
        ids = List[ElementId](); ids.Add(v.Id); o.SetViewsAndSheets(ids)
        o.FilePath = os.path.join(OUT, key); o.ZoomType = ZoomFitType.FitToPage; o.PixelSize = 1000
        o.ShadowViewsFileType = ImageFileType.PNG; o.HLRandWFViewsFileType = ImageFileType.PNG
        doc.ExportImage(o)
    res["warnings"] = len(doc.GetWarnings())
finally:
    tg.RollBack()
bad = sum(1 for w in res["walls"] for p in w["panels"] for nm in (u"высокая", u"низкая") if p[nm]["outside"])
__output__ = {"status": "completed_unverified" if not bad else "partial", "summary": u"панелей с телами вне габарита: %d; всё откатано" % bad, "result": res}
