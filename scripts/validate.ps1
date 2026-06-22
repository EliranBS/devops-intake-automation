$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$pytestCheck = & python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('pytest') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Error @"
pytest is not installed in the active Python environment.

Install development dependencies from Windows PowerShell:
  python -m pip install --upgrade pip
  python -m pip install -e `".[dev]`"

Then rerun:
  .\scripts\validate.ps1
"@
    exit 1
}

python -m pytest
