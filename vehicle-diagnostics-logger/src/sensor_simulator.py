"""
sensor_simulator.py

Simulates real-time sensor data from a locomotive/rail vehicle subsystem.
In a real system this would be replaced by a driver reading from CAN bus,
MVB/WTB (TCN), or serial-connected hardware. Here we generate realistic
synthetic values so the rest of the pipeline (logging, fault detection,
remote transmission) can be developed and tested independently of hardware.
"""

import random
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class SensorReading:
    timestamp: str
    vehicle_id: str
    engine_temp_c: float
    brake_pressure_bar: float
    traction_motor_current_a: float
    speed_kmh: float
    battery_voltage_v: float
    fault_code: str = "NONE"

    def to_dict(self):
        return asdict(self)


class SensorSimulator:
    """
    Generates a stream of SensorReading objects.

    Values drift slowly around a baseline to mimic real telemetry, with a
    configurable random chance of producing an out-of-range / fault reading
    so the fault detector has something meaningful to catch.
    """

    def __init__(self, vehicle_id: str = "LOCO-0042", fault_probability: float = 0.05):
        self.vehicle_id = vehicle_id
        self.fault_probability = fault_probability

        # Baselines representing "normal" operating conditions
        self._engine_temp = 75.0
        self._brake_pressure = 6.0
        self._traction_current = 120.0
        self._speed = 80.0
        self._battery_voltage = 74.0

    def _drift(self, value: float, step: float, low: float, high: float) -> float:
        value += random.uniform(-step, step)
        return max(low, min(high, value))

    def read(self) -> SensorReading:
        # Normal drift
        self._engine_temp = self._drift(self._engine_temp, 1.5, 60, 95)
        self._brake_pressure = self._drift(self._brake_pressure, 0.2, 4.5, 7.5)
        self._traction_current = self._drift(self._traction_current, 5, 90, 160)
        self._speed = self._drift(self._speed, 3, 0, 140)
        self._battery_voltage = self._drift(self._battery_voltage, 0.3, 68, 78)

        fault_code = "NONE"

        # Occasionally inject an out-of-range fault condition
        if random.random() < self.fault_probability:
            fault_type = random.choice(["OVERHEAT", "LOW_BRAKE_PRESSURE", "LOW_BATTERY"])
            if fault_type == "OVERHEAT":
                self._engine_temp = random.uniform(96, 110)
                fault_code = "ENG_OVERHEAT"
            elif fault_type == "LOW_BRAKE_PRESSURE":
                self._brake_pressure = random.uniform(2.0, 4.4)
                fault_code = "BRAKE_LOW_PRESSURE"
            elif fault_type == "LOW_BATTERY":
                self._battery_voltage = random.uniform(55, 67)
                fault_code = "BATTERY_LOW_VOLTAGE"

        return SensorReading(
            timestamp=datetime.now(timezone.utc).isoformat(),
            vehicle_id=self.vehicle_id,
            engine_temp_c=round(self._engine_temp, 2),
            brake_pressure_bar=round(self._brake_pressure, 2),
            traction_motor_current_a=round(self._traction_current, 2),
            speed_kmh=round(self._speed, 2),
            battery_voltage_v=round(self._battery_voltage, 2),
            fault_code=fault_code,
        )

    def stream(self, interval_seconds: float = 1.0):
        """Generator that yields readings forever at a fixed interval."""
        while True:
            yield self.read()
            time.sleep(interval_seconds)
