"""
Result Formatter for Cloud API v2
===================================

Functions for validating and formatting quantum circuit execution results.

Uses PennyLane's built-in measurement.process_counts() for correct
partial-wire marginalization across all measurement types.
"""

import logging
from typing import Dict, Any, List

import numpy as np
from pennylane.tape import QuantumScript
from pennylane.measurements import SampleMeasurement

logger = logging.getLogger(__name__)


def validate_results(job_results: List[Dict[str, Any]], expected_count: int):
    """
    Validate batch results.

    Args:
        job_results: List of job results
        expected_count: Expected number of results

    Raises:
        RuntimeError: If validation fails
    """
    if len(job_results) != expected_count:
        error_msg = f"Expected {expected_count} results, got {len(job_results)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    for i, job in enumerate(job_results):
        status = job.get("status")

        if status != "SUCCESS":
            error_msg = job.get("error_message", "Unknown error")
            logger.error(f"Job {i} failed: {error_msg}")
            raise RuntimeError(f"Job {i} failed: {error_msg}")


def process_result(job_result: Dict[str, Any], circuit: QuantumScript) -> Any:
    """
    Convert Cloud API v2 result to PennyLane format.

    Uses PennyLane's built-in measurement.process_counts() for correct
    partial-wire marginalization and result formatting across all
    measurement types (expval, var, counts, sample, probs).

    The backend returns counts over ALL circuit wires (since QASM measures
    every qubit), but the user may request measurements on a subset of wires
    (e.g., qml.counts(wires=range(n))). PennyLane's process_counts() handles
    the marginalization: extracting only the requested wire bits and summing
    over the rest.

    Args:
        job_result: Job result from Cloud API v2
        circuit: Original quantum circuit

    Returns:
        PennyLane execution result (numpy array, float, or dict)

    Raises:
        RuntimeError: If result format is unknown or circuit has no measurements
    """
    result_data = job_result.get("result", {})

    if not circuit.measurements:
        raise RuntimeError("Circuit has no measurements")

    measurement = circuit.measurements[0]

    if not isinstance(measurement, SampleMeasurement):
        raise RuntimeError(
            f"Unsupported measurement type: {type(measurement).__name__}"
        )

    if "counts" in result_data:
        normalized = _normalize_counts(result_data["counts"], len(circuit.wires))
        return measurement.process_counts(normalized, circuit.wires)
    elif "probabilities" in result_data:
        return np.array(result_data["probabilities"])
    else:
        raise RuntimeError(
            f"Expected 'counts' or 'probabilities' in result, "
            f"got: {list(result_data.keys())}"
        )


def parse_count_key(state_str: str) -> int:
    """
    Parse count key (hex or binary format) to integer.

    Args:
        state_str: State string in hex ("0x3") or binary ("11") format

    Returns:
        Integer value of the state

    Examples:
        >>> parse_count_key("0x3")
        3
        >>> parse_count_key("11")
        3
    """
    if state_str.startswith("0x"):
        return int(state_str, 16)
    else:
        return int(state_str, 2)


def _normalize_counts(raw_counts: Dict[str, int], num_wires: int) -> Dict[str, int]:
    """
    Convert backend counts (hex/binary keys) to binary string counts.

    Normalizes the backend's count format (hex like "0x3" or binary like "11")
    into standard binary strings of fixed width matching the total circuit wires.

    Args:
        raw_counts: Backend counts with hex ("0x3") or binary ("11") keys
        num_wires: Total number of circuit wires (determines binary string width)

    Returns:
        Counts with binary string keys of length num_wires

    Examples:
        >>> _normalize_counts({"0x3": 500, "0x0": 500}, 2)
        {'11': 500, '00': 500}
        >>> _normalize_counts({"11": 500, "00": 500}, 2)
        {'11': 500, '00': 500}
    """
    result = {}
    for state_str, count in raw_counts.items():
        value = parse_count_key(state_str)
        binary_key = format(value, f"0{num_wires}b")
        result[binary_key] = result.get(binary_key, 0) + count
    return result
