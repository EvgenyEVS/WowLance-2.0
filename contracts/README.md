# Contracts (OpenSpec)

Контракты сервиса WowLance. **Менять здесь раньше кода** (фаза C0).

| Файл | Статус |
|------|--------|
| [`wowlance/FounderHandoff.v1.yaml`](wowlance/FounderHandoff.v1.yaml) | draft v1 — обязателен для C1 |
| [`wowlance/examples/FounderHandoff.sale.json`](wowlance/examples/FounderHandoff.sale.json) | пример payload |
| [`wowlance/EntitlementGranted.v1.yaml`](wowlance/EntitlementGranted.v1.yaml) | draft v1 — обязателен для C2 |
| [`wowlance/examples/EntitlementGranted.json`](wowlance/examples/EntitlementGranted.json) | пример payload (`room_id` подставить после handoff) |
| [`wowlance/RoomRead.v1.yaml`](wowlance/RoomRead.v1.yaml) | draft v1 — C3 + C5 `pending_strategy` |
| [`wowlance/examples/RoomRead.sale.json`](wowlance/examples/RoomRead.sale.json) | пример GET-ответа |
| [`wowlance/StrategyPublished.v1.yaml`](wowlance/StrategyPublished.v1.yaml) | draft v1 — C5 publish + Accept/Reject |
| [`wowlance/examples/StrategyPublished.sale.json`](wowlance/examples/StrategyPublished.sale.json) | пример publish (`room_id` после handoff) |

Когда появится общий OpenSpec-репозиторий платформы — перенести схемы туда, здесь оставить версию/ссылку.

Следующие (не блокируют скелет): `TalentRosterUpsert`, `RoomCreated`.
