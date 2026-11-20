# -*- coding: utf-8 -*-
# Зазор 3 мм «торец заполнения — дно паза» во всех М2/М3 (кроме столбов): типы панелей под стойку.
# 1) загрузка rfa (панели с формулой размера по выступам; профили цс с пересрезом);
# 2) группы стоек: для каждого типа стены группы — новые типы панелей «<имя> (<суффикс>[, стекло X мм])» с «Выступ сбоку/сверху/снизу» = entry;
#    тип стены получает новую панель по умолчанию; панели в стенах этого типа переводятся на тип той же толщины своей группы;
#    ГКЛ — тип «<ГКЛ> (<суффикс>)» на группу.
# 3) цс-группы: выступ только сверху/снизу (сбоку 0 — стык FS.C-156 и срез профиля у стены); opt: замена импостов пола/потолка;
# 4) поправки FT_Стекло_Поправка_*: у стоек 0; у столбов = добавка по альбому − выступ (размер у столба как раньше);
# dry_run=true — всё откатывается.
import json, io, os, re, clr
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
if args.get("args_file"):
    a2 = json.loads(io.open(args["args_file"], encoding="utf-8-sig").read()); a2.update(dict((k, v) for k, v in args.items() if k != "args_file")); args = a2
doc = __revit__.ActiveUIDocument.Document
FT = 304.8
DRY = bool(args.get("dry_run", True))
POST = {u"М2": {u"FSC17": 16.0, u"FSC18": 12.5, u"FSC22": 14.5}, u"М3": {u"FSC08": 14.5, u"FSC04": 14.25}}
res = {"dry_run": DRY, "loaded": 0, "types_new": [], "types_set": [], "walls": [], "remapped": 0, "corrections": {"zero": 0, "post": 0}, "problems": []}
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
RX = re.compile(u"\\s*\\(стекло (\\d+) мм\\)$")


def new_name(old, suffix):
    m = RX.search(old)
    if m:
        return RX.sub(u"", old) + u" (%s, стекло %s мм)" % (suffix, m.group(1))
    return old + u" (%s)" % suffix


def set_entry(s, e, sides):
    for k in sides:
        p = s.LookupParameter(k)
        if p is None or p.IsReadOnly:
            res["problems"].append([u"нет параметра", s.Name, k]); continue
        p.Set(float(e) / FT)


