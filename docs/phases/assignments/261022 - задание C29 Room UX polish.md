# Задание: C29 — Room UX polish (shell + известные nits)

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-22 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c29-room-ux-polish` |
| **База** | актуальный `main` **после merge C25** |
| **Параллельность** | ⚠️ **осторожно с C27** (кнопки/роли); ✅ с C26 · C28 |
| **Фаза** | C29 (полировка UI комнаты на stubs) |
| **Стек** | **React · FastAPI (только если баг API)** · OpenSpec |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [зоны до согласования](../../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) |
| **Параллель** | [C26](261022%20-%20задание%20C26%20Founder%20demo%20pack.md) · [C27](261022%20-%20задание%20C27%20Room%20RBAC.md) · [C28](261022%20-%20задание%20C28%20QA%20C0-C25.md) |

> UI комнаты — владение WowLance. Live / новые граничные поля — не делать. Не ломать G1–G10.

---

## 1. Зачем

Shell работает, но UX сырой: пустые состояния, известные nits (Suggest Pick, chat «первые N», Earned без refresh). Нужен срез полировки **без** нового домена.

---

## 2. Параллель

| Можно | Нельзя |
|-------|--------|
| `frontend/src/pages/*`, `index.css`, мелкие API fix (chat order) | Новые граничные контракты / live |
| Empty states, копирайт, layout панелей | Большой редизайн «продуктовый бренд» (избыточно) |
| | Конфликт с C27: если оба трогают одни кнопки — C29 не вшивает role-hide (это C27) |

---

## 3. Must-fix (DoD)

1. **C23 Suggest Pick:** кнопка Pick не должна быть `disabled` до выбора — клик выставляет `picked` (или убрать отдельный Pick: клик по кандидату = select + достаточно Assign).  
2. **C20 chat list:** отдавать **последние** N (ORDER BY desc + reverse, или subquery), не первые N.  
3. **C16 Earned:** после Accept задачи на RoomPage — обновить блок Earned (callback/refresh), без обязательного F5.  
4. **Empty states:** когда нет slots/tasks/leads/messages — короткий hint «что сделать дальше» (не пустая дыра).  
5. **Мобильная базовая читаемость:** панели не ломают ширину &lt;640px (без идеального дизайна).

---

## 4. Nice-to-have (если останется время)

- Rematerialize orphaned hint заметнее.  
- Health Refresh после publish не мигает ошибкой.  
- Единый визуальный ритм заголовков панелей (без новой дизайн-системы).

---

## 5. Не делать

- RBAC hide (C27).  
- Founder-demo скрипт (C26).  
- Смена API контрактов соседей.  
- Полный visual rebrand.

---

## 6. Тесты / docs

- pytest: поправить/добавить тест chat limit = последние сообщения.  
- frontend README: 2–3 строки про empty states / Pick.  
- Ручной smoke: Suggest→Assign; chat 60+ msgs; Accept→Earned.

---

## 7. DoD

- [ ] Must-fix 1–5 закрыты.  
- [ ] pytest chat + ручной smoke.  
- [ ] Не ломает API контракты.  
- [ ] PR со скринами/описанием до/после по желанию.

---

## 8. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c29-room-ux-polish
База: origin/main после C25.
Параллелен C26/C28; с C27 не дублируй role-hide.
Задание: docs/261022 - задание C29 Room UX polish.md
Stub UI only; no live; keep G1–G10.

Сделай: fix Suggest Pick; chat last-N; Earned refresh after Accept; empty states; basic mobile.
План 5–8 шагов, маленькие коммиты.
```
