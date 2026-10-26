# Задание: C40 — Room chrome (шапка + вкладки) как в 1.0

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-26 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c40-ui-room-chrome` |
| **База** | `main` **после merge C39** (токены/shell обязательны) |
| **Параллельность** | ✅ с C41 после C39; ⚠️ не рефакторить внутренности панелей (C41) |
| **Фаза** | C40 (визуал only — chrome комнаты) |
| **Стек** | **React · CSS** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | 1.0: `apps/rooms/templates/rooms/_room_header.html` + `.page-header` / `.room-tabs` в `style.css` |
| **Параллель** | [C39](261026%20-%20задание%20C39%20UI%20tokens%20shell.md) · [C41](261026%20-%20задание%20C41%20UI%20panels.md) · [C42](261026%20-%20задание%20C42%20UI%20visual%20QA.md) |

> **Только визуал и навигация по якорям.** Не менять API, RBAC hide-логику, состав данных панелей.

---

## 1. Зачем

В 1.0 комната читается так: **название → subtitle (статус/тимлид) → вкладки**. В 2.0 сейчас длинный скролл панелей без chrome. Нужна та же **иерархия и ритм**, без новых backend-маршрутов.

---

## 2. Продуктовые правила (must-fix)

1. **Page header:** название комнаты (display font), badge staffing locked/unlocked, founder/viewer role как subtitle (существующие поля RoomRead).  
2. **Вкладки-якоря** (visual parity с `.room-tabs`): например Overview · Slots · Tasks · Leads · Chat · Meet · Health · Earned — `scrollIntoView` / hash. **Не** отдельные React Router pages, если нет нужды (по умолчанию — якоря на одной RoomPage).  
3. Активная вкладка подсвечивается при скролле (IntersectionObserver или click-state) — UX как active tab 1.0.  
4. Блок strategy snapshot / pending strategy — в «Overview» visually (карточка), не ломая Accept/Reject.  
5. Meet + earned chip в header **опционально** (nice), если не ломает плотность.  
6. RBAC: скрытие staff-кнопок **как сейчас** (логика C27 не трогать; только классы CSS).

---

## 3. Не делать

- Новые API routes `/rooms/:id/tasks` как отдельные страницы (если не строго для parity — по умолчанию **нет**).  
- Менять условия `canStaff`.  
- Переписывать SlotsPanel/TasksPanel разметку списка (C41).  
- Дашборды 1.0 вне комнаты.

---

## 4. DoD

- [ ] Room header + tabs визуально близки к 1.0 (скрин рядом с `_room_header.html`).  
- [ ] Клик по вкладке скроллит к секции; deep-link `#tasks` работает.  
- [ ] Backend не изменён.  
- [ ] README: как устроены якоря.  
- [ ] PR + скрины.

---

## 5. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c40-ui-room-chrome
База: origin/main после C39.
Reference: WowLance 1.0 _room_header.html + .room-tabs / .page-header.
Задание: docs/261026 - задание C40 UI room chrome.md
ТОЛЬКО визуал + якоря. Не меняй API/RBAC/panel internals (C41).

Сделай page-header + room-tabs на RoomPage.
План 5–7 шагов, маленькие коммиты.
```
