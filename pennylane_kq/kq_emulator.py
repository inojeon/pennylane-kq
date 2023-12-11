"""
A device that allows us to implement operation on a single qudit. The backend is a remote simulator.
"""

import numpy as np

import requests
from pennylane import DeviceError, QubitDevice
from qiskit import extensions as ex
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

from qiskit.compiler import transpile


QISKIT_OPERATION_MAP_SELF_ADJOINT = {
    # native PennyLane operations also native to qiskit
    "PauliX": ex.XGate,
    "PauliY": ex.YGate,
    "PauliZ": ex.ZGate,
    "Hadamard": ex.HGate,
    "CNOT": ex.CXGate,
    "CZ": ex.CZGate,
    "SWAP": ex.SwapGate,
    "ISWAP": ex.iSwapGate,
    "RX": ex.RXGate,
    "RY": ex.RYGate,
    "RZ": ex.RZGate,
    "Identity": ex.IGate,
    "CSWAP": ex.CSwapGate,
    "CRX": ex.CRXGate,
    "CRY": ex.CRYGate,
    "CRZ": ex.CRZGate,
    "PhaseShift": ex.PhaseGate,
    "QubitStateVector": ex.Initialize,
    "Toffoli": ex.CCXGate,
    "QubitUnitary": ex.UnitaryGate,
    "U1": ex.U1Gate,
    "U2": ex.U2Gate,
    "U3": ex.U3Gate,
    "IsingZZ": ex.RZZGate,
    "IsingYY": ex.RYYGate,
    "IsingXX": ex.RXXGate,
}

QISKIT_OPERATION_MAP_NON_SELF_ADJOINT = {"S": ex.SGate, "T": ex.TGate, "SX": ex.SXGate}

QISKIT_OPERATION_MAP = {
    **QISKIT_OPERATION_MAP_SELF_ADJOINT,
    **QISKIT_OPERATION_MAP_NON_SELF_ADJOINT,
}
QISKIT_OPERATION_INVERSES_MAP_SELF_ADJOINT = {
    "Adjoint(" + k + ")": v for k, v in QISKIT_OPERATION_MAP_SELF_ADJOINT.items()
}
QISKIT_OPERATION_INVERSES_MAP_NON_SELF_ADJOINT = {
    "Adjoint(S)": ex.SdgGate,
    "Adjoint(T)": ex.TdgGate,
    "Adjoint(SX)": ex.SXdgGate,
}


QISKIT_OPERATION_INVERSES_MAP = {
    **QISKIT_OPERATION_INVERSES_MAP_SELF_ADJOINT,
    **QISKIT_OPERATION_INVERSES_MAP_NON_SELF_ADJOINT,
}


