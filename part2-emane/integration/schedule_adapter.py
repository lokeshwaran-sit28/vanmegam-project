"""
schedule_adapter.py
-------------------
Converts a ScheduleResult from the TDMA Optimizer (Part 1) into an
official EMANE-compatible TDMA schedule XML file (<emane-tdma-schedule>).

Official EMANE XML Format:
    <emane-tdma-schedule>
      <structure frames="1" slots="9" slotduration="1000" slotoverhead="100" bandwidth="1000000"/>
      <multiframe frequency="2350000000" power="0.0" datarate="1000000">
        <frame index="0">
          <slot index="0" nodes="5 10 13 16">
            <tx/>
          </slot>
          ...
        </frame>
      </multiframe>
    </emane-tdma-schedule>

Execution Status:
    IMPLEMENTED & UNIT TESTED.
    Runtime EMANE execution requires Linux (Ubuntu 22.04 LTS).
"""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Union
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

try:
    from tdma_optimizer.models import ScheduleResult
except ImportError:
    ScheduleResult = None  # Fallback for standalone execution


class ScheduleAdapterError(ValueError):
    """Exception raised for errors during schedule conversion or validation."""
    pass


def generate_nem_map(
    assignments: Dict[str, int],
    custom_map: Optional[Dict[str, int]] = None
) -> Dict[str, int]:
    """
    Map logical node names (e.g., 'Node_01' or 'A') to numeric EMANE NEM IDs (1, 2, ...).

    Parameters
    ----------
    assignments : dict[str, int]
        Node name -> slot index dictionary from Part 1.
    custom_map : dict[str, int], optional
        Explicit node name -> NEM ID override map.

    Returns
    -------
    dict[str, int]
        Node name -> 1-based NEM ID dictionary.
    """
    if custom_map:
        missing = set(assignments.keys()) - set(custom_map.keys())
        if missing:
            raise ScheduleAdapterError(f"Custom NEM map missing nodes: {sorted(missing)}")
        for k, v in custom_map.items():
            if not isinstance(v, int) or v <= 0:
                raise ScheduleAdapterError(f"NEM ID for node '{k}' must be a positive integer, got {v}")
        return dict(custom_map)

    # Sort node names deterministically for reproducible 1-based mapping
    sorted_nodes = sorted(assignments.keys())
    return {node_name: idx + 1 for idx, node_name in enumerate(sorted_nodes)}


def validate_adapter_input(
    assignments: Dict[str, int],
    frame_length: int,
) -> None:
    """
    Validate that the Part 1 schedule input is structurally valid for EMANE conversion.

    Raises
    ------
    ScheduleAdapterError
        If assignments are empty, slots exceed frame length, or frame length is invalid.
    """
    if not assignments:
        raise ScheduleAdapterError("Assignments dictionary cannot be empty.")
    if frame_length <= 0:
        raise ScheduleAdapterError(f"Frame length must be positive, got {frame_length}.")

    max_slot = max(assignments.values())
    if max_slot >= frame_length:
        raise ScheduleAdapterError(
            f"Max slot assigned ({max_slot}) exceeds or equals frame length ({frame_length})."
        )

    for node, slot in assignments.items():
        if not isinstance(slot, int) or slot < 0:
            raise ScheduleAdapterError(f"Invalid slot {slot} for node '{node}'. Slot must be a non-negative int.")


