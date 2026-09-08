# Vehicle Diagnostics Data Logger

A simulated rail-vehicle diagnostics pipeline built to explore the
kind of embedded, Linux-based diagnostics and data-transmission
systems used in rolling-stock engineering (inspired by locomotive
diagnostics / Train IT systems at companies like Siemens Mobility).

## What it does

Simulates a stream of sensor telemetry from a locomotive (engine
temperature, brake pressure, traction motor current, speed, battery
voltage), evaluates each reading against safety thresholds, persists
every reading to a local log, and forwards diagnostic records to a
remote/landside system — with automatic local queuing if the
"vehicle" has no connectivity.

```
SensorSimulator -> FaultDetector -> DiagnosticsLogger -> Transmitter (REST or local queue)
```

## Why these design choices

- **Rule-based fault detection, not ML** — deterministic and auditable,
  which matters for anything safety-adjacent (see `docs/V-MODEL.md`
  for how this maps to IEC 50128 / IEC 61131-style requirements
  traceability).
- **Pluggable transmitter interface** — `BaseTransmitter` can be
  backed by REST today and swapped for MQTT or a TCN-based transport
  later without touching the detection or logging logic.
- **JSON Lines local logging** — append-only, human-readable, and
  trivial to tail/inspect on an embedded Linux target without a
  database dependency.
- **Local queue fallback** — mirrors how real vehicle telemetry
  systems handle loss of coverage (tunnels, remote track) by queuing
  data locally and flushing once connectivity returns.

## Project structure

```
vehicle-diagnostics-logger/
├── src/
│   ├── sensor_simulator.py     # generates synthetic sensor telemetry
│   ├── fault_detector.py       # threshold-based fault classification
│   ├── diagnostics_logger.py   # persists results to JSON Lines log
│   ├── remote_transmitter.py   # REST + local-queue transmission
│   └── main.py                 # wires the pipeline together (CLI entry point)
├── tests/
│   └── test_fault_detector.py  # unit tests for fault classification
├── docs/
│   └── V-MODEL.md              # requirements -> design -> test traceability
└── README.md
```

## Running it

```bash
cd src
python main.py --interval 1 --cycles 20 --transmitter local
```

Flags:
- `--vehicle-id` — vehicle identifier tag (default `LOCO-0042`)
- `--interval` — seconds between simulated readings
- `--cycles` — number of readings to generate (`0` = run forever)
- `--transmitter` — `local` (queue to disk) or `rest` (POST to `http://localhost:8000/telemetry`)

Output logs land in `logs/diagnostics.jsonl` (all readings) and
`logs/transmit_queue.jsonl` (records queued due to no connectivity).

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Possible extensions

- Swap the REST transmitter for MQTT (`paho-mqtt`) to more closely
  mirror real telemetry protocols
- Add a small Flask endpoint to receive and visualize transmitted
  records, demonstrating the landside/control-center side too
- Port the core detection logic to C++ to demonstrate the same design
  on an embedded target
- Add a simple TCN/MVB-style framing simulation for the sensor layer

## Relevance

This project was built to demonstrate the core responsibilities in a
Train IT / vehicle diagnostics software role: requirements-to-design
traceability (V-model), Linux-based embedded software structure,
diagnostics/data analysis, and remote (landside) data transmission
with fault-tolerant queuing.
