param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:LAB_PORT = "$Port"
& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\serve.py"
exit $LASTEXITCODE