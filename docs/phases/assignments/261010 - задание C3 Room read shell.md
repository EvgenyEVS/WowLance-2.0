# Задание: C3 — GET room + React room shell

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-10 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c3-room-read-shell` |
| **База** | актуальный `main` **после merge C1** (`feature/c1-founder-handoff`) |
| **Параллельность** | ✅ **можно делать параллельно с C2** (`feature/c2-entitlement-unlock`) |
| **Фаза** | C3 (read-модель + тонкий UI) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Связано** | [C1 Handoff](261010%20-%20задание%20C1%20FounderHandoff.md) · [C2 Entitlement](261010%20-%20задание%20C2%20Entitlement%20unlock.md) |

---

## 1. Зачем

После C1 комнату можно создать только через `curl`/Swagger. Нужен **просмотр**: API чтения + простой React-экран со снимком стратегии и флагом staffing. Так стейкхолдеры видят результат handoff без ожидания полного staffing.

C2 (entitlement) меняет только запись флага — этот тикет **читает** `staffing_unlocked` как есть (`false` до merge C2, `true` после). Конфликтов по смыслу почти нет.

---

## 2. Параллель с C2 — правила стыковки

| Можно | Нельзя |
|-------|--------|
| Новые файлы: `api/rooms.py`, `frontend/src/pages/*`, контракт read | Трогать `POST /internal/v1/handoffs` и логику create |
| Читать `Room.staffing_unlocked` | Менять схему entitlements / миграции C2 |
| Прокси Vite на `/api` или `/rooms` | Редактировать те же строки в `models.py`, что правит C2, без согласования |

Если C2 ещё не влит: UI показывает «Staffing locked». После merge C2 тот же экран начнёт показывать unlocked без доработки (или с крошечным регрессом).  
Merge order: безразличен; при конфликте в `main.py` (include_router) — оставить оба роутера.

---

## 3. Не трогать / не делать

- Staffing, слоты, Talent roster, matching.  
- Keycloak / настоящий login (достаточно открытого read или заглушки).  
- `POST /entitlements` (это C2).  
- Редактор стратегии, Accept `StrategyPublished`.  
- CRM, Jira, чат, задачи.  
- Полировка дизайна «как продукт» — один читаемый экран.  
- Копировать Django-шаблоны 1.0.

---

## 4. Контракт (лёгкий OpenSpec)

Файл: `contracts/wowlance/RoomRead.v1.yaml`  
Пример ответа: `contracts/wowlance/examples/RoomRead.sale.json`

```yaml
id: RoomRead
version: "1"
direction: client -> WowLance
channel: https
path: /api/v1/rooms/{room_id}
method: GET

response_200:
  required: [id, name, room_type, timezone, founder_sub, staffing_unlocked, strategy]
  properties:
    id: uuid
    name: string
    room_type: sale | develop
    timezone: string
    founder_sub: string
    handoff_id: uuid
    staffing_unlocked: boolean
    strategy:
      strategy_id: uuid
      strategy_version: string
      offer / audience / hot_criteria / utp?  # из snapshot.strategy_payload
      documents: [{ role, uri, checksum }]     # metadata only
      staffing_intent: object | null
    created_at: datetime

errors:
  - 404 when room missing
```

Строка в `contracts/README.md`.

---

## 5. Backend

### 5.1. API

```http
GET /api/v1/rooms/{room_id}
```

- 200 + тело по контракту; 404 если нет комнаты.  
- Join/load `StrategySnapshot`; не отдавать внутренний `request_fingerprint`, если нет нужды.  
- Роутер отдельно от handoffs; сервис `domain/room_read.py` (или аналог).

Опционально (не обязательно):

```http
GET /api/v1/rooms?founder_sub=...
```

список id+name для удобства демо — только если останется время.

### 5.2. Тесты

1. Handoff → GET по `room_id` → 200, поля offer/audience/hot_criteria совпадают с example.  
2. `staffing_unlocked` в ответе отражает БД (`false` после одного handoff).  
3. Несуществующий uuid → 404.  
4. Регрессия: handoff-тесты C1 зелёные.

### 5.3. CORS / proxy

Чтобы React ходил на API локально: уже есть proxy в `frontend/vite.config.ts` — добавить `/api`.  
При необходимости CORSMiddleware на FastAPI для `localhost:5173`.

---

## 6. Frontend (React + Vite + TS)

Минимальный shell:

1. Маршрут или query: `/rooms/:roomId` (react-router **или** без роутера — поле ввода UUID + кнопка «Open» на стартовой странице; роутер предпочтителен, но не обязателен).  
2. `fetch('/api/v1/rooms/' + id)` → показать:
   - название, тип, timezone;  
   - бейдж **Staffing locked** / **Staffing unlocked** по флагу;  
   - блок стратегии: offer, audience, hot_criteria;  
   - список documents (role + uri текстом, без скачивания).  
3. Состояния: loading / error 404 / ok.  
4. На стартовой странице — короткая подсказка: создать комнату через Swagger/curl C1, вставить `room_id`.

`npm install` + `npm run dev` должны работать (Node должен быть в PATH у исполнителя).

Стили: достаточно аккуратного CSS как у текущего shell; не тащить UI-kit.

---

## 7. DoD

- [ ] Ветка **`feature/c3-room-read-shell`** от `main` с C1.  
- [ ] Контракт `RoomRead.v1` + example.  
- [ ] `GET /api/v1/rooms/{room_id}` + pytest.  
- [ ] React: открыть комнату по id, видны снимок и бейдж staffing.  
- [ ] Не ломает C1; не реализует C2.  
- [ ] `backend/README.md` и при необходимости `frontend/README.md`: как проверить (handoff → скопировать id → UI).  
- [ ] PR готов к merge независимо от статуса C2.

---

## 8. Вне скоупа

- Форма entitlement в UI  
- Задачи / канбан / чат  
- Keycloak login  
- Редактирование snapshot  

---

## 9. Промпт для стажёра + ИИ (копировать целиком)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c3-room-read-shell
База: origin/main ПОСЛЕ merge C1 (feature/c1-founder-handoff).
Этот тикет ПАРАЛЛЕЛЕН C2 (feature/c2-entitlement-unlock): не трогай entitlements и миграции C2.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Читай AGENTS.md, docs/canon/ADR-002-wowlance-2.0-platform-room.md.
Задание: docs/261010 - задание C3 Room read shell.md

Сделай C3:
1) contracts/wowlance/RoomRead.v1.yaml + examples/RoomRead.sale.json + contracts/README.md
2) GET /api/v1/rooms/{room_id} — room + strategy snapshot; 404 если нет
3) pytest: после handoff GET совпадает с snapshot; 404; staffing_unlocked из БД
4) React: страница комнаты по room_id — name, type, badge locked/unlocked, offer/audience/hot_criteria, documents URIs
5) Vite proxy /api → backend; короткая инструкция в README

Не делай POST entitlements, staffing, Keycloak, задачи, CRM.
Не ломай FounderHandoff.
Сначала план 5–8 шагов, потом маленькие коммиты.
```

---

## 10. Ревьюеру

- Нет записи в БД на GET (кроме harmless).  
- Не дублировать и не «улучшать» handoff.  
- UI читает флаг, не вычисляет entitlement сам.  
- Параллельный merge с C2: оба `include_router` на месте.
