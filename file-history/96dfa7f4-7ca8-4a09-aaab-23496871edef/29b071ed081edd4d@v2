"""Проверка и упаковка skill в .skill (zip) без сторонних библиотек.

Правила как у skill-creator quick_validate: SKILL.md с фронтматтером; name — kebab-case до 64
символов и совпадает с папкой; description есть, без < >, не длиннее 1024 символов.
В архив не попадают evals/ (в корне skill), __pycache__, *.pyc.
Запуск: py -P -E pack_skills.py <папка skills> <папка dist>
"""
import re
import sys
import zipfile
from pathlib import Path


def frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep and not line.startswith(" "):
            fm[k.strip()] = v.strip()
    return fm


def validate(skill: Path):
    errs = []
    md = skill / "SKILL.md"
    if not md.exists():
        return ["нет SKILL.md"]
    fm = frontmatter(md.read_text(encoding="utf-8"))
    if fm is None:
        return ["нет фронтматтера"]
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        errs.append(f"name «{name}» не kebab-case/длинное")
    if name != skill.name:
        errs.append(f"name «{name}» ≠ папка «{skill.name}»")
    if not desc:
        errs.append("пустой description")
    if "<" in desc or ">" in desc:
        errs.append("в description есть < или >")
    if len(desc) > 1024:
        errs.append(f"description {len(desc)} > 1024 символов")
    return errs


def pack(skill: Path, dist: Path):
    out = dist / f"{skill.name}.skill"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(skill.rglob("*")):
            rel = f.relative_to(skill.parent)
            if f.is_dir() or "__pycache__" in rel.parts or f.suffix == ".pyc":
                continue
            if len(rel.parts) > 1 and rel.parts[1] == "evals":
                continue
            z.write(f, rel.as_posix())
    return out


def main(skills_dir, dist_dir):
    dist = Path(dist_dir); dist.mkdir(parents=True, exist_ok=True)
    bad = 0
    for skill in sorted(p for p in Path(skills_dir).iterdir() if p.is_dir()):
        errs = validate(skill)
        if errs:
            bad += 1
            print(f"FAIL {skill.name}: " + "; ".join(errs))
            continue
        out = pack(skill, dist)
        print(f"ok   {skill.name} -> {out.name} ({out.stat().st_size // 1024} КБ)")
    print("ошибок:", bad)
    return bad


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(1 if main(sys.argv[1], sys.argv[2]) else 0)