class KoreaQuantumEmulator(QubitDevice):
    """
    The base class for all devices that call to an external server.
    """

    name = "Korea Quantum Emulator"
    short_name = "kq.emulator"
    pennylane_requires = ">=0.16.0"
    version = "0.0.1"
    author = "Inho Jeon"

    operations = {"PauliX", "RX", "CNOT", "RY", "RZ"}
    observables = {"PauliZ", "PauliX", "PauliY"}
    _operation_map = {**QISKIT_OPERATION_MAP, **QISKIT_OPERATION_INVERSES_MAP}

    def __init__(self, shots=1024, accessKeyId=None, secretAccessKey=None):
        super().__init__(wires=4, shots=shots)
        self.accessKeyId = accessKeyId
        self.secretAccessKey = secretAccessKey
        # self.hardware_options = hardware_options or "kqEmulator"

    def qubit_state_vector_check(self, operation):
        """Input check for the the QubitStateVector operation.

        Args:
            operation (pennylane.Operation): operation to be checked

        Raises:
            DeviceError: If the operation is QubitStateVector
        """
        if operation == "QubitStateVector":
            if "unitary" in self.backend_name:
                raise DeviceError(
                    "The QubitStateVector operation "
                    "is not supported on the unitary simulator backend."
                )

    def apply_operations(self, operations):
        """Apply the circuit operations.

        This method serves as an auxiliary method to :meth:`~.QiskitDevice.apply`.

        Args:
            operations (List[pennylane.Operation]): operations to be applied

        Returns:
            list[QuantumCircuit]: a list of quantum circuit objects that
                specify the corresponding operations
        """
        circuits = []

        for operation in operations:
            # Apply the circuit operations
            device_wires = self.map_wires(operation.wires)
            par = operation.parameters

            for idx, p in enumerate(par):  # for loop index, value
                if isinstance(p, np.ndarray):  # if p type is np.ndarray
                    # Convert arrays so that Qiskit accepts the parameter
                    par[idx] = p.tolist()

            operation = operation.name

            mapped_operation = self._operation_map[operation]

            self.qubit_state_vector_check(operation)

            qregs = [self._reg[i] for i in device_wires.labels]

            # adjoint = operation.startswith("Adjoint(")
            # split_op = operation.split("Adjoint(")

            # if adjoint:
            #     if split_op[1] in ("QubitUnitary)", "QubitStateVector)"):
            #         # Need to revert the order of the quantum registers used in
            #         # Qiskit such that it matches the PennyLane ordering
            #         qregs = list(reversed(qregs))
            # else:
            #     if split_op[0] in ("QubitUnitary", "QubitStateVector"):
            #         # Need to revert the order of the quantum registers used in
            #         # Qiskit such that it matches the PennyLane ordering
            #         qregs = list(reversed(qregs))

            dag = circuit_to_dag(QuantumCircuit(self._reg, self._creg, name=""))
            gate = mapped_operation(*par)

            dag.apply_operation_back(gate, qargs=qregs)
            circuit = dag_to_circuit(dag)
            circuits.append(circuit)

        return circuits

    def create_circuit_object(self, operations, **kwargs):
        """Builds the circuit objects based on the operations and measurements
        specified to apply.

        Args:
            operations (list[~.Operation]): operations to apply to the device

        Keyword args:
            rotations (list[~.Operation]): Operations that rotate the circuit
                pre-measurement into the eigenbasis of the observables.
        """
        rotations = kwargs.get("rotations", [])
        applied_operations = self.apply_operations(operations)

        # Rotating the state for measurement in the computational basis
        rotation_circuits = self.apply_operations(rotations)
        applied_operations.extend(rotation_circuits)

        for circuit in applied_operations:
            self._circuit &= circuit
        for qr, cr in zip(self._reg, self._creg):
            self._circuit.measure(qr, cr)

    def apply(self, operations, **kwargs):
        self.create_circuit_object(operations, **kwargs)

        print("self._circuit22")
        print(self._circuit)

        print(self._circuit.qasm())

        # qiskit backend에 맞게 컴파일하는 과정 지금은 필요 없는듯
        #        compiled_circuit = self.compile()
        self.run(self._circuit)

        # applied_operations= self._circuit

    # def run(self, circuits):  # pragma: no cover, pylint:disable=arguments-differ
    #     print("run")
    #     print(circuits)
    #     # res = super().batch_execute(circuits, timeout=self.timeout_secs)
    #     # if self.tracker.active:
    #     #     self._track_run()
    #     return "{-1: 4, 1: 1020}"

    def compile_circuits(self, circuits):
        r"""Compiles multiple circuits one after the other.

        Args:
            circuits (list[.tapes.QuantumTape]): the circuits to be compiled

        Returns:
             list[QuantumCircuit]: the list of compiled circuits
        """
        # Compile each circuit object
        compiled_circuits = []

        for circuit in circuits:
            # We need to reset the device here, else it will
            # not start the next computation in the zero state
            self.reset()
            self.create_circuit_object(
                circuit.operations, rotations=circuit.diagonalizing_gates
            )

            # compiled_circ = self.compile()

            compiled_circ = self._circuit
            compiled_circ.name = f"circ{len(compiled_circuits)}"
            compiled_circuits.append(compiled_circ)

        return compiled_circuits

    def batch_execute(
        self, circuits
    ):  # pragma: no cover, pylint:disable=arguments-differ
        print(self.accessKeyId, self.secretAccessKey)

        compiled_circuits = self.compile_circuits(circuits)

        # print(self._circuit.qasm())
        # print(compiled_circuits)
        # print(compiled_circuits[0].qasm())
        # res = super().batch_execute(circuits, timeout=self.timeout_secs)
        # if self.tracker.active:
        #     self._track_run()
        return [{"-1": 4, "1": 1020}]

    def compile(self):
        """Compile the quantum circuit to target the provided compile_backend.

        If compile_backend is None, then the target is simply the
        backend.
        """
        compile_backend = self.compile_backend or self.backend
        compiled_circuits = transpile(
            self._circuit, backend=compile_backend, **self.transpile_args
        )
        return compiled_circuits

    def reset(self):
        # Reset only internal data, not the options that are determined on
        # device creation
        self._reg = QuantumRegister(self.num_wires, "q")
        self._creg = ClassicalRegister(self.num_wires, "c")
        self._circuit = QuantumCircuit(self._reg, self._creg, name="temp")

        self._current_job = None
        self._state = None  # statevector of a simulator backend

    # def expval():
    #     print("expval")

    # def reset():
    #     print("reset")
