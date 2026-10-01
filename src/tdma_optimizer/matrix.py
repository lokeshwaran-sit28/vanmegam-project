"""
matrix.py
---------
Builds the TDMA Schedule Matrix from a slot assignment.

The schedule matrix is a 2-D binary array of shape (frame_length × num_nodes).
Entry [slot][node_index] == 1 means that node is active in that slot.

This is a concise visual representation of the schedule suitable for
both the text report and the JSON output.
"""

from __future__ import annotations

from typing import Dict, List


def build_schedule_matrix(
    coloring: Dict[str, int],
    node_order: List[str],
) -> List[List[int]]:
    """
    Construct the binary schedule matrix.

    Parameters
    ----------
    coloring : dict[str, int]
        Node → slot mapping.
    node_order : list[str]
        Ordered list of node names that defines the column order in the
        matrix.  Should match the order used throughout the report.

    Returns
    -------
    list[list[int]]
        Matrix M where M[slot][col] == 1 iff node_order[col] is in slot.
        Rows are indexed by slot number (0-indexed), columns by node position
        in node_order.
    """
    frame_length = max(coloring.values(), default=-1) + 1
    num_nodes = len(node_order)

    # Initialise with all zeros.
    matrix: List[List[int]] = [
        [0] * num_nodes for _ in range(frame_length)
    ]

    for col, node in enumerate(node_order):
        slot = coloring[node]
        matrix[slot][col] = 1

    return matrix
