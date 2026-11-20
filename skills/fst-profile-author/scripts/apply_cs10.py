# -*- coding: utf-8 -*-
# Цельностеклянные М2/М3 под стекло 10 мм (вариант «отдельные типы стен»).
# 1) загрузка rfa из rfa_dir (профили *_Стекло10_* и FS.C-156 под 10 мм);
# 2) типы импостов «… (стекло 10 мм)»: копия типа, профиль которого = семейство без «_Стекло10», профиль -> копия _Стекло10;
#    межстекольные: копия типа FS.C-156 8 мм, профиль 10 мм, «Смещение» из joint_offsets;
# 3) панель «стойка широкая» под 10 мм (копия типа: толщина 10, U10 вкл, U8 выкл, артикул FS.C-U10);
# 4) типы стен: копия «…_Стекло 10 мм» (панель 10 мм, импосты 10 мм), исходный тип переименован в «…_Стекло 8 мм»;
# 5) проверка: временная стена каждого нового типа (2 панели, сетка посередине) — зазор у стыка, стекло спец./геометрия,
#    типы импостов на месте; временные стены откатываются.
# dry_run=true — всё откатывается.
import json, io, os, re, clr
from System.Collections.Generic import List
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    a2 = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read()); a2.update(dict((k, v) for k, v in args.items() if k != "args_file")); args = a2
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
DRY = bool(args.get("dry_run", True))
S10 = u" (стекло 10 мм)"
res = {"dry_run": DRY, "loaded": 0, "mullion_types": [], "panels": [], "walls": [], "check": [], "problems": []}
_T = Transaction
OPEN = []


def Transaction(d, n):
    x = _T(d, n); OPEN.append(x); return x


class LO(IFamilyLoadOptions):
    def OnFamilyFound(self, a, b):
        b.Value = True; return True

    def OnSharedFamilyFound(self, s, a, src, b):
        src.Value = FamilySource.Family; b.Value = True; return True


nm = lambda e: Element.Name.GetValue(e)
opt = Options(); opt.DetailLevel = ViewDetailLevel.Fine


def glass_solids(pn):
    out = []
    def walk(g):
        for o in g:
            if isinstance(o, Solid) and o.Volume > 1e-9 and o.Faces.Size:
                m = doc.GetElement(o.Faces.get_Item(0).MaterialElementId)
                if m is not None and u"Стекло" in m.Name:
                    out.append(o)
            elif isinstance(o, GeometryInstance):
                walk(o.GetInstanceGeometry())
    ge = pn.get_Geometry(opt)
    if ge:
        walk(ge)
    return out


