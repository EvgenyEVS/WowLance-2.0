# Задание: C41 — Панели комнаты в стиле карточек 1.0

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-26 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c41-ui-panels` |
| **База** | `main` **после merge C39** (токены); желательно после C40 (якоря), но можно параллельно с осторожностью к `RoomPage` |
| **Параллельность** | ⚠️ с C40 оба трогают RoomPage — согласовать или C40→C41; ✅ панели файлы можно делить |
| **Фаза** | C41 (визуал only — панели) |
| **Стек** | **React · CSS** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 3–4 дня |
| **Канон** | 1.0: карточки/списки/формы в `style.css` (`.card`, `.btn`, таблицы/списки задач); комнатные шаблоны overview/tasks |
| **Параллель** | [C39](261026%20-%20задание%20C39%20UI%20tokens%20shell.md) · [C40](261026%20-%20задание%20C40%20UI%20room%20chrome.md) · [C42](261026%20-%20задание%20C42%20UI%20visual%20QA.md) |

> **Только визуал.** Handlers, fetch, статусы, RBAC conditions — без изменения поведения. Менять className / обёртки / CSS.

---

## 1. Зачем

Даже с токенами панели 2.0 выглядят «техническим admin». В 1.0 — карточки, спокойная типографика, понятные primary/secondary. Нужен тот же **ритм компонентов** на существующих панелях.

---

## 2. Охват панелей

| Панель | Цель визуала |
|--------|----------------|
| SlotsPanel | карточка секции; seats как rows/chips; Assign/Unassign = `.btn` |
| TasksPanel | список/карточки задач; фильтр как chip-row 1.0; proof/reject forms |
| LeadsPanel | то же; deal-status заметный badge |
| ChatPanel | лента сообщений + composer в карточке |
| RosterPanel | компактный список |
| RoomHealthPanel + Earned | grid метрик как «статы» 1.0; publish secondary |
| PendingStrategyPanel | карточка pending + primary Accept |

---

## 3. Must-fix

1. Заменить визуальный язык `slot-action` / сырых `<select>` на **btn / input** стили 1.0 (токены C39).  
2. Каждая секция — **card** (белый `--bg-elevated`, border, radius, лёгкая shadow).  
3. Иерархия: `h2` секции = display/body как в 1.0 page blocks.  
4. Empty states и ошибки — в том же тоне (muted / danger), без смены текстов логики.  
5. Не менять: порядок запросов, disabled-условия (кроме CSS), payload.  
6. Mobile &lt;640: карточки не разъезжаются (как C29, но в новом CSS).

---

## 4. Не делать

- Новые фичи (фильтры, поля).  
- Backend / contracts.  
- Полный канбан drag-and-drop 1.0 (если в 1.0 был) — **не** тащить; список/карточки достаточно.  
- Редизайн «с нуля» другим брендбуком — только язык 1.0.

---

## 5. DoD

- [ ] Все панели комнаты в card-языке 1.0.  
- [ ] founder-demo UI walk-through узнаваем рядом со скрином 1.0 room.  
- [ ] Backend diff пустой.  
- [ ] PR + скрины ключевых панелей.

---

## 6. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c41-ui-panels
База: origin/main после C39 (лучше после C40).
Reference: WowLance 1.0 style.css cards/buttons/lists.
Задание: docs/261026 - задание C41 UI panels.md
ТОЛЬКО className/CSS/обёртки. Не меняй fetch/RBAC/бизнес-условия.

Сделай card-панели + btn primitives на Slots/Tasks/Leads/Chat/Health/Earned/Roster/Pending.
План 6–8 шагов, маленькие коммиты.
```
