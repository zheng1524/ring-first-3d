import time
import traceback
import numpy as np


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def timed_test(name, function):
    t = time.monotonic()
    try:
        details = function()
        return dict(name=name, status="PASS", seconds=time.monotonic() - t, details=clean(details))
    except (ImportError, FileNotFoundError) as e:
        return dict(name=name, status="NOT_EVALUABLE", seconds=time.monotonic() - t, reason=str(e))
    except Exception:
        return dict(name=name, status="FAIL", seconds=time.monotonic() - t, traceback=traceback.format_exc())
