param(
    [switch]$Demo,
    [ValidateRange(1, 65535)][int]$Port = 8000
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
$sourcePath = Join-Path $projectRoot 'backend\src'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create backend/.venv and install requirements first; see backend/DEVELOPMENT.md.'
}
$previousDemo = $env:CAMPUS_DEMO
try {
    $env:CAMPUS_DEMO = if ($Demo) { '1' } else { '0' }
    Write-Output "Preview: http://127.0.0.1:$Port/"
    if ($Demo) { Write-Output 'DEMO ONLY: synthetic data, not school rules.' }
    & $pythonPath -m uvicorn campus_assistant.main:app --app-dir $sourcePath --host 127.0.0.1 --port $Port --reload
} finally {
    $env:CAMPUS_DEMO = $previousDemo
}
