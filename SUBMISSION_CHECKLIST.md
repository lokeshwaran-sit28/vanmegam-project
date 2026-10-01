# GitHub Submission Checklist & Verification Report

> **Project**: TDMA Schedule Planner and Optimizer for Wireless Networks  
> **Role**: Wireless Protocol Development Internship Assignment  
> **Python Version**: Python 3.11+  
> **Overall Test Status**: **113 / 113 PASSED** (0.29s)

---

## 1. Project Overview

This repository provides an end-to-end Python application that plans, optimizes, validates, and exports collision-free TDMA (Time Division Multiple Access) time-slot schedules for wireless ad-hoc and mesh networks.

- **Part 1 (Core TDMA Optimizer)**: Parses 2-D node positions, builds a Distance-2 conflict graph to model direct and hidden-terminal interference, applies the **DSATUR graph coloring heuristic** with greedy local search, builds a Boolean schedule matrix, and validates conflict-free constraints.
- **Part 2 (EMANE Integration)**: Provides an official XML schedule adapter (`schedule_adapter.py`) that converts Part 1 schedules into official EMANE `<emane-tdma-schedule>` XML events with 1 ms slot timing, supported by complete Linux network namespace deployment scripts.

---

## 2. Repository Structure

```
tdma-schedule-optimizer/
├── SUBMISSION_CHECKLIST.md    # Final submission checklist & report (This file)
├── README.md                  # Main project landing page & documentation
├── pyproject.toml             # Package setup & build configuration
├── requirements.txt           # Dependency manifest
├── src/
│   └── tdma_optimizer/        # Part 1 Core Engine
│       ├── __init__.py        # Package exports
│       ├── cli.py             # CLI parser & pipeline entry point
│       ├── coloring.py        # DSATUR coloring & color normalization
│       ├── conflict_graph.py  # Distance-2 conflict graph builder
│       ├── matrix.py          # Boolean schedule matrix generator
│       ├── models.py          # Pure dataclass models
│       ├── optimizer.py       # Greedy local improvement pass
│       ├── reporting.py       # ASCII & JSON report formatters
│       ├── topology.py        # Coordinate parsing & graph builder
│       └── validator.py       # Independent conflict validator
├── part2-emane/               # Part 2 EMANE Integration
│   ├── README.md              # Part 2 user guide
│   ├── configs/               # EMANE XML configuration templates
│   │   ├── nem.xml            # MAC/PHY definition
│   │   ├── platform.xml       # Full 16-NEM platform topology
│   │   ├── transvirtual.xml   # Virtual transport configuration
│   │   └── tdma-schedule.xml  # Generated EMANE XML schedule output
│   ├── integration/
│   │   └── schedule_adapter.py# Schedule -> EMANE XML adapter
│   └── scripts/
│       ├── generate_schedule.py # CLI XML schedule generator
│       ├── run_demo.py        # End-to-end Python demo runner
│       ├── run_demo.sh        # Linux shell runner with event injection
│       ├── launch_emane.sh    # Network namespace & EMANE launcher
│       └── cleanup.sh         # Cleanup script for Linux interfaces
├── tests/                     # Automated Test Suite (113 tests)
│   ├── test_coloring.py       # 16 tests
│   ├── test_conflict_graph.py # 13 tests
│   ├── test_emane_adapter.py  # 10 tests (Part 2)
│   ├── test_end_to_end.py     # 33 tests
│   ├── test_topology.py       # 29 tests
│   └── test_validator.py      # 12 tests
├── docs/                      # Technical Documentation
│   ├── algorithm.md           # Graph formulations & complexity analysis
│   ├── design.md              # System design & module boundaries
│   ├── interview_questions.md # 20 technical Q&A for interview panel
│   └── part2_emane.md         # EMANE design specification
├── documentation/
│   └── TDMA_Project_Report.md # Comprehensive 25-section project report
├── presentation/
│   └── presentation_outline.md# 12-slide interview presentation outline
└── examples/
    ├── nodes16.json           # 16-node grid topology dataset
    └── small_network.json     # 3-node line topology dataset
```

---

## 3. How to Install

```bash
# Clone repository
git clone https://github.com/your-username/tdma-schedule-optimizer.git
cd tdma-schedule-optimizer

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .
```

