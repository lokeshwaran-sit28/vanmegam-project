"""
optimizer.py
------------
Optional local-improvement pass that tries to reduce the total number of
TDMA slots after the initial DSATUR coloring.

Strategy
~~~~~~~~
After DSATUR produces a valid (conflict-free) coloring, some nodes may be
assigned to higher-numbered slots when a lower-numbered slot is feasible.
This greedy post-processing pass iterates over all nodes in deterministic
order and tries to move each node to the smallest possible slot ≤ its
current slot without creating any new conflict.

The process repeats until a full pass produces no improvement.

This is deliberately simple – it is a **greedy local search** with no
backtracking.  It does not guarantee the global minimum.

Complexity
~~~~~~~~~~
Each pass is O(N × Δ) where Δ is the maximum degree of the conflict graph.
The number of passes is bounded by the initial number of slots.
"""

from __future__ import annotations

from typing import Dict

import networkx as nx

from .coloring import normalize_colors


def improve_coloring(
    C: nx.Graph,
    coloring: Dict[str, int],
) -> Dict[str, int]:
    """
    Attempt to reduce the total number of slots via greedy local improvement.

    The algorithm:
    1. Process nodes in **deterministic** (lexicographic) order each pass.
    2. For each node, determine the set of slots used by its conflict neighbors.
    3. Try to reassign the node to the smallest slot in [0, current_slot - 1]
       that is not used by any conflict neighbor.
    4. Accept the move if a better (lower-numbered) slot is found.
    5. Repeat passes until no improvement is made in a full pass.
    6. Normalize (compact) the slot numbers before returning.

    Parameters
    ----------
    C : nx.Graph
        Conflict graph (must not be modified in place here).
    coloring : dict[str, int]
        Initial node → slot mapping produced by DSATUR.

    Returns
    -------
    dict[str, int]
        Improved node → slot mapping with contiguous slot numbers.
    """
    # Work on a mutable copy so we do not mutate the caller's dict.
    current: Dict[str, int] = dict(coloring)

    # Sort nodes deterministically for reproducible results.
    node_order = sorted(C.nodes())

    improved = True
    while improved:
        improved = False
        for node in node_order:
            # Collect all slots used by this node's conflict neighbours.
            neighbor_slots = {current[nb] for nb in C.neighbors(node)}

            current_slot = current[node]

            # Try every slot below the current one.
            for candidate in range(current_slot):
                if candidate not in neighbor_slots:
                    # This slot is conflict-free and lower – accept the move.
                    current[node] = candidate
                    improved = True
                    break  # Take the smallest feasible improvement.

    return normalize_colors(current)
