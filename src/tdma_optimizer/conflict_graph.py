"""
conflict_graph.py
-----------------
Builds the Distance-2 Conflict Graph C from the communication graph G.

Why Distance-2 Coloring?
~~~~~~~~~~~~~~~~~~~~~~~~
In a TDMA network, two nodes must NOT share the same time slot if they
would cause interference.  Interference occurs in two scenarios:

1. **Direct-link interference** (distance 1 in G):
   Node A and node B can hear each other.  If both transmit in the
   same slot they collide at each other's receiver.

2. **Hidden-terminal interference** (distance 2 in G):
   Node A and node C cannot hear each other directly, but both can
   reach node B.  If A and C transmit in the same slot, the signals
   arrive simultaneously at B and corrupt the frame B is trying to
   receive.  This is the classic "hidden terminal" problem.

   Example:
       A ── B ── C
   A and C are two hops apart in G.  They must use different slots
   to avoid corrupting B's reception.

Distance > 2:
   Nodes more than two hops apart do not cause interference at any
   common intermediate node.  They MAY share a slot (spatial reuse).

The conflict graph C therefore contains an edge (u, v) for every pair
where shortest_path_length(G, u, v) ≤ 2.

This definition is based strictly on **graph topology** (hop distance),
NOT on raw Euclidean distance.  Two nodes that are physically far apart
but happen to share a common neighbour still conflict.

Complexity
~~~~~~~~~~
For N nodes and E edges in G:
  * BFS/SSSP from every node: O(N × (N + E))
  * Total: O(N² + N·E)

For small networks (N ≤ hundreds) this is completely acceptable.
"""

from __future__ import annotations

from typing import Dict, Tuple

import networkx as nx


def build_distance_two_conflict_graph(G: nx.Graph) -> nx.Graph:
    """
    Construct the **Distance-2 Conflict Graph** C from communication graph G.

    Two nodes u and v have a conflict edge in C if and only if:
        shortest_path_length(G, u, v) ∈ {1, 2}

    Isolated nodes (no neighbours in G) have no conflict with any other node
    unless another isolated cluster exists ≤ 2 hops away; because they are
    isolated their only reachable set is themselves, so they get no conflict
    edges and can freely share a slot with other similarly isolated nodes.

    Parameters
    ----------
    G : nx.Graph
        The undirected communication graph produced by :func:`build_communication_graph`.

    Returns
    -------
    nx.Graph
        Undirected conflict graph C.  Every node from G is present; edges
        represent pairs that must receive different TDMA slots.

    Notes
    -----
    NetworkX's ``single_source_shortest_path_length`` performs a BFS from a
    given source and returns a dictionary of {node: hop_distance}.  We cap the
    search at depth 2 (``cutoff=2``) for efficiency.
    """
    C: nx.Graph = nx.Graph()

    # Preserve all nodes (including isolated ones).
    C.add_nodes_from(G.nodes())

    nodes = list(G.nodes())

    for source in nodes:
        # BFS from `source`, only up to hop distance 2.
        # Returns {node: distance} for all reachable nodes within 2 hops.
        reachable: Dict[str, int] = nx.single_source_shortest_path_length(
            G, source, cutoff=2
        )

        for target, dist in reachable.items():
            if target == source:
                continue  # no self-loops
            if dist <= 2:
                # Add the conflict edge (undirected; NetworkX ignores duplicates).
                C.add_edge(source, target)

    return C


def conflict_summary(G: nx.Graph, C: nx.Graph) -> Tuple[int, int]:
    """
    Return (comm_edge_count, conflict_edge_count) for reporting purposes.

    Parameters
    ----------
    G : nx.Graph
        Communication graph.
    C : nx.Graph
        Conflict graph.

    Returns
    -------
    tuple[int, int]
        (|E(G)|, |E(C)|)
    """
    return G.number_of_edges(), C.number_of_edges()
