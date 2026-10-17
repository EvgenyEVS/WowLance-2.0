# Задание: C14 — Meet / Jitsi stub

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-17 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c14-meet-jitsi-stub` |
| **База** | актуальный `main` **после merge C10** (нужны C1 room + C3 UI) |
| **Параллельность** | ✅ **можно параллельно с C11 · C12 · C13 · C15 · C16 · C17** |
| **Фаза** | C14 (ссылка на видеозвонок комнаты, stub adapter) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 1–2 дня |
| **Канон** | [ADR-002](ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../AGENTS.md), [05-integration-map](architecture/05-integration-map.md) |
| **Предыдущее** | [C3 Room read](261010%20-%20задание%20C3%20Room%20read%20shell.md) |
| **Параллель** | [C11](261017%20-%20задание%20C11%20RoomCreated%20outbox.md) · [C12](261017%20-%20задание%20C12%20Slot%20unassign.md) · [C13](261017%20-%20задание%20C13%20Room%20health.md) · [C15](261017%20-%20задание%20C15%20Task%20roster%20assignee.md) · [C16](261017%20-%20задание%20C16%20Earnings%20stub.md) · [C17](261017%20-%20задание%20C17%20Member%20terminated.md) |

---

## 1. Зачем

По карте интеграций комната уводит людей во внешний Meet (Jitsi) по URL. Сейчас в RoomRead нет meeting-ссылки.

Нужен срез: при создании / по кнопке «Ensure meet» появляется **`meeting_url`** (stub Jitsi), отдаётся в GET room и в UI. Живой Jitsi API / SSO — **не** здесь.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `adapters/meet_stub.py`, поле `rooms.meeting_url`, RoomRead + RoomPage | Менять handoff outbox RoomCreated (C11) — кроме опционального поля в payload **только если** C11 ещё не влит и согласовано; иначе meet **после** create отдельным ensure |
| Миграция `009_c14_*` / `010_*` | Трогать slots unassign (C12), health агрегаты (C13) |
| Append contracts RoomRead | Ломать tasks/QG, earnings, termination |

**Рекомендация стыка с C11:** не писать meet внутри handoff create. Отдельный `POST …/meet/ensure` — безопаснее для параллели.

**Alembic:** колонка `meeting_url` nullable на `rooms`. Dual head с C11–C13/C15–C17 → merge на QA.

---

## 3. Не трогать / не делать

- Live Jitsi Admin API, JWT в ссылке, запись звонков.  
- RoomCreated / Quality Gate / staffing / health / earnings / termination.  
- Встраивать iframe Meet в SPA (достаточно внешней ссылки).

---

## 4. Продуктовые правила

1. `meeting_url` — nullable string; формат stub: `https://meet.jit.si/wowlance-{room_id}` (или из `MEET_BASE_URL` env).  
2. `POST /api/v1/rooms/{room_id}/meet/ensure`:  
   - нет комнаты → 404;  
   - url пустой → сгенерировать, сохранить, 200 `{ meeting_url, status: created }`;  
   - уже есть → 200 `{ meeting_url, status: already_exists }` (идемпотентно).  
3. `GET /api/v1/rooms/{id}` отдаёт `meeting_url` (null до ensure).  
4. Актор: валидный JWT / `X-Actor-Sub` как остальные `/api/v1` мутации.

---

## 5. Контракт

Дописать `contracts/wowlance/RoomRead.v1.yaml` (+ example):

```yaml
room.meeting_url: string | null

# новый фрагмент или RoomMeet.v1.yaml
paths:
  ensure:
    method: POST
    path: /api/v1/rooms/{room_id}/meet/ensure
response_200:
  required: [meeting_url, status]
  properties:
    meeting_url: string
    status: created | already_exists
```

Строка в `contracts/README.md`.

---

## 6. Код

### 6.1. Данные

`rooms.meeting_url` VARCHAR nullable. Миграция Alembic.

### 6.2. API / domain

`adapters/meet_stub.py` — `build_meeting_url(room_id) -> str`.  
`domain/meet.py` + тонкий `api` router (или метод в `rooms.py`).

### 6.3. Тесты

1. Ensure → url сохранён; повтор → `already_exists`, тот же url.  
2. GET room отражает `meeting_url`.  
3. Unknown room → 404.  
4. Регрессия: handoff / room read без meet зелёные.

### 6.4. Frontend

На `RoomPage`: показать ссылку Meet (если null — кнопка **Ensure meeting** / «Создать ссылку»).

### 6.5. Docs

`backend/README.md` — C14 curl ensure + env `MEET_BASE_URL`.

---

## 7. DoD

- [ ] Ветка `feature/c14-meet-jitsi-stub`.  
- [ ] Контракт + миграция + ensure + UI + pytest.  
- [ ] Не трогает C11–C13/C15–C17 зоны.  
- [ ] PR с ручным сценарием.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c14-meet-jitsi-stub
База: origin/main после C10.
Параллелен C11–C13 и C15–C17: не трогай handoff RoomCreated, staffing, health, tasks assignee, earnings, termination.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261017 - задание C14 Meet Jitsi stub.md

Сделай C14: meeting_url на room, meet_stub adapter, POST meet/ensure, RoomRead + UI ссылка, pytest, README.
Не делай live Jitsi API / iframe / outbox RoomCreated.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Ensure идемпотентен; handoff create не обязан создавать meet.  
- Параллель чистая (новая колонка + новый модуль).
