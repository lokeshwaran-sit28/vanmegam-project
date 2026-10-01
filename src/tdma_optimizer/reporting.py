"""
reporting.py
------------
Generates human-readable text and machine-readable JSON output.

This module is intentionally separated from the algorithmic logic so
that the report format can be changed without touching core logic and
vice-versa.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List

from .models import ScheduleResult


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------


def generate_text_report(result: ScheduleResult) -> str:
    """
    Build the full human-readable TDMA Topology Optimization Report.

    Parameters
    ----------
    result : ScheduleResult
        Completed schedule result from the pipeline.

    Returns
    -------
    str
        Multi-line report string ready for printing to stdout.
    """
    lines: List[str] = []
    sep = "=" * 64
    thin = "-" * 64
    node_names = result.node_names
    assignments = result.assignments
    frame_length = result.frame_length
    matrix = result.schedule_matrix
    vr = result.validation_result

    # ---------------------------------------------------------------
    # Header
    # ---------------------------------------------------------------
    lines.append(sep)
    lines.append("TDMA TOPOLOGY OPTIMIZATION REPORT")
    lines.append(sep)
    lines.append(f"Total Nodes Processed   : {len(node_names)}")
    lines.append(f"Configured Radio Range  : {result.radio_range} meters")
    lines.append(f"Communication Links     : {result.comm_edge_count}")
    lines.append(f"Conflict Graph Edges    : {result.conflict_edge_count}")
    lines.append(f"Optimized Frame Length  : {frame_length} unique timeslots")
    lines.append(thin)

    # ---------------------------------------------------------------
    # Node → Slot assignments
    # ---------------------------------------------------------------
    lines.append("NODE -> SLOT ASSIGNMENTS:")
    lines.append("")
    for node in node_names:
        slot = assignments[node]
        lines.append(f"  {node}: Slot {slot}")

    lines.append("")
    lines.append(thin)

    # ---------------------------------------------------------------
    # Schedule matrix
    # ---------------------------------------------------------------
    lines.append("STRUCTURAL TDMA SCHEDULE MATRIX")
    lines.append("(Slot x Node Boolean Matrix)")
    lines.append("")

    # Build header row.  Abbreviate node names to the numeric suffix.
    abbrevs = [_abbrev(n) for n in node_names]
    col_w = max(len(a) for a in abbrevs) + 2  # at least 2 padding
    slot_label_w = 8  # width for "Slot XX"

    header_parts = [f"{'Slot':<{slot_label_w}}"]
    for abbrev in abbrevs:
        header_parts.append(f"{abbrev:^{col_w}}")
    lines.append(" | ".join(header_parts))
    lines.append(thin)

    for slot_idx, row in enumerate(matrix):
        row_parts = [f"{'Slot ' + str(slot_idx).zfill(2):<{slot_label_w}}"]
        for val in row:
            row_parts.append(f"{'1' if val else '0':^{col_w}}")
        lines.append(" | ".join(row_parts))

    lines.append("")
    lines.append(thin)

    # ---------------------------------------------------------------
    # Slot utilization
    # ---------------------------------------------------------------
    lines.append("SLOT UTILIZATION:")
    lines.append("")

    slot_nodes: Dict[int, List[str]] = defaultdict(list)
    for node in node_names:
        slot_nodes[assignments[node]].append(node)

    for slot_idx in range(frame_length):
        members = slot_nodes.get(slot_idx, [])
        lines.append(
            f"  Slot {slot_idx}: {len(members)} node(s)  ->  {', '.join(members)}"
        )

    lines.append("")
    lines.append(thin)

    # ---------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------
    lines.append("VALIDATION:")
    lines.append("")
    lines.append(f"  Conflict edges checked : {vr.conflicts_checked}")
    lines.append(f"  Conflicts detected     : {vr.conflicts_found}")
    lines.append(f"  Schedule status        : {vr.status}")

    if vr.conflicts_found > 0:
        lines.append("")
        lines.append("  [!] Conflicting pairs:")
        for pair in vr.conflicting_pairs:
            lines.append(f"      {pair}")

    lines.append("")
    lines.append(sep)
    lines.append("Execution finalized cleanly.")
    lines.append(sep)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON report
# ---------------------------------------------------------------------------


def generate_json_report(result: ScheduleResult) -> str:
    """
    Produce a machine-readable JSON string of the complete schedule.

    Parameters
    ----------
    result : ScheduleResult
        Completed schedule result from the pipeline.

    Returns
    -------
    str
        Pretty-printed JSON string.
    """
    vr = result.validation_result

    payload = {
        "configuration": {
            "radio_range_m": result.radio_range,
        },
        "nodes": len(result.node_names),
        "communication_edges": result.comm_edge_count,
        "conflict_edges": result.conflict_edge_count,
        "frame_length": result.frame_length,
        "assignments": result.assignments,
        "schedule_matrix": result.schedule_matrix,
        "slot_utilization": _slot_utilization(result),
        "validation": {
            "conflicts_checked": vr.conflicts_checked,
            "conflicts_found": vr.conflicts_found,
            "status": vr.status,
        },
    }

    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _abbrev(name: str) -> str:
    """
    Return a short display label for a node name.

    Tries to extract the numeric suffix (e.g. 'Node_01' → '01').
    Falls back to the full name if no suffix is found.
    """
    parts = name.split("_")
    if len(parts) >= 2 and parts[-1].isdigit():
        return parts[-1]
    return name


def _slot_utilization(result: ScheduleResult) -> Dict[str, List[str]]:
    """Return a slot → list-of-node-names mapping (keys as strings for JSON)."""
    util: Dict[int, List[str]] = defaultdict(list)
    for node in result.node_names:
        util[result.assignments[node]].append(node)
    return {str(k): v for k, v in sorted(util.items())}