---

## 4. How to Run Part 1

```bash
# Run on 16-node grid topology (default output format)
python -m tdma_optimizer --file examples/nodes16.json

# Run with custom radio transmission range (e.g. 400m)
python -m tdma_optimizer --file examples/nodes16.json --radio-range 400

# Output report in machine-readable JSON format
python -m tdma_optimizer --file examples/nodes16.json --output-format json
```

---

## 5. How to Run Automated Tests

```bash
# Run full test suite quietly
pytest -q

# Run full test suite with verbose output
pytest tests/ -v
```

---

## 6. How to Generate EMANE Schedule XML (Part 2)

```bash
python part2-emane/scripts/generate_schedule.py --file examples/nodes16.json --output part2-emane/configs/tdma-schedule.xml
```

---

## 7. Linux & EMANE Requirements

EMANE execution requires Linux kernel-level TUN/TAP virtual devices and network namespaces (`ip netns`).

### Ubuntu 22.04 LTS Installation Commands
```bash
sudo apt-get update
sudo apt-get install -y emane emane-model-tdma emane-eventservice emanesh iperf3 iproute2 python3
```

### Linux Execution Commands
```bash
# Launch virtual TAP interfaces inside node-1..node-16 network namespaces
sudo bash part2-emane/scripts/launch_emane.sh 16 part2-emane/configs/tdma-schedule.xml

# Inject schedule event into EMANE
emaneevent-tdmaschedule part2-emane/configs/tdma-schedule.xml -i lo

# Verify schedule table via emanesh
emanesh localhost get table 1 mac scheduler.ScheduleInfoTable

# Test isolated namespace traffic (Node 5 -> Node 6)
sudo ip netns exec node-6 iperf3 -s -D
sudo ip netns exec node-5 iperf3 -c 10.0.0.6 -u -b 1M -t 10

# Cleanup interfaces and namespaces
sudo bash part2-emane/scripts/cleanup.sh
```

---

## 8. Testing Status & Honest Reporting

> **Critical Notice**: Live EMANE daemon execution and packet transmission were NOT performed in the current Windows development environment.

| Category | Description | Status |
|---|---|---|
| **A. Implemented & Unit-Tested** | Core DSATUR algorithm, optimizer, validator, matrix builder, EMANE schedule adapter, XML generator | **PASSED** (113/113 tests) |
| **B. Configuration Generated** | `tdma-schedule.xml` (official `<emane-tdma-schedule>` schema), `nem.xml`, `platform.xml` (all 16 NEMs), `transvirtual.xml` | **GENERATED** |
| **C. Designed for Linux** | Network namespace launcher (`launch_emane.sh`), `emaneevent-tdmaschedule` injection, `iperf3` namespace traffic test | **DESIGN-PREPARED** |
| **D. Actually Runtime-Tested** | Schedule optimization on 16-node grid, XML syntax validation, full Python test suite on host system | **PASSED** |

---

## 9. Known Limitations

1. **Host OS Constraint**: EMANE cannot run natively on Windows without WSL2 or an Ubuntu VM.
2. **Timer Precision**: 1 ms slot durations ($1000\text{ }\mu\text{s}$) require high-precision Linux kernel timers. Virtualized environments may experience timer jitter.
3. **Static Topology**: Schedule is calculated for static node coordinates. Dynamic mobility requires periodic `TDMAScheduleEvent` updates over multicast.

---

## 10. Presentation & Interview Readiness Checklist

- [x] Part 1 test suite passing 100% (103 tests).
- [x] Part 2 test suite passing 100% (10 tests).
- [x] Schedule verified conflict-free (0 conflicts across 90 edges).
- [x] 16-node grid optimized to 9 slots.
- [x] Matrix matches Node $\to$ Slot assignments.
- [x] EMANE XML verified against official `<emane-tdma-schedule>` DTD schema.
- [x] All 16 NEMs explicitly defined in `platform.xml`.
- [x] Network namespace isolation design (`ip netns`) implemented in `launch_emane.sh`.
- [x] Technical Q&A document created (`docs/interview_questions.md`).
- [x] Project Report & Presentation Outline updated with honest execution status.
