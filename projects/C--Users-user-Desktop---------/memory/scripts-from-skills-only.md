---
name: scripts-from-skills-only
description: "Скрипты Revit/horizun запускать только из ~\\.claude\\skills\\fst-*\\scripts; batches — аргументы и результаты, плагин — копия skills"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2a85cd97-e02d-45b1-9204-56593320c319
  modified: 2026-11-12T19:17:04.460Z
---

Скрипты запускать только из `~\.claude\skills\fst-*\scripts`. В `_bim\batches` хранятся только аргументы (.json), результаты и картинки. Все старые .py оттуда 13.11.2026 убраны в `_bim\archive\2026-11-13_scripts` (manifest.csv). Новый скрипт, который понадобится ещё раз, сразу кладётся в нужный skill. Плагин `_bim\plugin\fst-bim\skills` не правится: его пересобирают копией skills (`fst-pipeline\scripts\scripts_inventory.py` + `scripts_classify.py` проверяют расхождения).

**Why:** 12–13.11.2026 запущена старая копия corner_schemes.py из batches: на схеме FSC08 «примыкание съехало», и получился ложный вывод о пересечении. Пользователь сам заметил по картинке и попросил аудит скриптов.
**How to apply:** перед запуском убедиться, что путь начинается с `~\.claude\skills\`. После правки скрипта в skills перед выпуском обновить плагин (см. [[designer-tooling-deferred]]).
