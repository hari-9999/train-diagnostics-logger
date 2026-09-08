# V-Model Development Documentation

This project was structured using the V-Model, mapping each development
stage to its corresponding verification/validation stage — the same
approach referenced in Siemens Mobility's Train IT engineering process.

## 1. Requirements Definition (left side, top)

**System Requirement:** The vehicle shall continuously monitor key
subsystem parameters (engine temperature, brake pressure, traction
current, battery voltage) and report abnormal conditions to a landside
system for maintenance planning.

| ID | Requirement |
|----|-------------|
| REQ-01 | System shall sample sensor data at a configurable interval |
| REQ-02 | System shall classify each reading as OK / WARNING / CRITICAL against defined thresholds |
| REQ-03 | System shall persist every reading locally, regardless of network availability |
| REQ-04 | System shall transmit diagnostic records to a remote/landside endpoint when connectivity is available |
| REQ-05 | System shall queue records locally and retry transmission when connectivity is lost (loss-of-coverage tolerance) |
| REQ-06 | Fault thresholds shall be defined declaratively so they can be reviewed/changed without modifying detection logic |

## 2. System / Interface Specification (left side, middle)

**Interfaces:**
- `SensorReading` — data contract between the sensor layer and detection layer (dataclass, see `src/sensor_simulator.py`)
- `DiagnosticResult` — data contract between detection and logging/transmission layers (`src/fault_detector.py`)
- `BaseTransmitter.send(record: dict) -> bool` — abstract interface so transmission mechanism (REST, MQTT, local queue) can be swapped without touching upstream logic

This mirrors real Train IT architecture, where the vehicle diagnostics
bus (TCN / MVB / WTB) is abstracted behind a stable interface so that
downstream software isn't coupled to the physical transport layer.

## 3. Software Architecture / Module Design (left side, bottom)

```
SensorSimulator  -->  FaultDetector  -->  DiagnosticsLogger  -->  Transmitter
   (src/sensor_       (src/fault_        (src/diagnostics_       (src/remote_
    simulator.py)       detector.py)       logger.py)              transmitter.py)
```

Each module has a single responsibility and communicates only through
typed data objects, so any stage can be unit tested in isolation.

## 4. Implementation (bottom of the V)

Implemented in Python 3 for rapid development; the module boundaries
are deliberately kept close to what a C++ embedded implementation
would look like (no framework magic, explicit data contracts) so the
design could be ported to C++ for a production embedded target with
minimal restructuring.

## 5. Unit Testing (right side, bottom — verifies Implementation)

`tests/test_fault_detector.py` verifies each threshold rule in
isolation (nominal, warning, critical, and combined-fault cases).
Corresponds to REQ-02.

## 6. Integration Testing (right side, middle — verifies Architecture)

`src/main.py` wires all four modules together end-to-end and was run
manually to confirm: nominal readings log correctly, injected faults
are classified correctly, and records reach the transmitter/queue
regardless of "connectivity." Corresponds to REQ-01, REQ-03, REQ-04, REQ-05.

## 7. System / Acceptance Testing (right side, top — verifies Requirements)

Manual test run (`python main.py --cycles 20`) confirmed:
- Continuous sampling at the configured interval (REQ-01)
- Correct OK / WARNING / CRITICAL classification against thresholds (REQ-02)
- All readings persisted to `logs/diagnostics.jsonl` even with the
  local-queue transmitter selected, simulating no connectivity (REQ-03, REQ-05)

## Traceability Summary

| Requirement | Design Element | Test |
|---|---|---|
| REQ-01 | `SensorSimulator.stream()` | Manual run, `--interval` flag |
| REQ-02 | `FaultDetector.evaluate()` | `test_fault_detector.py` (6 cases) |
| REQ-03 | `DiagnosticsLogger.log()` | Manual run, `logs/diagnostics.jsonl` inspection |
| REQ-04 | `RestTransmitter.send()` | Manual run against local endpoint |
| REQ-05 | `LocalQueueTransmitter.send()` | Manual run, `logs/transmit_queue.jsonl` inspection |
| REQ-06 | `THRESHOLDS` dict in `fault_detector.py` | Code review — thresholds isolated from logic |
