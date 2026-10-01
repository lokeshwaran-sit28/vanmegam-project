"""
generate_schedule.py
--------------------
Generates an EMANE TDMA schedule XML file directly from a node coordinates JSON file.

Usage:
    python part2-emane/scripts/generate_schedule.py --file examples/nodes16.json --output part2-emane/configs/tdma-schedule.xml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root and integration directory to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "part2-emane" / "integration"))

from schedule_adapter import convert_schedule_result_to_emane
from tdma_optimizer import load_coordinates_from_file, run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Part 1 TDMA Schedule to official EMANE TDMA Schedule XML."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to JSON file containing node coordinates (e.g., examples/nodes16.json).",
    )
    parser.add_argument(
        "--radio-range",
        type=float,
        default=500.0,
        help="Radio range in metres (default: 500.0).",
    )
    parser.add_argument(
        "--output",
        default="part2-emane/configs/tdma-schedule.xml",
        help="Output XML file path (default: part2-emane/configs/tdma-schedule.xml).",
    )
    args = parser.parse_args()

    try:
        nodes = load_coordinates_from_file(args.file)
        result = run_pipeline(nodes, radio_range=args.radio_range, run_improvement=True)
        xml_str, nem_map = convert_schedule_result_to_emane(
            result, output_path=args.output, slot_duration_us=1000
        )

        print(f"[SUCCESS] EMANE TDMA Schedule XML generated successfully!")
        print(f"  Nodes         : {len(result.node_names)}")
        print(f"  Frame Length  : {result.frame_length} slots (1 ms per slot)")
        print(f"  NEM Mappings  : {len(nem_map)} nodes mapped")
        print(f"  Output File   : {args.output}")
        return 0
    except Exception as exc:
        print(f"[ERROR] Schedule generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
