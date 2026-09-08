"""
remote_transmitter.py

Forwards diagnostic records to a landside / remote system.
In production this maps to the "data remote transmission" and
"landside communication" requirements in the job description -- a
real vehicle would push data over cellular/Wi-Fi to a control center
whenever the vehicle is in range. Here we implement it against a
local REST endpoint so the whole pipeline can be tested end-to-end
without needing real network hardware.

Swap `RestTransmitter` for an MQTT-based transmitter by implementing
the same `send()` interface if you want to demonstrate MQTT as well.
"""

import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("remote_transmitter")


class BaseTransmitter(ABC):
    @abstractmethod
    def send(self, record: dict) -> bool:
        ...


class RestTransmitter(BaseTransmitter):
    def __init__(self, endpoint_url: str, timeout_seconds: float = 3.0):
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds

    def send(self, record: dict) -> bool:
        try:
            import requests  # imported lazily so the module works without the dependency installed
            response = requests.post(
                self.endpoint_url,
                json=record,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            logger.info("Transmitted record for %s -> %s", record.get("vehicle_id"), self.endpoint_url)
            return True
        except Exception as exc:
            logger.warning("Transmission failed, will retry from queue: %s", exc)
            return False


class LocalQueueTransmitter(BaseTransmitter):
    """
    Fallback transmitter used when there's no connectivity (e.g. vehicle is
    in a tunnel or out of coverage). Records are queued to disk and can be
    flushed later once connectivity resumes -- a common real-world pattern
    for vehicle telemetry systems.
    """

    def __init__(self, queue_path: str = "logs/transmit_queue.jsonl"):
        from pathlib import Path
        self.queue_path = Path(queue_path)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, record: dict) -> bool:
        with self.queue_path.open("a") as f:
            f.write(json.dumps(record) + "\n")
        logger.info("Queued record locally (no connectivity): %s", record.get("vehicle_id"))
        return True
