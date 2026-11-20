"""DWG → DXF локально бесплатными средствами: LibreDWG (dwg2dxf, GPL) или ODA File Converter (если установлен).

Ничего не скачивает и не отправляет. Конвертер ищется:
  1) --converter <путь к dwg2dxf.exe или ODAFileConverter.exe>;
  2) переменная окружения FST_DWG2DXF;
  3) C:\\Users\\<user>\\Tools\\libredwg-*\\**\\dwg2dxf.exe;
  4) ODA File Converter через ezdxf.addons.odafc (если ODA установлен).
Запуск:
  py -P -E dwg_to_dxf.py <файл.dwg> <папка_вывода> [--converter PATH] [--timeout 900]
Выход: <папка>/<имя>.dxf и <имя>.convert.json (конвертер, версия, sha256 исходника, время, stderr).
Замечание: LibreDWG — ночные сборки; результат проверять по dxf_extract (единицы, листы, тексты).
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def find_converter(explicit):
    if explicit:
        return explicit
    if os.environ.get("FST_DWG2DXF"):
        return os.environ["FST_DWG2DXF"]
    hits = sorted(glob.glob(str(Path.home() / "Tools" / "libredwg-*" / "**" / "dwg2dxf.exe"), recursive=True))
    return hits[-1] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dwg"); ap.add_argument("out_dir")
    ap.add_argument("--converter"); ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    src, out = Path(a.dwg), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dst = out / (src.stem + ".dxf")
    rec = {"source": str(src), "source_sha256": sha256(src), "dxf": str(dst), "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    conv = find_converter(a.converter)
    t0 = time.time()
    if conv and Path(conv).name.lower().startswith("dwg2dxf"):
        rec["converter"] = f"LibreDWG {conv}"
        # -y перезаписать, --as r2018 сохранить версию; минимальный вывод
        p = subprocess.run([conv, "-y", "-o", str(dst), str(src)], capture_output=True, text=True,
                           timeout=a.timeout, encoding="utf-8", errors="replace")
        rec.update(returncode=p.returncode, stderr_tail=p.stderr[-2000:])
    else:
        try:
            from ezdxf.addons import odafc
        except ImportError:
            sys.exit("нет конвертера: укажите --converter или установите LibreDWG/ODA")
        if conv:
            odafc.win_exec_path = conv
        if not odafc.is_installed():
            sys.exit("конвертер не найден: LibreDWG (dwg2dxf.exe) или ODA File Converter")
        rec["converter"] = "ODA File Converter (ezdxf.addons.odafc)"
        odafc.convert(str(src), str(dst), version="R2018", replace=True)
        rec["returncode"] = 0
    rec["seconds"] = round(time.time() - t0, 1)
    rec["ok"] = dst.exists() and dst.stat().st_size > 0
    (out / (src.stem + ".convert.json")).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: rec[k] for k in ("converter", "ok", "seconds", "dxf")}, ensure_ascii=False))
    sys.exit(0 if rec["ok"] else 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
