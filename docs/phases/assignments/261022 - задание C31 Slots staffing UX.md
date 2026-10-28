# Задание: C31 — Slots & staffing UX

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-22 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c31-slots-staffing-ux` |
| **База** | актуальный `main` **после merge C26–C29** |
| **Параллельность** | ✅ с C30 · C32 · C33; ⚠️ не трогай `TasksPanel` (C30) |
| **Фаза** | C31 (зона «Слоты и состав» — владение WL) |
| **Стек** | **React · FastAPI (багфикс OK) · OpenSpec `wowlance` / StaffingSlots / SlotMatch** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [зоны до согласования](../../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) |
| **Параллель** | [C30](261022%20-%20задание%20C30%20Tasks%20QG%20UX.md) · [C32](261022%20-%20задание%20C32%20Stub%20hardening.md) · [C33](261022%20-%20задание%20C33%20Contract%20owners.md) |

> Matching / roster — **local stub**. Live Talent JOIN / ProfileChanged — **не** делать. Не ломать G1–G10.

---

## 1. Зачем

C22 rematerialize и C23 matching lite работают, но founder/teamlead путаются: когда Rematerialize, что значит orphaned, куда делся assignee после Unassign, зачем Suggest→Pick. Нужна **ясность UX** на уже существующих endpoints.

---

## 2. Параллель

| Можно | Нельзя |
|-------|--------|
| `SlotsPanel.tsx`, `RosterPanel.tsx`, мелкие copy/hints | `TasksPanel` (C30) |
| Уточнение draft `StaffingSlots` / `SlotMatch` / RoomRead slot fields | Live Talent, новые поля FounderHandoff |
| | Ломать C27 canStaff hide на Assign/Unassign/Rematerialize |

---

## 3. Не делать

- Live matching / полный Talent profile.  
- Авто-найм «в один клик в прод».  
- Deep CRM / биллинг.  
- Смена стратегии snapshot ради слотов.

---

## 4. Продуктовые правила (must-fix)

1. **Rematerialize:** кнопка + короткий hint «когда жать» (после Accept strategy / смена functions); orphaned slots — **заметный** статус/бейдж (не только console).  
2. **Unassign / Reassign:** после успеха список слотов обновляется без F5; empty assignee = понятный «свободен».  
3. **Matching lite:** Suggest показывает shortlist; Pick/Assign путь из C29 не регрессировать; если ростер пуст — hint «сначала Roster upsert».  
4. **Staff-only:** member не видит Assign/Unassign/Rematerialize/Suggest (C27); при `ROOM_RBAC_DISABLED` — как сейчас для demo.  
5. **Ошибки:** 409/422 с коротким текстом в UI (не сырой JSON dump).

---

## 5. Nice-to-have

- Счётчик «занято / всего» слотов в заголовке.  
- Подсветка слота после successful reassign.

---

## 6. DoD

- [ ] Must-fix 1–5.  
- [ ] Ручной smoke: materialize → assign → unassign → reassign → suggest→assign; rematerialize orphaned path.  
- [ ] pytest существующих slot/match тестов зелёные; при правке API — доп. тест.  
- [ ] Нет live Talent.  
- [ ] PR.

---

## 7. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c31-slots-staffing-ux
База: origin/main после C26–C29.
Параллелен C30/C32/C33: не трогай TasksPanel и чужой hardening.
Задание: docs/261022 - задание C31 Slots staffing UX.md
Local roster/match only; no live Talent; keep G1–G10 + C27.

Сделай: rematerialize/orphaned hints, unassign/reassign refresh, match empty hints, staff errors.
План 5–7 шагов, маленькие коммиты.
```
