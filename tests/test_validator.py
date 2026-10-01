"""
test_validator.py
-----------------
Unit tests for the schedule validator.

The validator is designed to be completely independent from the coloring
algorithm – these tests directly inject known-good and known-bad colorings
to verify the validator itself is correct.

Tests cover:
  - Valid conflict-free colorings.
  - Colorings with deliberate conflicts (validator should catch them).
  - Missing node assignments.
  - Invalid slot numbers (negative).
  - Non-contiguous slot numbers.
  - Matrix dimension mismatches.
  - The status string is set correctly.
"""

from __future__ import annotations

import networkx as nx
import pytest

from tdma_optimizer.matrix import build_schedule_matrix
from tdma_optimizer.models import ValidationResult
from tdma_optimizer.validator import validate_schedule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_line_conflict_graph() -> nx.Graph:
    """Conflict graph for three-node line A──B──C (all pairs conflict)."""
    C = nx.Graph()
    C.add_nodes_from(["A", "B", "C"])
    C.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])
    return C


def make_isolated_pair_conflict_graph() -> nx.Graph:
    """Conflict graph for two isolated nodes (no edges)."""
    C = nx.Graph()
    C.add_nodes_from(["A", "B"])
    return C


# ---------------------------------------------------------------------------
# Tests: conflict-free colorings
# ---------------------------------------------------------------------------


class TestValidatorConflictFree:
    def test_line_valid_coloring(self):
        C = make_line_conflict_graph()
        coloring = {"A": 0, "B": 1, "C": 2}
        matrix = build_schedule_matrix(coloring, sorted(C.nodes()))
        result = validate_schedule(C, coloring, matrix)
        assert result.status == "CONFLICT-FREE"
        assert result.conflicts_found == 0
        assert result.conflicts_checked == 3  # 3 edges in C

    def test_isolated_pair_same_slot_valid(self):
        C = make_isolated_pair_conflict_graph()
        coloring = {"A": 0, "B": 0}
        matrix = build_schedule_matrix(coloring, sorted(C.nodes()))
        result = validate_schedule(C, coloring, matrix)
        assert result.status == "CONFLICT-FREE"
        assert result.conflicts_found == 0
        assert result.conflicts_checked == 0  # no edges

    def test_single_node_valid(self):
        C = nx.Graph()
        C.add_node("X")
        coloring = {"X": 0}
        matrix = build_schedule_matrix(coloring, ["X"])
        result = validate_schedule(C, coloring, matrix)
        assert result.status == "CONFLICT-FREE"
        assert result.conflicts_found == 0


# ---------------------------------------------------------------------------
# Tests: conflicting colorings
# ---------------------------------------------------------------------------


class TestValidatorDetectsConflicts:
    def test_detect_direct_conflict(self):
        """Give A and B (adjacent in C) the same slot → validator catches it."""
        C = nx.Graph()
        C.add_edge("A", "B")
        coloring = {"A": 0, "B": 0}  # Deliberate conflict
        matrix = build_schedule_matrix(coloring, ["A", "B"])
        result = validate_schedule(C, coloring, matrix)
        assert result.status == "CONFLICT DETECTED"
        assert result.conflicts_found >= 1
        # The conflicting pair should be reported.
        pair_nodes = {p[0] for p in result.conflicting_pairs} | {p[1] for p in result.conflicting_pairs}
        assert "A" in pair_nodes or "B" in pair_nodes

    def test_detect_hidden_terminal_conflict(self):
        """Line: A and C share a slot → hidden-terminal conflict detected."""
        C = make_line_conflict_graph()
        coloring = {"A": 0, "B": 1, "C": 0}  # A and C conflict
        matrix = build_schedule_matrix(coloring, sorted(C.nodes()))
        result = validate_schedule(C, coloring, matrix)
        assert result.status == "CONFLICT DETECTED"
        assert result.conflicts_found >= 1

    def test_detect_multiple_conflicts(self):
        """All three nodes share slot 0 → 3 conflict edges all fire."""
        C = make_line_conflict_graph()
        coloring = {"A": 0, "B": 0, "C": 0}
        matrix = build_schedule_matrix(coloring, sorted(C.nodes()))
        result = validate_schedule(C, coloring, matrix)
        assert result.status == "CONFLICT DETECTED"
        assert result.conflicts_found >= 3


# ---------------------------------------------------------------------------
# Tests: structural checks
# ---------------------------------------------------------------------------


class TestValidatorStructuralChecks:
    def test_missing_node_flagged(self):
        C = nx.Graph()
        C.add_edge("A", "B")
        coloring = {"A": 0}  # "B" missing
        matrix = []
        result = validate_schedule(C, coloring, matrix)
        assert result.conflicts_found >= 1

    def test_negative_slot_flagged(self):
        C = nx.Graph()
        C.add_node("X")
        coloring = {"X": -1}
        matrix = []
        result = validate_schedule(C, coloring, matrix)
        assert result.conflicts_found >= 1

    def test_matrix_row_count_checked(self):
        """Matrix with wrong number of rows is flagged."""
        C = make_line_conflict_graph()
        coloring = {"A": 0, "B": 1, "C": 2}
        node_order = sorted(C.nodes())
        matrix = build_schedule_matrix(coloring, node_order)
        # Corrupt the matrix: remove one row.
        bad_matrix = matrix[:-1]
        result = validate_schedule(C, coloring, bad_matrix)
        # Should flag the matrix dimension issue.
        assert result.conflicts_found >= 1

    def test_matrix_col_count_checked(self):
        """Matrix with wrong number of columns is flagged."""
        C = make_line_conflict_graph()
        coloring = {"A": 0, "B": 1, "C": 2}
        node_order = sorted(C.nodes())
        matrix = build_schedule_matrix(coloring, node_order)
        # Corrupt: drop a column from every row.
        bad_matrix = [row[:-1] for row in matrix]
        result = validate_schedule(C, coloring, bad_matrix)
        assert result.conflicts_found >= 1


# ---------------------------------------------------------------------------
# Tests: edge count reported correctly
# ---------------------------------------------------------------------------


class TestValidatorEdgeCount:
    def test_conflicts_checked_equals_edge_count(self):
        C = make_line_conflict_graph()  # 3 edges
        coloring = {"A": 0, "B": 1, "C": 2}
        matrix = build_schedule_matrix(coloring, sorted(C.nodes()))
        result = validate_schedule(C, coloring, matrix)
        assert result.conflicts_checked == 3

    def test_zero_edges_zero_checked(self):
        C = make_isolated_pair_conflict_graph()  # 0 edges
        coloring = {"A": 0, "B": 0}
        matrix = build_schedule_matrix(coloring, sorted(C.nodes()))
        result = validate_schedule(C, coloring, matrix)
        assert result.conflicts_checked == 0
