#!/usr/bin/env bash
# Optional helper for non-Windows environments only. The supported default workflow is scripts/validate.ps1 in Windows PowerShell.
set -euo pipefail
python -m pytest
