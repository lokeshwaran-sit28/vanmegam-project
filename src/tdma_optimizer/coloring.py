"""
coloring.py
-----------
Implements the **DSATUR heuristic** for Distance-2 Graph Coloring.

Background
~~~~~~~~~~
Assigning TDMA slots is equivalent to coloring the conflict graph C such
that no two adjacent (conflicting) nodes share the same color (slot).
Finding the minimum number of colors is the **Graph Coloring Problem**,
which is NP-hard in general.  For our use case we apply the **DSATUR**
(Degree of Saturation) heuristic, which consistently produces compact
colorings while remaining fast and entirely deterministic.

DSATUR Algorithm (Brélaz 1979)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DSATUR stands for "Degree of SATURation".  The saturation degree of an
uncolored node is the number of *distinct* colors already assigned to its
conflict neighbors.

At each step:
  1. Select the uncolored node with the **highest saturation degree**.
  2. Break ties by choosing the node with the **highest conflict degree**
     (total number of conflict-graph neighbours, colored or not).
  3. Break remaining ties by **lexicographic node name** for determinism.
  4. Assign that node the **smallest non-negative integer color** not already
     used by any of its conflict neighbors.
  5. Repeat until every node is colored.

Why DSATUR?
~~~~~~~~~~~
* It prioritizes "most constrained" nodes first – nodes that are hard to
  fit in remaining slots are handled early.
* It naturally supports **spatial reuse**: disconnected nodes in C receive
  the same color automatically.
* Deterministic tie-breaking guarantees reproducible output across runs.
* It is simple enough to implement from scratch and explain in an interview.
* It is NOT guaranteed to produce the globally optimal (minimum) coloring,
  but it typically performs well in practice.

Complexity
~~~~~~~~~~
O(N² × Δ) where Δ is the maximum degree of C.  For small N this is fine.
"""

from __future__ import annotations

from typing import Dict, Set

import networkx as nx


def dsatur_coloring(C: nx.Graph) -> Dict[str, int]:
    """
    Apply the DSATUR heuristic to the conflict graph C and return a
    node → slot (color) mapping.

    Parameters
    ----------
    C : nx.Graph
        Undirected conflict graph where nodes are radio-node names and
        edges represent TDMA-slot conflicts.

    Returns
    -------
    dict[str, int]
        Maps every node name to a non-negative integer slot.
        Slot numbers start from 0.

    Notes
    -----
    The result is deterministic because all tie-breaking uses sorted node
    names (lexicographic order).  Running the function twice on the same
    input will always produce identical output.
    """
    nodes = list(C.nodes())

    # Mapping: node → assigned color (slot).  Starts empty.
    coloring: Dict[str, int] = {}

    # For each node, track which colors are already used by its neighbours.
    # This is the "saturation" set.
    neighbor_colors: Dict[str, Set[int]] = {node: set() for node in nodes}

    # Pre-compute conflict degree (number of neighbors in C) for every node.
    conflict_degree: Dict[str, int] = {node: C.degree(node) for node in nodes}

    uncolored: Set[str] = set(nodes)

    while uncolored:
        # ---------------------------------------------------------------
        # Select the next node to color using DSATUR priority:
        #   Primary   – highest saturation degree (len of neighbor_colors).
        #   Secondary – highest conflict degree.
        #   Tertiary  – lexicographically smallest name (determinism).
        # ---------------------------------------------------------------
        chosen = min(
            uncolored,
            key=lambda n: (
                -len(neighbor_colors[n]),   # negate → highest saturation first
                -conflict_degree[n],         # negate → highest degree first
                n,                           # lexicographic (ascending)
            ),
        )

        # ---------------------------------------------------------------
        # Assign the smallest color not used by any conflict neighbor.
        # ---------------------------------------------------------------
        forbidden: Set[int] = neighbor_colors[chosen]
        slot = 0
        while slot in forbidden:
            slot += 1

        coloring[chosen] = slot
        uncolored.remove(chosen)

        # ---------------------------------------------------------------
        # Update the saturation sets of the newly-colored node's neighbors.
        # ---------------------------------------------------------------
        for neighbor in C.neighbors(chosen):
            if neighbor in uncolored:
                neighbor_colors[neighbor].add(slot)

    return coloring


def normalize_colors(coloring: Dict[str, int]) -> Dict[str, int]:
    """
    Remap slot numbers so they form a contiguous range [0, k-1].

    After the optional improvement pass, some slot numbers may become
    unused.  This function renumbers slots in ascending order of first
    appearance (sorted by slot number) so the output is clean.

    Example
    ~~~~~~~
    Input : {A: 0, B: 2, C: 0}   (slot 1 unused)
    Output: {A: 0, B: 1, C: 0}

    Parameters
    ----------
    coloring : dict[str, int]
        Node → slot mapping (may have gaps).

    Returns
    -------
    dict[str, int]
        Node → slot mapping with contiguous slot numbers.
    """
    # Collect unique used slots in sorted order.
    used_slots = sorted(set(coloring.values()))

    # Build a remapping table: old_slot → new_slot.
    remap: Dict[int, int] = {old: new for new, old in enumerate(used_slots)}

    return {node: remap[slot] for node, slot in coloring.items()}
