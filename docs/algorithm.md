# TDMA Schedule Planner and Optimizer – Algorithm Design

## 1. Communication Graph (G)

Each radio node is a vertex.  An edge (u, v) exists if and only if
`Euclidean_distance(u, v) ≤ radio_range`.  Isolated nodes (no
reachable neighbours) are still included as isolated vertices.

**Why Euclidean distance?**  
The problem states that radios have a fixed omnidirectional range.
Physical distance determines whether two radios can hear each other.

## 2. Distance-2 Conflict Graph (C)

Two nodes u and v must receive different TDMA slots if either:

| Condition | Reason |
|-----------|--------|
| `d_G(u,v) == 1` (direct link) | If both transmit simultaneously, each receiver hears a collision |
| `d_G(u,v) == 2` (hidden terminal) | Both reach a common intermediate node B; simultaneous transmission corrupts B's reception |

Nodes at distance > 2 are invisible to each other's interference and
**may share a slot** (spatial reuse).

The conflict graph C has an edge (u, v) iff `shortest_path_G(u,v) ≤ 2`.

Implementation uses `networkx.single_source_shortest_path_length`
with `cutoff=2` for efficiency – O(N × (N + E)).

## 3. DSATUR Heuristic

**Greedy graph colouring with saturation-degree priority.**

1. Start: all nodes uncoloured; each node's saturation degree = 0.  
2. Loop until all nodes are coloured:  
   a. Select the uncoloured node with highest **saturation degree**  
      (= number of distinct colours used by its already-coloured conflict neighbours).  
   b. Break ties by highest **conflict degree** (total neighbours in C).  
   c. Break remaining ties by **lexicographic node name** (determinism).  
   d. Assign the **smallest non-negative integer** not used by any conflict neighbour.  
   e. Update the saturation sets of newly-coloured node's neighbours.

**Why DSATUR?**  
- Prioritises the most constrained nodes first → compact colourings.  
- Simple to implement, understand, and explain.  
- Deterministic (important for reproducibility and testing).  
- NP-hard to find the absolute minimum; DSATUR is an accepted industry heuristic.

## 4. Local Improvement Pass

After DSATUR:

1. Sort nodes lexicographically (deterministic order).  
2. For each node, try reassigning it to any slot number **lower** than its current one, provided no conflict neighbour uses that slot.  
3. Repeat until a full pass produces zero moves.  
4. Normalize (compact) slot numbers so they are contiguous [0, k-1].

This is a greedy local search – no backtracking, no guarantee of global optimum.

## 5. Complexity Summary

| Step | Complexity |
|------|-----------|
| Communication graph G | O(N²) distance evaluations |
| Conflict graph C | O(N × (N + E_G)) via BFS |
| DSATUR coloring | O(N² × Δ) where Δ = max degree of C |
| Local improvement | O(passes × N × Δ), passes ≤ initial slot count |
| Validation | O(E_C) |

For 16 nodes this runs in milliseconds.  For hundreds of nodes it
remains well within practical limits.

## 6. Correctness Guarantee

**Every** edge (u, v) in C is checked by the independent validator.
If `slot[u] == slot[v]` for any such edge, the program exits with
code 1 and reports the violating pair.  The coloring and validation
share no code paths, ensuring genuine independence.
