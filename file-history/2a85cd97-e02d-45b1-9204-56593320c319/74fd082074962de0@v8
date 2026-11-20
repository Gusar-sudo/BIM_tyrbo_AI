# -*- coding: utf-8 -*-
# Проба с откатом: зазор «торец заполнения (стекло/ГКЛ) — ближайший профиль» у стены (слева/справа), у пола, у потолка и на стыке,
# плюс размер заполнения в спецификации против модели.
# Аргументы: walls [имена] ИЛИ items [{wall, panel?, panel_family?, set_mm?{параметр типа панели: мм}}], preload_rfas, origin_mm, length_mm.
# Луч из точки за 30 мм до торца (внутри заполнения) наружу; зазор со знаком (минус — заполнение заходит в профиль).
import json, io, clr
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    a2 = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read()); a2.update(dict((k, v) for k, v in args.items() if k != "args_file")); args = a2
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
opt = Options(); opt.DetailLevel = ViewDetailLevel.Fine
FILL = (u"Стекло", u"ГКЛ", u"Гипс", u"гипс")


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


def solids(e, fill_only=False):
    out = []
    def walk(g):
        for o in g:
            if isinstance(o, Solid) and o.Volume > 1e-9 and o.Faces.Size:
                if fill_only:
                    m = doc.GetElement(o.Faces.get_Item(0).MaterialElementId)
                    if m is None or not any(k in m.Name for k in FILL):
                        continue
                out.append(o)
            elif isinstance(o, GeometryInstance):
                walk(o.GetInstanceGeometry())
    ge = e.get_Geometry(opt)
    if ge:
        walk(ge)
    return out


def ray(p, d, msol, L=60 / FT):
    back = 30 / FT
    p = p - d * back
    ln = Line.CreateBound(p, p + d * (L + back)); best = None
    so = SolidCurveIntersectionOptions()
    for s in msol:
        try:
            r = s.IntersectWithCurve(ln, so)
        except Exception:
            continue
        for i in range(r.SegmentCount):
            c = r.GetCurveSegment(i); t = c.GetEndPoint(0).DistanceTo(p)
            if best is None or t < best:
                best = t
    return round(best * FT - 30, 2) if best is not None else None


