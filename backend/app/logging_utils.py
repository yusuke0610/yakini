import json
import logging
from typing import Any

logger = logging.getLogger("devforge")


def log_event(level: int, event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.log(level, json.dumps(payload, ensure_ascii=False))
