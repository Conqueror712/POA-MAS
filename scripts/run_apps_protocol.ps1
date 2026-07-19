param(
    [string]$Config = "configs/experiments_apps.json",
    [int[]]$Seeds = @(712, 713, 714),
    [string[]]$Splits = @("test", "shifted_test"),
    [int]$Limit = 0,
    [string]$Prefix = ""
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$configText = Get-Content $Config -Raw
$usesDeepSeek = $configText -match '"provider"\s*:\s*"deepseek"'

if ($usesDeepSeek -and -not $env:DEEPSEEK_API_KEY) {
    $keyFile = "configs/.deepseek_api_key"
    if (-not (Test-Path $keyFile)) {
        throw "Missing DeepSeek API key. Set `$env:DEEPSEEK_API_KEY or create configs/.deepseek_api_key."
    }
}

if (-not $Prefix) {
    $Prefix = "apps_protocol_$(Get-Date -Format yyyyMMdd_HHmmss)"
}

foreach ($Seed in $Seeds) {
    $trainName = "${Prefix}_s${Seed}_train_free"
    Write-Host "==> Training assets for seed $Seed ($trainName)"
    $trainArgs = @(
        "-m", "src.runners.run_training",
        "--config", $Config,
        "--split", "train",
        "--seed", "$Seed",
        "--run-name", $trainName
    )
    if ($Limit -gt 0) {
        $trainArgs += @("--limit", "$Limit")
    }
    python @trainArgs

    Write-Host "==> Extracting assets from trajectories/$trainName"
    python -m src.runners.run_extract_assets --config $Config --run-dir "trajectories/$trainName"

    Write-Host "==> Running held-out APPS protocol for seed $Seed"
    $args = @(
        "-m", "src.runners.run_apps_protocol",
        "--config", $Config,
        "--seed", "$Seed",
        "--run-prefix", "${Prefix}_s${Seed}",
        "--splits"
    )
    $args += $Splits
    if ($Limit -gt 0) {
        $args += @("--limit", "$Limit")
    }
    python @args
}

Write-Host "==> Aggregating APPS protocol results"
python scripts/aggregate_apps_results.py

Write-Host "Done. See results/tables/apps_protocol_summary.md"
