"""
validator.py
------------
Independent schedule validation pass.

This module verifies that the produced slot assignment is genuinely
conflict-free.  It is implemented as a stand-alone function (not calling
any coloring logic) so it serves as a true *independent check*.

Validation checks performed
~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Every input node has exactly one slot assignment.
2. All slot numbers are non-negative integers.
3. Slot numbers form a contiguous range [0, k-1] (no gaps after normalization).
4. For every conflict edge (u, v) in C:  slot[u] ≠ slot[v].
5. The schedule matrix dimensions are correct:
      rows  == frame_length
      cols  == number of nodes

Why an independent validator?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A coloring implementation can have subtle bugs – the validator acts as a
"second pair of eyes" without any shared code paths with the coloring step.
It catches mistakes such as:
  * Off-by-one errors in the DSATUR loop.
  * Incorrect saturation-degree updates.
  * Mishandling of isolated nodes.
"""

from __future__ import annotations

import sys
from typing import Dict, List

import networkx as nx

from .models import ValidationResult


def validate_schedule(
    C: nx.Graph,
    coloring: Dict[str, int],
    schedule_matrix: List[List[int]],
) -> ValidationResult:
    """
    Validate a completed TDMA slot assignment against the conflict graph.

    Parameters
    ----------
    C : nx.Graph
        Distance-2 conflict graph.
    coloring : dict[str, int]
        Node → slot mapping to validate.
    schedule_matrix : list[list[int]]
        Binary matrix (frame_length × num_nodes).

    Returns
    -------
    ValidationResult
        Object containing counts of conflicts and a status string.

    Notes
    -----
    This function does NOT raise on conflict.  The caller should inspect
    ``result.conflicts_found`` and act accordingly (e.g. exit with code 1).
    """
    result = ValidationResult()

    nodes = sorted(C.nodes())
    num_nodes = len(nodes)

    # ------------------------------------------------------------------
    # Check 1: every node has exactly one non-negative integer slot.
    # ------------------------------------------------------------------
    for node in nodes:
        if node not in coloring:
            result.conflicts_found += 1
            result.conflicting_pairs.append((node, "MISSING", -1))
            continue

        slot = coloring[node]
        if not isinstance(slot, int) or slot < 0:
            result.conflicts_found += 1
            result.conflicting_pairs.append((node, "INVALID_SLOT", slot))

    frame_length = max(coloring.values(), default=-1) + 1

    # ------------------------------------------------------------------
    # Check 2: slot numbers are contiguous [0, frame_length-1].
    # ------------------------------------------------------------------
    used_slots = set(coloring.values())
    expected_slots = set(range(frame_length))
    if used_slots != expected_slots:
        # Non-contiguous – treat as a structural error but do not abort;
        # report the discrepancy in conflicting_pairs.
        missing = expected_slots - used_slots
        for m in missing:
            result.conflicts_found += 1
            result.conflicting_pairs.append(("SLOT_GAP", str(m), m))

    # ------------------------------------------------------------------
    # Check 3: verify every conflict edge.
    # ------------------------------------------------------------------
    for u, v in C.edges():
        result.conflicts_checked += 1
        slot_u = coloring.get(u, -1)
        slot_v = coloring.get(v, -1)
        if slot_u == slot_v:
            result.conflicts_found += 1
            result.conflicting_pairs.append((u, v, slot_u))

    # ------------------------------------------------------------------
    # Check 4: schedule matrix dimensions.
    # ------------------------------------------------------------------
    if schedule_matrix:
        actual_rows = len(schedule_matrix)
        if actual_rows != frame_length:
            result.conflicts_found += 1
            result.conflicting_pairs.append(
                ("MATRIX_ROWS", f"expected={frame_length}", actual_rows)
            )

        for row in schedule_matrix:
            if len(row) != num_nodes:
                result.conflicts_found += 1
                result.conflicting_pairs.append(
                    ("MATRIX_COLS", f"expected={num_nodes}", len(row))
                )
                break  # Report once per bad row.

    # ------------------------------------------------------------------
    # Finalise status.
    # ------------------------------------------------------------------
    if result.conflicts_found == 0:
        result.status = "CONFLICT-FREE"
    else:
        result.status = "CONFLICT DETECTED"

    return result


def exit_on_conflict(result: ValidationResult) -> None:
    """
    Print conflict details and exit with code 1 if any violations exist.

    Call this after :func:`validate_schedule` to enforce fail-fast behavior
    in production mode.

    Parameters
    ----------
    result : ValidationResult
        Output from :func:`validate_schedule`.
    """
    if result.conflicts_found > 0:
        print("\n[ERROR] Schedule validation FAILED.", file=sys.stderr)
        print(
            f"  Conflicts detected : {result.conflicts_found}",
            file=sys.stderr,
        )
        for pair in result.conflicting_pairs:
            print(f"  Conflicting pair   : {pair}", file=sys.stderr)
        sys.exit(1)
