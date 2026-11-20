# -*- coding: utf-8 -*-
# Типы стен «Глухое заполнение ГКЛ»: краевые и внутренние импосты типа -> вариант «глухой ГКЛ» той же ситуации.
# «М2 FSC21 примыкание к стене с однослойным остеклением левый» -> «М2 FSC21 примыкание к стене глухой ГКЛ левый».
# Аргументы: name_contains («Глухое заполнение ГКЛ»), dry_run.
import json, re
from Autodesk.Revit.DB import *
a = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
DRY = bool(a.get("dry_run", True))
P = [BuiltInParameter.AUTO_MULLION_BORDER1_HORIZ, BuiltInParameter.AUTO_MULLION_BORDER2_HORIZ, BuiltInParameter.AUTO_MULLION_INTERIOR_HORIZ,
     BuiltInParameter.AUTO_MULLION_BORDER1_VERT, BuiltInParameter.AUTO_MULLION_BORDER2_VERT, BuiltInParameter.AUTO_MULLION_INTERIOR_VERT]
mt = dict((m.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString(), m) for m in FilteredElementCollector(doc).OfClass(MullionType))
def gkl_name(n):
    return re.sub(u" с (одно|двух)слойным остеклением", u" глухой ГКЛ", n)
rows = []; miss = []
t = Transaction(doc, u"FT: импосты ГКЛ в типах стен"); t.Start()
try:
    for w in FilteredElementCollector(doc).OfClass(WallType):
        if a.get("name_contains", u"Глухое заполнение ГКЛ") not in w.Name:
            continue
        for bp in P:
            p = w.get_Parameter(bp)
            if p is None:
                continue
            cur = doc.GetElement(p.AsElementId())
            if cur is None:
                continue
            cn = cur.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
            nn = gkl_name(cn)
            if nn == cn:
                rows.append([w.Name[-45:], str(bp)[14:], cn, u"без изменений"]); continue
            if nn not in mt:
                miss.append([w.Name[-45:], cn, nn]); continue
            p.Set(mt[nn].Id)
            rows.append([w.Name[-45:], str(bp)[14:], cn, nn])
    doc.Regenerate()
    bad = []
    for w in FilteredElementCollector(doc).OfClass(Wall):
        if a.get("name_contains", u"Глухое заполнение ГКЛ") in w.Name and w.CurtainGrid:
            for mid in w.CurtainGrid.GetMullionIds():
                n = doc.GetElement(mid).Name
                if u"ГКЛ" not in n:
                    bad.append([w.Id.Value, n])
    res = {"changes": rows, "missing": miss, "walls_with_non_gkl_mullions": bad[:20]}
    if DRY or miss:
        t.RollBack(); res["committed"] = False
    else:
        t.Commit(); res["committed"] = True
except Exception:
    if t.HasStarted() and not t.HasEnded():
        t.RollBack()
    raise
res["status"] = "completed_unverified" if not miss and not bad else "partial"
res["summary"] = u"%sзамен %d, не найдено %d, импостов не ГКЛ на стенах %d" % (
    u"ПРОБА (откат): " if DRY else u"", len([r for r in rows if r[3] != u"без изменений"]), len(miss), len(bad))
__output__ = res
