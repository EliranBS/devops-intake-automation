import json, logging, time
from contextlib import contextmanager
from src.intake.security import redact_secrets

logger = logging.getLogger("devops_intake")

def log_event(**fields):
    safe = {k: redact_secrets(str(v)) if v is not None else None for k, v in fields.items()}
    logger.info(json.dumps(safe, sort_keys=True))

@contextmanager
def timed_event(action: str, **fields):
    start = time.perf_counter()
    try:
        yield
        log_event(action=action, status="success", durationMs=int((time.perf_counter()-start)*1000), **fields)
    except Exception as exc:
        log_event(action=action, status="failure", errorCode=exc.__class__.__name__, durationMs=int((time.perf_counter()-start)*1000), **fields)
        raise
