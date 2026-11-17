<div align="center">

<img src="docs/banner.png" alt="BIM_tyrbo_AI" width="100%"/>

# 🏗️ BIM_tyrbo_AI

**Скилы создания BIM-моделей и BIM-семейств — с ИИ-навигацией**

[![BIM](https://img.shields.io/badge/BIM-Revit%20%7C%20IFC%20%7C%20Dynamo-1f6feb?style=for-the-badge)](#)
[![AI-Ready](https://img.shields.io/badge/AI--Ready-RAG%20%7C%20LLM-8957e5?style=for-the-badge)](#)
[![Status](https://img.shields.io/badge/status-active-2ea043?style=for-the-badge)](#)
[![Access](https://img.shields.io/badge/access-semi--private-d29922?style=for-the-badge)](#)

🌐 **Русский** · [English](./README.en.md)

</div>

---

## 📖 О репозитории

**BIM_tyrbo_AI** — база знаний и методологий для быстрого и предсказуемого
создания BIM-моделей и BIM-семейств. Репозиторий спроектирован так, чтобы
**ИИ-ассистент мог находить и подтягивать нужный скил** по запросу, а человек —
читать как понятную инструкцию.

> 🎯 Один скил = один структурированный `.md` с метаданными, примерами и проверкой результата.

---

## ✨ Что внутри

| Раздел | Что даёт |
|--------|----------|
| 🧩 **Skills** | Пошаговые скилы создания моделей и семейств |
| 👪 **Families** | Параметрические BIM-семейства и шаблоны |
| 📐 **Methodologies** | Стандарты, LOD/LOI, правила именования |
| 🔗 **Workflows** | Связки «семейство + методология + скрипт» |
| 🤖 **AI-ready** | Метаданные и каталог для RAG/LLM-поиска |

---

## 🧠 Как это работает

```mermaid
flowchart LR
    A[Запрос: «нужна дверь LOD 300»] --> B{AI-ассистент}
    B --> C[Каталог скилов]
    C --> D[Скил + семейство]
    D --> E[Готовая BIM-модель]
