# Technical Interview Q&A Guide
## TDMA Schedule Planner and Optimizer & EMANE Integration

This document contains 20 core technical interview questions with concise, defensible answers designed for a **Wireless Protocol Development** technical interview panel.

---

### Part A: Wireless Networking & TDMA Theory

#### Q1. What is TDMA, and why is it used in wireless networks?
**Answer**:  
Time Division Multiple Access (TDMA) is a channel access method that divides a shared physical radio frequency channel into distinct, non-overlapping time slots. Each radio node is assigned specific slots in a repeating time frame during which it is permitted to transmit. TDMA eliminates contention-based packet collisions (unlike CSMA/CA), provides deterministic latency, and guarantees Quality of Service (QoS) in tactical, ad-hoc, and industrial wireless networks.

#### Q2. What is the difference between Direct (Distance-1) Interference and Hidden Terminal (Distance-2) Interference?
**Answer**:  
- **Direct Interference (Distance-1)**: Occurs when two nodes within mutual transmission range transmit simultaneously, causing collision at each other's receiver.
- **Hidden Terminal Interference (Distance-2)**: Occurs when two nodes ($u$ and $w$) are out of range of each other but both within range of an intermediate node ($v$). If $u$ and $w$ transmit simultaneously, their signals collide at $v$'s receiver. Therefore, nodes sharing a common 1-hop neighbor must not use the same slot.

#### Q3. What is Spatial Reuse in TDMA networks?
**Answer**:  
Spatial reuse is the technique of allowing two or more geographically separated radio nodes to transmit in the exact same time slot without interference. If the distance between nodes $u$ and $v$ is greater than 2 hops in the communication graph (i.e., they share no common receiver), they can safely reuse a time slot, increasing overall network throughput.

---

### Part B: Graph Formulations & Algorithms

#### Q4. Why is ordinary graph coloring insufficient for TDMA scheduling?
**Answer**:  
Ordinary graph coloring enforces that no adjacent vertices share the same color (Distance-1 constraint). However, in wireless networks, nodes that are 2 hops apart can collide at a shared neighbor (hidden terminal problem). Ordinary graph coloring on the communication graph $G$ ignores 2-hop conflicts. We must construct a **Distance-2 Conflict Graph ($C$)** where an edge is added between any pair of nodes with topological distance $\le 2$ in $G$, and then solve standard vertex coloring on $C$.

