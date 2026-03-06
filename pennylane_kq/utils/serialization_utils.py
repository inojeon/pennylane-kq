"""
JSON Serialization/Deserialization utilities for quantum circuits

Phase 2: Simple structure for circuit serialization
- Serialize operations (gates and parameters)
- Serialize measurements
- Deserialize back to executable circuits
"""

import json
from typing import Dict, Any, List
import pennylane as qml
from pennylane.tape import QuantumScript


def serialize_operation(op) -> Dict[str, Any]:
    """
    Serialize a single operation to JSON-compatible dict

    Parameters
    ----------
    op : qml.operation.Operation
        PennyLane operation (gate)

    Returns
    -------
    dict
        {"name": str, "wires": list, "params": list}
    """
    return {
        "name": op.name,
        "wires": list(op.wires),
        "params": [float(p) for p in op.parameters] if op.parameters else [],
    }


def deserialize_operation(data: Dict[str, Any]):
    """
    Deserialize dict to PennyLane operation

    Parameters
    ----------
    data : dict
        {"name": str, "wires": list, "params": list}

    Returns
    -------
    qml.operation.Operation
        Reconstructed operation
    """
    name = data["name"]
    wires = data["wires"]
    params = data["params"]

    # Get operation class from qml module
    op_class = getattr(qml, name)

    # Create operation with params and wires
    if params:
        return op_class(*params, wires=wires)
    else:
        return op_class(wires=wires)


def serialize_observable(obs) -> Dict[str, Any]:
    """
    Serialize observable to JSON-compatible dict

    Parameters
    ----------
    obs : qml.operation.Observable
        Observable (PauliX, PauliY, PauliZ, Identity, Hamiltonian, Tensor)

    Returns
    -------
    dict
        Observable representation
    """
    # Handle Hamiltonian
    if isinstance(obs, qml.Hamiltonian):
        return {
            "type": "Hamiltonian",
            "coeffs": [float(c) for c in obs.coeffs],
            "obs": [serialize_observable(o) for o in obs.ops],
        }

    # Handle Tensor/Prod (e.g., PauliX(0) @ PauliY(1))
    # In PennyLane v0.36+, @ operator creates Prod objects
    # Check for "Prod" in class name or if it has operands
    obs_class_name = obs.__class__.__name__
    if (
        obs_class_name == "Prod"
        or obs_class_name == "Tensor"
        or (hasattr(obs, "operands") and obs.operands)
    ):
        # Get operands (for Prod) or obs (for Tensor)
        if hasattr(obs, "operands"):
            sub_obs = obs.operands
        elif hasattr(obs, "obs"):
            sub_obs = obs.obs
        else:
            sub_obs = []

        return {"type": "Tensor", "obs": [serialize_observable(o) for o in sub_obs]}

    # Handle simple observables (PauliX, PauliY, PauliZ, Identity)
    return {"type": "Simple", "name": obs.name, "wires": list(obs.wires)}


def deserialize_observable(data: Dict[str, Any]):
    """
    Deserialize dict to PennyLane observable

    Parameters
    ----------
    data : dict
        Observable representation

    Returns
    -------
    qml.operation.Observable
        Reconstructed observable
    """
    obs_type = data["type"]

    # Hamiltonian
    if obs_type == "Hamiltonian":
        coeffs = data["coeffs"]
        obs = [deserialize_observable(o) for o in data["obs"]]
        return qml.Hamiltonian(coeffs, obs)

    # Tensor (e.g., PauliX(0) @ PauliY(1))
    if obs_type == "Tensor":
        obs_list = [deserialize_observable(o) for o in data["obs"]]
        result = obs_list[0]
        for o in obs_list[1:]:
            result = result @ o
        return result

    # Simple observables
    if obs_type == "Simple":
        name = data["name"]
        wires = data["wires"]
        obs_class = getattr(qml, name)
        return obs_class(wires=wires)

    raise ValueError(f"Unknown observable type: {obs_type}")


def serialize_measurement(measurement) -> Dict[str, Any]:
    """
    Serialize measurement to JSON-compatible dict

    Parameters
    ----------
    measurement : qml.measurements.MeasurementProcess
        Measurement (e.g., expval)

    Returns
    -------
    dict
        {"type": str, "obs": dict}
    """
    # Get measurement type from class name
    # ExpectationMP -> "expval", VarianceMP -> "var", etc.
    meas_class_name = measurement.__class__.__name__

    # Map class names to measurement types
    type_map = {
        "ExpectationMP": "expval",
        "VarianceMP": "var",
        "SampleMP": "sample",
        "ProbabilityMP": "probs",
        "StateMP": "state",
        "CountsMP": "counts",
    }

    meas_type = type_map.get(meas_class_name, meas_class_name.lower())

    return {
        "type": meas_type,
        "obs": serialize_observable(measurement.obs) if measurement.obs else None,
    }


