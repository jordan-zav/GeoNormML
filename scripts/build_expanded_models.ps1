$ErrorActionPreference = 'Stop'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:NUMEXPR_NUM_THREADS = '1'
$slots = @()
try {
    while ($slots.Count -eq 0) {
        foreach ($index in 0..1) {
            try {
                $slots += [IO.File]::Open("D:\DevResources\Locks\build-slot-$index.lock", 'OpenOrCreate', 'ReadWrite', 'None')
            } catch [IO.IOException] { }
        }
        if ($slots.Count -eq 0) { Start-Sleep -Seconds 1 }
    }
    $workers = $slots.Count
    $logRoot = 'D:\DevResources\Projects\GeoNormML\Reports\ExpandedRuns'
    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
    $log = Join-Path $logRoot ('2026-10-27-' + [guid]::NewGuid().ToString('N') + '.log')
    Write-Output "Workers: $workers; log: $log"
    & .\DEVRESOURCES_RUN.cmd python scripts/train_expanded_generation.py --previous D:\DevResources\Projects\GeoNormML\CandidateModels\profiles_nested_v3_20261026 --output D:\DevResources\Projects\GeoNormML\CandidateModels\expanded_nested_v4_20261027 --workers $workers *> $log
    if ($LASTEXITCODE -ne 0) { throw "Expanded training failed; inspect $log" }
    Write-Output 'Expanded comparison completed'
} finally {
    foreach ($slot in $slots) { $slot.Dispose() }
}
