# Technical Presentation & Interview Outline
## TDMA Schedule Planner and Optimizer for Wireless Networks

---

### Slide 1 – Title Slide
**TDMA Schedule Planner and Optimizer for Wireless Networks**  
*Wireless Protocol Development Internship Assignment*

> **Speaker Notes**:  
> "Good morning/afternoon. Today I will present my implementation of a collision-free TDMA Schedule Planner and Optimizer for wireless networks. The project consists of two core parts: Part 1 implements a Python-based graph-coloring optimizer using the DSATUR heuristic and a greedy local search pass. Part 2 bridges our calculated schedule with the EMANE network emulator using official XML event specifications and Linux network namespace isolation."

---

### Slide 2 – Problem Statement & Interference Constraints
- **Wireless Channel Sharing**: Multiple radio nodes sharing a single RF channel using Time Division Multiple Access (TDMA).
- **Interference Types**:
  1. **Direct (1-hop) Interference**: Adjacent nodes within transmission range $R_{\text{radio}}$ cannot transmit simultaneously.
  2. **Hidden Terminal (2-hop) Interference**: Nodes that share a common 1-hop neighbor cannot transmit simultaneously, as their signals collide at the intermediate receiver.

> **Speaker Notes**:  
> "Why is distance-2 coloring required? In a wireless ad-hoc network, ordinary graph coloring only prevents adjacent 1-hop neighbors from sharing a slot. However, if two nodes $u$ and $w$ are out of range of each other but both within range of node $v$, simultaneous transmission causes a collision at $v$'s receiver. This is the classic hidden terminal problem. To guarantee zero collisions at all receivers, any pair of nodes separated by 1 or 2 hops must be assigned different slots."

---

### Slide 3 – Mathematical Formulation & NP-Hardness
- **Communication Graph ($G = (V, E_G)$)**: Edge $(u, v) \in E_G \iff \text{dist}(u, v) \le R_{\text{radio}}$.
- **Conflict Graph ($C = (V, E_C)$)**: Edge $(u, w) \in E_C \iff \text{dist}_G(u, w) \le 2$.
- **Complexity**: Distance-2 Graph Coloring is **NP-hard**.

> **Speaker Notes**:  
> "Why is ordinary graph coloring insufficient, and why is this problem NP-hard? Ordinary graph coloring solves 1-hop conflicts on $G$. Distance-2 coloring solves 1-hop and 2-hop conflicts by constructing a new conflict graph $C$. Finding the exact minimum chromatic number $\chi(C)$ is NP-hard because it reduces directly to the classic vertex coloring problem (one of Karp's 21 NP-complete problems). Since computing optimal chromatic numbers for arbitrary graphs is computationally intractable for large networks, we chose a dynamic heuristic approach."

---

### Slide 4 – Schedule Algorithm: DSATUR Heuristic
- **Dynamic Saturation Degree ($\text{sat}(v)$)**: Number of distinct colors used by already-colored neighbors in $C$.
- **Algorithm Flow**:
  1. Select uncolored node with highest $\text{sat}(v)$ (tie-breaker: static degree in $C$).
  2. Assign smallest feasible slot index $s \in \{0, 1, 2, \dots\}$.
  3. Dynamically update saturation degrees of uncolored neighbors.
  4. Repeat until all nodes are colored.

> **Speaker Notes**:  
> "How does DSATUR work? Unlike static ordering algorithms like Welsh-Powell which sort nodes once before coloring, DSATUR (Degree of Saturation) dynamically tracks how constrained each node becomes. At every step, it colors the node that has the fewest remaining choices—the node with the highest saturation degree. This greedy choice prevents color bottlenecks later in the coloring process and consistently achieves near-optimal slot counts."

---

### Slide 5 – Post-Processing: Greedy Local Search & Spatial Reuse
- **Spatial Reuse**: Non-conflicting nodes ($\text{dist}_G > 2$) share the same time slot.
- **Local Search Pass**: Iterates over nodes in deterministic order, re-assigning each node to the smallest slot $s' < s_{\text{current}}$ that is conflict-free in $C$.
- **Compaction**: Normalizes slot indices to eliminate empty slot gaps.

> **Speaker Notes**:  
> "How does spatial reuse work in our pipeline? When two nodes are separated by 3 or more hops in $G$, they have no edge in $C$. Our algorithm allows them to share a slot safely. After DSATUR generates an initial valid coloring, our greedy local search pass iterates through the nodes and attempts to push nodes into lower-numbered slots. In our 16-node grid test, this pass successfully packs 16 nodes into just 9 time slots, achieving significant spatial reuse."

---

### Slide 6 – Part 1 Results (16-Node Grid Dataset)
- **Dataset**: `examples/nodes16.json` ($4 \times 4$ grid, 500m range).
- **Graph Metrics**: 42 Communication Links, 90 Conflict Edges.
- **Optimized Schedule**: 9 unique slots.
- **Validation**: Independent validator inspected all 90 conflict edges $\to$ **0 Conflicts Detected**.

