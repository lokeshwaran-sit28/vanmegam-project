"""
conftest.py – shared pytest fixtures.
"""

from __future__ import annotations

import pytest

from tdma_optimizer.topology import parse_coordinates


# ---------------------------------------------------------------------------
# Coordinate fixture helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def line_coords():
    """Three-node line: A -- B -- C."""
    return parse_coordinates({"A": [0.0, 0.0], "B": [300.0, 0.0], "C": [600.0, 0.0]})


@pytest.fixture
def triangle_coords():
    """Triangle: all three nodes within 500 m of each other."""
    return parse_coordinates(
        {"A": [0.0, 0.0], "B": [400.0, 0.0], "C": [200.0, 346.0]}
    )


@pytest.fixture
def isolated_coords():
    """Two nodes > 500 m apart – no communication link."""
    return parse_coordinates({"A": [0.0, 0.0], "B": [1000.0, 0.0]})


@pytest.fixture
def nodes16_coords():
    """The 16-node grid example from the assignment."""
    raw = {
        "Node_01": [0.0, 0.0],
        "Node_02": [300.0, 0.0],
        "Node_03": [600.0, 0.0],
        "Node_04": [0.0, 300.0],
        "Node_05": [300.0, 300.0],
        "Node_06": [600.0, 300.0],
        "Node_07": [0.0, 600.0],
        "Node_08": [300.0, 600.0],
        "Node_09": [600.0, 600.0],
        "Node_10": [900.0, 0.0],
        "Node_11": [900.0, 300.0],
        "Node_12": [900.0, 600.0],
        "Node_13": [0.0, 900.0],
        "Node_14": [300.0, 900.0],
        "Node_15": [600.0, 900.0],
        "Node_16": [900.0, 900.0],
    }
    return parse_coordinates(raw)
