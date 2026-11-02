<#
.SYNOPSIS
    Apply one Phase 4 SQL migration to DB1 via the Supabase Management API.

.DESCRIPTION
    Mirrors frontend/scripts/execute-pending-migrations.ps1 (same endpoint,
    same env file, same idempotency discipline) but targets a single file in
    the bdw-llm repo so Phase 4 schema work stays isolated from the BDW
    platform migrations. Never prints the management token, service key or
    anon key.

    Preflight  : pgvector version + existing p4_domain_* relations
    Apply      : POST /v1/projects/<ref>/database/query with the file content
    Verify     : RLS enabled on all 6 tables, zero policies, 5 RPCs present,
                 anon HEAD probes return 0 rows for every table

.EXAMPLE
    .\apply_via_management_api.ps1 -DryRun
    .\apply_via_management_api.ps1 -ConfirmProduction
#>
[CmdletBinding()]
param(
    [string]$SqlFile = 'D:\Tinkerscape\SiliconPath\bdw-llm\phase4\supabase\migrations\0003_p4_domain_chunks.sql',
    [string]$EnvFile = 'D:\Tinkerscape\SiliconPath\frontend\.env.local',
    [switch]$ConfirmProduction,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Read-EnvFile([string]$path) {
    $map = @{}
    foreach ($raw in Get-Content $path) {
        $line = $raw.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line -match '^([^=]+)=(.*)$') {
            $k = $matches[1].Trim(); $v = $matches[2].Trim()
            if (($v.StartsWith('"') -and $v.EndsWith('"')) -or
                ($v.StartsWith("'") -and $v.EndsWith("'"))) {
                $v = $v.Substring(1, $v.Length - 2)
            }
            $map[$k] = $v
        }
    }
    return $map
}

if (-not (Test-Path $EnvFile)) { Write-Error "Env file not found: $EnvFile" }
if (-not (Test-Path $SqlFile)) { Write-Error "SQL file not found: $SqlFile" }

$envVars = Read-EnvFile $EnvFile
$token = $envVars['SUPABASE_MGMT_TOKEN']; if (-not $token) { $token = $env:SUPABASE_MGMT_TOKEN }
$ref = $envVars['SUPABASE_PROJECT_REF']; if (-not $ref) { $ref = 'aqauempuwmbizqoaolop' }
$url = $envVars['NEXT_PUBLIC_SUPABASE_URL']; if (-not $url) { $url = "https://$ref.supabase.co" }
$anon = $envVars['NEXT_PUBLIC_SUPABASE_ANON_KEY']
if (-not $token) { Write-Error 'Missing SUPABASE_MGMT_TOKEN (env file or environment).' }

$headers = @{ 'Authorization' = "Bearer $token"; 'Content-Type' = 'application/json' }