> **Speaker Notes**:  
> "Here are the concrete Part 1 results. For a 16-node grid with 42 communication links and 90 conflict edges, our optimizer produced a 9-slot frame. Our independent validator verified all 90 conflict edges and confirmed 0 conflicts. Notice how Slot 8 is shared by Nodes 1, 10, 13, and 16—these nodes are spatially separated by 3+ hops, demonstrating working spatial reuse."

---

### Slide 7 – Part 2 Architecture & EMANE Schedule Adapter
- **EMANE (Extendable Mobile Ad-hoc Network Emulator)**: Real-time MAC/PHY emulation framework.
- **Adapter (`schedule_adapter.py`)**: Converts `ScheduleResult` into official `<emane-tdma-schedule>` XML syntax.
- **Timing Configuration**: $1\text{ ms}$ slot duration (`slotduration="1000"` $\mu\text{s}$).

> **Speaker Notes**:  
> "How does the EMANE adapter work? The schedule adapter takes the Part 1 schedule output and translates logical node names into 1-based EMANE NEM IDs (`Node_01` $\to$ `NEM 1`). It then generates an official EMANE TDMA Schedule XML document conforming to `<emane-tdma-schedule>`. It configures a 1 ms slot duration using `slotduration="1000"` microseconds and groups allocated NEM IDs into the `nodes` attribute of each `<slot>` tag."

---

### Slide 8 – EMANE Linux Network Namespace Architecture
- **Host Routing Bypass Issue**: Placing TAP devices in root namespace causes Linux kernel to route IP packets locally via loopback (`lo`), bypassing EMANE.
- **Solution**: Network Namespace isolation (`node-1` .. `node-16`).
- **Topology**: Each TAP device `emane{i}` is placed inside `node-{i}` namespace, forcing packets through EMANE.

> **Speaker Notes**:  
> "Why are Linux network namespaces required for EMANE testing? If all TAP interfaces are placed in the main host namespace, sending traffic between 10.0.0.5 and 10.0.0.6 causes the Linux kernel to route packets internally via loopback, bypassing the TAP devices and EMANE entirely. By moving each TAP device into an isolated Linux network namespace (`node-1` .. `node-16`), each node gets its own network stack, forcing traffic through the TAP interface into EMANE's MAC/PHY layer."

---

### Slide 9 – EMANE Event Service & Table Inspection
- **Event Injection**: `emaneevent-tdmaschedule part2-emane/configs/tdma-schedule.xml -i lo`
- **Mechanism**: Serializes XML schedule into a `TDMAScheduleEvent` broadcast over multicast.
- **Inspection Command**: `emanesh localhost get table 1 mac scheduler.ScheduleInfoTable`

> **Speaker Notes**:  
> "How is the schedule delivered to EMANE at runtime? EMANE uses an Event Service daemon (`emaneeventservice`). The utility `emaneevent-tdmaschedule` parses our XML schedule and broadcasts a `TDMAScheduleEvent` over loopback multicast. Active EMANE NEM instances receive the event and apply the new schedule at the next multiframe boundary. We can verify active slot tables using `emanesh`."

---

### Slide 10 – Software Quality & Test Suite Verification
- **Automated Tests**: 113 / 113 tests passed (`pytest tests/`).
- **Execution Speed**: 0.29 seconds.
- **Coverage**: Topology, Conflict Graph, DSATUR, Local Search, Validator, Matrix, and EMANE Adapter.

> **Speaker Notes**:  
> "Our codebase is thoroughly tested. The automated test suite consists of 113 unit and end-to-end tests, all passing cleanly in under 0.3 seconds. This includes 103 tests for Part 1 and 10 tests for Part 2 verifying XML schema generation, NEM mapping, and input validation."

---

### Slide 11 – Testing Status & Implementation Transparency
- **Implemented & Unit-Tested**:
  - Part 1 Optimizer Core & Validator (103 tests)
  - Part 2 Schedule Adapter & XML Generator (10 tests)
  - Full EMANE XML configuration set (`tdma-schedule.xml`, `nem.xml`, `platform.xml`, `transvirtual.xml`)
- **Designed for Linux (Not Runtime-Tested)**:
  - Live EMANE daemon execution and real-time packet delivery were **not** performed because the host development environment is Windows.
  - Linux deployment scripts (`launch_emane.sh`) are design-prepared for Ubuntu 22.04 LTS.

> **Speaker Notes**:  
> "To be completely transparent about what was actually tested: All Python algorithms, schedule generation, XML serialization, and structural validation were fully executed and unit-tested on our host system. However, live EMANE daemon execution and real packet delivery were not performed because our development environment is Windows. All Linux networking scripts and namespace configurations are fully prepared and defensible for Ubuntu 22.04 deployment."

---

### Slide 12 – Conclusion & Q&A
- **Summary**:
  - Collision-free spatial reuse TDMA schedule optimization.
  - Formally verified Distance-2 conflict graph model.
  - Official EMANE TDMA XML event integration.
  - 113 / 113 automated unit tests passing.
- **Open for Questions**.

> **Speaker Notes**:  
> "Thank you for your time. I am now ready to take any questions from the panel regarding TDMA protocol design, graph algorithms, NetworkX implementation, or EMANE network emulation."