tg = TransactionGroup(doc, u"FT: цс под стекло 10 мм"); tg.Start()
try:
    t = Transaction(doc, u"FT: цс 10 — загрузка"); t.Start()
    for f in sorted(os.listdir(args["rfa_dir"])):
        if f.lower().endswith(".rfa") and not re.search(r"\.\d{4}\.rfa$", f.lower()):
            if doc.LoadFamily(os.path.join(args["rfa_dir"], f), LO(), clr.Reference[Family]()):
                res["loaded"] += 1
            else:
                res["problems"].append([u"не загружено", f])
    t.Commit()
    fams = dict((fa.Name, fa) for fa in FilteredElementCollector(doc).OfClass(Family))
    sym = lambda fn: list(fams[fn].GetFamilySymbolIds())[0]
    mts = dict((nm(m), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
    t = Transaction(doc, u"FT: цс 10 — типы"); t.Start()
    # 2) импосты
    prof_of = {}
    for n, m in mts.items():
        pe = doc.GetElement(m.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId())
        if pe is not None and hasattr(pe, "Family"):
            prof_of[n] = pe.Family.Name
    m10 = {}   # имя 8 мм -> тип 10 мм
    for n, fn in sorted(prof_of.items()):
        f10 = fn.replace(u"_ФристайлТехнолоджи", u"_Стекло10_ФристайлТехнолоджи")
        if u"Стекло10" in fn or f10 not in fams or n.endswith(S10):
            continue
        new = n + S10
        m = mts.get(new) or mts[n].Duplicate(new); mts[new] = m
        m.get_Parameter(BuiltInParameter.MULLION_PROFILE).Set(sym(f10))
        off = args.get("joint_offsets", {}).get(n)
        if off is not None:
            m.LookupParameter(u"Смещение").Set(float(off) / FT)
        m10[n] = m
        res["mullion_types"].append([new, f10, off])
    # 3) панель «стойка широкая» под 10 мм
    pans = [s for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_CurtainWallPanels) if s.Family.Name == args["panel_family"]]
    pn_by = dict((s.Name, s) for s in pans)
    for src, new in args.get("panel_new", {}).items():
        s = pn_by.get(new) or pn_by[src].Duplicate(new)
        pn_by[new] = s
        s.LookupParameter(u"Толщина стекла").Set(10 / FT)
        for pn_, v_ in ((u"FT_Уплотнитель_U10_Показать", 1), (u"FT_Уплотнитель_U8_Показать", 0), (u"FT_Стекло_Уплотнитель_Артикул", u"FS.C-U10")):
            q = s.LookupParameter(pn_)
            if q is not None and not q.IsReadOnly:
                q.Set(v_)
        doc.Regenerate()
        rd = lambda n_: (s.LookupParameter(n_).AsInteger() if s.LookupParameter(n_).StorageType == StorageType.Integer else s.LookupParameter(n_).AsString())
        got = [round(s.LookupParameter(u"Толщина стекла").AsDouble() * FT, 1), rd(u"FT_Уплотнитель_U10_Показать"), rd(u"FT_Уплотнитель_U8_Показать"), rd(u"FT_Стекло_Уплотнитель_Артикул")]
        res["panels"].append([new] + got)
        if got[1:] != [1, 0, u"FS.C-U10"]:
            res["problems"].append([u"панель 10 мм: уплотнитель не переключился", new, got])
    # 4) стены
    wts = dict((w.Name, w) for w in FilteredElementCollector(doc).OfClass(WallType))
    MULL_BIPS = [BuiltInParameter.AUTO_MULLION_BORDER1_VERT, BuiltInParameter.AUTO_MULLION_BORDER2_VERT, BuiltInParameter.AUTO_MULLION_INTERIOR_VERT,
                 BuiltInParameter.AUTO_MULLION_BORDER1_HORIZ, BuiltInParameter.AUTO_MULLION_BORDER2_HORIZ, BuiltInParameter.AUTO_MULLION_INTERIOR_HORIZ]
    new_walls = []
    for wn in args["walls"]:
        w8n = wn + u"_Стекло 8 мм"; w10n = wn + u"_Стекло 10 мм"
        w8 = wts.get(w8n) or wts[wn]
        w10 = wts.get(w10n) or w8.Duplicate(w10n)
        if w8.Name != w8n:
            w8.Name = w8n
        p8 = nm(doc.GetElement(w8.get_Parameter(BuiltInParameter.AUTO_PANEL_WALL).AsElementId()))
        p10n = args["panel_map"][p8]
        w10.get_Parameter(BuiltInParameter.AUTO_PANEL_WALL).Set(pn_by[p10n].Id)
        sw = {}
        for b in MULL_BIPS:
            p = w10.get_Parameter(b)
            if p is None or p.AsElementId() == ElementId.InvalidElementId:
                continue
            cur = nm(doc.GetElement(p.AsElementId()))
            base = cur[:-len(S10)] if cur.endswith(S10) else cur
            if base in m10:
                p.Set(m10[base].Id); sw[str(b)[14:]] = nm(m10[base])
            else:
                sw[str(b)[14:]] = cur + u" (без изменений)"
        res["walls"].append({"8": w8n, "10": w10n, "panel_10": p10n, "mullions_10": sw})
        new_walls.append(w10)
    t.Commit()
    # 5) проверка на временных стенах
    lvl = sorted(FilteredElementCollector(doc).OfClass(Level), key=lambda l: abs(l.Elevation))[0]
    t = Transaction(doc, u"FT: цс 10 — проверка (откат)"); t.Start()
    ox, oy = args.get("probe_origin_mm", [60000, -60000]); ox /= FT; oy /= FT
    for i, w10 in enumerate(new_walls):
        y = oy - i * 3000 / FT
        P0 = XYZ(ox, y, lvl.Elevation); L = 1600 / FT
        w = Wall.Create(doc, Line.CreateBound(P0, XYZ(ox + L, y, lvl.Elevation)), w10.Id, lvl.Id, 2700 / FT, 0, False, False)
        doc.Regenerate()
        w.CurtainGrid.AddGridLine(False, XYZ(ox + L / 2, y, lvl.Elevation + 1), False)
        doc.Regenerate()
        mul = [doc.GetElement(i_) for i_ in w.CurtainGrid.GetMullionIds()]
        names = sorted(set(nm(doc.GetElement(m.GetTypeId())) for m in mul))
        mid = [m for m in mul if u"межстекол" in nm(doc.GetElement(m.GetTypeId()))]
        row = {"wall": w10.Name, "mullion_types": names}
        if mid:
            bb = mid[0].get_BoundingBox(None); mc = (bb.Min.X + bb.Max.X) / 2
            pieces = []
            for pid in w.CurtainGrid.GetPanelIds():
                pn = doc.GetElement(pid)
                for s in glass_solids(pn):
                    b2 = s.GetBoundingBox(); a = b2.Transform.OfPoint(b2.Min); c = b2.Transform.OfPoint(b2.Max)
                    pieces.append((round(((a.Y + c.Y) / 2 - y) * FT, 1), min(a.X, c.X), max(a.X, c.X), pn, round(abs(a.Y - c.Y) * FT, 1)))
            gaps = {}; spec = []
            for yc in sorted(set(p[0] for p in pieces)):
                Lp = [p for p in pieces if p[0] == yc and p[2] <= mc + 1e-3]; Rp = [p for p in pieces if p[0] == yc and p[1] >= mc - 1e-3]
                if Lp and Rp:
                    l = max(Lp, key=lambda p: p[2]); r = min(Rp, key=lambda p: p[1])
                    gaps[str(yc)] = [round((r[1] - l[2]) * FT, 2), l[4]]
                    q = l[3].LookupParameter(u"FT_Стекло_Ширина")
                    spec.append([round(q.AsDouble() * FT, 1) if q else None, round((l[2] - l[1]) * FT, 1)])
            row.update(gaps_mm_and_glass_thk=gaps, spec_vs_geo=spec[:2])
            if not gaps or any(abs(v[0] - 4.0) > 0.2 or abs(v[1] - 10.0) > 0.2 for v in gaps.values()) or any(s_[0] is None or not (0 <= s_[1] - s_[0] < 1.0) for s_ in spec):
                res["problems"].append(row)
        else:
            res["problems"].append([u"нет межстекольного", w10.Name, names])
        res["check"].append(row)
    t.RollBack()
    if DRY:
        tg.RollBack()
    else:
        tg.Assimilate()
except Exception:
    import traceback
    res["error"] = traceback.format_exc()[-700:]
    for x in reversed(OPEN):
        if x.HasStarted() and not x.HasEnded():
            x.RollBack()
    if tg.HasStarted() and not tg.HasEnded():
        tg.RollBack()
st = "failed" if res.get("error") else ("partial" if res["problems"] else "completed_unverified")
__output__ = {"status": st, "summary": (u"ПРОБА (откат): " if DRY else u"ПРИМЕНЕНО: ") + u"загружено %d, импостов 10 мм %d, панелей %d, стен %d, проверено %d, проблем %d" % (res["loaded"], len(res["mullion_types"]), len(res["panels"]), len(res["walls"]), len(res["check"]), len(res["problems"])), "r": res}
