---
name: git-save-everything
description: "Всё, что требует сохранения (skills, память, документы _bim), отправлять в git-репозиторий Desktop\\git_bim → github.com/Gusar-sudo/BIM_tyrbo_AI"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2a85cd97-e02d-45b1-9204-56593320c319
  modified: 2026-11-20T13:00:04.224Z
---

С 17–20.11.2026 у пользователя есть git: репозиторий `C:\Users\user\Desktop\git_bim` (remote `https://github.com/Gusar-sudo/BIM_tyrbo_AI.git`, ветка main). Это зеркало папки `~\.claude` (skills/, projects/…/memory, CLAUDE.md, sessions). Пользователь: «теперь ты отправляешь туда всё, что требует сохранения».

20.11.2026: `~\.claude\skills` и `~\.claude\projects\C--Users-user-Desktop---------\memory` — **ссылки (junction)** на папки в `git_bim`; правки skills и памяти сразу попадают в рабочую копию репозитория — остаётся `git add/commit/push`. Транскрипты сессий пишутся в `~\.claude\projects\…` (не в репозиторий).

**Why:** надёжное хранение и история изменений вне одной машины; сессии/транскрипты уже лежат там (LFS для больших .jsonl).

**How to apply:** после каждой сохранённой партии работы — синхронизировать изменённые skills (`~\.claude\skills\fst-*` → `git_bim\skills\`), память (`projects\C--Users-user-Desktop---------\memory`) и текстовые документы `_bim` (отчёты аудита, findings, decisions, handoff, params, questions, plugin) в `git_bim`, коммит с понятным русским сообщением, `git push`. Модели .rvt/.rfa (200+ МБ) в git не класть (лимит GitHub 100 МБ) — для них снимки в `_bim\archive`. Не коммитить секреты (токены, ключи `sessions\*.key`). Связано с [[scripts-from-skills-only]].
