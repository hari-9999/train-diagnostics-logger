"""
diagnostics_logger.py

Persists diagnostic results to a local log store (JSON Lines format).
JSON Lines is used because it is append-only, human-readable, and easy
to tail/stream on an embedded Linux system without needing a database.
"""

import json
import logging
from pathlib import Path
from fault_detector import DiagnosticResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("diagnostics_logger")


class DiagnosticsLogger:
    def __init__(self, log_path: str = "logs/diagnostics.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, result: DiagnosticResult) -> dict:
        record = {
            "timestamp": result.reading.timestamp,
            "vehicle_id": result.reading.vehicle_id,
            "severity": result.severity.value,
            "messages": result.messages,
            "readings": result.reading.to_dict(),
        }

        with self.log_path.open("a") as f:
            f.write(json.dumps(record) + "\n")

        if result.severity.value == "CRITICAL":
            logger.error("CRITICAL fault on %s: %s", result.reading.vehicle_id, result.messages)
        elif result.severity.value == "WARNING":
            logger.warning("Warning on %s: %s", result.reading.vehicle_id, result.messages)
        else:
            logger.info("Nominal reading logged for %s", result.reading.vehicle_id)

        return record
