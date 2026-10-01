"""
test_coloring.py
----------------
Unit tests for the DSATUR coloring algorithm and color normalization.

Tests verify:
  - No two adjacent nodes in the conflict graph share a slot.
  - The number of colors is sensible (≥ clique number of the graph).
  - Isolated nodes can share a slot.
  - The coloring is deterministic (same input → same output).
  - normalize_colors produces contiguous slot numbers.
  - Triangle requires exactly 3 slots.
  - Line topology requires exactly 3 slots (A, B, C all conflict).
  - Two isolated nodes share slot 0.
"""

from __future__ import annotations

import pytest

from tdma_optimizer.coloring import dsatur_coloring, normalize_colors
from tdma_optimizer.conflict_graph import build_distance_two_conflict_graph
from tdma_optimizer.topology import build_communication_graph, parse_coordinates


def _run_coloring(raw_coords: dict, radio_range: float = 500.0):
    """Helper: full pipeline → (C, coloring)."""
    nodes = parse_coordinates(raw_coords)
    G = build_communication_graph(nodes, radio_range=radio_range)
    C = build_distance_two_conflict_graph(G)
    coloring = dsatur_coloring(C)
    coloring = normalize_colors(coloring)
    return C, coloring


def _assert_conflict_free(C, coloring):
    """Assert no two adjacent nodes in C share a slot."""
    for u, v in C.edges():
        assert coloring[u] != coloring[v], (
            f"Conflict detected: {u}(slot={coloring[u]}) and "
            f"{v}(slot={coloring[v]}) share the same slot!"
        )


class TestColoringCorrectness:
    """Basic correctness: every coloring must be conflict-free."""

    def test_line_network_conflict_free(self, line_coords):
        G = build_communication_graph(line_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        coloring = normalize_colors(dsatur_coloring(C))
        _assert_conflict_free(C, coloring)

    def test_triangle_conflict_free(self, triangle_coords):
        G = build_communication_graph(triangle_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        coloring = normalize_colors(dsatur_coloring(C))
        _assert_conflict_free(C, coloring)

    def test_isolated_pair_conflict_free(self, isolated_coords):
        G = build_communication_graph(isolated_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        coloring = normalize_colors(dsatur_coloring(C))
        _assert_conflict_free(C, coloring)

    def test_16_node_grid_conflict_free(self, nodes16_coords):
        G = build_communication_graph(nodes16_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        coloring = normalize_colors(dsatur_coloring(C))
        _assert_conflict_free(C, coloring)

    def test_every_node_receives_exactly_one_slot(self, nodes16_coords):
        G = build_communication_graph(nodes16_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        coloring = normalize_colors(dsatur_coloring(C))
        assert set(coloring.keys()) == set(C.nodes())


class TestColoringSlotCounts:
    """Verify minimum slot requirements for known topologies."""

    def test_line_requires_three_slots(self, line_coords):
        """A, B, C all mutually conflict in the conflict graph → 3 slots."""
        G = build_communication_graph(line_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        coloring = normalize_colors(dsatur_coloring(C))
        assert max(coloring.values()) + 1 == 3, (
            "Three-node line network requires exactly 3 slots"
        )

    def test_triangle_requires_three_slots(self, triangle_coords):
        """Triangle clique → chromatic number = 3."""
        G = build_communication_graph(triangle_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        coloring = normalize_colors(dsatur_coloring(C))
        assert max(coloring.values()) + 1 == 3

    def test_isolated_pair_uses_one_slot(self, isolated_coords):
        """Two disconnected nodes share one slot (spatial reuse)."""
        G = build_communication_graph(isolated_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        coloring = normalize_colors(dsatur_coloring(C))
        assert max(coloring.values()) + 1 == 1, (
            "Two isolated nodes should share slot 0"
        )
        assert coloring["A"] == coloring["B"] == 0

    def test_single_node_uses_slot_zero(self):
        C, coloring = _run_coloring({"X": [0, 0]})
        assert coloring["X"] == 0


class TestNormalizeColors:
    """Verify normalize_colors compacts gaps in slot numbering."""

    def test_no_gap_unchanged(self):
        coloring = {"A": 0, "B": 1, "C": 2}
        result = normalize_colors(coloring)
        assert result == {"A": 0, "B": 1, "C": 2}

    def test_gap_compacted(self):
        """Slots [0, 2, 4] should become [0, 1, 2]."""
        coloring = {"A": 0, "B": 2, "C": 4}
        result = normalize_colors(coloring)
        assert result["A"] == 0
        assert result["B"] == 1
        assert result["C"] == 2

    def test_all_same_slot(self):
        coloring = {"A": 5, "B": 5, "C": 5}
        result = normalize_colors(coloring)
        assert all(v == 0 for v in result.values())

    def test_contiguous_after_normalization(self):
        coloring = {"X": 0, "Y": 3, "Z": 7}
        result = normalize_colors(coloring)
        values = sorted(set(result.values()))
        assert values == list(range(len(values)))


class TestColoringDeterminism:
    """Same input → same output, always."""

    def test_deterministic_on_16_node_grid(self, nodes16_coords):
        G = build_communication_graph(nodes16_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        c1 = normalize_colors(dsatur_coloring(C))
        c2 = normalize_colors(dsatur_coloring(C))
        assert c1 == c2

    def test_deterministic_on_line(self, line_coords):
        G = build_communication_graph(line_coords, radio_range=500.0)
        C = build_distance_two_conflict_graph(G)
        c1 = normalize_colors(dsatur_coloring(C))
        c2 = normalize_colors(dsatur_coloring(C))
        assert c1 == c2


class TestSpatialReuse:
    """
    Four-node chain: A──B──C──D (300 m apart, range 500 m).
    A and D are 3 hops apart: they do NOT conflict and may share a slot.
    """

    def test_a_and_d_can_share_slot(self):
        raw = {"A": [0, 0], "B": [300, 0], "C": [600, 0], "D": [900, 0]}
        C, coloring = _run_coloring(raw)
        _assert_conflict_free(C, coloring)
        # A and D are 3 hops apart → no conflict edge → they may (should) share a slot.
        # DSATUR should naturally assign the same slot to A and D.
        assert coloring["A"] == coloring["D"], (
            "A and D are 3 hops apart and should share a slot (spatial reuse)"
        )
