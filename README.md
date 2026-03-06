# PennyLane-KQ

PennyLane plugin for KISTI Quantum Cloud API v2.

## Overview

**pennylane-kq** provides a PennyLane device (`kq.cloudv2`) for executing quantum circuits on KISTI's quantum computing cloud infrastructure.

### Features

- Execute PennyLane circuits on remote quantum hardware/emulator
- Real-time SSE (Server-Sent Events) streaming with automatic fallback to HTTP polling
- Batch job submission
- Automatic retry with exponential backoff

## Installation

### From Source

```bash
pip install git+https://github.com/inojeon/pennylane-kq.git
```
or
```bash
pip install https://github.com/inojeon/pennylane-kq/releases/download/v0.0.29/pennylane_kq-0.0.29-py3-none-any.whl
```

### From PyPI (Coming Soon)

```bash
pip install pennylane-kq
```

## Requirements

- Python >= 3.8
- PennyLane >= 0.40
- KISTI Quantum Cloud API key (`api_key`)

## Quick Start

```python
import pennylane as qml

# Create device
dev = qml.device('kq.cloudv2',
                 wires=2,
                 shots=1024,
                 api_key="your-api-key",
                 target="kisti.sim1")

# Define circuit
@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# Execute
result = circuit()
print(f"Expectation value: {result}")
```

## Device Parameters

- `wires` (int, required): Number of qubits
- `shots` (int, required): Number of shots (statevector mode is not supported)
- `api_key` (str, required): QCC-API-KEY for authentication
- `target` (str, required): QCC-TARGET device code
- `host` (str): Cloud API v2 URL (default: "https://qc-api.kisti.re.kr")
- `use_streaming` (bool): Use SSE streaming (default: False)
- `stream_timeout` (float): SSE timeout in seconds (default: 1800.0)
- `poll_interval` (float): Polling interval in seconds (default: 2.0)
- `max_retries` (int): Maximum retries for failed requests (default: 3)

## Examples

```python
dev = qml.device('kq.cloudv2',
                 wires=2,
                 shots=1024,
                 api_key="your-api-key",
                 target="kisti.sim1")

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.sample(qml.PauliZ(0))

samples = circuit()  # Returns numpy array of 1024 samples
```

## Documentation

- **Developer Guide**: [CLAUDE.md](CLAUDE.md) - Comprehensive developer documentation
- **API Specification**: [docs/API_SPECIFICATION_QCC.md](docs/API_SPECIFICATION_QCC.md) - API details

## Testing

Run basic tests:
```bash
python tests/test_kq_cloudv2_basic.py
```

Run integration tests (requires valid `api_key` and `target`):
```bash
python tests/test_kq_cloudv2_integration.py
```

## Troubleshooting

### SSE Streaming Fails

SSE Streaming is not available now. 
Please use HTTP polling mode instead. (`use_streaming=False`)
### Device Not Found Error

If you get `DeviceError: Device 'kq.cloudv2' not found`, make sure the package is installed:

```bash
pip install -e .
python -c "from pennylane_kq import KQCloudV2Device; print('OK')"
```

### Authentication Error

If you get an authentication error, check that your `api_key` and `target` are correct:

```python
dev = qml.device('kq.cloudv2',
                 wires=2,
                 shots=1024,
                 api_key="your-api-key",   # Check this
                 target="kisti.sim1")       # Check this
```



## Version

Current version: **0.0.29**

## Authors

**KISTI Quantum Computing Team**

Korea Institute of Science and Technology Information (KISTI)

## License

BSD-2-Clause

## Contributing

For development setup and guidelines, see [CLAUDE.md](CLAUDE.md).

## Support

For issues and questions:
- GitHub Issues: https://github.com/inojeon/pennylane-kq/issues
- Contact: inojeon@kisti.re.kr / soyeongp@kisti.re.kr
