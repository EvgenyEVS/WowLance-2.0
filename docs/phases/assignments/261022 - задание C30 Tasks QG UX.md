# Задание: C30 — Tasks + Quality Gate UX

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-22 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c30-tasks-qg-ux` |
| **База** | актуальный `main` **после merge C26–C29** (`c033a2a`+) |
| **Параллельность** | ✅ с C31 · C32 · C33; ⚠️ не трогай `SlotsPanel` (C31) |
| **Фаза** | C30 (зона «Задачи + Quality Gate» — владение WL) |
| **Стек** | **React · FastAPI (только если баг API) · OpenSpec `wowlance`** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [зоны до согласования](../../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) · [ADR-002](../../canon/ADR-002-wowlance-2.0-platform-room.md) |
| **Параллель** | [C31](261022%20-%20задание%20C31%20Slots%20staffing%20UX.md) · [C32](261022%20-%20задание%20C32%20Stub%20hardening.md) · [C33](261022%20-%20задание%20C33%20Contract%20owners.md) |

> Контракты `wowlance/*` / `RoomTasks` — уточнять только внутри комнаты. Live Talent / новые граничные поля — **не** делать. Не ломать G1–G10.

---

## 1. Зачем

QG есть (start → proof → accept/reject), но список задач сырой: нет фильтра по статусу, reject/proof читаются плохо, member видит лишний шум. Нужен **UI/API-lite срез** без live Talent и без смены границы `TaskAccepted`.

---

## 2. Параллель

| Можно | Нельзя |
|-------|--------|
| `TasksPanel.tsx`, типы, мелкий query `?status=` на GET tasks | `SlotsPanel` / rematerialize / matching (C31) |
| Уточнение `contracts/wowlance/RoomTasks*.yaml` (draft) | Менять payload outbox `TaskAccepted` / talent YAML |
| pytest на filter + reject path | RBAC-матрицу ломать; demo при `AUTH_DISABLED` / `ROOM_RBAC_DISABLED` |

**Alembic:** не нужен, если только filter query + UI. Если всё же — `015_c30_*`, не dual с C32 без merge.

---

## 3. Не делать

- Live Talent / ProfileChanged.  
- Биллинг задачи, Jira sync.  
- Новый граничный контракт v1 «под arch».  
- Большой редизайн комнаты.

---

## 4. Продуктовые правила (must-fix)

1. **Фильтр статусов** в UI: `all | todo | in_progress | submitted | done | rejected` (или фактические enum из кода).  
   - GET list поддерживает optional `status=` (server-side) **или** клиентский filter, если list уже полный — зафиксируй в README.  
2. **Proof UX:** у `submitted`/`done` — кликабельный URI + note; пустой proof не даёт Submit (уже есть — сохрани).  
3. **Reject-flow:** после Reject задача снова в работе (как сейчас); **видимая** last reject reason; поле reason не теряется при refresh списка.  
4. **Счётчик / подпись:** «N задач · фильтр: submitted» (коротко).  
5. **RBAC:** не ломать C27 hide; member по-прежнему start/complete **своих**, без staff Accept.

---

## 5. Nice-to-have

- Сортировка: submitted сверху для staff.  
- Collapse длинного proof note.

---

## 6. DoD

- [ ] Must-fix 1–5.  
- [ ] pytest: filter (если server) + reject→reason виден в GET.  
- [ ] README frontend: 3–5 строк.  
- [ ] Нет live / нет смены `TaskAccepted` payload.  
- [ ] PR.

---

## 7. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c30-tasks-qg-ux
База: origin/main после C26–C29.
Параллелен C31–C33: не трогай SlotsPanel / stub hardening чужих модулей / docs owners.
Задание: docs/261022 - задание C30 Tasks QG UX.md
Draft wowlance only; stub; no live Talent; keep G1–G10 + C27 RBAC.

Сделай: status filter, proof/reject UX, counters; pytest.
План 5–7 шагов, маленькие коммиты.
```
