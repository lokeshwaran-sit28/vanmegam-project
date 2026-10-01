# TDMA Schedule Planner and Optimizer for Wireless Networks

> **Internship Assignment**: Wireless Protocol Development Role  
> **Python Version**: Python 3.11+  
> **Test Status**: 113 / 113 unit & integration tests passing (`pytest tests/`)

---

## Project Overview

This repository implements a **Collision-Free Spatial Reuse TDMA Schedule Planner and Optimizer** for wireless ad-hoc networks.

In wireless communications using Time Division Multiple Access (TDMA), nodes share the physical radio channel by transmitting in assigned time slots. To prevent packet collisions at receivers, slot assignments must satisfy two key constraints:
1. **Direct Interference (Distance-1)**: Immediate neighbors within transmission range must not share a slot.
2. **Hidden Terminal Interference (Distance-2)**: Nodes that share a common neighbor must not share a slot.

This project solves this scheduling problem by mapping it to a **Distance-2 Graph Coloring Problem** on a communication graph $G$, constructing a conflict graph $C$, and applying the **DSATUR heuristic** alongside a greedy local improvement pass.

---

## Repository Structure

```
tdma-schedule-optimizer/
├── src/
│   └── tdma_optimizer/        # Part 1 Core Engine
│       ├── __init__.py        # Package exports
│       ├── cli.py             # CLI parser & pipeline driver
│       ├── coloring.py        # DSATUR coloring & color normalization
│       ├── conflict_graph.py  # Distance-2 conflict graph builder
│       ├── matrix.py          # Boolean schedule matrix builder
│       ├── models.py          # Dataclass models (NodeCoordinate, ScheduleResult)
│       ├── optimizer.py       # Greedy local improvement pass
│       ├── reporting.py       # ASCII & JSON report formatters
│       ├── topology.py        # Coordinate parsing & graph construction
│       └── validator.py       # Conflict validator & sanity checker
├── part2-emane/               # Part 2 EMANE Integration
│   ├── README.md              # Part 2 standalone user guide
│   ├── configs/               # EMANE XML configuration templates
│   │   ├── nem.xml            # MAC/PHY definition
│   │   ├── platform.xml       # Full 16-NEM platform topology
│   │   ├── transvirtual.xml   # Virtual transport configuration
│   │   └── tdma-schedule.xml  # Generated EMANE XML schedule output
│   ├── integration/
│   │   └── schedule_adapter.py# Part 1 -> EMANE XML schedule adapter
│   └── scripts/
│       ├── generate_schedule.py # CLI generator for EMANE XML schedule
│       ├── run_demo.py        # End-to-end Python demo runner
│       ├── run_demo.sh        # Linux shell runner with event service injection
│       ├── launch_emane.sh    # Network namespace & EMANE launcher script
│       └── cleanup.sh         # Cleanup script for Linux interfaces & namespaces
├── tests/                     # Automated Test Suite (113 tests)
│   ├── test_conflict_graph.py
│   ├── test_emane_adapter.py  # Part 2 EMANE Schedule Adapter tests
│   ├── test_end_to_end.py
│   ├── test_topology.py
│   └── test_validator.py
├── docs/                      # Technical Documentation
│   ├── algorithm.md           # Graph formulations & complexity analysis
│   ├── design.md              # System design & data flow diagrams
│   └── part2_emane.md         # Detailed EMANE integration design & specification
├── documentation/
│   └── TDMA_Project_Report.md # Comprehensive 25-section project report
├── presentation/
│   └── presentation_outline.md# 12-slide interview presentation outline
└── examples/
    ├── nodes16.json           # 16-node grid test topology
    └── small_network.json     # 3-node line topology
```

---

## Quick Start (Part 1 - TDMA Optimizer)

### 1. Setup Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Run Scheduling Pipeline
```bash
# Run on 16-node grid topology
python -m tdma_optimizer --file examples/nodes16.json

# Run with custom radio range (e.g., 400m)
python -m tdma_optimizer --file examples/nodes16.json --radio-range 400

# Output in JSON format
python -m tdma_optimizer --file examples/nodes16.json --output-format json
```

### 3. Run Automated Tests
```bash
pytest tests/ -v
```

---

## Part 2 – EMANE Integration

> **Testing Status Note**: Live EMANE runtime execution and packet delivery were not performed in the current Windows development environment.

### Architecture
```
  Python TDMA Schedule Optimizer (Part 1)
                    │
                    ▼ Node -> Slot
   Schedule Adapter (schedule_adapter.py)
                    │
                    ▼ XML Schedule (<emane-tdma-schedule>)
    EMANE TDMA Event Scheduler (emaneevent-tdmaschedule)
                    │
                    ▼
     Linux Network Namespaces (node-1 .. node-16)
                    │
                    ▼
       Virtual TAP Interfaces (emane1..16)
```

### Categorization of Implementation Status
- **A. Implemented & Unit-Tested**: `schedule_adapter.py`, deterministic NEM mapping, 1 ms slot XML generator, 10 unit tests (`pytest tests/test_emane_adapter.py`).
- **B. Configuration Generated**: `tdma-schedule.xml` (official `<emane-tdma-schedule>` syntax), `nem.xml`, `platform.xml` (all 16 NEMs), `transvirtual.xml`.
- **C. Designed but NOT Runtime-Tested**: Linux network namespace creation (`ip netns`), TAP interface binding, live EMANE event service injection (`emaneevent-tdmaschedule`), `iperf3` packet flow testing.
- **D. Actually Runtime-Tested**: Python schedule generation, XML structure validation, and unit tests run on host environment.

### Generating EMANE Schedule XML
```bash
python part2-emane/scripts/generate_schedule.py --file examples/nodes16.json --output part2-emane/configs/tdma-schedule.xml
```

### Running EMANE Demo Runner
```bash
python part2-emane/scripts/run_demo.py --file examples/nodes16.json
```

---

## Testing Summary

| Test Module | Status | Count | Details |
|---|---|---|---|
| `test_coloring.py` | **PASSED** | 16 | DSATUR heuristic & color normalization |
| `test_conflict_graph.py` | **PASSED** | 13 | Distance-1 & Distance-2 edge generation |
| `test_emane_adapter.py` | **PASSED** | 10 | Part 2 EMANE XML schedule adapter & NEM mapping |
| `test_end_to_end.py` | **PASSED** | 33 | 16-node grid, spatial reuse, invalid inputs |
| `test_topology.py` | **PASSED** | 29 | Coordinate parsing & Communication graph |
| `test_validator.py` | **PASSED** | 12 | Dynamic conflict detection & matrix checks |
| **Total Test Suite** | **PASSED** | **113** | Executed in 0.28s via `pytest tests/` |
