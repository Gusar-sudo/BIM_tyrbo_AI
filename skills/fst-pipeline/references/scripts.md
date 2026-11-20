# Скрипты `fst-pipeline` (каталог, собран `fst-pipeline/scripts/scripts_catalog.py`)

Запуск в Revit — `horizun_execute_python` с `code_path`; вне Revit — `python -I` (с графикой — `python -P -E`). Новый скрипт записи — из шаблона `fst-curtainwall-author/scripts/_template_write.py`. После добавления скрипта — пересобрать каталог.

| Скрипт | Что делает | Аргументы / запуск |
|---|---|---|
| `scripts_catalog.py` | Каталог скриптов skills: для каждого fst-* skill пишет references/scripts.md — скрипт, назначение (шапка), аргументы. Назначение — первые строки комментария/докстринга после «coding»; аргументы — строка с « | Аргумент»/«Запуск»/«Usage». Запуск: python -I scripts_catalog.py [skills_dir] |
| `scripts_classify.py` | Разбор описи: что держать (skills — единственный источник), что продвинуть из batches в skills, что в архив, что синхронизировать в plugin. py scripts_classify.py <scripts.csv> <plan.md> <plan.csv> | — |
| `scripts_inventory.py` | Опись скриптов: skills, _bim\batches, _bim\plugin — дубли по имени, совпадение содержимого, какая копия новее. py scripts_inventory.py <out.csv> <out.md> | — |
| `scripts_reorg.py` | Наведение порядка в скриптах 2026-11-13 (по плану audit\scripts_2026-11-13\README.md). Ничего не удаляет — только копирует/переносит в архив. | — |
