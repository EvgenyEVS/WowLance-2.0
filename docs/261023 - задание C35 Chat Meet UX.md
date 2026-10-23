# Задание: C35 — Chat + Meet UX

| Поле | Значение |
|------|----------|
| **Дата** | 2026-10-23 |
| **Репозиторий** | [EvgenyEVS/WowLance-2.0](https://github.com/EvgenyEVS/WowLance-2.0) |
| **Ветка** | `feature/c35-chat-meet-ux` |
| **База** | актуальный `main` **после merge C30–C33** |
| **Параллельность** | ✅ с C34 · C36 · C37; ⚠️ не трогай `LeadsPanel` (C34) и Health/Earned (C36) |
| **Фаза** | C35 (зона «Чат / Meet» — владение WL) |
| **Стек** | **React · FastAPI (багфикс OK) · OpenSpec `wowlance` / Meet stub** |
| **Исполнитель** | сильный стажёр + хороший ИИ |
| **Срок** | 2–3 дня |
| **Канон** | [зоны до согласования](261022%20-%20зоны%20разработки%20до%20согласования%20контрактов.md) |
| **Параллель** | [C34](261023%20-%20задание%20C34%20Leads%20UX.md) · [C36](261023%20-%20задание%20C36%20Earnings%20Health%20UX.md) · [C37](261023%20-%20задание%20C37%20QA%20C0-C33.md) |

> Meet / chat — stubs. Live Jitsi SSO / WebSocket bus — **не** делать. Не ломать G1–G10. Last-N chat из C29 не регрессировать.

---

## 1. Зачем

Chat (C20) и Meet (C14) есть, но UX «ручной»: нет poll, после post список не всегда комфортен, Meet — голая ссылка. Нужен срез **удобства комнатной коммуникации** без realtime-инфры.

---

## 2. Параллель

| Можно | Нельзя |
|-------|--------|
| `ChatPanel.tsx`, блок Meet на `RoomPage.tsx`, CSS | `LeadsPanel` (C34); `RoomHealthPanel` / Earned block (C36) |
| Уточнение draft `RoomMessages` / `RoomMeet` / RoomRead meeting fields | Live Jitsi auth, WebSocket gateway |
| pytest chat poll/limit | Ломать C27: chat post / meet ensure доступны member |

---

## 3. Не делать

- WebSocket / SSE «настоящий realtime».  
- Live Jitsi JWT / SSO.  
- Смена граничных Strategy/CRM YAML.  
- Полноценный мессенджер (треды, реакции, файлы).

---

## 4. Продуктовые правила (must-fix)

1. **Chat poll:** интервал 5–10 с (или «Refresh» + опциональный poll); после POST — сразу reload списка; не мигать всей панелью в «Loading…» на каждый poll (soft update).  
2. **Last-N:** сохранить семантику C29 (последние N); пустой чат — empty hint.  
3. **Автор/время:** сообщение показывает actor + короткое время (locale OK).  
4. **Meet:** Ensure meeting идемпотентен; если `meeting_url` уже есть — кнопка «Open» + «Re-ensure» (или одна Ensure без ошибки); ошибка ensure — короткий текст.  
5. **RoomRead:** после ensure UI подхватывает URL без обязательного F5 всей страницы (callback/`loadRoom` или локальный state).  
6. **RBAC:** member может post + ensure (как C27); не прятать чат у member.

---

## 5. Nice-to-have

- Scroll to bottom после post.  
- Индикатор «updated Xs ago» у poll.  
- Copy meeting URL.

---

## 6. DoD

- [ ] Must-fix 1–6.  
- [ ] pytest: chat list last-N + post; meet ensure idempotent (существующие + при правках).  
- [ ] README frontend: 3–5 строк (poll interval, meet).  
- [ ] Нет live Jitsi/WS.  
- [ ] PR.

---

## 7. Промпт

```text
Репозиторий: https://github.com/EvgenyEVS/WowLance-2.0
Ветка: feature/c35-chat-meet-ux
База: origin/main после C30–C33.
Параллелен C34/C36/C37: не трогай Leads и Health/Earned.
Задание: docs/261023 - задание C35 Chat Meet UX.md
Stub chat/meet; no WebSocket/live Jitsi; keep last-N + G1–G10 + C27.

Сделай: soft poll, post→reload, meet ensure UX without full page F5.
План 5–7 шагов, маленькие коммиты.
```
