"""
fault_detector.py

Applies threshold-based rules to sensor readings to classify severity.
This is intentionally simple (rule-based, not ML) because on real
diagnostics systems, deterministic, auditable fault logic is preferred
over black-box models -- traceability matters for safety-related systems
(see IEC 61131 / IEC 50128 style requirements referenced in docs/).
"""

from enum import Enum
from dataclasses import dataclass
from sensor_simulator import SensorReading


class Severity(Enum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class DiagnosticResult:
    reading: SensorReading
    severity: Severity
    messages: list


THRESHOLDS = {
    "engine_temp_c": {"warning": 90, "critical": 100},
    "brake_pressure_bar": {"warning": 5.0, "critical": 4.0},  # lower is worse
    "battery_voltage_v": {"warning": 69, "critical": 65},     # lower is worse
}


class FaultDetector:
    def evaluate(self, reading: SensorReading) -> DiagnosticResult:
        messages = []
        severity = Severity.OK

        # Engine temperature (higher = worse)
        if reading.engine_temp_c >= THRESHOLDS["engine_temp_c"]["critical"]:
            severity = Severity.CRITICAL
            messages.append(f"Engine temp critical: {reading.engine_temp_c}C")
        elif reading.engine_temp_c >= THRESHOLDS["engine_temp_c"]["warning"]:
            severity = max(severity, Severity.WARNING, key=self._rank)
            messages.append(f"Engine temp elevated: {reading.engine_temp_c}C")

        # Brake pressure (lower = worse)
        if reading.brake_pressure_bar <= THRESHOLDS["brake_pressure_bar"]["critical"]:
            severity = Severity.CRITICAL
            messages.append(f"Brake pressure critical: {reading.brake_pressure_bar} bar")
        elif reading.brake_pressure_bar <= THRESHOLDS["brake_pressure_bar"]["warning"]:
            severity = max(severity, Severity.WARNING, key=self._rank)
            messages.append(f"Brake pressure low: {reading.brake_pressure_bar} bar")

        # Battery voltage (lower = worse)
        if reading.battery_voltage_v <= THRESHOLDS["battery_voltage_v"]["critical"]:
            severity = Severity.CRITICAL
            messages.append(f"Battery voltage critical: {reading.battery_voltage_v} V")
        elif reading.battery_voltage_v <= THRESHOLDS["battery_voltage_v"]["warning"]:
            severity = max(severity, Severity.WARNING, key=self._rank)
            messages.append(f"Battery voltage low: {reading.battery_voltage_v} V")

        if not messages:
            messages.append("All parameters nominal")

        return DiagnosticResult(reading=reading, severity=severity, messages=messages)

    @staticmethod
    def _rank(sev: Severity) -> int:
        order = {Severity.OK: 0, Severity.WARNING: 1, Severity.CRITICAL: 2}
        return order[sev]
