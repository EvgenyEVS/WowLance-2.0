# Задание: C26 — Founder-demo пакет

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-22 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c26-founder-demo-pack` |
| **База** | актуальный `main` **после merge C25** |
| **Параллельность** | ✅ **можно параллельно с C27 · C28 · C29** |
| **Фаза** | C26 (упакованный demo-сценарий на stubs) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](../../canon/ADR-002-wowlance-2.0-platform-room.md), [зоны до согласования](../../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) |
| **Параллель** | [C27 RBAC](261022%20-%20задание%20C27%20Room%20RBAC.md) · [C28 QA](261022%20-%20задание%20C28%20QA%20C0-C25.md) · [C29 UX](261022%20-%20задание%20C29%20Room%20UX%20polish.md) |

> Контракты граничные — **draft**. Реализация через stub. Live не делать. Не ломать золотой путь G1–G10.

---

## 1. Зачем

Стейкхолдерам нужен **один** воспроизводимый путь: handoff → entitlement → команда → QG → Hot → health — без знания всех curl из README.

Нужен пакет: чеклист + скрипт (PowerShell) + короткая страница «Demo» в docs/frontend. Без live соседей.

---

## 2. Параллель

| Можно | Нельзя |
|-------|--------|
| `docs/demo/`, `scripts/founder-demo.ps1`, ссылка в README | Менять RBAC (C27), продукт API ради demo |
| Seed через существующие endpoints | Live Strategy/CRM/Talent |
| Минимальная кнопка «Demo room» в UI **опционально** | Ломать pytest / миграции |

---

## 3. Не делать

- Live adapters, Gateway, новый граничный контракт.  
- Авто-создание «магической» комнаты в БД в обход handoff.  
- Deep CRM / биллинг.

---

## 4. Продуктовые правила

1. Скрипт `scripts/founder-demo.ps1` (или `backend/scripts/`):  
   - handoff (sale example) → print `room_id`  
   - entitlement  
   - materialize → roster upsert ×2 → assign  
   - task create/start/complete(proof)/accept  
   - lead create/hot/handoff-crm  
   - meet ensure, health GET (+ publish optional)  
   - печатает URL UI `/rooms/{id}`  
2. Чеклист `docs/demo/founder-demo.md` — те же шаги глазами + что смотреть в UI.  
3. Prefers `AUTH_DISABLED=true`; если internal strict — читает `INTERNAL_SERVICE_TOKEN` из env.  
4. Идемпотентность: повторный прогон либо новый handoff id, либо документ «создаёт новую комнату каждый раз».  
5. Не требует Node для API-части; UI — ручной шаг.

---

## 5. DoD

- [ ] Скрипт + docs чеклист + строка в корневом README / backend README.  
- [ ] Прогон на чистом `main` после `alembic upgrade head` успешен.  
- [ ] Не меняет доменную логику (или только минимальный glue).  
- [ ] PR.

---

## 6. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c26-founder-demo-pack
База: origin/main после C25.
Параллелен C27–C29: не трогай RBAC, не большой UX-рефактор.
Задание: docs/261022 - задание C26 Founder demo pack.md
Контракты draft; stub only; live не делать; не ломать G1–G10.

Сделай: scripts/founder-demo.ps1 + docs/demo/founder-demo.md + ссылка в README.
План 5–7 шагов, маленькие коммиты.
```
