param([string]$Adb = 'adb', [string]$Serial = '')
$ErrorActionPreference = 'Stop'
$adbPrefix = @()
if ($Serial) { $adbPrefix = @('-s', $Serial) }
$outputDir = Join-Path $PSScriptRoot ('../diagnostics/' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$checks = [ordered]@{
    'device.txt' = @('shell', 'getprop', 'ro.product.device')
    'lineage.txt' = @('shell', 'getprop', 'ro.lineage.version')
    'api.txt' = @('shell', 'getprop', 'ro.build.version.sdk')
    'package.txt' = @('shell', 'dumpsys', 'package', 'com.android.camera')
    'camera.txt' = @('shell', 'dumpsys', 'media.camera')
    'camera-processes.txt' = @('shell', 'ps', '-AZ')
    'crash.txt' = @('logcat', '-b', 'crash', '-d', '-t', '300')
}
foreach ($entry in $checks.GetEnumerator()) {
    $commandArgs = $adbPrefix + $entry.Value
    & $Adb @commandArgs 2>&1 | Set-Content -LiteralPath (Join-Path $outputDir $entry.Key) -Encoding utf8
}
& $Adb @adbPrefix logcat -b all -d -t 3000 2>&1 |
    Select-String 'com.android.camera|miuicamera|campostproc|mianode|algoup|avc: denied|linker|CameraService|CameraProvider' |
    Set-Content -LiteralPath (Join-Path $outputDir 'camera-log.txt') -Encoding utf8
Write-Output "Logs saved to $((Resolve-Path $outputDir).Path)"
