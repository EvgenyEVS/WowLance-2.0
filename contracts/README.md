# Contracts (OpenSpec)

Контракты разложены **по микросервисам-соседям**.  
Полный реестр с проверкой кода: **[REGISTRY.md](REGISTRY.md)**.  
Владельцы / `proposed`→`agreed`: **[docs/contracts-owners.md](../docs/contracts-owners.md)**.

| Папка | Микросервис | Контракты |
|-------|-------------|-----------|
| [`strategy/`](strategy/) | Стратегия (US Closer) | FounderHandoff, StrategyPublished (+ Decide), RoomCreated, RoomHealth |
| [`order/`](order/) | Order / Payments | EntitlementGranted, StaffingUnlocked |
| [`talent/`](talent/) | Talent | TalentRosterUpsert, MemberTerminated, TaskAccepted |
| [`crm/`](crm/) | CRM / SRM | HotLeadToCrm, CrmDealStatus |
| [`keycloak/`](keycloak/) | Keycloak | AuthBearer |
| [`platform/`](platform/) | Platform / Gateway | InternalServiceAuth |
| [`meet/`](meet/) | Jitsi / Meet | RoomMeet |
| [`wowlance/`](wowlance/) | WowLance (API комнаты) | RoomRead, StaffingSlots, SlotMatch, RoomTasks, RoomLeads, RoomMessages, RoomEarnings, RoomMembers |

**Правило:** менять YAML (+ example) в папке сервиса **раньше** кода.  
Когда появится общий OpenSpec-репозиторий платформы — перенести граничные папки туда, здесь оставить ссылки.

### Быстрые ссылки (граничные)

| Сосед | YAML | Example |
|------|------|---------|
| Стратегия (US Closer) | [FounderHandoff](strategy/FounderHandoff.v1.yaml) | [sale.json](strategy/examples/FounderHandoff.sale.json) |
| Стратегия (US Closer) | [StrategyPublished](strategy/StrategyPublished.v1.yaml) | [sale.json](strategy/examples/StrategyPublished.sale.json) |
| Стратегия (US Closer) | [RoomCreated](strategy/RoomCreated.v1.yaml) | [sale.json](strategy/examples/RoomCreated.sale.json) |
| Стратегия (US Closer) | [RoomHealth](strategy/RoomHealth.v1.yaml) | [sale.json](strategy/examples/RoomHealth.sale.json) |
| Order | [EntitlementGranted](order/EntitlementGranted.v1.yaml) | [json](order/examples/EntitlementGranted.json) |
| Order | [StaffingUnlocked](order/StaffingUnlocked.v1.yaml) | [sale.json](order/examples/StaffingUnlocked.sale.json) |
| Talent | [TalentRosterUpsert](talent/TalentRosterUpsert.v1.yaml) | [json](talent/examples/TalentRosterUpsert.json) |
| Talent | [MemberTerminated](talent/MemberTerminated.v1.yaml) | [sale.json](talent/examples/MemberTerminated.sale.json) |
| Talent | [TaskAccepted](talent/TaskAccepted.v1.yaml) | [example.json](talent/examples/TaskAccepted.example.json) |
| CRM | [HotLeadToCrm](crm/HotLeadToCrm.v1.yaml) | [json](crm/examples/HotLeadToCrm.json) |
| CRM | [CrmDealStatus](crm/CrmDealStatus.v1.yaml) | — |
| Keycloak | [AuthBearer](keycloak/AuthBearer.v1.yaml) | — |
| Platform | [InternalServiceAuth](platform/InternalServiceAuth.v1.yaml) | — |
| Meet | [RoomMeet](meet/RoomMeet.v1.yaml) | — |
