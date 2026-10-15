# Contracts (OpenSpec)

Контракты сервиса WowLance. **Менять здесь раньше кода** (фаза C0).

| Файл | Статус |
|------|--------|
| [`wowlance/FounderHandoff.v1.yaml`](wowlance/FounderHandoff.v1.yaml) | draft v1 — обязателен для C1 |
| [`wowlance/examples/FounderHandoff.sale.json`](wowlance/examples/FounderHandoff.sale.json) | пример payload |
| [`wowlance/EntitlementGranted.v1.yaml`](wowlance/EntitlementGranted.v1.yaml) | draft v1 — обязателен для C2 |
| [`wowlance/examples/EntitlementGranted.json`](wowlance/examples/EntitlementGranted.json) | пример payload (`room_id` подставить после handoff) |

Когда появится общий OpenSpec-репозиторий платформы — перенести схемы туда, здесь оставить версию/ссылку.

Следующие (не блокируют скелет): `TalentRosterUpsert`, `RoomCreated`, `StrategyPublished`.
