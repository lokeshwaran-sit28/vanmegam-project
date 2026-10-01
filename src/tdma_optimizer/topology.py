"""
topology.py
-----------
Builds the communication graph G from raw node coordinates.

Key concepts
~~~~~~~~~~~~
* A node is a radio unit with a fixed 2-D position.
* Two nodes u and v are **directly connected** (have an edge) if and only if
  their Euclidean distance is ≤ radio_range.
* The resulting graph G is the **communication graph** – it models which pairs
  of nodes can hear each other.

Complexity
~~~~~~~~~~
Building G requires O(N²) distance evaluations for N nodes.  For the
expected scale (tens of nodes) this is trivially fast.
"""

from __future__ import annotations

import json
import math
from typing import Dict, List, Tuple

import networkx as nx

from .models import NodeCoordinate


# ---------------------------------------------------------------------------
# Input parsing / validation
# ---------------------------------------------------------------------------


def parse_coordinates(raw: Dict[str, list]) -> List[NodeCoordinate]:
    """
    Convert a raw dictionary (as read from JSON) into a validated list of
    :class:`NodeCoordinate` objects.

    Parameters
    ----------
    raw : dict
        Mapping of node-name → [x, y].  Names must be unique strings;
        coordinates must be a two-element list of numbers.

    Returns
    -------
    list[NodeCoordinate]
        Sorted alphabetically by node name for deterministic ordering.

    Raises
    ------
    ValueError
        On any validation failure with a descriptive message.
    """
    if not isinstance(raw, dict):
        raise ValueError("Coordinates must be a JSON object mapping node-name → [x, y].")

    if len(raw) == 0:
        raise ValueError("At least one node must be provided.")

    nodes: List[NodeCoordinate] = []

    for name, coords in raw.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Node name must be a non-empty string; got: {name!r}")

        if not isinstance(coords, (list, tuple)) or len(coords) != 2:
            raise ValueError(
                f"Node '{name}': coordinates must be a list of exactly two numbers [x, y]; "
                f"got {coords!r}"
            )

        x_raw, y_raw = coords
        try:
            x = float(x_raw)
            y = float(y_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"Node '{name}': coordinate values must be numeric; "
                f"got [{x_raw!r}, {y_raw!r}]"
            )

        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            raise ValueError(
                f"Node '{name}': coordinate values must be finite real numbers."
            )

        nodes.append(NodeCoordinate(name=name, x=x, y=y))

    # Node names must already be unique because they are dictionary keys in
    # Python, but we check explicitly in case caller passed a non-dict mapping
    # constructed from a JSON source with duplicate keys (some parsers keep
    # the last value silently).
    seen: set = set()
    for node in nodes:
        if node.name in seen:
            raise ValueError(f"Duplicate node name detected: '{node.name}'")
        seen.add(node.name)

    # Return in deterministic order (alphabetical by name).
    return sorted(nodes, key=lambda n: n.name)


def load_coordinates_from_json_string(json_str: str) -> List[NodeCoordinate]:
    """
    Parse a JSON string directly from the CLI ``--coordinates`` argument.

    Raises
    ------
    ValueError
        On JSON decode error or coordinate validation failure.
    """
    try:
        raw = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON string: {exc}") from exc

    return parse_coordinates(raw)


def load_coordinates_from_file(path: str) -> List[NodeCoordinate]:
    """
    Read node coordinates from a JSON file.

    Parameters
    ----------
    path : str
        Path to a ``.json`` file containing a single object mapping
        node-names to ``[x, y]`` pairs.

    Raises
    ------
    ValueError
        On file-not-found, JSON decode error, or coordinate validation error.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        raise ValueError(f"File not found: '{path}'")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in file '{path}': {exc}") from exc

    return parse_coordinates(raw)


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def euclidean_distance(a: NodeCoordinate, b: NodeCoordinate) -> float:
    """
    Return the Euclidean distance (metres) between two nodes.

    Uses ``math.hypot`` for numerical robustness.
    """
    return math.hypot(a.x - b.x, a.y - b.y)


def build_communication_graph(
    nodes: List[NodeCoordinate],
    radio_range: float,
) -> nx.Graph:
    """
    Construct the **communication graph** G.

    Every node in ``nodes`` becomes a vertex.  An edge (u, v) is added if and
    only if the Euclidean distance between u and v is ≤ ``radio_range``.

    Node attributes stored in the graph
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    * ``pos`` – (x, y) tuple, useful for NetworkX drawing.
    * ``x``, ``y`` – individual coordinate floats.

    Edge attributes stored in the graph
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    * ``distance`` – exact Euclidean distance in metres.

    Parameters
    ----------
    nodes : list[NodeCoordinate]
        Validated list of node positions.
    radio_range : float
        Maximum transmission range in metres (must be > 0).

    Returns
    -------
    nx.Graph
        Undirected communication graph.

    Raises
    ------
    ValueError
        If radio_range ≤ 0.
    """
    if radio_range <= 0:
        raise ValueError(f"radio_range must be positive; got {radio_range!r}")

    G: nx.Graph = nx.Graph()

    # Add all nodes first (some may be isolated).
    for node in nodes:
        G.add_node(node.name, pos=node.as_tuple(), x=node.x, y=node.y)

    # Add edges for every pair within range.
    n = len(nodes)
    for i in range(n):
        for j in range(i + 1, n):
            dist = euclidean_distance(nodes[i], nodes[j])
            if dist <= radio_range:
                G.add_edge(nodes[i].name, nodes[j].name, distance=round(dist, 4))

    return G
