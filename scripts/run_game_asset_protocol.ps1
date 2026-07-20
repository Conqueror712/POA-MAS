param(
    [string]$Config = "configs/experiments_game.json",
    [string[]]$Seeds = @("712"),
    [string[]]$Splits = @("test", "shifted_test"),
    [int]$Limit = 0,
    [string]$Prefix = "",
    [string]$AssetFilename = "latest_strategy_assets.json"
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

function Invoke-PythonChecked {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$PythonArgs
    )
    python @PythonArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code ${LASTEXITCODE}: python $($PythonArgs -join ' ')"
    }
}

$configText = Get-Content $Config -Raw
$usesDeepSeek = $configText -match '"provider"\s*:\s*"deepseek"'

if ($usesDeepSeek -and -not $env:DEEPSEEK_API_KEY) {
    $keyFile = "configs/.deepseek_api_key"
    if (-not (Test-Path $keyFile)) {
        throw "Missing DeepSeek API key. Set `$env:DEEPSEEK_API_KEY or create configs/.deepseek_api_key."
    }
}

if (-not $Prefix) {
    $Prefix = "game_asset_protocol_$(Get-Date -Format yyyyMMdd_HHmmss)"
}

$SeedValues = @()
foreach ($SeedItem in $Seeds) {
    foreach ($Part in ($SeedItem -split ",")) {
        $Trimmed = $Part.Trim()
        if ($Trimmed) {
            $SeedValues += [int]$Trimmed
        }
    }
}

foreach ($Seed in $SeedValues) {
    $trainPrefix = "${Prefix}_s${Seed}_train"
    Write-Host "==> Running Domain 2 source trajectories for seed $Seed ($trainPrefix)"
    $trainArgs = @(
        "-m", "src.runners.run_game_domain",
        "--config", $Config,
        "--splits", "train",
        "--settings", "persona",
        "--seed", "$Seed",
        "--run-prefix", $trainPrefix
    )
    if ($Limit -gt 0) {
        $trainArgs += @("--limit", "$Limit")
    }
    Invoke-PythonChecked @trainArgs

    Write-Host "==> Extracting trajectory-derived game assets from prefix $trainPrefix"
    Invoke-PythonChecked -m src.runners.run_extract_game_assets --config $Config --run-prefix $trainPrefix --filename $AssetFilename

    $assetFile = "assets/game_assets/$AssetFilename"
    Write-Host "==> Running Domain 2 held-out evaluation for seed $Seed using $assetFile"
    $evalArgs = @(
        "-m", "src.runners.run_game_domain",
        "--config", $Config,
        "--splits"
    )
    $evalArgs += $Splits
    $evalArgs += @(
        "--settings", "no_persona", "persona", "reuse_assets",
        "--seed", "$Seed",
        "--run-prefix", "${Prefix}_s${Seed}",
        "--game-asset-file", $assetFile
    )
    if ($Limit -gt 0) {
        $evalArgs += @("--limit", "$Limit")
    }
    Invoke-PythonChecked @evalArgs
}

Write-Host "==> Aggregating Domain 2 results"
$aggregateArgs = @("scripts/aggregate_game_results.py", "--prefix", $Prefix, "--splits")
$aggregateArgs += $Splits
if (-not $usesDeepSeek) {
    $aggregateArgs += @("--exclude-markers", "__no_exclusion_marker__")
}
Invoke-PythonChecked @aggregateArgs

Write-Host "==> Regenerating Domain 2 paper tables and figures"
Invoke-PythonChecked scripts/generate_game_paper_assets.py

Write-Host "Done. See results/tables/game_domain_aggregate.md and results/figures/game_domain_*.svg"
