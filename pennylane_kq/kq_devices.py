"""
KQ Cloud API v2 Device
======================

PennyLane device for executing quantum circuits via Cloud API v2 with SSE streaming.

This device integrates with the KISTI Quantum Cloud API v2 service, which provides:
- REST API for batch job submission
- Server-Sent Events (SSE) for real-time status updates
- RabbitMQ-based event distribution
- Support for both state vector and sampling execution

Author: SY Park, QInfo team, KISTI
Date: 2025-11-04
"""

import logging
from collections.abc import Sequence
from typing import List, Dict, Any, Tuple, Optional, Union

import pennylane as qml
from pennylane.devices import Device
from pennylane.tape import QuantumScript
from pennylane.transforms import broadcast_expand
from pennylane.transforms.core.compile_pipeline import CompilePipeline
from pennylane.typing import Result
from pennylane.devices import ExecutionConfig
from pennylane.measurements import ExpectationMP, SampleMP, CountsMP, ProbabilityMP

from .utils import http_client, result_formatter

logger = logging.getLogger(__name__)


class KQCloudV2Device(Device):
    """
    PennyLane device for KRISS Quantum Cloud API with SSE streaming.

    This device submits quantum circuits to the KRISS Quantum Cloud API service
    and receives execution results via Server-Sent Events (SSE) or HTTP polling.

    Args:
        wires (int or Iterable[Number, str]]): Number of wires or wire labels
        shots (int): Number of circuit evaluations/random samples. Required;
            statevector mode is not supported by the KRISS API.
        host (str): API base URL. Default: "https://qc-api.kisti.re.kr"
        api_key (str): QCC-API-KEY for authentication. Required.
        target (str): QCC-TARGET device code. Required.
        stream_timeout (float): SSE stream timeout in seconds. Default: 1800.0 (30 minutes)
        max_retries (int): Maximum number of retries for failed requests. Default: 3
        use_streaming (bool): Use SSE streaming (True) or HTTP polling (False). Default: False
        poll_interval (float): Polling interval in seconds when use_streaming=False. Default: 2.0
        verify_ssl (bool): Whether to verify SSL certificates. Default: True

    Example:
        >>> import pennylane as qml
        >>> dev = qml.device('kq.cloudv2', wires=2, shots=1024,
        ...                  api_key="your-api-key", target="kisti.sim1")
        >>> @qml.qnode(dev)
        ... def circuit(params):
        ...     qml.RY(params[0], wires=0)
        ...     qml.CNOT(wires=[0, 1])
        ...     return qml.expval(qml.PauliZ(0))
        >>> result = circuit([0.5])
    """

    short_name = "kq.cloudv2"
    pennylane_requires = ">=0.30.0"
    version = "0.0.29"
    author = "KISTI Quantum Computing Team"

    @property
    def name(self) -> str:
        return "KQ Cloud API v2 Device"

    # Supported operations (gates)
    operations = {
        "Identity",
        "Snapshot",
        "Barrier",
        # Single-qubit gates
        "PauliX",
        "PauliY",
        "PauliZ",
        "Hadamard",
        "S",
        "T",
        "SX",
        "RX",
        "RY",
        "RZ",
        "PhaseShift",
        "U1",
        "U2",
        "U3",
        # Two-qubit gates
        "CNOT",
        "CZ",
        "CY",
        "SWAP",
        "ISWAP",
        "ECR",
        "SISWAP",
        "CRX",
        "CRY",
        "CRZ",
        "ControlledPhaseShift",
        # Three-qubit gates
        "CSWAP",
        "Toffoli",
        # Multi-qubit gates
        "MultiControlledX",
    }

    # Supported observables (measurements)
    observables = {
        "PauliX",
        "PauliY",
        "PauliZ",
        "Hadamard",
        "Identity",
        "Hermitian",
        "Projector",
        "Prod",
        "Sum",
        "SProd",  # Arithmetic observables
        "Hamiltonian",
    }

    def __init__(
        self,
        wires: Optional[Any] = None,
        shots: Optional[int] = None,
        host: str = "https://qc-api.kisti.re.kr",
        api_key: Optional[str] = None,
        target: Optional[str] = None,
        stream_timeout: float = 1800.0,
        max_retries: int = 3,
        use_streaming: bool = False,
        poll_interval: float = 2.0,
        verify_ssl: bool = True,
    ):
        """
        Initialize KQ Cloud API v2 device.

        Args:
            wires: Number of wires or wire labels
            shots: Number of shots (required; KRISS API does not support statevector mode)
            host: API base URL
            api_key: QCC-API-KEY for authentication (required)
            target: QCC-TARGET device code (required)
            stream_timeout: SSE timeout in seconds
            max_retries: Maximum number of retries for failed requests
            use_streaming: Use SSE streaming (True) or polling (False)
            poll_interval: Polling interval in seconds (used when use_streaming=False)
            verify_ssl: Whether to verify SSL certificates
        """
        if not api_key:
            raise ValueError("api_key is required")
        if not target:
            raise ValueError("target is required")
        if shots is None:
            raise ValueError(
                "shots is required (KRISS API does not support statevector mode)"
            )

        super().__init__(wires=wires, shots=shots)

        self.host = host.rstrip("/")
        self.api_key = api_key
        self.target = target
        self.stream_timeout = stream_timeout
        self.max_retries = max_retries
        self.use_streaming = use_streaming
        self.poll_interval = poll_interval
        self.verify_ssl = verify_ssl

        logger.info(
            f"Initialized KQCloudV2Device: host={self.host}, "
            f"wires={len(self.wires)}, shots={self.shots}, "
            f"target={self.target}, use_streaming={self.use_streaming}"
        )

    def preprocess(
        self, execution_config: Optional[ExecutionConfig] = None
    ) -> Tuple[CompilePipeline, ExecutionConfig]:
        """
        Preprocess execution configuration.

        Args:
            execution_config: Execution configuration options

        Returns:
            Tuple of (preprocessing function, updated execution config)
        """
        if execution_config is None:
            execution_config = ExecutionConfig()

        from pennylane.transforms.core import TransformProgram

        program = TransformProgram()
        program.add_transform(broadcast_expand)

        return program, execution_config

    def execute(
        self,
        circuits: Union[QuantumScript, Sequence[QuantumScript]],
        execution_config: Optional[ExecutionConfig] = None,
    ):
        """
        Execute quantum circuits via Cloud API v2 with SSE streaming.

        Args:
            circuits: List of quantum circuits (QuantumScript)
            execution_config: Execution configuration

        Returns:
            Tuple of execution results

        Raises:
            DeviceError: If execution fails
        """
        if isinstance(circuits, QuantumScript):
            circuits = [circuits]
        if execution_config is None:
            execution_config = ExecutionConfig()

        logger.info(f"Executing {len(circuits)} circuit(s)")

        # 1. Serialize circuits to Cloud API v2 format
        jobs_data = self._prepare_jobs(circuits)
        logger.debug(f"Prepared jobs data: {len(jobs_data['jobs'])} jobs")

        # 2. Submit batch
        batch_uuid, job_uuids = http_client.submit_batch(
            self.host,
            jobs_data,
            self.api_key,
            self.target,
            self.max_retries,
            self.verify_ssl,
        )
        logger.info(f"Submitted batch: batch_uuid={batch_uuid}, jobs={len(job_uuids)}")

        # 3. Get results via SSE streaming or HTTP polling
        if self.use_streaming:
            try:
                logger.info("Using SSE streaming mode")
                job_results = http_client.stream_batch_results(
                    self.host, batch_uuid, self.stream_timeout, self.verify_ssl
                )
                logger.debug(f"Received {len(job_results)} results via SSE")
            except Exception as e:
                logger.warning(f"SSE streaming failed: {e}")
                logger.warning("Falling back to HTTP polling mode")
                job_results = http_client.poll_batch_results(
                    self.host,
                    batch_uuid,
                    self.api_key,
                    self.target,
                    self.poll_interval,
                    self.stream_timeout,
                    self.max_retries,
                    self.verify_ssl,
                )
                logger.debug(f"Received {len(job_results)} results via polling")
        else:
            logger.info("Using HTTP polling mode")
            job_results = http_client.poll_batch_results(
                self.host,
                batch_uuid,
                self.api_key,
                self.target,
                self.poll_interval,
                self.stream_timeout,
                self.max_retries,
                self.verify_ssl,
            )
            logger.debug(f"Received {len(job_results)} results via polling")

        # 4. Validate results
        result_formatter.validate_results(job_results, len(circuits))

        # 5. Convert to PennyLane format
        results = [
            result_formatter.process_result(result, circuit)
            for result, circuit in zip(job_results, circuits)
        ]

        logger.info(f"Successfully executed {len(results)} circuit(s)")
        return tuple(results)

    def _prepare_jobs(self, circuits: Sequence[QuantumScript]) -> Dict[str, Any]:
        """
        Prepare jobs data for Cloud API v2 submission.

        Args:
            circuits: List of quantum circuits

        Returns:
            Jobs data in Cloud API v2 format
        """
        jobs = []

        for circuit in circuits:
            qasm_str = qml.to_openqasm(circuit)
            shots_value = self.shots.total_shots  # shots=None은 __init__에서 차단됨

            job = {"type": "qasm", "circuit": qasm_str, "shots": shots_value}

            jobs.append(job)

        return {"jobs": jobs}


