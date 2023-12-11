import pennylane as qml

operations = [qml.RX(0.54, wires=0), qml.RY(0.1, wires=0)]

circuits = []

for operation in operations:
    # Apply the circuit operations
    device_wires = self.map_wires(operation.wires)
    par = operation.parameters

    for idx, p in enumerate(par):
        if isinstance(p, np.ndarray):
            # Convert arrays so that Qiskit accepts the parameter
            par[idx] = p.tolist()

    operation = operation.name

    mapped_operation = self._operation_map[operation]

    self.qubit_state_vector_check(operation)

    qregs = [self._reg[i] for i in device_wires.labels]

    adjoint = operation.startswith("Adjoint(")
    split_op = operation.split("Adjoint(")

    if adjoint:
        if split_op[1] in ("QubitUnitary)", "QubitStateVector)"):
            # Need to revert the order of the quantum registers used in
            # Qiskit such that it matches the PennyLane ordering
            qregs = list(reversed(qregs))
    else:
        if split_op[0] in ("QubitUnitary", "QubitStateVector"):
            # Need to revert the order of the quantum registers used in
            # Qiskit such that it matches the PennyLane ordering
            qregs = list(reversed(qregs))

    dag = circuit_to_dag(QuantumCircuit(self._reg, self._creg, name=""))
    gate = mapped_operation(*par)

    dag.apply_operation_back(gate, qargs=qregs)
    circuit = dag_to_circuit(dag)
    circuits.append(circuit)
