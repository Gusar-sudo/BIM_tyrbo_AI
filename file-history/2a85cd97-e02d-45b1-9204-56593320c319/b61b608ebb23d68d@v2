# -*- coding: utf-8 -*-
# Include ПОСЛЕ prep_fullglass_edge.py: объединяет его PREP с prep_type_params.py.
# pa: {"fg": {...аргументы prep_fullglass_edge...}, "tp": {"set": [...]}} — сначала края, потом параметры типов.
import io
_FG_PREP = PREP
exec(io.open(r"C:\Users\user\.claude\skills\fst-project-test\scripts\prep_type_params.py", encoding="utf-8").read())
_TP_PREP = PREP


def PREP(doc, pa=None):
    a = _FG_PREP(doc, pa["fg"]) if pa.get("fg") else {"loaded": 0, "load_fail": [], "swapped": [], "swap_fail": []}
    b = _TP_PREP(doc, pa["tp"]) if pa.get("tp") else {"loaded": 0, "load_fail": [], "swapped": [], "swap_fail": []}
    return {"loaded": a["loaded"] + b["loaded"], "load_fail": a["load_fail"] + b["load_fail"],
            "swapped": a["swapped"] + b["swapped"], "swap_fail": a["swap_fail"] + b["swap_fail"],
            "types_created": a.get("types_created", [])}
