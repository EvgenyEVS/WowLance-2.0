# Задание: C20 — Room chat stub

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-19 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c20-room-chat` |
| **База** | актуальный `main` **после merge C15** (нужны C3 RoomPage + C8 actor) |
| **Параллельность** | ✅ **можно параллельно с C16 · C17 · C18 · C19 · C21** |
| **Фаза** | C20 (лента сообщений комнаты) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md) · наследие 1.0 room comms |
| **Предыдущее** | [C3 Room read](261010%20-%20задание%20C3%20Room%20read%20shell.md) · [C8 JWT](261016%20-%20задание%20C8%20Keycloak%20JWT.md) |
| **Параллель** | [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) · [C18](261019%20-%20задание%20C18%20StaffingUnlocked%20outbox.md) · [C19](261019%20-%20задание%20C19%20CRM%20deal%20status.md) · [C21](261019%20-%20задание%20C21%20Internal%20service%20token.md) |

---

## 1. Зачем

В 1.0 в комнате был канал общения. В 2.0 UI — только staffing/tasks/leads. Нужен тонкий срез: **сообщения комнаты** (list + post), без WebSocket, без директор↔тимлид отдельного канала и без файлов.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Новые `room_messages`, `domain/chat.py`, `api/chat.py`, `ChatPanel` | Трогать accept/earnings (C16), terminate/slots (C17) |
| Append RoomPage | Менять entitlement outbox, CRM webhook, auth middleware (C18/C19/C21) |
| Миграция своей таблицы | Ломать TasksPanel/LeadsPanel сверх вставки соседа |

**Alembic:** `010_c20_*` / `011_*`. Dual head с C16–C19/C21 → merge на QA.

**Auth:** мутации под `/api/v1` + `get_actor_sub` (как tasks).

---

## 3. Не трогать / не делать

- WebSocket / SSE realtime (достаточно poll Refresh).  
- Вложения / object storage.  
- RBAC «только teamlead пишет».  
- Отдельные треды DT / личные чаты.  
- Jira comments sync.

---

## 4. Продуктовые правила

1. Сообщение: `id`, `room_id`, `author_sub`, `body` (1…2000 chars), `created_at`.  
2. `GET /api/v1/rooms/{room_id}/messages` — последние N (default 50, max 100), order by created_at asc.  
3. `POST /api/v1/rooms/{room_id}/messages` body `{ "body": "…" }` — author = actor; 201/200.  
4. Нет комнаты → 404. Пустой body / >max → 422.  
5. Без actor → 422 (AUTH_DISABLED) / 401 (строгий C8).  
6. Редактирование/удаление — **вне scope** (нет).

---

## 5. Контракт

Файл: `contracts/wowlance/RoomMessages.v1.yaml`  
Пример: `contracts/wowlance/examples/RoomMessages.sale.json`

```yaml
id: RoomMessages
version: "1"
channel: https

message:
  required: [id, room_id, author_sub, body, created_at]

paths:
  list:  GET  /api/v1/rooms/{room_id}/messages
  post:  POST /api/v1/rooms/{room_id}/messages
    request: { required: [body], properties: { body: string } }
```

`contracts/README.md` — строка.

---

## 6. Код

### 6.1. Данные

Таблица `room_messages` + FK room + index `(room_id, created_at)`.

### 6.2. API / domain

Тонкий CRUD list/create.

### 6.3. Тесты

1. Post → list содержит сообщение с author_sub.  
2. Unknown room → 404.  
3. Empty body → 422.  
4. Регрессия: room read / tasks не ломаются.

### 6.4. Frontend

`ChatPanel` на RoomPage: список + форма Send + Refresh (без websocket).

### 6.5. Docs

backend/frontend README — C20.

---

## 7. DoD

- [ ] Ветка `feature/c20-room-chat`.  
- [ ] Контракт + миграция + API + UI + pytest.  
- [ ] Не трогает C16–C19/C21 зоны.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c20-room-chat
База: origin/main после C15.
Параллелен C16–C19 и C21: не трогай earnings, terminate, entitlement outbox, CRM deal, service-token.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261019 - задание C20 Room chat.md

Сделай C20: room_messages; GET/POST messages; ChatPanel; pytest; контракт; README.
Не делай WebSocket, вложения, RBAC ролей, удаление сообщений.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Изолированный модуль — идеален для параллели.  
- Poll-only OK для DoD.
