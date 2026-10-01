"""
tests/test_emane_adapter.py
----------------------------
Unit and integration tests for Part 2 EMANE Schedule Adapter.
Verifies conversion of Part 1 TDMA schedules to official EMANE XML schedules.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

# Add part2-emane/integration to sys.path
part2_dir = Path(__file__).resolve().parent.parent / "part2-emane" / "integration"
if str(part2_dir) not in sys.path:
    sys.path.insert(0, str(part2_dir))

from schedule_adapter import (
    ScheduleAdapterError,
    convert_schedule_result_to_emane,
    generate_nem_map,
    generate_tdma_schedule_xml,
    validate_adapter_input,
    validate_emane_config,
)
from tdma_optimizer import parse_coordinates, run_pipeline


class TestNemMapping:
    def test_deterministic_nem_map(self):
        assignments = {"Node_03": 0, "Node_01": 1, "Node_02": 0}
        nem_map = generate_nem_map(assignments)
        assert nem_map == {"Node_01": 1, "Node_02": 2, "Node_03": 3}

    def test_custom_nem_map(self):
        assignments = {"A": 0, "B": 1}
        custom = {"A": 10, "B": 20}
        nem_map = generate_nem_map(assignments, custom_map=custom)
        assert nem_map == custom

    def test_custom_nem_map_missing_key_raises(self):
        assignments = {"A": 0, "B": 1}
        custom = {"A": 10}
        with pytest.raises(ScheduleAdapterError, match="missing nodes"):
            generate_nem_map(assignments, custom_map=custom)

    def test_invalid_nem_id_raises(self):
        assignments = {"A": 0, "B": 1}
        custom = {"A": 0, "B": -1}
        with pytest.raises(ScheduleAdapterError, match="positive integer"):
            generate_nem_map(assignments, custom_map=custom)


class TestAdapterValidation:
    def test_empty_assignments_raises(self):
        with pytest.raises(ScheduleAdapterError, match="cannot be empty"):
            validate_adapter_input({}, 3)

    def test_invalid_frame_length_raises(self):
        with pytest.raises(ScheduleAdapterError, match="must be positive"):
            validate_adapter_input({"A": 0}, 0)

    def test_slot_out_of_bounds_raises(self):
        with pytest.raises(ScheduleAdapterError, match="exceeds or equals frame length"):
            validate_adapter_input({"A": 3}, frame_length=3)


class TestXmlGeneration:
    def test_xml_structure_nodes_attribute_and_1ms_slot_duration(self):
        assignments = {"Node_01": 0, "Node_02": 1, "Node_03": 0}
        xml_str = generate_tdma_schedule_xml(assignments, frame_length=2, slot_duration_us=1000)

        root = ET.fromstring(xml_str)
        assert root.tag == "emane-tdma-schedule"

        structure = root.find("structure")
        assert structure is not None
        assert structure.get("slotduration") == "1000"
        assert structure.get("slots") == "2"

        frame = root.find("./multiframe/frame")
        assert frame is not None
        slots = frame.findall("slot")
        assert len(slots) == 2

        # Slot 0 should have nodes attribute "1 3" and child element <tx/>
        slot0 = slots[0]
        assert slot0.get("index") == "0"
        assert slot0.get("nodes") == "1 3"
        tx0 = slot0.find("tx")
        assert tx0 is not None

        # Slot 1 should have nodes attribute "2" and child element <tx/>
        slot1 = slots[1]
        assert slot1.get("index") == "1"
        assert slot1.get("nodes") == "2"
        tx1 = slot1.find("tx")
        assert tx1 is not None

    def test_convert_pipeline_result_to_emane(self, tmp_path):
        nodes = parse_coordinates({"A": [0, 0], "B": [100, 0], "C": [1000, 0]})
        result = run_pipeline(nodes, radio_range=500.0, run_improvement=True)

        out_file = tmp_path / "emane-schedule.xml"
        xml_str, nem_map = convert_schedule_result_to_emane(result, output_path=str(out_file))

        assert out_file.exists()
        assert "emane-tdma-schedule" in xml_str
        assert nem_map == {"A": 1, "B": 2, "C": 3}

    def test_config_validator_detects_missing(self, tmp_path):
        is_valid, errors = validate_emane_config(str(tmp_path))
        assert not is_valid
        assert len(errors) == 4  # All 4 files missing
