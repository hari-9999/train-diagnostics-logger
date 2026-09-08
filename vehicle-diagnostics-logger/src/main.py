"""
main.py

Entry point for the Vehicle Diagnostics Data Logger.

Pipeline:
    SensorSimulator -> FaultDetector -> DiagnosticsLogger -> Transmitter

Run:
    python main.py --interval 1 --cycles 20 --transmitter local
"""

import argparse
import sys

from sensor_simulator import SensorSimulator
from fault_detector import FaultDetector
from diagnostics_logger import DiagnosticsLogger
from remote_transmitter import RestTransmitter, LocalQueueTransmitter


def build_transmitter(kind: str):
    if kind == "rest":
        return RestTransmitter(endpoint_url="http://localhost:8000/telemetry")
    return LocalQueueTransmitter()


def run(vehicle_id: str, interval: float, cycles: int, transmitter_kind: str):
    simulator = SensorSimulator(vehicle_id=vehicle_id)
    detector = FaultDetector()
    logger_ = DiagnosticsLogger()
    transmitter = build_transmitter(transmitter_kind)

    count = 0
    for reading in simulator.stream(interval_seconds=interval):
        result = detector.evaluate(reading)
        record = logger_.log(result)
        transmitter.send(record)

        count += 1
        if cycles and count >= cycles:
            break


def parse_args():
    parser = argparse.ArgumentParser(description="Vehicle Diagnostics Data Logger")
    parser.add_argument("--vehicle-id", default="LOCO-0042")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between readings")
    parser.add_argument("--cycles", type=int, default=20, help="Number of readings to generate (0 = run forever)")
    parser.add_argument("--transmitter", choices=["local", "rest"], default="local")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run(args.vehicle_id, args.interval, args.cycles, args.transmitter)
    except KeyboardInterrupt:
        sys.exit(0)
