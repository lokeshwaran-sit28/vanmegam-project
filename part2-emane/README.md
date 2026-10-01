# Part 2: EMANE TDMA Radio Model Integration

## Overview & Architecture

The goal of Part 2 is to bridge the slot schedule calculated by Part 1 (`ScheduleResult`) with **EMANE** (Extendable Mobile Ad-hoc Network Emulator) using the official **EMANE TDMA Radio Model** (`tdmaeventscheduler`).

```
                PART 1
                   │
                   ▼
      Python TDMA Schedule Optimizer
                   │
                   ▼ Node -> Slot (e.g., Node_01 -> Slot 8)
       Schedule Adapter (schedule_adapter.py)
                   │
                   ▼
       EMANE TDMA XML Schedule (<emane-tdma-schedule>)
                   │
                   ▼
    emaneevent-tdmaschedule -i lo tdma-schedule.xml
                   │
                   ▼
      EMANE TDMA Event Scheduler Engine
                   │
                   ▼
    Linux Network Namespaces (node-1 .. node-16)
                   │
                   ▼
        Virtual TAP Interfaces (emane1 .. emane16)
```

## Status & Capabilities

> **Important Note**: Live EMANE runtime execution and packet delivery were not performed in the current Windows development environment.

| Category | Status | Details |
|---|---|---|
| **A. Implemented and Unit-Tested** | **PASSED** | `schedule_adapter.py`, deterministic NEM mapping, 1 ms slot XML serializer, 10 unit tests (`pytest tests/test_emane_adapter.py`). |
| **B. Configuration Generated** | **GENERATED** | `tdma-schedule.xml` (official `<emane-tdma-schedule>` syntax), `nem.xml`, `platform.xml` (all 16 NEMs), `transvirtual.xml`. |
| **C. Designed but NOT Runtime-Tested** | **PREPARED** | Linux network namespace creation (`ip netns`), TAP interface binding, live EMANE event service injection (`emaneevent-tdmaschedule`), `iperf3` packet flow testing. |
| **D. Actually Runtime-Tested** | **PASSED** | Python schedule generation, XML structure validation, and unit tests run on host environment. |

## Official EMANE Schedule XML Format

```xml
<?xml version="1.0" ?>
<emane-tdma-schedule>
  <structure frames="1" slots="9" slotduration="1000" slotoverhead="100" bandwidth="1000000"/>
  <multiframe frequency="2350000000" power="0.0" datarate="1000000">
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

## Target Linux Deployment Commands (Ubuntu 22.04 LTS)

To execute the live EMANE simulation on a Linux system:

```bash
# 1. Install EMANE and networking tools
sudo apt-get update
sudo apt-get install -y emane emane-model-tdma emane-eventservice emanesh iperf3 iproute2

# 2. Generate EMANE XML schedule
python3 part2-emane/scripts/generate_schedule.py --file examples/nodes16.json --output part2-emane/configs/tdma-schedule.xml

# 3. Create Network Namespaces, TAP interfaces, and launch EMANE
sudo bash part2-emane/scripts/launch_emane.sh 16 part2-emane/configs/tdma-schedule.xml

# 4. Inject TDMA Schedule via EMANE Event Service
emaneevent-tdmaschedule part2-emane/configs/tdma-schedule.xml -i lo

# 5. Verify active schedule table via emanesh
emanesh localhost get table 1 mac scheduler.ScheduleInfoTable

# 6. Test isolated namespace traffic (e.g. Node 5 -> Node 6)
sudo ip netns exec node-6 iperf3 -s -D
sudo ip netns exec node-5 iperf3 -c 10.0.0.6 -u -b 1M -t 10

# 7. Cleanup
sudo bash part2-emane/scripts/cleanup.sh
```
