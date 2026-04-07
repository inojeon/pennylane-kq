"""
Result Formatter for Cloud API v2
===================================

Functions for validating and formatting quantum circuit execution results.
"""

import logging
from typing import Dict, Any, List, Union

import numpy as np
from pennylane.tape import QuantumScript
from pennylane.measurements import ExpectationMP, SampleMP, CountsMP, ProbabilityMP

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


def process_result(
    job_result: Dict[str, Any], circuit: QuantumScript
) -> Union[float, np.ndarray, Dict[str, int]]:
    """
    Convert Cloud API v2 result to PennyLane format.

    Args:
        job_result: Job result from Cloud API v2
        circuit: Original quantum circuit

    Returns:
        PennyLane execution result (numpy array or float)

    Raises:
        RuntimeError: If result format is unknown
    """
    result_data = job_result.get("result", {})

    # Determine measurement type from circuit
    if not circuit.measurements:
        raise RuntimeError("Circuit has no measurements")

    measurement = circuit.measurements[0]

    # Handle different measurement types
    if isinstance(measurement, ExpectationMP):
        # Expectation value computed from counts
        if "counts" in result_data:
            return convert_counts_to_exp(
                result_data["counts"], measurement.obs.wires, circuit.wires
            )
        else:
            raise RuntimeError(
                f"Expected 'counts' in result for ExpectationMP, got: {result_data}"
            )

    elif isinstance(measurement, CountsMP):
        if "counts" in result_data:
            return convert_counts_to_dict(result_data["counts"], len(circuit.wires))
        else:
            raise RuntimeError(f"Expected 'counts' in result, got: {result_data}")

    elif isinstance(measurement, SampleMP):
        if "counts" in result_data:
            return convert_counts_to_samples(result_data["counts"], circuit.wires)
        else:
            raise RuntimeError(f"Expected 'counts' in result, got: {result_data}")

    elif isinstance(measurement, ProbabilityMP):
        # Probability
        if "probabilities" in result_data:
            return np.array(result_data["probabilities"])
        elif "counts" in result_data:
            # Compute probabilities from counts
            counts = result_data["counts"]
            return counts_to_probs(counts, len(circuit.wires))
        else:
            raise RuntimeError(
                f"Expected 'probabilities' or 'counts' in result, got: {result_data}"
            )

    else:
        raise RuntimeError(f"Unsupported measurement type: {type(measurement)}")


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


def convert_counts_to_dict(counts: Dict[str, int], num_wires: int) -> Dict[str, int]:
    result = {}
    for state_str, count in counts.items():
        value = parse_count_key(state_str)
        binary_key = format(value, f"0{num_wires}b")
        result[binary_key] = count
    return result


def convert_counts_to_samples(counts: Dict[str, int], wires: Any) -> np.ndarray:
    """
    Convert counts to binary samples (supports both hex and binary formats).

    Args:
        counts: Dictionary of state strings to counts
            Supports hex format: {"0x3": 512, "0x0": 512}
            Supports binary format: {"11": 512, "00": 512}
        wires: Circuit wires

    Returns:
        Binary samples array of shape (num_shots, num_wires)

    Raises:
        ValueError: If count format is invalid or no samples extracted

    Examples:
        >>> counts = {"0x0": 50, "0x3": 50}
        >>> wires = [0, 1]
        >>> samples = convert_counts_to_samples(counts, wires)
        >>> samples.shape
        (100, 2)
    """
    num_wires = len(wires)
    samples = []

    logger.debug(f"Converting counts to samples: {counts}, num_wires={num_wires}")

    for state_str, count in counts.items():
        try:
            # Parse state key using helper function
            value = parse_count_key(state_str)

            # Convert to binary array
            binary = format(value, f"0{num_wires}b")
            binary_array = np.array([int(b) for b in binary])

            # Repeat for count
            for _ in range(count):
                samples.append(binary_array)

        except ValueError as e:
            logger.error(f"Failed to parse state '{state_str}': {e}")
            logger.error(f"Full counts dict: {counts}")
            raise ValueError(f"Invalid count state format '{state_str}': {e}")

    if not samples:
        raise ValueError(f"No valid samples extracted from counts: {counts}")

    return np.array(samples)


def convert_counts_to_exp(
    counts: Dict[str, int], obs_wires: Any, all_wires: Any
) -> float:
    """
    Compute expectation value of a Z-basis observable from counts.

    Uses parity of measured bits on obs_wires: eigenvalue is (-1)^(sum of bits).

    Args:
        counts: Dictionary of state strings to counts
        obs_wires: Wires of the observable
        all_wires: All circuit wires (for bit indexing)

    Returns:
        Expectation value as float
    """
    total_shots = sum(counts.values())
    expval = 0.0
    num_wires = len(all_wires)
    wire_indices = [list(all_wires).index(w) for w in obs_wires]

    for state_str, count in counts.items():
        value = parse_count_key(state_str)
        binary = format(value, f"0{num_wires}b")
        parity = (-1) ** sum(int(binary[i]) for i in wire_indices)
        expval += parity * count

    return expval / total_shots


def counts_to_probs(counts: Dict[str, int], num_wires: int) -> np.ndarray:
    """
    Convert counts to probabilities (supports both hex and binary formats).

    Args:
        counts: Dictionary of state strings to counts
            Supports hex format: {"0x3": 512, "0x0": 512}
            Supports binary format: {"11": 512, "00": 512}
        num_wires: Number of qubits (determines array size as 2^num_wires)

    Returns:
        Probability array of length 2^num_wires

    Examples:
        >>> counts = {"0x0": 512, "0x3": 512}
        >>> probs = counts_to_probs(counts, num_wires=2)
        >>> probs[0]  # Probability of state 0
        0.5
        >>> probs[3]  # Probability of state 3
        0.5
    """
    total_shots = sum(counts.values())
    probs = np.zeros(2**num_wires)

    for state_str, count in counts.items():
        value = parse_count_key(state_str)
        probs[value] = count / total_shots

    return probs
