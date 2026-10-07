$ErrorActionPreference = 'Stop'

# Prefer a real python.exe on PATH. The Windows py launcher may retain a stale
# default interpreter after an older Python version was uninstalled.
$pythonCommand = Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
}
if (-not $pythonCommand) {
    throw 'Python 3.11 or newer is required. Install it from https://www.python.org/downloads/ and run this script again.'
}

$pythonExe = $pythonCommand.Source
$versionOutput = & $pythonExe --version 2>&1
if ($LASTEXITCODE -ne 0 -or $versionOutput -notmatch 'Python\s+(\d+)\.(\d+)') {
    throw "Unable to run Python at $pythonExe. Repair or reinstall Python, then run this script again."
}
if ([int]$Matches[1] -lt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -lt 11)) {
    throw "Python 3.11+ is required; found $versionOutput at $pythonExe."
}

$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating virtual environment with $versionOutput..."
    & $pythonExe -m venv (Join-Path $PSScriptRoot '.venv')
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
& $venvPython -c "import PySide6, rapidfuzz; print('Dependencies validated.')"
Write-Host 'Installation complete. Run .\run_windows.ps1 to open the application.' -ForegroundColor Green