def generate_tdma_schedule_xml(
    assignments: Dict[str, int],
    frame_length: int,
    slot_duration_us: int = 1000,
    slot_overhead_us: int = 100,
    frequency_hz: int = 2_350_000_000,
    bandwidth_hz: int = 1_000_000,
    tx_power_dbm: float = 0.0,
    data_rate_bps: int = 1_000_000,
    custom_nem_map: Optional[Dict[str, int]] = None,
) -> str:
    """
    Convert Part 1 TDMA schedule into official EMANE TDMA schedule XML (<emane-tdma-schedule>).

    Parameters
    ----------
    assignments : dict[str, int]
        Node name -> slot assignment dictionary.
    frame_length : int
        Total number of slots in a frame.
    slot_duration_us : int, default=1000
        Slot duration in microseconds (1000 us = 1 ms).
    slot_overhead_us : int, default=100
        Guard time / overhead per slot in microseconds.
    frequency_hz : int, default=2_350_000_000
        Center operating frequency in Hz.
    bandwidth_hz : int, default=1_000_000
        Bandwidth in Hz.
    tx_power_dbm : float, default=0.0
        Transmit power in dBm.
    data_rate_bps : int, default=1_000_000
        Data rate in bits per second.
    custom_nem_map : dict[str, int], optional
        Optional custom node -> NEM ID mapping.

    Returns
    -------
    str
        Formatted XML string conforming to official EMANE TDMA Schedule schema.
    """
    validate_adapter_input(assignments, frame_length)
    nem_map = generate_nem_map(assignments, custom_nem_map)

    # Invert assignment: slot_idx -> list of NEM IDs allowed to transmit
    slot_to_nems: Dict[int, List[int]] = defaultdict(list)
    for node, slot in assignments.items():
        slot_to_nems[slot].append(nem_map[node])

    # Build official EMANE XML hierarchy
    root = Element("emane-tdma-schedule")

    # <structure> tag defines frame and slot parameters
    structure = SubElement(root, "structure")
    structure.set("frames", "1")
    structure.set("slots", str(frame_length))
    structure.set("slotduration", str(slot_duration_us))
    structure.set("slotoverhead", str(slot_overhead_us))
    structure.set("bandwidth", str(bandwidth_hz))

    # <multiframe> defines default RF settings across the frame
    multiframe = SubElement(root, "multiframe")
    multiframe.set("frequency", str(frequency_hz))
    multiframe.set("power", f"{tx_power_dbm:.1f}")
    multiframe.set("datarate", str(data_rate_bps))

    frame = SubElement(multiframe, "frame")
    frame.set("index", "0")

    # Generate <slot> definitions for every slot index 0..frame_length-1
    for slot_idx in range(frame_length):
        slot_elem = SubElement(frame, "slot")
        slot_elem.set("index", str(slot_idx))

        allowed_nems = sorted(slot_to_nems.get(slot_idx, []))
        if allowed_nems:
            # Official EMANE schema: nodes attribute contains space-separated NEM IDs
            slot_elem.set("nodes", " ".join(str(n) for n in allowed_nems))
            SubElement(slot_elem, "tx")

    raw_xml = tostring(root, encoding="unicode")
    parsed = minidom.parseString(raw_xml)
    return parsed.toprettyxml(indent="  ")


def convert_schedule_result_to_emane(
    result: Union[ScheduleResult, Dict[str, int]],
    frame_length: Optional[int] = None,
    output_path: Optional[str] = None,
    slot_duration_us: int = 1000,
) -> Tuple[str, Dict[str, int]]:
    """
    Convenience wrapper converting a ScheduleResult object or dict into EMANE XML file.
    """
    if hasattr(result, "assignments") and hasattr(result, "frame_length"):
        assignments = result.assignments
        flen = result.frame_length
    elif isinstance(result, dict):
        assignments = result
        if frame_length is None:
            flen = max(assignments.values()) + 1 if assignments else 0
        else:
            flen = frame_length
    else:
        raise ScheduleAdapterError("Expected ScheduleResult object or assignments dictionary.")

    nem_map = generate_nem_map(assignments)
    xml_str = generate_tdma_schedule_xml(
        assignments=assignments,
        frame_length=flen,
        slot_duration_us=slot_duration_us,
        custom_nem_map=nem_map,
    )

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

    return xml_str, nem_map


def validate_emane_config(config_dir: str) -> Tuple[bool, List[str]]:
    """
    Validate that all required EMANE XML files exist and are syntactically valid.

    Parameters
    ----------
    config_dir : str
        Directory containing EMANE XML configurations (nem.xml, platform.xml, etc.).

    Returns
    -------
    tuple[bool, list[str]]
        (is_valid, list_of_error_messages)
    """
    errors = []
    required_files = ["nem.xml", "platform.xml", "transvirtual.xml", "tdma-schedule.xml"]
    
    for filename in required_files:
        path = os.path.join(config_dir, filename)
        if not os.path.exists(path):
            errors.append(f"Missing required configuration file: {filename}")
        else:
            try:
                minidom.parse(path)
            except Exception as exc:
                errors.append(f"Invalid XML syntax in {filename}: {exc}")

    return len(errors) == 0, errors
