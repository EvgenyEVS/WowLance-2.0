# Задание: C23 — Matching lite (shortlist из локального roster)

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-21 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c23-matching-lite` |
| **База** | актуальный `main` **после merge C21** (нужны C6 roster + C4/C12 slots) |
| **Параллельность** | ✅ **можно параллельно с C19 · C22 · C24 · C25** (с **C22** — осторожно в `staffing.py`) |
| **Фаза** | C23 (подбор кандидатов на слот без live Talent) |
| **Стек** | **FastAPI · React · PostgreSQL · OpenSpec · Superpowers** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [ADR-002](../../canon/ADR-002-wowlance-2.0-platform-room.md), [AGENTS.md](../../../AGENTS.md), [01-overview](../../architecture/01-overview.md) |
| **Предыдущее** | [C6 Roster assign](261015%20-%20задание%20C6%20Roster%20assign.md) |
| **Параллель** | [C19](261019%20-%20задание%20C19%20CRM%20deal%20status.md) · [C22](261021%20-%20задание%20C22%20Slot%20rematerialize.md) · [C24](261021%20-%20задание%20C24%20TaskAccepted%20outbox.md) · [C25](261021%20-%20задание%20C25%20Health%20earnings.md) |

Matching читает **только** локальный roster. Live JOIN Talent — запрещён.

---

## 1. Зачем

Assign сейчас — ручной выбор sub. Нужен тонкий срез: для **open** слота вернуть **shortlist** кандидатов из roster (skills overlap / level), UI «Suggest». Без скоринга ML и без HTTP в Talent.

---

## 2. Параллель — правила стыковки

| Можно | Нельзя |
|-------|--------|
| `domain/matching.py` (новый) + `GET …/slots/{id}/match` | Менять rematerialize C22 (кроме чтения slot/intent) |
| Read roster + slot `role_key` / `level_min` | Leads / CRM (C19) |
| UI: кнопка Suggest → список → Assign (существующий) | Писать TaskAccepted / health |

**Alembic:** нет. Dual не ожидается от C23.

---

## 3. Не трогать / не делать

- Live Talent API.  
- Авто-assign без клика тимлида.  
- Rematerialize (C22).  
- RBAC ролей.  
- Leads.

---

## 4. Продуктовые правила

1. `GET /api/v1/rooms/{room_id}/slots/{slot_id}/match?limit=5`  
2. Слот должен быть `open` + room unlocked; иначе **409** / **403**.  
3. Кандидаты: из `freelancer_roster`, **не** уже seated в этой комнате (`already_seated` rule C6).  
4. Скор (простой, зафиксируй):  
   - +2 если `level` слота/`level_min` совместим (или level отсутствует = ок);  
   - +1 за каждый skill из intent/role hints пересекающийся с `roster.skills` (если skills пустые — все с score 0, стабильный order по `freelancer_sub`).  
5. Сортировка: score desc, затем `freelancer_sub` asc; truncate `limit` (default 5, max 20).  
6. Ответ: `{ slot_id, candidates: [{ freelancer_sub, display_name, skills, level, score }] }`.  
7. Match **не** меняет БД.

---

## 5. Контракт

Файл: `contracts/wowlance/SlotMatch.v1.yaml` (+ строка в StaffingSlots или отдельно)

```yaml
id: SlotMatch
path: /api/v1/rooms/{room_id}/slots/{slot_id}/match
method: GET
query: { limit?: int }
response_200:
  required: [slot_id, candidates]
```

`contracts/README.md`.

---

## 6. Код

### 6.1. Domain

`domain/matching.py` — чистая функция скоринга + query roster/slots.

### 6.2. Тесты

1. Roster с skills → match отдаёт упорядоченный shortlist.  
2. Seated freelancer отсутствует в candidates.  
3. Filled slot → 409.  
4. Locked → 403.  
5. Регрессия assign после выбора из shortlist.

### 6.3. Frontend

На open слоте: **Suggest** → показать candidates → Assign выбранного (существующий POST assign).

### 6.4. Docs

backend/frontend README.

---

## 7. DoD

- [ ] Ветка `feature/c23-matching-lite`.  
- [ ] GET match + скоринг + UI Suggest + pytest + контракт.  
- [ ] Только локальный roster.  
- [ ] PR.

---

## 8. Промпт (копировать)

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c23-matching-lite
База: origin/main после C21.
Параллелен C19 (не leads), C22 rematerialize (не меняй его API), C24–C25.
Стек: FastAPI · React · PostgreSQL · OpenSpec · Superpowers.
Задание: docs/261021 - задание C23 Matching lite.md

Сделай C23: GET slot match shortlist из roster; простой score; UI Suggest→Assign; pytest.
Не делай live Talent, auto-assign, rematerialize.
План 5–8 шагов, маленькие коммиты.
```

---

## 9. Ревьюеру

- Нет записи в БД на GET.  
- already_seated учитывается.  
- Параллель с C22: разные endpoints.