lvl = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
items = args.get("items") or [{"wall": w} for w in args["walls"]]
rows = []
tg = TransactionGroup(doc, u"замер зазоров (откат)"); tg.Start()
try:
    t = Transaction(doc, u"замер: семейства"); t.Start()
    for f in args.get("preload_rfas", []):
        doc.LoadFamily(f, LO(), clr.Reference[Family]())
    t.Commit()
    wts = dict((w.Name, w) for w in FilteredElementCollector(doc).OfClass(WallType))
    pans = list(FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_CurtainWallPanels))
    t = Transaction(doc, u"замер"); t.Start()
    for i, it in enumerate(items):
        wn = it["wall"]
        ox = args.get("origin_mm", [80000, -80000])[0] / FT; oy = (args.get("origin_mm", [80000, -80000])[1] - i * 3000) / FT
        L = args.get("length_mm", 1600) / FT
        pst = None
        if it.get("panel"):
            found = [s for s in pans if s.Name == it["panel"] and (not it.get("panel_family") or s.Family.Name == it["panel_family"])]
            if not found:
                rows.append({"wall": wn, "panel": it["panel"], "error": u"нет типа панели"}); continue
            pst = found[0]
            for k, v in (it.get("set_mm") or {}).items():
                pst.LookupParameter(k).Set(float(v) / FT)
            wts[wn].get_Parameter(BuiltInParameter.AUTO_PANEL_WALL).Set(pst.Id)
        w = Wall.Create(doc, Line.CreateBound(XYZ(ox, oy, lvl.Elevation), XYZ(ox + L, oy, lvl.Elevation)), wts[wn].Id, lvl.Id, 2700 / FT, 0, False, False)
        doc.Regenerate()
        w.CurtainGrid.AddGridLine(False, XYZ(ox + L / 2, oy, lvl.Elevation + 1), False)
        doc.Regenerate()
        HZ = args.get("hgrid_mm")
        if HZ:
            w.CurtainGrid.AddGridLine(True, XYZ(ox + L / 4, oy, lvl.Elevation + float(HZ) / FT), False)
            doc.Regenerate()
        if pst is not None:
            for pid in w.CurtainGrid.GetPanelIds():
                pn = doc.GetElement(pid)
                if pn.GetTypeId() != pst.Id:
                    pn.ChangeTypeId(pst.Id)
            doc.Regenerate()
        if it.get("joint_mullion"):
            # средний вертикальный импост -> заданный тип (столб); стык меряется так же лучом
            jm = [m for m in FilteredElementCollector(doc).OfClass(MullionType) if Element.Name.GetValue(m) == it["joint_mullion"]]
            if not jm:
                rows.append({"wall": wn, "joint_mullion": it["joint_mullion"], "error": u"нет типа импоста"}); continue
            for mid in w.CurtainGrid.GetMullionIds():
                mu = doc.GetElement(mid); c = mu.LocationCurve.GetEndPoint(0) if mu.LocationCurve else None
                if c is not None and abs(c.X - (ox + L / 2)) < 0.01 and abs((mu.LocationCurve.GetEndPoint(1) - c).Normalize().Z) > 0.9:
                    mu.Pinned = False; mu.ChangeTypeId(jm[0].Id)
            doc.Regenerate()
        if it.get("post_side"):
            # заход стекла за край столба (мм): minus — сторона −X столба (панель слева от него), plus — сторона +X
            for pid in w.CurtainGrid.GetPanelIds():
                pn = doc.GetElement(pid)
                ql = pn.LookupParameter(u"FT_Стекло_Поправка_Слева"); qr = pn.LookupParameter(u"FT_Стекло_Поправка_Справа")
                if ql is None or qr is None:
                    rows.append({"wall": wn, "error": u"в панели нет поправок слева/справа"}); break
                vs = doc.GetElement(pn.GetTypeId()).LookupParameter(u"Выступ сбоку").AsDouble() * FT
                bb = pn.get_BoundingBox(None); xc_ = (bb.Min.X + bb.Max.X) / 2
                if xc_ < ox + L / 2:
                    qr.Set((float(it["post_side"]["minus"]) - vs) / FT)
                else:
                    ql.Set((float(it["post_side"]["plus"]) - vs) / FT)
            doc.Regenerate()
        msol = []
        mnames = set()
        for mid in w.CurtainGrid.GetMullionIds():
            mu_ = doc.GetElement(mid); msol += solids(mu_)
            mnames.add(Element.Name.GetValue(doc.GetElement(mu_.GetTypeId())))
        r = {"wall": wn.replace(u"BIMLIB_Витраж_Без разрезки_", u""), "panel": it.get("panel"), "joint_mullion": it.get("joint_mullion"),"left": [], "joint": [], "right": [], "floor": [], "ceiling": [], "spec": []}
        if it.get("list_mullions"):
            r["mullion_types"] = sorted(mnames)
        for pid in w.CurtainGrid.GetPanelIds():
            pn = doc.GetElement(pid)
            for s in solids(pn, True):
                bb = s.GetBoundingBox(); a = bb.Transform.OfPoint(bb.Min); b = bb.Transform.OfPoint(bb.Max)
                x0, x1 = min(a.X, b.X), max(a.X, b.X); y0, y1 = min(a.Y, b.Y), max(a.Y, b.Y); z0, z1 = min(a.Z, b.Z), max(a.Z, b.Z)
                yc = (y0 + y1) / 2; zc = (z0 + z1) / 2; xc = (x0 + x1) / 2; e = 0.02 / FT
                left_side = xc < ox + L / 2
                r["left" if left_side else "joint"].append(ray(XYZ(x0 - e, yc, zc), -XYZ.BasisX, msol))
                r["joint" if left_side else "right"].append(ray(XYZ(x1 + e, yc, zc), XYZ.BasisX, msol))
                # торец стекла у среднего стыка: расстояние от оси стыка (мм), y стекла от оси стены
                r.setdefault("joint_edge_mm", []).append(round(((ox + L / 2) - x1 if left_side else x0 - (ox + L / 2)) * FT, 2))
                r.setdefault("joint_edge_minus" if left_side else "joint_edge_plus", []).append(round(((ox + L / 2) - x1 if left_side else x0 - (ox + L / 2)) * FT, 2))
                r.setdefault("glass_y_mm", []).append([round((y0 - oy) * FT, 2), round((y1 - oy) * FT, 2)])
                hz_ = (lvl.Elevation + float(HZ) / FT) if HZ else None
                bot = ray(XYZ(xc, yc, z0 - e), -XYZ.BasisZ, msol); top = ray(XYZ(xc, yc, z1 + e), XYZ.BasisZ, msol)
                if hz_ is not None and z0 > hz_ - 0.2:
                    r.setdefault("transom_above", []).append(bot)
                else:
                    r["floor"].append(bot)
                if hz_ is not None and z1 < hz_ + 0.2:
                    r.setdefault("transom_below", []).append(top)
                else:
                    r["ceiling"].append(top)
                r.setdefault("fill_thk", round((y1 - y0) * FT, 1))
                qw = pn.LookupParameter(u"FT_Стекло_Ширина"); qh = pn.LookupParameter(u"FT_Стекло_Высота")
                if len(r["spec"]) < 1:
                    r["spec"] = [round(qw.AsDouble() * FT, 1) if qw else None, round((x1 - x0) * FT, 1), round(qh.AsDouble() * FT, 1) if qh else None, round((z1 - z0) * FT, 1)]
        for k in ("left", "joint", "right", "floor", "ceiling", "transom_above", "transom_below", "joint_edge_mm", "joint_edge_minus", "joint_edge_plus"):
            if k in r:
                r[k] = sorted(set(r[k]))
        rows.append(r)
    t.Commit()
finally:
    try:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
    except Exception:
        pass
    tg.RollBack()
__output__ = {"status": "completed_unverified", "summary": u"замерено стен %d (всё откатано)" % len(rows), "rows": rows}
