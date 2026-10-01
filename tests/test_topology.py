"""
test_topology.py
----------------
Unit tests for the topology module: coordinate parsing and communication
graph construction.

Covers:
  - Valid coordinate parsing
  - Alphabetical ordering
  - Invalid JSON / coordinate format detection
  - Negative / zero radio range rejection
  - Edge weight accuracy
  - Isolated node handling
  - Numeric type coercion
"""

from __future__ import annotations

import math

import pytest

from tdma_optimizer.topology import (
    build_communication_graph,
    euclidean_distance,
    load_coordinates_from_json_string,
    parse_coordinates,
)
from tdma_optimizer.models import NodeCoordinate


# ---------------------------------------------------------------------------
# parse_coordinates
# ---------------------------------------------------------------------------


class TestParseCoordinates:
    def test_basic_valid(self):
        nodes = parse_coordinates({"A": [0, 0], "B": [100, 200]})
        assert len(nodes) == 2
        names = [n.name for n in nodes]
        assert "A" in names
        assert "B" in names

    def test_returns_sorted_alphabetically(self):
        raw = {"Zeta": [0, 0], "Alpha": [100, 0], "Mu": [50, 0]}
        nodes = parse_coordinates(raw)
        names = [n.name for n in nodes]
        assert names == sorted(names)

    def test_float_coordinates(self):
        nodes = parse_coordinates({"P": [1.5, 2.7]})
        assert nodes[0].x == pytest.approx(1.5)
        assert nodes[0].y == pytest.approx(2.7)

    def test_integer_coordinates_coerced_to_float(self):
        nodes = parse_coordinates({"P": [10, 20]})
        assert isinstance(nodes[0].x, float)
        assert isinstance(nodes[0].y, float)

    def test_empty_dict_raises(self):
        with pytest.raises(ValueError, match="(?i)at least one"):
            parse_coordinates({})

    def test_not_a_dict_raises(self):
        with pytest.raises(ValueError, match="JSON object"):
            parse_coordinates([1, 2, 3])  # type: ignore

    def test_missing_y_coordinate_raises(self):
        with pytest.raises(ValueError, match="exactly two"):
            parse_coordinates({"A": [100]})

    def test_extra_coordinate_raises(self):
        with pytest.raises(ValueError, match="exactly two"):
            parse_coordinates({"A": [1, 2, 3]})

    def test_non_numeric_coordinate_raises(self):
        with pytest.raises(ValueError, match="numeric"):
            parse_coordinates({"A": ["east", 0]})

    def test_nan_coordinate_raises(self):
        with pytest.raises(ValueError, match="finite"):
            parse_coordinates({"A": [float("nan"), 0]})

    def test_inf_coordinate_raises(self):
        with pytest.raises(ValueError, match="finite"):
            parse_coordinates({"A": [float("inf"), 0]})

    def test_single_node_valid(self):
        nodes = parse_coordinates({"Solo": [0, 0]})
        assert len(nodes) == 1
        assert nodes[0].name == "Solo"


# ---------------------------------------------------------------------------
# load_coordinates_from_json_string
# ---------------------------------------------------------------------------


class TestLoadFromJsonString:
    def test_valid_json_string(self):
        json_str = '{"A": [0, 0], "B": [300, 0]}'
        nodes = load_coordinates_from_json_string(json_str)
        assert len(nodes) == 2

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_coordinates_from_json_string("{not valid json}")

    def test_empty_json_object_raises(self):
        with pytest.raises(ValueError, match="(?i)at least one"):
            load_coordinates_from_json_string("{}")


# ---------------------------------------------------------------------------
# euclidean_distance
# ---------------------------------------------------------------------------


class TestEuclideanDistance:
    def test_zero_distance(self):
        a = NodeCoordinate("A", 0, 0)
        assert euclidean_distance(a, a) == pytest.approx(0.0)

    def test_horizontal_distance(self):
        a = NodeCoordinate("A", 0, 0)
        b = NodeCoordinate("B", 300, 0)
        assert euclidean_distance(a, b) == pytest.approx(300.0)

    def test_pythagorean(self):
        a = NodeCoordinate("A", 0, 0)
        b = NodeCoordinate("B", 300, 400)
        assert euclidean_distance(a, b) == pytest.approx(500.0)

    def test_symmetry(self):
        a = NodeCoordinate("A", 100, 200)
        b = NodeCoordinate("B", 400, 600)
        assert euclidean_distance(a, b) == pytest.approx(euclidean_distance(b, a))


# ---------------------------------------------------------------------------
# build_communication_graph
# ---------------------------------------------------------------------------


class TestBuildCommunicationGraph:
    def test_single_node_no_edges(self):
        nodes = parse_coordinates({"Solo": [0, 0]})
        G = build_communication_graph(nodes, radio_range=500.0)
        assert G.number_of_nodes() == 1
        assert G.number_of_edges() == 0

    def test_two_nodes_within_range_connected(self):
        nodes = parse_coordinates({"A": [0, 0], "B": [300, 0]})
        G = build_communication_graph(nodes, radio_range=500.0)
        assert G.has_edge("A", "B")

    def test_two_nodes_at_range_boundary_connected(self):
        """Exactly at range – must include (≤ condition)."""
        nodes = parse_coordinates({"A": [0, 0], "B": [500, 0]})
        G = build_communication_graph(nodes, radio_range=500.0)
        assert G.has_edge("A", "B")

    def test_two_nodes_beyond_range_not_connected(self):
        nodes = parse_coordinates({"A": [0, 0], "B": [501, 0]})
        G = build_communication_graph(nodes, radio_range=500.0)
        assert not G.has_edge("A", "B")

    def test_isolated_nodes_present_in_graph(self):
        """Even nodes with no neighbours must appear as vertices."""
        nodes = parse_coordinates({"A": [0, 0], "B": [9000, 0]})
        G = build_communication_graph(nodes, radio_range=500.0)
        assert "A" in G.nodes()
        assert "B" in G.nodes()
        assert G.number_of_edges() == 0

    def test_edge_distance_attribute_stored(self):
        nodes = parse_coordinates({"A": [0, 0], "B": [300, 400]})
        G = build_communication_graph(nodes, radio_range=500.0)
        assert G.has_edge("A", "B")
        assert G["A"]["B"]["distance"] == pytest.approx(500.0, abs=0.01)

    def test_zero_radio_range_raises(self):
        nodes = parse_coordinates({"A": [0, 0], "B": [1, 0]})
        with pytest.raises(ValueError, match="positive"):
            build_communication_graph(nodes, radio_range=0.0)

    def test_negative_radio_range_raises(self):
        nodes = parse_coordinates({"A": [0, 0]})
        with pytest.raises(ValueError, match="positive"):
            build_communication_graph(nodes, radio_range=-100.0)

    def test_line_network_edges(self, line_coords):
        """A──B──C at 300 m spacing with range 500 m: 2 edges."""
        G = build_communication_graph(line_coords, radio_range=500.0)
        assert G.number_of_edges() == 2
        assert G.has_edge("A", "B")
        assert G.has_edge("B", "C")
        assert not G.has_edge("A", "C")  # 600 m > 500 m range

    def test_custom_radio_range(self):
        nodes = parse_coordinates({"A": [0, 0], "B": [400, 0]})
        G_small = build_communication_graph(nodes, radio_range=300.0)
        G_large = build_communication_graph(nodes, radio_range=500.0)
        assert not G_small.has_edge("A", "B")
        assert G_large.has_edge("A", "B")
