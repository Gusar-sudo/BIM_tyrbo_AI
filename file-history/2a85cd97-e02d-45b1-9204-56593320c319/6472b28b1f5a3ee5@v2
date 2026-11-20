# -*- coding: utf-8 -*-
# Локально: как контур семейства уплотнителя (seal_profiles.json) ложится в сечение (seal_sections.json):
# перебор 8 ориентаций (поворот 0/90/180/270 × зеркало) + сдвиг, лучшая — по среднему расстоянию точек.
# Печатает для каждого сечения и уплотнителя (U по толщине стекла): ориентацию, сдвиг, ошибку, положение стекла.
# py -P -E seal_fit.py <sections.json> <seal_profiles.json> <out.json>
import json, io, sys, math
import numpy as np
S = json.load(io.open(sys.argv[1], encoding="utf-8")); P = json.load(io.open(sys.argv[2], encoding="utf-8"))
U = {5: "U5", 6: "U6", 8: "U8", 10: "U10"}
fam = {}
for k, v in P.items():
    u = k.split("FS.C-")[1].split("_")[0]
    cs = list(v.values())[0]
    pts = np.array([p for c in cs for p in c["pts"]], float)
    fam[u] = pts


def samp(loop, step=0.2):
    out = []
    for i in range(len(loop)):
        a = np.array(loop[i]); b = np.array(loop[(i + 1) % len(loop)])
        n = max(1, int(np.linalg.norm(b - a) / step))
        for t in range(n): out.append(a + (b - a) * t / n)
    return np.array(out)


def dist(A, B):
    d = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(-1))
    return 0.5 * (d.min(1).mean() + d.min(0).mean())


ORI = []
for m in (1, -1):
    for r in range(4):
        c, s = [(1, 0), (0, 1), (-1, 0), (0, -1)][r]
        ORI.append(((m, r), np.array([[c * m, -s], [s * m, c]], float)))
res = []
for rec in S:
    glass = [it for it in rec["items"] if u"Стекл" in it["mat"]]
    seals = [it for it in rec["items"] if u"Уплотн" in it["mat"]]
    for sl in seals:
        L = np.array(sl["loops"][0], float); c0 = L.mean(0)
        # ближайшее стекло -> толщина
        best_g = None
        for g in glass:
            G = np.array(g["loops"][0], float)
            dd = np.abs(G[:, None, :] - c0[None, None, :]).sum()
            t = round(np.ptp(G[:, 1]), 1) if np.ptp(G[:, 0]) > np.ptp(G[:, 1]) else round(np.ptp(G[:, 0]), 1)
            dc = np.linalg.norm(G.mean(0) - c0)
            if best_g is None or dc < best_g[0]: best_g = (dc, t, G)
        t = int(round(best_g[1])); u = U.get(t)
        if u is None or u not in fam: continue
        A = samp(L.tolist()); F = fam[u]
        best = None
        for key, M in ORI:
            Fr = F @ M.T
            sh = (A.min(0) + A.max(0)) / 2 - (Fr.min(0) + Fr.max(0)) / 2
            e = dist(A[::3], Fr + sh)
            if best is None or e < best[0]: best = (e, key, sh.tolist())
        G = best_g[2]
        res.append({"profile": rec["profile"], "type": rec["mullion_type"], "glass_mm": t, "seal": u, "err_mm": round(best[0], 3),
                    "ori": best[1], "shift": [round(v, 3) for v in best[2]],
                    "glass_bbox": [round(G[:, 0].min(), 2), round(G[:, 1].min(), 2), round(G[:, 0].max(), 2), round(G[:, 1].max(), 2)],
                    "seal_loop": L.tolist(), "glass_loop": G.tolist()})
io.open(sys.argv[3], "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False))
for r in res[:200]:
    if r["err_mm"] > 0.05 or r["glass_mm"] != 5:
        print(r["type"], r["seal"], "err", r["err_mm"], "ori", r["ori"], "shift", r["shift"], "glass", r["glass_bbox"])
print("всего", len(res), "макс ошибка", max(r["err_mm"] for r in res))
