"""Optional self-hosted services; the generation node pack is always independent."""
import importlib
import logging
import os

VERSION = "0.3.0"
BATCH_ENV = "MINIMX_ENABLE_BATCH_SERVICE"


def initialize_batch_service():
    """Default: no queue import, DB creation, worker or local prompt submission."""
    requested = os.environ.get(BATCH_ENV, "0") == "1"
    state = {"version": VERSION, "batch_requested": requested,
             "batch_enabled": False, "runninghub_member_supported": False,
             "batch_error_type": None}
    if not requested:
        return state
    try:
        importlib.import_module(".batch_service", __package__)
    except Exception as exc:
        # Only optional services are isolated. Core node import errors still
        # propagate normally so missing generation dependencies remain visible.
        state["batch_error_type"] = type(exc).__name__
        logging.exception("[MiniMX] Optional batch service unavailable; generation nodes remain loaded")
    else:
        state["batch_enabled"] = True
    return state
