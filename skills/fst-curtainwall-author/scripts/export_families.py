# -*- coding: utf-8 -*-
# Выгрузить семейства из АКТИВНОГО документа (тест) по id типоразмеров (из args-файлов загрузок) и по именам семейств:
# EditFamily -> SaveAs в out_dir -> Close без сохранения. Модель не меняется. Ход — в log_json построчно.
# Аргументы: args_files (с items[].symbol_id), symbol_ids, family_names, out_dir, log_json
import json, os
from Autodesk.Revit.DB import *
args = json.loads(HORIZUN_ARGS_JSON)
doc = __revit__.ActiveUIDocument.Document
sids = set(int(s) for s in args.get("symbol_ids", []))
for af in args.get("args_files", []):
    with open(af, encoding="utf-8-sig") as f:
        for it in json.load(f)["items"]:
            sids.add(int(it["symbol_id"]))
fams = {}
missing = []
for s in sorted(sids):
    e = doc.GetElement(ElementId(s))
    if isinstance(e, FamilySymbol):
        fams[e.Family.Name] = e.Family
    else:
        missing.append(s)
byname = dict((f.Name, f) for f in FilteredElementCollector(doc).OfClass(Family))
for n in args.get("family_names", []):
    if n in byname:
        fams[n] = byname[n]
    else:
        missing.append(n)
done = []
log = open(args["log_json"], "w", encoding="utf-8")
for i, (name, fam) in enumerate(sorted(fams.items())):
    rec = {"family": name, "ok": False}
    try:
        fd = doc.EditFamily(fam)
        try:
            opts = SaveAsOptions(); opts.OverwriteExistingFile = True
            fd.SaveAs(os.path.join(args["out_dir"], name + u".rfa"), opts)
            rec["ok"] = True
        finally:
            fd.Close(False)
    except Exception as ex:
        rec["error"] = str(ex)[:150]
    done.append(rec)
    log.write(json.dumps(rec, ensure_ascii=False) + "\n"); log.flush()
    checkpoint(name, i + 1, len(fams))
log.close()
__output__ = {"status": "completed_unverified", "summary": u"выгружено %d из %d; модель не изменена" % (sum(1 for r in done if r["ok"]), len(done)),
              "families": [r["family"] for r in done if r["ok"]], "errors": [r for r in done if not r["ok"]], "missing": missing}
