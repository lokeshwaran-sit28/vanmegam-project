"""
cli.py
------
Command-line interface for the TDMA Schedule Optimizer.

Uses only ``argparse`` from the standard library – no external CLI
frameworks required.

Example usage
~~~~~~~~~~~~~
# From a JSON file:
python -m tdma_optimizer --file examples/nodes16.json

# From a JSON string (inline):
python -m tdma_optimizer --coordinates '{"Node_01":[0,0],"Node_02":[300,0]}'

# With custom radio range:
python -m tdma_optimizer --file examples/nodes16.json --radio-range 400

# JSON output:
python -m tdma_optimizer --file examples/nodes16.json --output-format json

# Disable local improvement pass:
python -m tdma_optimizer --file examples/nodes16.json --no-improvement
"""

from __future__ import annotations

import argparse
import sys

from .coloring import dsatur_coloring, normalize_colors
from .conflict_graph import build_distance_two_conflict_graph, conflict_summary
from .matrix import build_schedule_matrix
from .models import ScheduleResult
from .optimizer import improve_coloring
from .reporting import generate_json_report, generate_text_report
from .topology import (
    build_communication_graph,
    load_coordinates_from_file,
    load_coordinates_from_json_string,
)
from .validator import exit_on_conflict, validate_schedule


def build_arg_parser() -> argparse.ArgumentParser:
    """
    Create and return the configured argument parser.

    Separating this from ``main()`` makes the parser testable without
    actually running the full application.
    """
    parser = argparse.ArgumentParser(
        prog="tdma_optimizer",
        description=(
            "TDMA Schedule Planner and Optimizer for Wireless Networks.\n\n"
            "Builds a Distance-2 conflict graph from node coordinates and applies\n"
            "the DSATUR heuristic to assign TDMA time slots such that no two\n"
            "conflicting nodes share the same slot (collision-free scheduling)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m tdma_optimizer --file examples/nodes16.json\n"
            "  python -m tdma_optimizer --coordinates '{\"A\":[0,0],\"B\":[300,0]}'\n"
            "  python -m tdma_optimizer --file examples/nodes16.json --radio-range 400\n"
            "  python -m tdma_optimizer --file examples/nodes16.json --output-format json\n"
        ),
    )

    # Mutually exclusive input group (must supply exactly one).
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--coordinates",
        metavar="JSON",
        help=(
            "Node coordinates as a JSON string, e.g. "
            "'{\"Node_01\":[0,0],\"Node_02\":[300,0]}'"
        ),
    )
    input_group.add_argument(
        "--file",
        metavar="PATH",
        help="Path to a JSON file containing node coordinates.",
    )

    parser.add_argument(
        "--radio-range",
        type=float,
        default=500.0,
        metavar="METRES",
        help="Maximum transmission range in metres (default: 500.0).",
    )

    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format: 'text' (default) or 'json'.",
    )

    parser.add_argument(
        "--no-improvement",
        action="store_true",
        default=False,
        help=(
            "Disable the optional local-improvement pass.  The schedule "
            "will still be conflict-free; just potentially using more slots."
        ),
    )

    return parser


def run_pipeline(
    nodes_raw,
    radio_range: float,
    run_improvement: bool,
) -> ScheduleResult:
    """
    Execute the full scheduling pipeline and return a :class:`ScheduleResult`.

    This function is separate from the CLI argument handling so it can be
    called directly from tests without subprocess overhead.

    Parameters
    ----------
    nodes_raw : list[NodeCoordinate]
        Validated list of node coordinates.
    radio_range : float
        Radio transmission range in metres.
    run_improvement : bool
        Whether to run the local-improvement pass after DSATUR.

    Returns
    -------
    ScheduleResult
        Fully populated result including validation.
    """
    # Step 1 – Build communication graph.
    G = build_communication_graph(nodes_raw, radio_range)

    # Step 2 – Build Distance-2 conflict graph.
    C = build_distance_two_conflict_graph(G)

    # Step 3 – DSATUR coloring.
    coloring = dsatur_coloring(C)
    coloring = normalize_colors(coloring)

    # Step 4 (optional) – Local improvement.
    if run_improvement:
        coloring = improve_coloring(C, coloring)
        # improve_coloring already normalizes, but normalizing again is safe.
        coloring = normalize_colors(coloring)

    # Derive ordered node names (same alphabetical order as topology module).
    node_names = sorted(coloring.keys())
    frame_length = max(coloring.values(), default=-1) + 1

    # Step 5 – Build schedule matrix.
    matrix = build_schedule_matrix(coloring, node_names)

    # Step 6 – Validate.
    comm_edges, conflict_edges = conflict_summary(G, C)
    validation = validate_schedule(C, coloring, matrix)

    return ScheduleResult(
        node_names=node_names,
        assignments=coloring,
        comm_edge_count=comm_edges,
        conflict_edge_count=conflict_edges,
        frame_length=frame_length,
        radio_range=radio_range,
        schedule_matrix=matrix,
        validation_result=validation,
    )


def main(argv=None) -> int:
    """
    Entry point for the TDMA Optimizer CLI.

    Parameters
    ----------
    argv : list[str] | None
        Argument list (defaults to ``sys.argv[1:]``).

    Returns
    -------
    int
        Exit code (0 = success, 1 = error).
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # Load and validate coordinates.
    # ------------------------------------------------------------------
    try:
        if args.coordinates:
            nodes = load_coordinates_from_json_string(args.coordinates)
        else:
            nodes = load_coordinates_from_file(args.file)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # Validate radio range.
    # ------------------------------------------------------------------
    if args.radio_range <= 0:
        print(
            f"[ERROR] --radio-range must be positive; got {args.radio_range}",
            file=sys.stderr,
        )
        return 1

    # ------------------------------------------------------------------
    # Run the scheduling pipeline.
    # ------------------------------------------------------------------
    try:
        result = run_pipeline(
            nodes_raw=nodes,
            radio_range=args.radio_range,
            run_improvement=not args.no_improvement,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Unexpected failure during scheduling: {exc}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # Output.
    # ------------------------------------------------------------------
    if args.output_format == "json":
        print(generate_json_report(result))
    else:
        print(generate_text_report(result))

    # ------------------------------------------------------------------
    # Fail fast if the validator detected conflicts.
    # ------------------------------------------------------------------
    exit_on_conflict(result.validation_result)

    return 0
