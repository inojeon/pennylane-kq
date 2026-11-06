# PennyLane-KQ Device User Guide

PennyLane-KQ provides two public devices for use from the KISTI cloud service's
Jupyter notebooks:

| Device | Class | Target | Resource |
| --- | --- | --- | --- |
| `kq.emulator` | `KQEmulatorDevice` | `kisti.sim1` | Simulator |
| `kq.emulator` | `KQEmulatorDevice` | `kisti.emulator` | KISTI emulator |
| `kq.qpu` | `KQQPUDevice` | `kriss.hw_20q` | KRISS 20-qubit QPU |
| `kq.qpu` | `KQQPUDevice` | `kriss.hw_50q` | KRISS 50-qubit QPU |

Both devices use the internal `_KQBaseDevice` for preprocessing, OpenQASM 2
serialization, submission, and result formatting. It is not a public device.
For existing notebooks using the removed cloudv2 interface, follow the
[migration instructions](README.md#migrating-existing-notebooks).

## Installation

Install from a local checkout with PennyLane >= 0.40:

```bash
python -m pip install -e .
```

Restart the Jupyter kernel after updating or reinstalling the package so
PennyLane reloads its device registrations.

## Emulator example

Replace `"your-api-key"` with your cloud service API key before running this
example. Creating a device does not submit a job; calling the QNode does.

```python
import pennylane as qml

dev = qml.device(
    "kq.emulator",
    wires=2,
    shots=1024,
    api_key="your-api-key",
    target="kisti.emulator",
)

@qml.qnode(dev)
def bell():
    qml.Hadamard(0)
    qml.CNOT([0, 1])
    return qml.counts(wires=[0, 1])

counts = bell()  # Submits a remote emulator job.
print(counts)
```

To run on the simulator local to the cloud service, use the same device with
`target="kisti.sim1"`:

```python
local_sim = qml.device(
    "kq.emulator",
    wires=2,
    shots=1024,
    api_key="your-api-key",
    target="kisti.sim1",
)
```

Both targets use the cloud API. The `QC-TARGET` header selects which simulator
the service uses. For `kisti.sim1`, execution takes place on the cloud server;
the notebook submits the circuit and receives the results.

## QPU configuration

Use `kq.qpu` with either KRISS target and an explicit wire count or wire labels:

```python
qpu = qml.device(
    "kq.qpu",
    wires=2,
    shots=1024,
    api_key="your-api-key",
    target="kriss.hw_20q",
)
```

The plugin validates nominal limits of 20 or 50 wires. The server determines
actual availability, native gates, topology, calibration, routing, and physical
qubit mapping. Device wires are logical labels. Gate and observable lists on
the classes are legacy metadata, not enforced native gate sets.

## Parameters

| Parameter | Default | Meaning |
| --- | --- | --- |
| `wires` | `None` | Wire count or labels; required for QPU |
| `shots` | Required | One positive integer; analytic execution and shot vectors are unsupported |
| `api_key` | Required | API credential sent in the `QC-API-KEY` header |
| `target` | Required | Device code sent in the `QC-TARGET` header |
| `host` | `https://qc-api.kisti.re.kr` | KISTI cloud service URL |
| `use_streaming` | `False` | Opt into SSE with HTTP polling fallback |
| `poll_interval` | `2.0` | Seconds between HTTP polls |
| `stream_timeout` | `1800.0` | Total polling wait limit in seconds; also used as the SSE timeout |
| `max_retries` | `3` | Request retries after transient failures |
| `verify_ssl` | `True` | Verify the server's TLS certificate |

HTTP polling is the default for the production service. The optional SSE path
requires server support. A timeout stops waiting locally; it does not cancel
the server job.

## Measurements and batches

The service returns counts. The plugin supports sample-based measurements such
as counts, samples, probabilities, expectation values, and variances. Analytic
measurements such as `qml.state()` are rejected before submission.

Preprocessing expands parameter broadcasts and splits incompatible
measurements into separate circuits. Compatible measurements may share a tape;
a QNode returning several measurements receives a tuple of results.

For direct batch execution, put a finite shot count on each `QuantumScript`:

```python
from pennylane.tape import QuantumScript

tapes = [
    QuantumScript(
        [qml.Hadamard(0), qml.CNOT([0, 1])],
        [qml.counts(wires=[0, 1])],
        shots=1024,
    ),
    QuantumScript(
        [qml.X(0)],
        [qml.counts(wires=[0, 1])],
        shots=512,
    ),
]
results = dev.execute(tapes)  # Submits remote jobs; returns one result per tape.
```

QNodes apply the preprocessing pipeline automatically. Direct `execute()` calls
expect tapes with compatible measurements and no unexpanded broadcasts.

## Service flow

The plugin sends OpenQASM 2 batches to the KISTI cloud service at
`https://qc-api.kisti.re.kr/kriss/batch-jobs`. Submission, status, and result
requests carry `QC-API-KEY` and `QC-TARGET`. For QPU jobs, the cloud service
routes execution to KRISS `emulator_api`, which uses krios.
Jobs targeting `kisti.sim1` run on the simulator local to the cloud service.

## Verification and troubleshooting

Run the offline suites listed in [README testing](README.md#testing). They use
mocked HTTP responses and do not certify production routing or hardware
availability. Files prefixed `test_` are offline tests; files prefixed
`example_` or `benchmark_` submit remote jobs when executed. See the
[execution examples](README.md#execution-examples-and-benchmarks) for commands.

- **Device not found:** reinstall the checkout with `python -m pip install -e .`
  and restart the Jupyter kernel. Use `kq.emulator` or `kq.qpu`.
- **Authentication or target error:** check the credential and target code with
  the cloud service. Replace `"your-api-key"` with your issued API key.
- **Timeout:** check the submitted job's status in the cloud service. Increase
  `stream_timeout` for longer queues; the timed-out job may still be running.
- **SSE error:** use `use_streaming=False` for HTTP polling.