class KQEmulatorDevice(KQCloudV2Device):
    """PennyLane device for KQ Emulator.

    Same API/auth/execution as KQCloudV2Device. See parent class for full parameter docs.
    """

    short_name = "kq.emulator"

    @property
    def name(self) -> str:
        return "KQ Emulator Device"

    operations = {
        "Identity",
        "BasisState",
        "QubitStateVector",
        "StatePrep",
        "QubitUnitary",
        "ControlledQubitUnitary",
        "MultiControlledX",
        "DiagonalQubitUnitary",
        "PauliX",
        "PauliY",
        "PauliZ",
        "MultiRZ",
        "Hadamard",
        "S",
        "Adjoint(S)",
        "T",
        "Adjoint(T)",
        "SX",
        "Adjoint(SX)",
        "CNOT",
        "SWAP",
        "ISWAP",
        "PSWAP",
        "Adjoint(ISWAP)",
        "SISWAP",
        "Adjoint(SISWAP)",
        "SQISW",
        "CSWAP",
        "Toffoli",
        "CY",
        "CZ",
        "PhaseShift",
        "ControlledPhaseShift",
        "CPhase",
        "RX",
        "RY",
        "RZ",
        "Rot",
        "CRX",
        "CRY",
        "CRZ",
        "CRot",
        "IsingXX",
        "IsingYY",
        "IsingZZ",
        "IsingXY",
        "SingleExcitation",
        "SingleExcitationPlus",
        "SingleExcitationMinus",
        "DoubleExcitation",
        "DoubleExcitationPlus",
        "DoubleExcitationMinus",
        "QubitCarry",
        "QubitSum",
        "OrbitalRotation",
        "QFT",
        "ECR",
    }

    observables = {
        "PauliX",
        "PauliY",
        "PauliZ",
        "Hadamard",
        "Hermitian",
        "Identity",
        "Projector",
        "SparseHamiltonian",
        "Hamiltonian",
        "Sum",
        "SProd",
        "Prod",
        "Exp",
    }
