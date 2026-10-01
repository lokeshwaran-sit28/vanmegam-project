"""
models.py
---------
Pure data structures (dataclasses) shared across the project.

These are deliberately kept dependency-free so they can be imported
anywhere without pulling in heavy libraries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class NodeCoordinate:
    """
    Represents the 2-D position of a single radio node.

    Attributes
    ----------
    name : str
        Unique identifier for the node (e.g. "Node_01").
    x : float
        X-coordinate in meters.
    y : float
        Y-coordinate in meters.
    """

    name: str
    x: float
    y: float

    def as_tuple(self) -> Tuple[float, float]:
        """Return coordinates as a plain (x, y) tuple."""
        return (self.x, self.y)


@dataclass
class ScheduleResult:
    """
    Holds every artefact produced by the scheduling pipeline so that
    downstream consumers (reporter, validator, CLI) have a single object
    to pass around.

    Attributes
    ----------
    node_names : list[str]
        Ordered list of node identifiers exactly as supplied by the user.
    assignments : dict[str, int]
        Maps each node name to its TDMA slot number (0-indexed).
    comm_edge_count : int
        Number of edges in the communication graph G.
    conflict_edge_count : int
        Number of edges in the distance-2 conflict graph C.
    frame_length : int
        Total number of unique TDMA slots (= chromatic number of C
        as approximated by DSATUR).
    radio_range : float
        Configured radio range in meters.
    schedule_matrix : list[list[int]]
        Binary matrix of shape (frame_length × num_nodes).
        schedule_matrix[slot][node_index] == 1 means that node is
        assigned to that slot.
    validation_result : ValidationResult
        The outcome of the conflict-checking pass.
    """

    node_names: List[str]
    assignments: Dict[str, int]
    comm_edge_count: int
    conflict_edge_count: int
    frame_length: int
    radio_range: float
    schedule_matrix: List[List[int]]
    validation_result: "ValidationResult" = field(default_factory=lambda: ValidationResult())


@dataclass
class ValidationResult:
    """
    Contains the outcome of the schedule validation pass.

    Attributes
    ----------
    conflicts_checked : int
        Number of conflict edges that were inspected.
    conflicts_found : int
        Number of edges where both endpoints share the same slot.
    conflicting_pairs : list[tuple[str, str, int]]
        Triples of (node_u, node_v, shared_slot) for every violation.
    status : str
        Human-readable status string, either "CONFLICT-FREE" or "CONFLICT DETECTED".
    """

    conflicts_checked: int = 0
    conflicts_found: int = 0
    conflicting_pairs: List[Tuple[str, str, int]] = field(default_factory=list)
    status: str = "NOT VALIDATED"