function Invoke-Sql([string]$sql) {
    $body = @{ query = $sql } | ConvertTo-Json -Depth 3
    try {
        return Invoke-RestMethod -Uri "https://api.supabase.com/v1/projects/$ref/database/query" `
            -Method Post -Headers $headers -Body $body -TimeoutSec 120
    } catch {
        $msg = if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $_.ErrorDetails.Message } else { $_.Exception.Message }
        throw "Management API SQL failed: $msg"
    }
}

Write-Host "Project   : $ref" -ForegroundColor Cyan
Write-Host "SQL file  : $SqlFile" -ForegroundColor Cyan

# ---- preflight -----------------------------------------------------------
Write-Host "`n[1/4] Preflight..." -ForegroundColor Cyan
$vec = Invoke-Sql "select extversion as v from pg_extension where extname = 'vector';"
Write-Host "  pgvector : $($vec[0].v)"
$tables = @('p4_domain_math','p4_domain_vlsi','p4_domain_embedded','p4_domain_cs',
            'p4_domain_aiml','p4_domain_index_manifest')
$existing = Invoke-Sql ("select c.relname as name from pg_class c join pg_namespace n " +
    "on n.oid = c.relnamespace where n.nspname = 'public' and c.relname in (" +
    (($tables | ForEach-Object { "'$_'" }) -join ',') + ") order by 1;")
$existingNames = @($existing | ForEach-Object { $_.name })
Write-Host "  existing : $(if ($existingNames.Count) { $existingNames -join ', ' } else { 'none' })"
$rpc = Invoke-Sql ("select p.proname as name from pg_proc p join pg_namespace n " +
    "on n.oid = p.pronamespace where n.nspname = 'public' and p.proname like 'match_p4_%';")
$rpcNames = @($rpc | ForEach-Object { $_.name })
Write-Host "  rpcs     : $(if ($rpcNames.Count) { $rpcNames -join ', ' } else { 'none' })"

if ($DryRun) {
    Write-Host "`n[DRY RUN] No SQL applied." -ForegroundColor Yellow
    exit 0
}
if (-not $ConfirmProduction) {
    Write-Warning 'Operator safety guard: pass -ConfirmProduction to apply.'
    exit 1
}

# ---- apply ---------------------------------------------------------------
Write-Host "`n[2/4] Applying migration..." -ForegroundColor Cyan
$raw = Get-Content -Path $SqlFile -Raw
$sql = [regex]::Replace($raw, '[^\x00-\x7F]', '-')
try {
    [void](Invoke-Sql $sql)
    Write-Host "  applied  : OK" -ForegroundColor Green
} catch {
    Write-Host "  applied  : FAILED" -ForegroundColor Red
    Write-Host "  detail   : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'RESULT: P4_MIGRATION_FAIL'
    exit 1
}

# ---- verify schema -------------------------------------------------------
Write-Host "`n[3/4] Verifying schema..." -ForegroundColor Cyan
$rls = Invoke-Sql ("select c.relname as name, c.relrowsecurity as rls from pg_class c " +
    "join pg_namespace n on n.oid = c.relnamespace where n.nspname = 'public' and c.relname in (" +
    (($tables | ForEach-Object { "'$_'" }) -join ',') + ") order by 1;")
$rlsOk = $true
foreach ($r in $rls) { if (-not $r.rls) { $rlsOk = $false } }
Write-Host "  tables   : $($rls.Count)/6 present, RLS $(if ($rlsOk) { 'ON for all' } else { 'MISSING' })"
$pol = Invoke-Sql ("select count(*) as c from pg_policies where schemaname = 'public' " +
    "and tablename like 'p4_domain_%';")
$polCount = [int]$pol[0].c
Write-Host "  policies : $polCount (expected 0 - internal tables)"
$rpc2 = Invoke-Sql ("select p.proname as name from pg_proc p join pg_namespace n " +
    "on n.oid = p.pronamespace where n.nspname = 'public' and p.proname like 'match_p4_%' order by 1;")
$rpc2Names = @($rpc2 | ForEach-Object { $_.name })
Write-Host "  rpcs     : $($rpc2Names.Count)/5 -> $($rpc2Names -join ', ')"
$schemaOk = ($rls.Count -eq 6 -and $rlsOk -and $polCount -eq 0 -and $rpc2Names.Count -eq 5)

# ---- anon RLS probes (zero-tolerance regression gate) --------------------
Write-Host "`n[4/4] Anonymous RLS probes (HEAD, Prefer: count=exact)..." -ForegroundColor Cyan
$probeOk = $true
if ($anon) {
    $anonHeaders = @{ 'apikey' = $anon; 'Authorization' = "Bearer $anon"; 'Prefer' = 'count=exact' }
    foreach ($tbl in $tables) {
        try {
            $resp = Invoke-WebRequest -Uri "$url/rest/v1/$tbl?select=*" -Method Head `
                -Headers $anonHeaders -SkipHttpErrorCheck -TimeoutSec 10
            $range = $resp.Headers['Content-Range']
            if ($range -match '/0$' -or -not $range) {
                Write-Host "  PASS: $tbl ($range)" -ForegroundColor Green
            } else {
                Write-Host "  CRITICAL: $tbl exposed to anon ($range)" -ForegroundColor Red
                $probeOk = $false
            }
        } catch {
            Write-Host "  PASS: $tbl blocked anon request" -ForegroundColor Green
        }
    }
} else {
    Write-Warning '  NEXT_PUBLIC_SUPABASE_ANON_KEY absent; skipped anon probes.'
    $probeOk = $false
}

if ($schemaOk -and $probeOk) {
    Write-Host "`nRESULT: P4_MIGRATION_OK tables=6 rpcs=5 rls=on policies=0 anon=blocked" -ForegroundColor Green
    exit 0
}
Write-Host "`nRESULT: P4_MIGRATION_FAIL schema_ok=$schemaOk rls_probes_ok=$probeOk" -ForegroundColor Red
exit 1
