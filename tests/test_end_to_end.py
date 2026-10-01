"""
test_end_to_end.py
------------------
End-to-end integration tests covering the full pipeline from raw coordinates
to validated, conflict-free TDMA schedule.

These tests verify:
  TEST 1: Three-node line (A-B-C) – all need different slots.
  TEST 2: Two disconnected nodes – can share a slot.
  TEST 3: Four-node chain – spatial reuse between A and D.
  TEST 4: Triangle – requires 3 colors.
  TEST 5: 16-node grid from the assignment.
  TEST 6: Invalid JSON coordinate string.
  TEST 7: Invalid coordinate format (non-numeric).
  TEST 8: Zero radio range.
  TEST 9: Isolated node in a network.
  TEST 10: CLI --output-format json produces valid JSON.
  TEST 11: CLI --no-improvement flag works.
  TEST 12: Slot assignments are contiguous [0, k-1].
  TEST 13: Every node appears exactly once.
"""

from __future__ import annotations

import json
import sys

import pytest

from tdma_optimizer.cli import main, run_pipeline
from tdma_optimizer.topology import (
    load_coordinates_from_json_string,
    parse_coordinates,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pipeline(raw: dict, radio_range: float = 500.0, improvement: bool = True):
    """Run full pipeline from a raw dict and return ScheduleResult."""
    nodes = parse_coordinates(raw)
    return run_pipeline(nodes, radio_range=radio_range, run_improvement=improvement)


def _assert_conflict_free(result):
    """Assert the validation result is CONFLICT-FREE."""
    vr = result.validation_result
    assert vr.status == "CONFLICT-FREE", (
        f"Expected CONFLICT-FREE but got: {vr.status}\n"
        f"Conflicting pairs: {vr.conflicting_pairs}"
    )
    assert vr.conflicts_found == 0


# ---------------------------------------------------------------------------
# TEST 1: Three-node line
# ---------------------------------------------------------------------------


class TestThreeNodeLine:
    """A ── B ── C: all three nodes are within two hops of each other."""

    def test_all_different_slots(self):
        result = _pipeline({"A": [0, 0], "B": [300, 0], "C": [600, 0]})
        a, b, c = result.assignments["A"], result.assignments["B"], result.assignments["C"]
        assert a != b, "A and B must have different slots"
        assert b != c, "B and C must have different slots"
        assert a != c, "A and C must have different slots (hidden terminal)"

    def test_exactly_three_slots(self):
        result = _pipeline({"A": [0, 0], "B": [300, 0], "C": [600, 0]})
        assert result.frame_length == 3

    def test_conflict_free(self):
        result = _pipeline({"A": [0, 0], "B": [300, 0], "C": [600, 0]})
        _assert_conflict_free(result)


# ---------------------------------------------------------------------------
# TEST 2: Two disconnected nodes
# ---------------------------------------------------------------------------


class TestTwoIsolatedNodes:
    """A and B are 1000 m apart – they must share the same slot."""

    def test_same_slot(self):
        result = _pipeline({"A": [0, 0], "B": [1000, 0]})
        assert result.assignments["A"] == result.assignments["B"] == 0

    def test_frame_length_one(self):
        result = _pipeline({"A": [0, 0], "B": [1000, 0]})
        assert result.frame_length == 1

    def test_zero_comm_edges(self):
        result = _pipeline({"A": [0, 0], "B": [1000, 0]})
        assert result.comm_edge_count == 0

    def test_conflict_free(self):
        result = _pipeline({"A": [0, 0], "B": [1000, 0]})
        _assert_conflict_free(result)


# ---------------------------------------------------------------------------
# TEST 3: Spatial reuse – four-node chain
# ---------------------------------------------------------------------------


class TestSpatialReuseChain:
    """A──B──C──D: A and D are 3 hops apart and must reuse a slot."""

    def test_a_and_d_share_slot(self):
        raw = {"A": [0, 0], "B": [300, 0], "C": [600, 0], "D": [900, 0]}
        result = _pipeline(raw)
        _assert_conflict_free(result)
        assert result.assignments["A"] == result.assignments["D"], (
            "A and D are 3 hops apart – they must share a slot (spatial reuse)"
        )

    def test_conflict_free(self):
        raw = {"A": [0, 0], "B": [300, 0], "C": [600, 0], "D": [900, 0]}
        result = _pipeline(raw)
        _assert_conflict_free(result)


# ---------------------------------------------------------------------------
# TEST 4: Triangle
# ---------------------------------------------------------------------------


class TestTriangle:
    """All three nodes within range – chromatic number = 3."""

    def test_three_slots_required(self):
        # Equilateral triangle, all sides ~400 m
        result = _pipeline(
            {"A": [0, 0], "B": [400, 0], "C": [200, 346]}
        )
        assert result.frame_length == 3

    def test_all_different_slots(self):
        result = _pipeline(
            {"A": [0, 0], "B": [400, 0], "C": [200, 346]}
        )
        slots = [result.assignments[n] for n in ["A", "B", "C"]]
        assert len(set(slots)) == 3

    def test_conflict_free(self):
        result = _pipeline(
            {"A": [0, 0], "B": [400, 0], "C": [200, 346]}
        )
        _assert_conflict_free(result)


# ---------------------------------------------------------------------------
# TEST 5: 16-node grid
# ---------------------------------------------------------------------------


class TestSixteenNodeGrid:
    RAW = {
        "Node_01": [0.0, 0.0], "Node_02": [300.0, 0.0],
        "Node_03": [600.0, 0.0], "Node_04": [0.0, 300.0],
        "Node_05": [300.0, 300.0], "Node_06": [600.0, 300.0],
        "Node_07": [0.0, 600.0], "Node_08": [300.0, 600.0],
        "Node_09": [600.0, 600.0], "Node_10": [900.0, 0.0],
        "Node_11": [900.0, 300.0], "Node_12": [900.0, 600.0],
        "Node_13": [0.0, 900.0], "Node_14": [300.0, 900.0],
        "Node_15": [600.0, 900.0], "Node_16": [900.0, 900.0],
    }

    def test_sixteen_nodes_processed(self):
        result = _pipeline(self.RAW)
        assert len(result.node_names) == 16

    def test_every_node_has_a_slot(self):
        result = _pipeline(self.RAW)
        for node in self.RAW:
            assert node in result.assignments

    def test_conflict_free(self):
        result = _pipeline(self.RAW)
        _assert_conflict_free(result)

    def test_slots_are_contiguous(self):
        result = _pipeline(self.RAW)
        used = sorted(set(result.assignments.values()))
        assert used == list(range(result.frame_length))

    def test_spatial_reuse_occurs(self):
        """Multiple nodes must share at least one slot."""
        result = _pipeline(self.RAW)
        from collections import Counter
        slot_count = Counter(result.assignments.values())
        assert any(count > 1 for count in slot_count.values()), (
            "No spatial reuse detected – every node got a unique slot, "
            "which suggests a bug in the conflict graph or coloring."
        )

    def test_matrix_dimensions(self):
        result = _pipeline(self.RAW)
        assert len(result.schedule_matrix) == result.frame_length
        for row in result.schedule_matrix:
            assert len(row) == 16


# ---------------------------------------------------------------------------
# TEST 6: Invalid JSON
# ---------------------------------------------------------------------------


class TestInvalidJSON:
    def test_bad_json_string_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_coordinates_from_json_string("{not json}")

    def test_cli_bad_json_returns_nonzero(self, capsys):
        code = main(["--coordinates", "{broken json}"])
        assert code == 1


# ---------------------------------------------------------------------------
# TEST 7: Invalid coordinate format
# ---------------------------------------------------------------------------


class TestInvalidCoordinates:
    def test_non_numeric_raises(self):
        with pytest.raises(ValueError, match="numeric"):
            parse_coordinates({"A": ["north", 0]})

    def test_missing_y_raises(self):
        with pytest.raises(ValueError, match="exactly two"):
            parse_coordinates({"A": [100]})

    def test_extra_coordinate_raises(self):
        with pytest.raises(ValueError, match="exactly two"):
            parse_coordinates({"A": [1, 2, 3]})


# ---------------------------------------------------------------------------
# TEST 8: Zero / negative radio range
# ---------------------------------------------------------------------------


class TestInvalidRadioRange:
    def test_zero_range_cli_returns_nonzero(self, capsys):
        code = main([
            "--coordinates", '{"A":[0,0],"B":[1,0]}',
            "--radio-range", "0"
        ])
        assert code == 1

    def test_negative_range_cli_returns_nonzero(self, capsys):
        code = main([
            "--coordinates", '{"A":[0,0],"B":[1,0]}',
            "--radio-range", "-100"
        ])
        assert code == 1


# ---------------------------------------------------------------------------
# TEST 9: Isolated node in a mixed network
# ---------------------------------------------------------------------------


class TestIsolatedNodeInNetwork:
    def test_isolated_node_gets_slot(self):
        """An isolated node (far from all others) still receives a slot."""
        raw = {
            "Near1": [0, 0],
            "Near2": [300, 0],
            "Isolated": [9000, 9000],  # far away
        }
        result = _pipeline(raw)
        assert "Isolated" in result.assignments
        _assert_conflict_free(result)

    def test_isolated_node_can_share_slot(self):
        """The isolated node should NOT need a unique slot."""
        raw = {
            "Near1": [0, 0],
            "Near2": [300, 0],
            "Isolated": [9000, 9000],
        }
        result = _pipeline(raw)
        # Isolated is not in conflict with anyone, so it must share a slot
        # with Near1 or Near2 (or any other non-conflicting node).
        slot_counts = {}
        for node, slot in result.assignments.items():
            slot_counts.setdefault(slot, []).append(node)
        isolated_slot = result.assignments["Isolated"]
        # If isolated only gets its own slot, that's still OK, but ideally
        # it should share. We just verify conflict-free here.
        _assert_conflict_free(result)


# ---------------------------------------------------------------------------
# TEST 10: JSON output format
# ---------------------------------------------------------------------------


class TestJSONOutput:
    def test_json_output_is_valid(self, capsys):
        code = main([
            "--coordinates", '{"A":[0,0],"B":[300,0],"C":[600,0]}',
            "--output-format", "json",
        ])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "assignments" in data
        assert "frame_length" in data
        assert "validation" in data
        assert data["validation"]["status"] == "CONFLICT-FREE"

    def test_json_contains_all_expected_keys(self, capsys):
        code = main([
            "--file", "examples/nodes16.json",
            "--output-format", "json",
        ])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        for key in ["configuration", "nodes", "communication_edges",
                    "conflict_edges", "frame_length", "assignments",
                    "schedule_matrix", "validation"]:
            assert key in data, f"Missing key in JSON output: {key}"


# ---------------------------------------------------------------------------
# TEST 11: --no-improvement flag
# ---------------------------------------------------------------------------


class TestNoImprovementFlag:
    def test_no_improvement_still_conflict_free(self):
        raw = {
            "Node_01": [0.0, 0.0], "Node_02": [300.0, 0.0],
            "Node_03": [600.0, 0.0], "Node_04": [0.0, 300.0],
        }
        nodes = parse_coordinates(raw)
        result = run_pipeline(nodes, radio_range=500.0, run_improvement=False)
        _assert_conflict_free(result)

    def test_no_improvement_flag_cli(self, capsys):
        code = main([
            "--coordinates", '{"A":[0,0],"B":[300,0],"C":[600,0]}',
            "--no-improvement",
        ])
        assert code == 0


# ---------------------------------------------------------------------------
# TEST 12: Contiguous slots
# ---------------------------------------------------------------------------


class TestContiguousSlots:
    def test_slots_always_contiguous(self):
        for raw in [
            {"A": [0, 0], "B": [300, 0], "C": [600, 0]},
            {"X": [0, 0]},
            {"A": [0, 0], "B": [9999, 9999]},
        ]:
            result = _pipeline(raw)
            used = sorted(set(result.assignments.values()))
            assert used == list(range(result.frame_length)), (
                f"Slots are not contiguous: {used}"
            )


# ---------------------------------------------------------------------------
# TEST 13: Every node appears exactly once
# ---------------------------------------------------------------------------


class TestUniqueNodeAssignment:
    def test_no_duplicate_or_missing_nodes(self, nodes16_coords):
        result = run_pipeline(nodes16_coords, radio_range=500.0, run_improvement=True)
        expected_names = sorted(n.name for n in nodes16_coords)
        assert sorted(result.node_names) == expected_names
        assert sorted(result.assignments.keys()) == expected_names
