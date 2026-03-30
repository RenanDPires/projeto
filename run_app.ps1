Param(
    [int]$Port = 8501,
    [string]$Address = "localhost"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
}
$appEntry = Join-Path $projectRoot "app\main.py"

if (-not (Test-Path $appEntry)) {
    Write-Error "Arquivo de entrada nao encontrado: $appEntry"
}

if (-not (Test-Path $venvPython)) {
    Write-Error "Python do ambiente virtual nao encontrado em .venv\Scripts\python.exe nem venv\Scripts\python.exe"
}

Push-Location $projectRoot
try {
    $env:PYTHONPATH = $projectRoot
    & $venvPython -m streamlit run $appEntry --server.port $Port --server.address $Address
}
finally {
    Pop-Location
}
