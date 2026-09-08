"""
Unit tests for fault_detector.py

Run with:
    python -m pytest tests/ -v
(run from project root, with src/ on PYTHONPATH -- see README)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sensor_simulator import SensorReading
from fault_detector import FaultDetector, Severity


def make_reading(**overrides) -> SensorReading:
    base = dict(
        timestamp="2026-01-01T00:00:00Z",
        vehicle_id="TEST-001",
        engine_temp_c=75.0,
        brake_pressure_bar=6.0,
        traction_motor_current_a=120.0,
        speed_kmh=80.0,
        battery_voltage_v=74.0,
        fault_code="NONE",
    )
    base.update(overrides)
    return SensorReading(**base)


def test_nominal_reading_is_ok():
    detector = FaultDetector()
    result = detector.evaluate(make_reading())
    assert result.severity == Severity.OK


def test_engine_overheat_critical():
    detector = FaultDetector()
    result = detector.evaluate(make_reading(engine_temp_c=105))
    assert result.severity == Severity.CRITICAL
    assert any("Engine temp" in m for m in result.messages)


def test_engine_temp_warning_threshold():
    detector = FaultDetector()
    result = detector.evaluate(make_reading(engine_temp_c=92))
    assert result.severity == Severity.WARNING


def test_brake_pressure_critical():
    detector = FaultDetector()
    result = detector.evaluate(make_reading(brake_pressure_bar=3.5))
    assert result.severity == Severity.CRITICAL


def test_battery_low_warning():
    detector = FaultDetector()
    result = detector.evaluate(make_reading(battery_voltage_v=68))
    assert result.severity == Severity.WARNING


def test_multiple_faults_reports_all_messages():
    detector = FaultDetector()
    result = detector.evaluate(make_reading(engine_temp_c=105, battery_voltage_v=60))
    assert result.severity == Severity.CRITICAL
    assert len(result.messages) == 2
