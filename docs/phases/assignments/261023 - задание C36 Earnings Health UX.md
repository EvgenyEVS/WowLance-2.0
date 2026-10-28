# Задание: C36 — Earnings + Room Health UX

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-23 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c36-earnings-health-ux` |
| **База** | актуальный `main` **после merge C30–C33** |
| **Параллельность** | ✅ с C34 · C35 · C37; ⚠️ не трогай Leads (C34) и Chat/Meet (C35) |
| **Фаза** | C36 (зона «Earnings / health UI» — владение WL) |
| **Стек** | **React · FastAPI (багфикс OK) · OpenSpec RoomEarnings / RoomHealth** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [зоны до согласования](../../guides/261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) |
| **Параллель** | [C34](261023%20-%20задание%20C34%20Leads%20UX.md) · [C35](261023%20-%20задание%20C35%20Chat%20Meet%20UX.md) · [C37](261023%20-%20задание%20C37%20QA%20C0-C33.md) |

> Health publish → outbox stub. Live витрина в Strategy — **не** делать. Не менять граничный payload `RoomHealthSnapshot` без YAML+REGISTRY. Не ломать G1–G10.

---

## 1. Зачем

Earned (C16) и health.earnings (C25) есть, но блоки на RoomPage выглядят «техническими»: дублирование Earned vs health, publish мигает, после Accept не везде ясно, что обновилось (C29 частично закрыл). Нужен **читаемый срез «я заработал / снимок комнаты»** для demo.

---

## 2. Параллель

| Можно | Нельзя |
|-------|--------|
| `RoomHealthPanel.tsx`, блок Earned на `RoomPage.tsx`, CSS | `LeadsPanel` (C34); Chat/Meet (C35) |
| Уточнение draft `RoomEarnings` / `RoomHealth` (чтение) | Live Strategy dashboard; новые поля snapshot «с потолка» |
| pytest health/earnings read | Ломать refresh после Accept (C29) |

---

## 3. Не делать

- Live publish в Strategy UI.  
- Биллинг / счета / payouts.  
- Breaking change outbox payload без версии.  
- Deep аналитика / графики.

---

## 4. Продуктовые правила (must-fix)

1. **Earned list:** показывать entries (или top-N + total); empty — «Пока нет начислений — Accept задачу».  
2. **Связка с health:** в Room health блок earnings совпадает с total/count; не два противоречащих числа.  
3. **Refresh:** кнопка Refresh у health; после publish — snapshot обновлён, ошибка не мигает ложно (C29 nit).  
4. **Publish stub:** явная подпись «outbox stub → Strategy (не live)»; показать `outbox_id` кратко.  
5. **После Accept задачи:** RoomPage по-прежнему дергает reload earned (C29); health — либо тот же callback, либо hint «Refresh health».  
6. **Агрегаты health:** slots/tasks/leads counts читаемы одной строкой/сеткой без «сырого JSON».

---

## 5. Nice-to-have

- Фильтр earned «мои» по `viewerSub()` если RBAC on.  
- Timestamp `captured_at` крупнее.

---

## 6. DoD

- [ ] Must-fix 1–6.  
- [ ] pytest существующих health/earnings зелёные; при API fix — доп. тест.  
- [ ] README: 3–5 строк.  
- [ ] Нет live Strategy витрины.  
- [ ] PR.

---

## 7. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c36-earnings-health-ux
База: origin/main после C30–C33.
Параллелен C34/C35/C37: не трогай Leads и Chat/Meet.
Задание: docs/261023 - задание C36 Earnings Health UX.md
Stub health publish; no live Strategy; keep G1–G10 + C29 Accept→Earned.

Сделай: readable Earned + health earnings, publish stub copy, refresh без ложных ошибок.
План 5–7 шагов, маленькие коммиты.
```
