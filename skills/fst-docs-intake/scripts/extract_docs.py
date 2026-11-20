"""Извлекает текст из документов производителя (PDF, DOCX, XLSX) в папку extract/.

Работает только локально: читает файлы, пишет .txt и index.json. Сеть не используется.
Запуск:  py -I extract_docs.py <папка_с_документами> <папка_для_результата>

Для каждого файла пишется <имя>.txt с метками страниц «=== стр. N ===» (для PDF),
а в index.json — путь, размер, дата, sha256, число страниц, число символов и пометка
«мало текста» (вероятно скан или чертёж — нужен визуальный разбор).
"""
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime
from html import unescape
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:  # pypdf нужен только для PDF
    PdfReader = None

SKIP_DIRS = {"_bim", "extract"}
LOW_TEXT_PER_PAGE = 80  # меньше — вероятно скан/чертёж


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_xml(xml: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", xml))


def read_docx(path: Path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
        images = sum(1 for n in z.namelist() if n.startswith("word/media/"))
    xml = xml.replace("</w:p>", "\n").replace("<w:tab/>", "\t").replace("</w:tc>", " | ")
    return strip_xml(xml), 1, images


def read_xlsx(path: Path):
    out = []
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            sx = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
            shared = [strip_xml(m) for m in re.findall(r"<si>(.*?)</si>", sx, re.S)]
        sheets = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml", n))
        for name in sheets:
            out.append(f"=== {name} ===")
            wx = z.read(name).decode("utf-8", "replace")
            for row in re.findall(r"<row[^>]*>(.*?)</row>", wx, re.S):
                cells = []
                for attrs, inner in re.findall(r"<c ([^>]*?)(?:/>|>(.*?)</c>)", row, re.S):
                    v = re.search(r"<v>(.*?)</v>", inner or "")
                    v = v.group(1) if v else ""
                    if 't="s"' in attrs and v:
                        v = shared[int(v)]
                    elif 't="inlineStr"' in attrs:
                        v = strip_xml(inner)
                    cells.append(v)
                out.append(" | ".join(cells))
    return "\n".join(out), len(sheets), 0


def read_pdf(path: Path):
    if PdfReader is None:
        raise RuntimeError("pypdf не установлен")
    reader = PdfReader(str(path))
    parts = []
    for i, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
        except Exception as e:  # битая страница не должна ронять весь файл
            text = f"[ошибка извлечения: {e}]"
        parts.append(f"=== стр. {i} ===\n{text}")
    return "\n".join(parts), len(reader.pages), 0


READERS = {".pdf": read_pdf, ".docx": read_docx, ".xlsx": read_xlsx}


def main(src: Path, dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    index = []
    for path in sorted(src.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in READERS:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(src).parts):
            continue
        rel = path.relative_to(src)
        entry = {
            "file": str(rel),
            "size_kb": round(path.stat().st_size / 1024),
            "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            "sha256": sha256(path),
        }
        try:
            text, pages, images = READERS[path.suffix.lower()](path)
            out_name = re.sub(r"[\\/]", "__", str(rel)) + ".txt"
            (dst / out_name).write_text(text, encoding="utf-8")
            entry.update(txt=out_name, pages=pages, chars=len(text), images=images,
                         low_text=len(text.strip()) < LOW_TEXT_PER_PAGE * max(pages, 1))
        except Exception as e:
            entry.update(error=str(e))
        index.append(entry)
        print(("ERR " if "error" in entry else "ok  ") + str(rel), entry.get("pages", ""), entry.get("chars", ""))
    (dst / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"files: {len(index)}  errors: {sum('error' in e for e in index)}  low_text: {sum(e.get('low_text', False) for e in index)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: extract_docs.py <src_dir> <dst_dir>")
    sys.stdout.reconfigure(encoding="utf-8")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
