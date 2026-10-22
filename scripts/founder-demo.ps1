# C26 founder-demo pack: seed a sale room through existing stub endpoints.
# Each run uses a fresh handoff_id (new room). Requires API on $ApiBase.
# AUTH_DISABLED=true is the expected demo mode. If INTERNAL_AUTH_DISABLED=false,
# set INTERNAL_SERVICE_TOKEN in the environment.
#
# Usage (repo root, API already running):
#   powershell -File scripts/founder-demo.ps1

[CmdletBinding()]
param(
    [string]$ApiBase = "http://127.0.0.1:8000",
    [string]$UiBase = "http://127.0.0.1:5173",
    [string]$ActorSub = "founder-demo-sub"
)

$ErrorActionPreference = "Stop"
$script:ActorSub = $ActorSub

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ExamplePath = Join-Path $RepoRoot "contracts\strategy\examples\FounderHandoff.sale.json"
if (-not (Test-Path $ExamplePath)) {
    throw "Sale example not found: $ExamplePath"
}

function Invoke-WlApi {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Path,
        [object]$BodyObj,
        [switch]$Actor,
        [string]$ActorSubOverride
    )
    $headers = @{ Accept = "application/json" }
    if ($Path.StartsWith("/internal/") -and $env:INTERNAL_AUTH_DISABLED -eq "false") {
        if (-not $env:INTERNAL_SERVICE_TOKEN) {
            throw "INTERNAL_SERVICE_TOKEN is required when INTERNAL_AUTH_DISABLED=false"
        }
        $headers["X-Service-Token"] = $env:INTERNAL_SERVICE_TOKEN
    }
    if ($Actor) {
        $sub = if ($ActorSubOverride) { $ActorSubOverride } else { $script:ActorSub }
        $headers["X-Actor-Sub"] = $sub
    }
    $params = @{
        Uri             = "$ApiBase$Path"
        Method          = $Method
        Headers         = $headers
        UseBasicParsing = $true
    }
    if ($null -ne $BodyObj) {
        $json = $BodyObj | ConvertTo-Json -Depth 20 -Compress
        $params.ContentType = "application/json; charset=utf-8"
        $params.Body = [System.Text.Encoding]::UTF8.GetBytes($json)
    }
    Write-Host ">> $Method $Path"
    try {
        $res = Invoke-WebRequest @params
    }
    catch {
        $resp = $_.Exception.Response
        if ($resp) {
            $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
            $text = $reader.ReadToEnd()
            throw "$Method $Path failed: HTTP $([int]$resp.StatusCode) $text"
        }
        throw
    }
    $text = $res.Content
    if ([string]::IsNullOrWhiteSpace($text)) {
        return $null
    }
    return $text | ConvertFrom-Json
}

$handoff = Get-Content -Raw -Encoding UTF8 $ExamplePath | ConvertFrom-Json
$handoff.handoff_id = [guid]::NewGuid().ToString()
$handoff.strategy_id = [guid]::NewGuid().ToString()
$handoff.founder_sub = $script:ActorSub

$created = Invoke-WlApi -Method POST -Path "/internal/v1/handoffs" -BodyObj $handoff
$roomId = [string]$created.room_id
Write-Host "room_id = $roomId  (handoff status=$($created.status))"

$entitlement = [pscustomobject]@{
    entitlement_id = [guid]::NewGuid().ToString()
    room_id        = $roomId
    order_id       = $null
    source         = "stub"
}
$granted = Invoke-WlApi -Method POST -Path "/internal/v1/entitlements" -BodyObj $entitlement
Write-Host "entitlement $($granted.status); staffing_unlocked=$($granted.staffing_unlocked)"

$mat = Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/slots/materialize"
Write-Host "materialize $($mat.status); slots=$($mat.slots.Count)"

$freelancerA = "freelancer-demo-sub"
$freelancerB = "teamlead-demo-sub"

Invoke-WlApi -Method POST -Path "/internal/v1/roster" -BodyObj ([pscustomobject]@{
        freelancer_sub = $freelancerA
        display_name   = "Demo Freelancer"
        skills         = @("writing", "advisory")
        level          = "B"
        source         = "stub"
    }) | Out-Null
Invoke-WlApi -Method POST -Path "/internal/v1/roster" -BodyObj ([pscustomobject]@{
        freelancer_sub = $freelancerB
        display_name   = "Demo Teamlead"
        skills         = @("advisory")
        level          = "A"
        source         = "stub"
    }) | Out-Null
Write-Host "roster upserted: $freelancerA, $freelancerB"

$slots = Invoke-WlApi -Method GET -Path "/api/v1/rooms/$roomId/slots"
$open = @($slots.slots | Where-Object { $_.status -eq "open" })
if ($open.Count -lt 1) {
    throw "No open slots after materialize"
}
$slotId = [string]$open[0].id
$assigned = Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/slots/$slotId/assign" -Actor -BodyObj ([pscustomobject]@{
        freelancer_sub = $freelancerA
    })
Write-Host "assign $($assigned.status) slot=$slotId -> $freelancerA"

$task = Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/tasks" -Actor -BodyObj ([pscustomobject]@{
        title        = "Demo first dials"
        assignee_sub = $freelancerA
    })
$taskId = [string]$task.id
Write-Host "task created $taskId status=$($task.status)"

Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/tasks/$taskId/start" -Actor -ActorSubOverride $freelancerA | Out-Null
Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/tasks/$taskId/complete" -Actor -ActorSubOverride $freelancerA -BodyObj ([pscustomobject]@{
        proof_uri  = "s3://platform/demo/proof.txt"
        proof_note = "founder-demo pack"
    }) | Out-Null
$accepted = Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/tasks/$taskId/accept" -Actor
Write-Host "task $($accepted.status) (QG accept)"

$lead = Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/leads" -Actor -BodyObj ([pscustomobject]@{
        title        = "Demo hot account"
        contact_name = "Alex Buyer"
        notes        = "founder-demo pack"
    })
$leadId = [string]$lead.id
Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/leads/$leadId/mark-hot" -Actor | Out-Null
$handed = Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/leads/$leadId/handoff-crm" -Actor
Write-Host "lead $($handed.lead.status) crm_ref=$($handed.lead.crm_ref)"

$meet = Invoke-WlApi -Method POST -Path "/api/v1/rooms/$roomId/meet/ensure" -Actor
Write-Host "meet $($meet.status) $($meet.meeting_url)"

$health = Invoke-WlApi -Method GET -Path "/api/v1/rooms/$roomId/health"
Write-Host ("health slots filled={0} tasks done={1} leads handed={2} earned={3} {4}" -f `
        $health.slots.filled, $health.tasks.done, $health.leads.handed_to_crm, `
        $health.earnings.total_amount, $health.earnings.currency)

try {
    $pub = Invoke-WlApi -Method POST -Path "/internal/v1/rooms/$roomId/health/publish"
    Write-Host "health publish $($pub.status)"
}
catch {
    Write-Host "health publish skipped: $($_.Exception.Message)"
}

$uiUrl = "$UiBase/rooms/$roomId"
Write-Host ""
Write-Host "UI: $uiUrl"
Write-Host "API room: $ApiBase/api/v1/rooms/$roomId"
Write-Host "Done. Open the UI URL and walk through docs/demo/founder-demo.md."
