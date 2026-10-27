param([switch]$Resume)
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
    $logRoot = 'D:\DevResources\Projects\GeoNormML\Reports\StabilityRuns'
    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
    $log = Join-Path $logRoot ('2026-10-27-' + [guid]::NewGuid().ToString('N') + '.log')
    $parameters = @('python', 'scripts/train_stability_generation.py',
        '--previous', 'D:\DevResources\Projects\GeoNormML\CandidateModels\profiles_nested_v3_20261026',
        '--v4', 'D:\DevResources\Projects\GeoNormML\CandidateModels\expanded_nested_v4_20261027',
        '--output', 'D:\DevResources\Projects\GeoNormML\CandidateModels\partition_stability_v5_20261027',
        '--workers', [string]$slots.Count)
    if ($Resume) { $parameters += '--resume' }
    Write-Output "Workers: $($slots.Count); log: $log"
    $nativePreference = $ErrorActionPreference
    try {
        # Windows PowerShell reports native stderr as error records; preserve warnings in the log.
        $ErrorActionPreference = 'Continue'
        & .\DEVRESOURCES_RUN.cmd @parameters *> $log
        $result = $LASTEXITCODE
    } finally { $ErrorActionPreference = $nativePreference }
    if ($result -ne 0) { throw "Stability training failed; inspect $log" }
    Write-Output 'Stability comparison completed'
} finally {
    foreach ($slot in $slots) { $slot.Dispose() }
}
