#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import json
from pathlib import Path
from src.correlation.strategy import InMemoryCorrelationStore
from src.intake.pipeline import process_message
store = InMemoryCorrelationStore()
for p in sorted(Path('tests/fixtures').glob('*.json')):
    decision = process_message(json.loads(p.read_text()), 'devops-intake@example.com', store)
    print(p.name, decision.action, decision.category, decision.classification.missing_fields)
PY