def deserialize_measurement(data: Dict[str, Any]):
    """
    Deserialize dict to PennyLane measurement

    Parameters
    ----------
    data : dict
        {"type": str, "obs": dict}

    Returns
    -------
    qml.measurements.MeasurementProcess
        Reconstructed measurement
    """
    meas_type = data["type"]
    obs_data = data["obs"]

    if obs_data:
        obs = deserialize_observable(obs_data)
    else:
        obs = None

    # Create measurement based on type
    if meas_type == "expval":
        return qml.expval(obs)
    elif meas_type == "var":
        return qml.var(obs)
    elif meas_type == "sample":
        return qml.sample(obs) if obs else qml.sample()
    elif meas_type == "probs":
        return qml.probs(wires=obs.wires) if obs else qml.probs()
    else:
        raise ValueError(f"Unknown measurement type: {meas_type}")


def serialize_circuit(circuit: QuantumScript) -> Dict[str, Any]:
    """
    Serialize entire circuit to JSON-compatible dict

    Parameters
    ----------
    circuit : QuantumScript
        PennyLane quantum circuit/tape

    Returns
    -------
    dict
        {
            "operations": list,
            "measurements": list,
            "trainable_params": list,
            "shots": int or None,
            "batch_size": int or None,
            "wires": list,
            "num_wires": int
        }
    """
    # Basic operations and measurements
    result = {
        "operations": [serialize_operation(op) for op in circuit.operations],
        "measurements": [serialize_measurement(m) for m in circuit.measurements],
    }

    # Add metadata
    if hasattr(circuit, "trainable_params"):
        result["trainable_params"] = list(circuit.trainable_params)
    else:
        result["trainable_params"] = None

    # Shots (convert Shots object to int or None)
    if hasattr(circuit, "shots"):
        shots_obj = circuit.shots
        if shots_obj.total_shots is not None:
            result["shots"] = shots_obj.total_shots
        else:
            result["shots"] = None
    else:
        result["shots"] = None

    # Batch size
    if hasattr(circuit, "batch_size"):
        result["batch_size"] = circuit.batch_size
    else:
        result["batch_size"] = None

    # Wires
    if hasattr(circuit, "wires"):
        result["wires"] = list(circuit.wires)
        result["num_wires"] = len(circuit.wires)
    else:
        result["wires"] = []
        result["num_wires"] = 0

    return result


def deserialize_circuit(data: Dict[str, Any]) -> QuantumScript:
    """
    Deserialize dict to executable QuantumScript

    Parameters
    ----------
    data : dict
        {
            "operations": list,
            "measurements": list,
            "trainable_params": list (optional),
            "shots": int or None (optional),
            "batch_size": int or None (optional),
            "wires": list (optional),
            "num_wires": int (optional)
        }

    Returns
    -------
    QuantumScript
        Reconstructed circuit

    Notes
    -----
    - trainable_params, wires, num_wires are automatically computed by QuantumScript
    - shots can be passed during QuantumScript creation
    - batch_size is typically inferred from operations
    """
    operations = [deserialize_operation(op_data) for op_data in data["operations"]]
    measurements = [deserialize_measurement(m_data) for m_data in data["measurements"]]

    # Extract shots if provided
    shots = data.get("shots", None)

    # Create QuantumScript with shots
    # Note: QuantumScript will automatically compute trainable_params, wires, etc.
    if shots is not None:
        from pennylane.measurements import Shots

        shots_obj = Shots(shots)
        circuit = QuantumScript(operations, measurements, shots=shots_obj)
    else:
        circuit = QuantumScript(operations, measurements)

    return circuit


def circuit_to_json_string(circuit: QuantumScript) -> str:
    """
    Convert circuit to JSON string (for debugging/inspection)

    Parameters
    ----------
    circuit : QuantumScript
        PennyLane circuit

    Returns
    -------
    str
        JSON string representation
    """
    circuit_dict = serialize_circuit(circuit)
    return json.dumps(circuit_dict, indent=2)


def json_string_to_circuit(json_str: str) -> QuantumScript:
    """
    Convert JSON string to circuit

    Parameters
    ----------
    json_str : str
        JSON string representation

    Returns
    -------
    QuantumScript
        Reconstructed circuit
    """
    circuit_dict = json.loads(json_str)
    return deserialize_circuit(circuit_dict)
