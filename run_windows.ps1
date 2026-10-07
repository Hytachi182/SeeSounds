$ErrorActionPreference = 'Stop'

$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host 'Virtual environment is missing; installing dependencies now...' -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot 'install_windows.ps1')
}
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw 'Installation did not create the virtual environment. Review the error above and run .\install_windows.ps1 again.'
}
& $venvPython (Join-Path $PSScriptRoot 'app.py')
if ($LASTEXITCODE -ne 0) { throw "Application exited with error code $LASTEXITCODE." }
