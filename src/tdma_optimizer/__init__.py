"""
__init__.py
-----------
Public API surface for the tdma_optimizer package.

Importing from this package exposes only the high-level entry points
needed by external consumers (tests, notebooks, integrations).
"""

from .cli import run_pipeline
from .coloring import dsatur_coloring, normalize_colors
from .conflict_graph import build_distance_two_conflict_graph
from .matrix import build_schedule_matrix
from .models import NodeCoordinate, ScheduleResult, ValidationResult
from .optimizer import improve_coloring
from .reporting import generate_json_report, generate_text_report
from .topology import (
    build_communication_graph,
    load_coordinates_from_file,
    load_coordinates_from_json_string,
    parse_coordinates,
)
from .validator import validate_schedule

__version__ = "1.0.0"

__all__ = [
    # Pipeline entry-point
    "run_pipeline",
    # Graph construction
    "build_communication_graph",
    "build_distance_two_conflict_graph",
    # Coloring
    "dsatur_coloring",
    "normalize_colors",
    "improve_coloring",
    # Matrix
    "build_schedule_matrix",
    # Validation
    "validate_schedule",
    # Reporting
    "generate_text_report",
    "generate_json_report",
    # Models
    "NodeCoordinate",
    "ScheduleResult",
    "ValidationResult",
    # I/O helpers
    "parse_coordinates",
    "load_coordinates_from_json_string",
    "load_coordinates_from_file",
    # Meta
    "__version__",
]
