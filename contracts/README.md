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
| [`wowlance/StaffingSlots.v1.yaml`](wowlance/StaffingSlots.v1.yaml) | draft v1 — C4 list/materialize + C6 SlotAssign + C12 Unassign/Reassign |
| [`wowlance/examples/StaffingSlots.sale.json`](wowlance/examples/StaffingSlots.sale.json) | пример list/materialize (один seat `filled`) |
| [`wowlance/StrategyPublished.v1.yaml`](wowlance/StrategyPublished.v1.yaml) | draft v1 — C5 publish + Accept/Reject |
| [`wowlance/examples/StrategyPublished.sale.json`](wowlance/examples/StrategyPublished.sale.json) | пример publish (`room_id` после handoff) |
| [`wowlance/TalentRosterUpsert.v1.yaml`](wowlance/TalentRosterUpsert.v1.yaml) | draft v1 — C6 upsert локального roster (stub Talent) |
| [`wowlance/examples/TalentRosterUpsert.json`](wowlance/examples/TalentRosterUpsert.json) | пример payload upsert |
| [`wowlance/RoomTasks.v1.yaml`](wowlance/RoomTasks.v1.yaml) | draft v1 — C7 трекер задач + C10 Quality Gate (`submitted`/`proof_*`, accept/reject) |
| [`wowlance/examples/RoomTasks.sale.json`](wowlance/examples/RoomTasks.sale.json) | пример list-ответа задач (todo/in_progress/submitted + proof) |
| [`wowlance/AuthBearer.v1.yaml`](wowlance/AuthBearer.v1.yaml) | draft v1 — C8 Bearer JWT на `/api/v1/*` + shadow User |

| [`wowlance/RoomLeads.v1.yaml`](wowlance/RoomLeads.v1.yaml) | draft v1 — C9 лиды комнаты (open → hot → handed_to_crm) |
| [`wowlance/examples/RoomLeads.sale.json`](wowlance/examples/RoomLeads.sale.json) | пример list-ответа лидов |
| [`wowlance/HotLeadToCrm.v1.yaml`](wowlance/HotLeadToCrm.v1.yaml) | draft v1 — C9 исходящее событие Hot → CRM (outbox) |
| [`wowlance/examples/HotLeadToCrm.json`](wowlance/examples/HotLeadToCrm.json) | пример outbox payload |
| [`wowlance/RoomCreated.v1.yaml`](wowlance/RoomCreated.v1.yaml) | draft v1 — C11 исходящее событие RoomCreated при создании комнаты (outbox) |
| [`wowlance/examples/RoomCreated.sale.json`](wowlance/examples/RoomCreated.sale.json) | пример outbox payload |
| [`wowlance/RoomHealth.v1.yaml`](wowlance/RoomHealth.v1.yaml) | draft v1 — C13 агрегат комнаты (slots/tasks/leads) для витрины Стратегии |
| [`wowlance/examples/RoomHealth.sale.json`](wowlance/examples/RoomHealth.sale.json) | пример GET health-ответа |

Когда появится общий OpenSpec-репозиторий платформы — перенести схемы туда, здесь оставить версию/ссылку.

Следующие (не блокируют скелет): `RoomHealthSnapshot`.