tg = TransactionGroup(doc, u"FT: зазор 3 мм — типы панелей под стойку"); tg.Start()
try:
    t = Transaction(doc, u"FT: зазор 3 мм — загрузка"); t.Start()
    for d in args.get("rfa_dirs", []):
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(".rfa") and not re.search(r"\.\d{4}\.rfa$", f.lower()):
                if doc.LoadFamily(os.path.join(d, f), LO(), clr.Reference[Family]()):
                    res["loaded"] += 1
                else:
                    res["problems"].append([u"не загружено", f])
    t.Commit()
    t = Transaction(doc, u"FT: зазор 3 мм — типы"); t.Start()
    pans = [s for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_CurtainWallPanels) if s.Family.Name.startswith(u"BIMLIB_ПанельВитража")]
    by = dict(((s.Family.Name, s.Name), s) for s in pans)
    wts = dict((w.Name, w) for w in FilteredElementCollector(doc).OfClass(WallType))
    mts = dict((nm(m), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
    SIDES_ALL = (u"Выступ сбоку", u"Выступ сверху", u"Выступ снизу"); SIDES_TB = (u"Выступ сверху", u"Выступ снизу")
    entry_of_type = {}   # id типа -> (entry_side, entry_tb)

    def get_type(src, suffix, entry, sides):
        if suffix is None:   # на месте (тип уже свой у группы)
            set_entry(src, entry, sides); entry_of_type[src.Id.Value] = entry
            res["types_set"].append([src.Name, entry]); return src
        nn = new_name(src.Name, suffix); key = (src.Family.Name, nn)
        s = by.get(key)
        if s is None:
            s = src.Duplicate(nn); by[key] = s; res["types_new"].append([nn, entry])
        set_entry(s, entry, sides); entry_of_type[s.Id.Value] = entry
        return s

    walls_of = {}
    for w in FilteredElementCollector(doc).OfClass(Wall):
        if w.CurtainGrid is not None:
            walls_of.setdefault(w.WallType.Name, []).append(w)
    for g in args["groups"]:
        sides = SIDES_TB if g.get("cs") else SIDES_ALL
        for wn in g["walls"]:
            wt = wts.get(wn)
            if wt is None:
                res["problems"].append([u"нет типа стены", wn]); continue
            p0 = doc.GetElement(wt.get_Parameter(BuiltInParameter.AUTO_PANEL_WALL).AsElementId())
            n0 = get_type(p0, g.get("suffix"), g["entry_mm"], sides)
            wt.get_Parameter(BuiltInParameter.AUTO_PANEL_WALL).Set(n0.Id)
            if not g.get("cs"):   # все толщины стекла для этой стойки
                for X in (6, 8, 10):
                    src = by.get((p0.Family.Name, p0.Name + u" (стекло %d мм)" % X))
                    if src is not None:
                        get_type(src, g.get("suffix"), g["entry_mm"], sides)
                    else:
                        res["problems"].append([u"нет исходного типа толщины", p0.Name, X])
            hz = {}
            for b, k in ((BuiltInParameter.AUTO_MULLION_BORDER1_HORIZ, "bottom"), (BuiltInParameter.AUTO_MULLION_BORDER2_HORIZ, "top")):
                if g.get(k):
                    wt.get_Parameter(b).Set(mts[g[k]].Id); hz[k] = g[k]
            # панели в стенах этого типа
            cnt = 0
            for w in walls_of.get(wn, []):
                for pid in w.CurtainGrid.GetPanelIds():
                    pn = doc.GetElement(pid); st = doc.GetElement(pn.GetTypeId())
                    if not isinstance(st, FamilySymbol) or not st.Family.Name.startswith(u"BIMLIB_ПанельВитража") or u"М1" in st.Name:
                        continue
                    if st.Id.Value in entry_of_type:
                        continue
                    if g.get("cs") and u"цельностекл" not in st.Name:
                        continue
                    tgt = get_type(st, g.get("suffix"), g["entry_mm"], sides) if (u"Глухая" not in st.Family.Name or not g.get("cs")) else None
                    if tgt is not None and tgt.Id != st.Id:
                        pn.ChangeTypeId(tgt.Id); cnt += 1
            res["remapped"] += cnt
            res["walls"].append({"wall": wn.replace(u"BIMLIB_Витраж_Без разрезки_", u""), "panel": n0.Name, "entry": g["entry_mm"], "panels_remapped": cnt, "horizontals": hz})
        for gk in g.get("gkl", []):   # типы ГКЛ группы
            src = by.get((u"BIMLIB_ПанельВитража_Глухая_ФристайлТехнолоджи", gk))
            if src is not None:
                get_type(src, g["suffix"], g["entry_mm"], SIDES_ALL)
    t.Commit()
    # 4) поправки по соседним импостам
    t = Transaction(doc, u"FT: зазор 3 мм — поправки"); t.Start()
    mulls = []
    for m in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallMullions).WhereElementIsNotElementType():
        try:
            c = m.LocationCurve
        except Exception:
            c = None
        if c is None:
            continue
        mt = doc.GetElement(m.GetTypeId()); sym = doc.GetElement(mt.get_Parameter(BuiltInParameter.MULLION_PROFILE).AsElementId()) if mt else None
        mm = re.search(u"Профиль_(М\\d)_(FSC\\d+К?)", sym.FamilyName if sym else u"")
        d_ = (c.GetEndPoint(1) - c.GetEndPoint(0)).Normalize()
        mulls.append((c, abs(d_.Z) > 0.9, mm.group(1) if mm else None, mm.group(2) if mm else None))

    def near(P, vert, tol=150 / FT):
        best, bd = None, tol
        for c, v, s_, code in mulls:
            if v != vert:
                continue
            r = c.Project(P)
            if r is not None and r.Distance < bd:
                best, bd = (s_, code), r.Distance
        return best
    for pn in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_CurtainWallPanels).WhereElementIsNotElementType():
        st = doc.GetElement(pn.GetTypeId())
        if not isinstance(st, FamilySymbol) or not st.Family.Name.startswith(u"BIMLIB_ПанельВитража") or u"М1" in st.Name:
            continue
        qw = pn.LookupParameter(u"FT_Стекло_Поправка_Ширина"); qh = pn.LookupParameter(u"FT_Стекло_Поправка_Высота")
        if qw is None or qh is None:
            continue
        bb = pn.get_BoundingBox(None); w = pn.Host
        if bb is None or w is None or not isinstance(w.Location, LocationCurve):
            continue
        d_ = w.Location.Curve.Direction; c = (bb.Min + bb.Max) * 0.5
        hw = abs((bb.Max - bb.Min).DotProduct(d_)) / 2.0
        es = st.LookupParameter(u"Выступ сбоку").AsDouble() * FT; et = st.LookupParameter(u"Выступ сверху").AsDouble() * FT; eb = st.LookupParameter(u"Выступ снизу").AsDouble() * FT
        cw = 0.0; ch = 0.0
        for P, vert, e in ((c - d_ * hw, True, es), (c + d_ * hw, True, es)):
            k = near(P, vert)
            if k and k[0] in POST and k[1] in POST[k[0]]:
                cw += POST[k[0]][k[1]] - e
        for P, e in ((XYZ(c.X, c.Y, bb.Min.Z), eb), (XYZ(c.X, c.Y, bb.Max.Z), et)):
            k = near(P, False)
            if k and k[0] in POST and k[1] in POST[k[0]]:
                ch += POST[k[0]][k[1]] - e
        qw.Set(cw / FT); qh.Set(ch / FT)
        if cw or ch:
            res["corrections"]["post"] += 1
        else:
            res["corrections"]["zero"] += 1
    t.Commit()
    res["warnings"] = len(doc.GetWarnings())
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
st_ = "failed" if res.get("error") else ("partial" if res["problems"] else "completed_unverified")
__output__ = {"status": st_, "summary": (u"ПРОБА (откат): " if DRY else u"ПРИМЕНЕНО: ") + u"загружено %d, новых типов %d, типов на месте %d, стен %d, панелей переведено %d, поправки: у столбов %d, обнулено %d, предупреждений %s, проблем %d" % (res["loaded"], len(res["types_new"]), len(res["types_set"]), len(res["walls"]), res["remapped"], res["corrections"]["post"], res["corrections"]["zero"], res.get("warnings"), len(res["problems"])), "r": res}
