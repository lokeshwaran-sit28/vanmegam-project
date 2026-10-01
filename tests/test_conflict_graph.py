"""
test_conflict_graph.py
-----------------------
Unit tests for the distance-2 conflict graph construction.

Key invariants verified:
  - Distance-1 edges always produce conflict edges.
  - Distance-2 paths (hidden terminal) produce conflict edges.
  - Distance > 2 nodes have NO conflict edge (spatial reuse allowed).
  - Isolated nodes receive no conflict edges.
  - The conflict graph contains every node from the communication graph.
"""

from __future__ import annotations

import networkx as nx
import pytest

from tdma_optimizer.conflict_graph import build_distance_two_conflict_graph
from tdma_optimizer.topology import build_communication_graph, parse_coordinates


class TestConflictGraphLineNetwork:
    """
    Three-node line topology: A ── B ── C
    
    In G:  A-B, B-C  (A-C distance = 2)
    In C:  A-B, B-C, A-C  (all three must have different slots)
    """

    def test_all_pairs_conflict_in_line(self, line_coords):
        G = build_communication_graph(line_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        # Direct neighbours
        assert C.has_edge("A", "B"), "A-B are direct neighbours, must conflict"
        assert C.has_edge("B", "C"), "B-C are direct neighbours, must conflict"
        # Hidden terminal: A and C are 2 hops apart
        assert C.has_edge("A", "C"), "A-C are 2 hops apart (hidden terminal), must conflict"

    def test_line_conflict_graph_has_three_edges(self, line_coords):
        G = build_communication_graph(line_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        assert C.number_of_edges() == 3

    def test_all_nodes_present_in_conflict_graph(self, line_coords):
        G = build_communication_graph(line_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        for node in ["A", "B", "C"]:
            assert node in C.nodes()


class TestConflictGraphIsolatedNodes:
    """
    Two completely isolated nodes must NOT have a conflict edge – they can
    share the same TDMA slot (spatial reuse).
    """

    def test_isolated_pair_no_conflict(self, isolated_coords):
        """A and B are 1000 m apart (> 500 m range): no comm edge, no conflict edge."""
        G = build_communication_graph(isolated_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        assert not C.has_edge("A", "B"), "Isolated nodes must NOT conflict"
        assert C.number_of_edges() == 0

    def test_isolated_nodes_still_in_conflict_graph(self, isolated_coords):
        G = build_communication_graph(isolated_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        assert "A" in C.nodes()
        assert "B" in C.nodes()


class TestConflictGraphTriangle:
    """
    Triangle topology: A, B, C all within 500 m of each other.
    Every pair is distance 1 → every pair conflicts.
    Requires 3 colors (chromatic number = 3).
    """

    def test_triangle_all_pairs_conflict(self, triangle_coords):
        G = build_communication_graph(triangle_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        assert C.has_edge("A", "B")
        assert C.has_edge("B", "C")
        assert C.has_edge("A", "C")

    def test_triangle_edge_count(self, triangle_coords):
        G = build_communication_graph(triangle_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        assert C.number_of_edges() == 3


class TestConflictGraphSpatialReuse:
    """
    Four-node chain: A ── B ── C ── D (each 300 m apart)

    A-B: distance 1 → conflict
    B-C: distance 1 → conflict
    C-D: distance 1 → conflict
    A-C: distance 2 → conflict
    B-D: distance 2 → conflict
    A-D: distance 3 → NO conflict → spatial reuse possible
    """

    def setup_method(self):
        raw = {
            "A": [0.0, 0.0],
            "B": [300.0, 0.0],
            "C": [600.0, 0.0],
            "D": [900.0, 0.0],
        }
        nodes = parse_coordinates(raw)
        G = build_communication_graph(nodes, radio_range=500.0)
        self.C = build_distance_two_conflict_graph(G)

    def test_direct_edges_conflict(self):
        assert self.C.has_edge("A", "B")
        assert self.C.has_edge("B", "C")
        assert self.C.has_edge("C", "D")

    def test_two_hop_edges_conflict(self):
        assert self.C.has_edge("A", "C")
        assert self.C.has_edge("B", "D")

    def test_three_hop_no_conflict(self):
        assert not self.C.has_edge("A", "D"), (
            "A and D are 3 hops apart; they must NOT conflict (spatial reuse)"
        )


class TestConflictGraphNodesPreserved:
    """Every node from G must appear in C, even if it has no conflict edges."""

    def test_single_isolated_node_preserved(self):
        nodes = parse_coordinates({"Solo": [0, 0]})
        G = build_communication_graph(nodes, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        assert "Solo" in C.nodes()
        assert C.number_of_edges() == 0

    def test_node_count_preserved(self, nodes16_coords):
        G = build_communication_graph(nodes16_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        assert C.number_of_nodes() == 16

    def test_no_self_loops(self, nodes16_coords):
        G = build_communication_graph(nodes16_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        for node in C.nodes():
            assert not C.has_edge(node, node), f"Self-loop found on {node}"
