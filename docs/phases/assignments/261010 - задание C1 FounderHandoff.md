# Задание: C1 — FounderHandoff → комната со снимком

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-10 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c1-founder-handoff` от актуального `main` |
| **Фаза** | C1 (первый вертикальный срез после скелета) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–4 дня |
| **Канон** | [ADR-002](../../canon/ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../../../AGENTS.md) |
| **Контракт** | [`contracts/strategy/FounderHandoff.v1.yaml`](../../../contracts/strategy/FounderHandoff.v1.yaml) |
| **Пример** | [`contracts/strategy/examples/FounderHandoff.sale.json`](../../../contracts/strategy/examples/FounderHandoff.sale.json) |

---

## 1. Зачем

Пока нет рабочего «кнопка из Стратегии → комната в WowLance», 2.0 — пустой каркас. C1 доказывает архитектуру: **своя PostgreSQL**, снимок стратегии, идемпотентный handoff, staffing ещё закрыт без entitlement.

React и Keycloak в этом тикете **не** цель. UI можно не трогать.

---

## 2. Не трогать / не делать

- Django-репозиторий WowLance 1.0 (код не копировать; смыслы — только reference).
- Реальный Keycloak / Gateway / чтение БД Strategy или Talent.
- Staffing, слоты, matching, каталог фрилансеров.
- CRM, Jira, Accept `StrategyPublished`, биллинг end-to-end.
- Полировка React, админка, Alembic-история «на будущее» без рабочей миграции create.
- Менять ADR и концепции A/B/C без явной причины; контракт — только если найден баг схемы (тогда PR с обоснованием в `contracts/`).

---

## 3. Продуктовые правила (жёстко)

1. Чужую БД не читать. Payload приходит в теле POST.  
2. Комната **может** создаться до оплаты.  
3. В ответе всегда `staffing_unlocked: false` (entitlement — следующий тикет).  
4. Один `handoff_id` → одна комната (идемпотентность).  
5. Снимок стратегии после создания **не редактируется** этим endpoint’ом.  
6. Файлы в payload — только URI + checksum; байты не качать в C1 (достаточно сохранить metadata).

---

## 4. Что сделать

### 4.1. Инфра

- `docker compose up -d db` работает из корня репо.  
- Backend читает `DATABASE_URL` (см. `.env.example`).  
- SQLAlchemy 2 + миграции (Alembic **или** эквивалент с одной начальной ревизией — на твой выбор, но `upgrade` должен поднимать схему с нуля).

### 4.2. Модели (минимум)

Имена можно уточнить, смысл сохранить:

| Сущность | Поля (минимум) |
|----------|----------------|
| `User` (shadow) | `sub` (PK или unique), `display_name` optional |
| `Room` | `id`, `room_type` (`sale`\|`develop`), `name`, `timezone`, `founder_sub` FK/ref, `handoff_id` **unique**, `staffing_unlocked` default `false`, timestamps |
| `StrategySnapshot` | `room_id`, `strategy_id`, `strategy_version`, JSON strategy payload, documents JSON, staffing_intent JSON optional, commercial JSON optional; **immutable** после insert |

Связь: Room 1—1 StrategySnapshot (или 1—N с «current» — для C1 достаточно одной строки на комнату).

### 4.3. API

```http
POST /internal/v1/handoffs
Content-Type: application/json
```

- Валидация тела строго по контракту v1 (Pydantic-модели, зеркало YAML).  
- Успех **200** (или **201** на первый create — выбери одно и зафиксируй в OpenAPI/README; идемпотентный повтор — тот же код + `status: already_exists`).  
- Тело ответа: `{ "room_id", "status": "created"|"already_exists", "staffing_unlocked": false }`.  
- Повтор с **тем же** `handoff_id` и тем же смысловым payload → `already_exists`, тот же `room_id`.  
- Повтор с тем же `handoff_id` и **другим** payload → **409**.  
- Битый JSON / нет required → **422**.

Auth: в C1 **не** внедрять Keycloak. Допустимо: открытый internal endpoint + комментарий «за Gateway / service token later». Не оставляй TODO без строки в README backend.

### 4.4. Сервисный слой

Логику создания комнаты держать в `domain/` или `services/`, не в толстом router. Router = validate + call + map errors.

### 4.5. Тесты (обязательно)

pytest + TestClient; БД — PostgreSQL из compose **или** отдельная test DB (не SQLite, если можно избежать; если очень нужно — только с явной пометкой в PR, предпочтение PG).

Минимум:

1. Happy path: example `FounderHandoff.sale.json` → `created`, строка Room + Snapshot в БД, `staffing_unlocked is False`.  
2. Идемпотентность: второй POST → `already_exists`, count(Room)==1.  
3. Conflict: тот же `handoff_id`, другой `strategy_version` → 409.  
4. Validation: без `offer` → 422.  
5. `room_type: develop` тоже создаётся (достаточно одного теста).

`GET /health` не ломать.

### 4.6. Документация в репо

Кратко в `backend/README.md` (создать, если нет):

- как поднять db + uvicorn;  
- пример `curl` с example JSON;  
- выбранный статус-код create vs already_exists.

---

## 5. Критерии приёмки (DoD)

- [ ] Ветка от свежего `main`, PR в `main` (или готовая ветка на review).  
- [ ] Миграции поднимают схему на чистой PG.  
- [ ] `POST /internal/v1/handoffs` соответствует контракту v1.  
- [ ] Идемпотентность и 409 покрыты тестами.  
- [ ] `staffing_unlocked` всегда false.  
- [ ] Нет обращения к внешним БД/HTTP Strategy.  
- [ ] `pytest` зелёный в CI локально: `cd backend && pytest`.  
- [ ] В PR: 5–10 строк «как проверить руками» + что сознательно отложено.

---

## 6. Вне скоупа (следующими тикетами)

- `EntitlementGranted` → `staffing_unlocked=true`  
- React: экран комнаты / список  
- Keycloak JWT  
- Скачивание файлов из object storage  
- Outbox `RoomCreated`  

---

## 7. Промпт для стажёра + ИИ (копировать целиком)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c1-founder-handoff от origin/main
Стек только: FastAPI, React (не трогать в этом тикете), PostgreSQL, OpenSpec (contracts/), Superpowers.
Читай AGENTS.md и docs/canon/ADR-002-wowlance-2.0-platform-room.md.
Задание: docs/261010 - задание C1 FounderHandoff.md

Сделай C1:
1) docker compose db + SQLAlchemy модели User(shadow sub), Room, StrategySnapshot
2) миграции схемы
3) POST /internal/v1/handoffs по contracts/strategy/FounderHandoff.v1.yaml
   - идемпотентность по handoff_id
   - same id + different payload → 409
   - staffing_unlocked всегда false
   - снимок immutable после create
4) pytest: happy path (examples/FounderHandoff.sale.json), idempotent, 409, 422, develop room_type
5) backend/README.md с curl

Не копируй Django WowLance 1.0. Не читай чужие БД. Не делай Keycloak, React UI, staffing, CRM, Jira.
Сначала план из 5–8 шагов, потом код маленькими коммитами. Контракт YAML не ломай без причины.
```

---

## 8. Ревьюеру (чеклист)

- Соответствие path/полям YAML, не «почти как в ADR».  
- Уникальный индекс на `handoff_id`.  
- Нет скрытого «обновить snapshot» на повторном POST.  
- Тесты реально бьют БД, не только мок сервиса.  
- Секреты/`.env` не в git.
