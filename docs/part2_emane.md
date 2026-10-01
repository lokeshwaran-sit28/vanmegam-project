# Part 2 – EMANE Integration Design & Specification

> **Execution & Testing Status**:  
> - **Live EMANE runtime execution and packet delivery were not performed in the current Windows development environment.**
> - **Implemented & Unit-Tested**: `schedule_adapter.py` Python module, node-to-NEM mapping, 1 ms slot XML serializer, and 10 unit tests (`tests/test_emane_adapter.py`).
> - **Configuration Generated**: `part2-emane/configs/tdma-schedule.xml` conforming to official EMANE schema (`<emane-tdma-schedule>`), `nem.xml`, `platform.xml` (all 16 NEMs), `transvirtual.xml`.
> - **Designed but NOT Runtime-Tested**: Linux network namespace isolation (`ip netns`), TAP interface creation, live EMANE event service injection (`emaneevent-tdmaschedule`), `iperf3` packet flow testing.

---

## 1. Objective

The objective of Part 2 is to take the optimized TDMA slot schedule calculated by Part 1 (`ScheduleResult`) and convert it into an official EMANE TDMA Schedule XML file for consumption by the **EMANE (Extendable Mobile Ad-hoc Network Emulator) TDMA Radio Model** (`tdmaeventscheduler`).

---

## 2. EMANE Overview

**EMANE** is an open-source framework developed by Adjacent Link / NRL for emulating mobile ad-hoc wireless networks.

- It emulates physical (PHY) and medium access control (MAC) layers in real time.
- It attaches to network applications using TUN/TAP virtual interfaces.
- The **EMANE TDMA Radio Model** enforces time-slot access for Network Emulation Modules (NEMs) driven by `TDMAScheduleEvent` messages.

---

## 3. Architecture & Network Namespace Isolation

To prevent Linux host routing from bypassing EMANE (which occurs if all TAP interfaces reside in the root namespace), each node is assigned an isolated **Linux Network Namespace** (`node-1` .. `node-16`).

```
  Linux Network Namespace (node-5)        Linux Network Namespace (node-6)
     ┌───────────────────────┐               ┌───────────────────────┐
     │  iperf3 client        │               │  iperf3 server        │
     │  10.0.0.5/24          │               │  10.0.0.6/24          │
     └──────────┬────────────┘               └──────────┬────────────┘
                │ TAP                                   │ TAP
                ▼ (emane5)                              ▼ (emane6)
     ┌───────────────────────────────────────────────────────────────┐
     │                 EMANE Platform Daemon                         │
     │  NEM 5 (MAC/PHY) <── TDMAScheduleEvent ──> NEM 6 (MAC/PHY)    │
     └───────────────────────────────────────────────────────────────┘
```

---

## 4. Categorization of Features

| Category | Description | Status |
|---|---|---|
| **A. Implemented & Unit-Tested** | Schedule adapter Python code, NEM mapper, XML generator, 10 unit tests | **PASSED** (10/10) |
| **B. Configuration Generated** | `tdma-schedule.xml`, `nem.xml`, `platform.xml`, `transvirtual.xml` | **GENERATED** |
| **C. Designed but NOT Runtime-Tested** | `launch_emane.sh`, `cleanup.sh`, `emaneevent-tdmaschedule`, `iperf3` namespace traffic | **DESIGN-PREPARED** |
| **D. Actually Runtime-Tested** | Python schedule calculation & XML structure validation | **PASSED** |

---

## 5. Target Environment & Installation Requirements

EMANE requires Linux kernel TUN/TAP support and `iproute2` network namespaces.

### Package Installation Commands (Ubuntu 22.04 LTS)
```bash
sudo apt-get update
sudo apt-get install -y \
    emane \
    emane-model-tdma \
    emane-eventservice \
    emanesh \
    iperf3 \
    iproute2 \
    python3
```

---

## 6. Official EMANE Schedule XML Format

The generated schedule format matches official EMANE specification:

```xml
<?xml version="1.0" ?>
<emane-tdma-schedule>
  <structure bandwidth="1000000" frames="1" slotduration="1000" slotoverhead="100" slots="9"/>
  <multiframe datarate="1000000" frequency="2350000000" power="0.0">
    <frame index="0">
      <slot index="0" nodes="5">
        <tx/>
      </slot>
      <slot index="4" nodes="2 14">
        <tx/>
      </slot>
      <slot index="8" nodes="1 10 13 16">
        <tx/>
      </slot>
    </frame>
  </multiframe>
</emane-tdma-schedule>
```

- **`slotduration`**: `1000` $\mu\text{s}$ (1 ms).
- **`nodes` attribute**: Space-separated NEM IDs assigned to transmit in that slot.

---

## 7. Packet-Flow Test Procedure (Linux)

To execute packet testing inside isolated network namespaces:

```bash
# Start iperf3 server in node-6 namespace
sudo ip netns exec node-6 iperf3 -s -D

# Transmit UDP stream from node-5 namespace to node-6
sudo ip netns exec node-5 iperf3 -c 10.0.0.6 -u -b 1M -t 10
```

---

## 8. Verification Commands (Linux)

```bash
# Verify active TDMA schedule in EMANE
emanesh localhost get table 1 mac scheduler.ScheduleInfoTable

# Verify active TDMA structure parameters
emanesh localhost get table 1 mac scheduler.StructureInfoTable
```

---

## 9. Reproduction Steps

```bash
# Run full test suite (113 tests)
pytest tests/ -v

# Generate EMANE XML schedule
python part2-emane/scripts/generate_schedule.py --file examples/nodes16.json --output part2-emane/configs/tdma-schedule.xml

# Run Python integration demo
python part2-emane/scripts/run_demo.py --file examples/nodes16.json
```
