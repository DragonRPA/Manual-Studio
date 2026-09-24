param(
    [string[]]$RunnerArgs
)

$Host.UI.RawUI.WindowTitle = 'Manual Studio - Batch Test Runner (83 Tests)'
$env:MANUAL_STUDIO_DEBUG = '1'
$env:QT_LOGGING_RULES = '*.warning=false;qt.text.*=false;qt.gui.fonts=false'
Set-Location $PSScriptRoot

Write-Host '===============================================================================' -ForegroundColor Cyan
Write-Host '  Manual Studio Batch Test Runner (83 Tests) - Live Console Monitor' -ForegroundColor Cyan
Write-Host '===============================================================================' -ForegroundColor Cyan
Write-Host ''

$argsStr = ''
if ($RunnerArgs) {
    $argsStr = $RunnerArgs -join ' '
}

cmd.exe /c "python -u batch_test_runner.py $argsStr 2>&1" | Tee-Object -FilePath 'batch_test_live.log'
$testExitCode = $LASTEXITCODE

Write-Host ''
if ($testExitCode -ne 0) {
    Write-Host '===============================================================================' -ForegroundColor Red
    Write-Host "  [FAIL] Batch tests failed with exit code $testExitCode" -ForegroundColor Red
    Write-Host '===============================================================================' -ForegroundColor Red
    Write-Host "`nPress any key to close this console..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
} else {
    Write-Host '===============================================================================' -ForegroundColor Green
    Write-Host '  [PASS] All 83 tests passed with 100% integrity!' -ForegroundColor Green
    Write-Host '===============================================================================' -ForegroundColor Green
    Write-Host "`nClosing console window in 5 seconds..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}

exit $testExitCode