#### Q5. Is Distance-2 Graph Coloring NP-Hard? Why?
**Answer**:  
Yes. Vertex coloring on an arbitrary graph is a classic NP-complete decision problem (Karp's 21 NP-complete problems). Constructing a Distance-2 conflict graph $C$ from $G$ takes polynomial time $O(V \cdot \Delta^2)$, but finding the minimal chromatic number $\chi(C)$ remains NP-hard. Hence, exact chromatic optimization is intractable for large networks, justifying the use of heuristic algorithms like DSATUR.

#### Q6. How does the DSATUR algorithm work?
**Answer**:  
DSATUR (Degree of Saturation) is a dynamic greedy graph coloring heuristic developed by Daniel Brélaz (1979):
1. **Saturation Degree ($\text{sat}(v)$)**: Defined as the number of *distinct* colors used by already-colored neighbors of $v$ in $C$.
2. **Vertex Selection**: At each step, DSATUR selects the uncolored node with the highest saturation degree $\text{sat}(v)$. Ties are broken using the node's static degree in $C$, followed by lexicographic order.
3. **Color Assignment**: The chosen node is assigned the lowest-indexed color (slot) not used by any of its conflict neighbors.
4. **Update**: Saturation degrees of uncolored neighbors are updated dynamically.

#### Q7. Why did you choose DSATUR over Simple Greedy (Sequential) Coloring or Welsh-Powell?
**Answer**:  
Static ordering heuristics like Welsh-Powell order vertices once by static degree before coloring. DSATUR dynamically updates saturation degrees after every node assignment, prioritizing highly constrained nodes that are running out of available colors. DSATUR consistently achieves chromatic numbers close to optimal $\chi(C)$ and outperforms static greedy ordering on spatial wireless graphs.

#### Q8. What does your Local Search / Post-Processing Pass do?
**Answer**:  
After initial DSATUR coloring, some nodes may be assigned higher slot numbers due to greedy choices made early. Our greedy local search pass iterates through all nodes in deterministic order and attempts to move each node to the smallest feasible slot $s' < s_{\text{current}}$ that creates no conflict with its neighbors in $C$. Passes repeat until no further slot reduction occurs, compacting the schedule.

#### Q9. What is the Time and Space Complexity of your Part 1 scheduling pipeline?
**Answer**:  
- **Communication Graph $G$**: $O(N^2)$ distance checks for $N$ nodes.
- **Conflict Graph $C$**: $O(N \cdot \Delta_G^2)$ where $\Delta_G$ is max degree in $G$.
- **DSATUR Coloring**: $O(N^2 \log N)$ maintaining saturation priority queue.
- **Local Search Pass**: $O(K \cdot N \cdot \Delta_C)$ where $K$ is number of passes and $\Delta_C$ is max degree in $C$.
- **Space Complexity**: $O(N + E_C)$ storing NetworkX graphs.

---

### Part C: Code Architecture & Design Tradeoffs

#### Q10. Why did you use NetworkX instead of writing custom graph data structures?
**Answer**:  
NetworkX is a mature, battle-tested Python library providing efficient graph representations (`nx.Graph`) and fast graph traversal primitives like `nx.single_source_shortest_path_length`. Using NetworkX avoids re-inventing basic graph adjacency routines while keeping our custom DSATUR dynamic saturation logic, local search optimizer, and validation code transparent and fully defensible.

#### Q11. How does your Validator (`validator.py`) guarantee schedule correctness?
**Answer**:  
The validator operates independently of the coloring algorithm:
1. It verifies structural properties: every node has a slot, slot numbers are non-negative, and frame length matches matrix dimensions.
2. It iterates over **every edge $(u, v)$ in the conflict graph $C$** and asserts that $\text{slot}(u) \neq \text{slot}(v)$. If any edge endpoints share a slot, it flags a violation and reports the conflicting pair.

#### Q12. How is the Boolean Schedule Matrix constructed and validated?
**Answer**:  
The schedule matrix is a 2D binary array of dimension $\text{Frame Length} \times N$.
Entry $\text{matrix}[s][i] = 1$ if node $i$ is assigned to slot $s$, else $0$. The validator asserts that every column $i$ contains exactly one $1$ (every node has 1 slot) and that for any two nodes $i, j$ sharing a row $s$, edge $(i, j) \notin E_C$.

---

### Part D: Part 2 – EMANE Integration & Linux Networking

#### Q13. What is EMANE and what is its role in wireless network emulation?
**Answer**:  
EMANE (Extendable Mobile Ad-hoc Network Emulator) is an open-source real-time emulation framework developed by Adjacent Link / NRL. It emulates physical (PHY) and MAC layer behavior for wireless networks. In this project, EMANE's TDMA Radio Model (`tdmaeventscheduler`) takes our calculated slot schedule and enforces real-time transmission windowing on emulated radio nodes.

#### Q14. What is an EMANE NEM (Network Emulation Module)?
**Answer**:  
An NEM represents an emulated wireless node stack in EMANE. It encapsulates a MAC layer plugin, a PHY layer plugin, and a Transport plugin (e.g., Virtual Transport connecting to a Linux TAP device). NEMs are identified by numeric integer IDs ($1, 2, 3, \dots$).

#### Q15. How does the EMANE Event Service work for TDMA schedules?
**Answer**:  
EMANE uses an Event Service daemon (`emaneeventservice`) that broadcasts multicast event messages over a control network. The utility `emaneevent-tdmaschedule` parses an XML schedule file (`<emane-tdma-schedule>`), packages it into a `TDMAScheduleEvent` (Event ID 102), and publishes it. Running NEM MAC instances receive the event and update their frame transmission timing at the next multiframe boundary.

#### Q16. What is the official XML schema format for EMANE TDMA schedules?
**Answer**:  
Root element `<emane-tdma-schedule>`, containing:
- `<structure frames="1" slots="S" slotduration="1000" slotoverhead="100" bandwidth="1000000"/>`
- `<multiframe frequency="2350000000" power="0.0" datarate="1000000">`
- `<frame index="0">`
- `<slot index="0" nodes="5 10 13 16"><tx/></slot>`

Nodes allocated to transmit in a slot are specified via the space-separated `nodes` attribute on the `<slot>` element.

#### Q17. Why are Linux Network Namespaces (`ip netns`) required for testing EMANE?
**Answer**:  
If all virtual TAP devices (`emane1` .. `emane16`) are created in the host's root network namespace, sending IP traffic between `10.0.0.5` and `10.0.0.6` causes the Linux kernel to route packets internally via loopback (`lo`), bypassing TAP devices and EMANE entirely. Placing each TAP device in an isolated network namespace (`node-1` .. `node-16`) isolates each node's network stack, forcing traffic through the TAP device and into EMANE's MAC/PHY emulation.

#### Q18. How do you test packet delivery inside Linux Network Namespaces?
**Answer**:  
Using `ip netns exec`:
```bash
# Start iperf3 server in node-6 namespace
sudo ip netns exec node-6 iperf3 -s -D

# Send UDP traffic from node-5 namespace to node-6
sudo ip netns exec node-5 iperf3 -c 10.0.0.6 -u -b 1M -t 10
```
This forces packets out through `emane5`, through EMANE TDMA slot timing, over the emulated channel, and into `emane6`.

---

### Part E: Engineering Honesty & Execution Limitations

#### Q19. Was EMANE runtime simulation actually executed during this project?
**Answer**:  
No. Live EMANE daemon execution and packet transmission were **not** performed because the host development environment is **Windows** (EMANE requires Linux kernel TUN/TAP devices and network namespaces). However, the Python schedule adapter (`schedule_adapter.py`), NEM mapping, XML generation, and structural validation were fully implemented and 100% unit-tested (10 Part 2 tests). All Linux execution scripts (`launch_emane.sh`, `cleanup.sh`) are design-prepared for Ubuntu 22.04 LTS deployment.

#### Q20. What are the key technical limitations or risks of this implementation?
**Answer**:  
1. **Host OS Constraint**: EMANE cannot run natively on Windows without WSL2 or an Ubuntu VM.
2. **Clock Synchronization Jitter**: A 1 ms slot duration ($1000\text{ }\mu\text{s}$) requires high-precision OS timers. Virtualized environments may experience timer jitter.
3. **Static Topology**: The current optimizer calculates a schedule for a static node topology. Mobile networks would require dynamic schedule updates via periodic `TDMAScheduleEvent` broadcasts.
