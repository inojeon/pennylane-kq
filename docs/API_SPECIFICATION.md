# Cloud API v2 Specification

This document describes the REST API specification used by **pennylane-kq** to communicate with the KISTI Quantum Cloud API v2.

---

## Base URL

```
http://localhost:8080
```

For production deployments, replace with your actual Cloud API v2 server URL.

---

## Authentication

**Current version**: No authentication required

**Future versions**: May require API keys via HTTP headers

---

## Endpoints

### 1. Submit Batch Job

**Endpoint**: `POST /api/jobs`

**Description**: Submit a batch of quantum circuit jobs for execution

**Request Headers**:
```http
Content-Type: application/json
```

**Request Body**:
```json
{
  "jobs": [
    {
      "type": "json",
      "circuit": {
        "operations": [
          {
            "name": "Hadamard",
            "wires": [0],
            "params": []
          },
          {
            "name": "CNOT",
            "wires": [0, 1],
            "params": []
          }
        ],
        "measurements": [
          {
            "type": "expval",
            "obs": {
              "type": "Simple",
              "name": "PauliZ",
              "wires": [0]
            }
          }
        ],
        "shots": 1024,
        "batch_size": null,
        "wires": [0, 1],
        "num_wires": 2,
        "trainable_params": null
      },
      "shots": 1024
    }
  ]
}
```

**Request Body Schema**:
```typescript
interface BatchJobRequest {
  jobs: Job[];
}

interface Job {
  type: "json";           // Circuit type (always "json" for PennyLane)
  circuit: Circuit;       // Serialized quantum circuit
  shots?: number | null;  // Number of shots (null for state vector)
}

interface Circuit {
  operations: Operation[];
  measurements: Measurement[];
  shots?: number | null;
  batch_size?: number | null;
  wires: number[];
  num_wires: number;
  trainable_params?: number[] | null;
}

interface Operation {
  name: string;      // Gate name (e.g., "Hadamard", "CNOT", "RY")
  wires: number[];   // Wire indices
  params: number[];  // Gate parameters (e.g., rotation angles)
}

interface Measurement {
  type: "expval" | "var" | "sample" | "probs" | "counts";
  obs?: Observable | null;  // Observable (optional for some measurements)
}

interface Observable {
  type: "Simple" | "Hamiltonian" | "Tensor";
  name?: string;           // For Simple observables
  wires?: number[];        // For Simple observables
  coeffs?: number[];       // For Hamiltonian
  obs?: Observable[];      // For Hamiltonian or Tensor
}
```

**Success Response (201 Created)**:
```json
{
  "batch_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "job_uuids": [
    "660e8400-e29b-41d4-a716-446655440000"
  ],
  "status": "submitted",
  "created_at": "2025-01-01T00:00:00.000000Z"
}
```

**Response Schema**:
```typescript
interface BatchJobResponse {
  batch_uuid: string;    // UUID for the entire batch
  job_uuids: string[];   // UUIDs for individual jobs
  status: "submitted";   // Initial status
  created_at: string;    // ISO 8601 timestamp
}
```

**Error Responses**:

**400 Bad Request**:
```json
{
  "detail": "Invalid circuit format: missing required field 'operations'"
}
```

**422 Unprocessable Entity** (Pydantic validation error):
```json
{
  "detail": [
    {
      "loc": ["body", "jobs", 0, "circuit", "operations"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Internal server error"
}
```

---

### 2. Stream Batch Results (SSE)

**Endpoint**: `GET /api/stream/batch/{batch_uuid}`

**Description**: Stream job status updates and results via Server-Sent Events (SSE)

**Path Parameters**:
- `batch_uuid` (string): UUID of the batch (from POST response)

**Request Headers**:
```http
Accept: text/event-stream
```

**Response**: SSE stream (text/event-stream)

**SSE Event Format**:
```
event: job.created
data: {"job_uuid": "660e8400-e29b-41d4-a716-446655440000", "status": "created"}

event: job.running
data: {"job_uuid": "660e8400-e29b-41d4-a716-446655440000", "status": "running"}

event: job.completed
data: {"job_uuid": "660e8400-e29b-41d4-a716-446655440000", "status": "completed", "result": {...}}

event: batch.completed
data: {"batch_uuid": "550e8400-e29b-41d4-a716-446655440000", "status": "completed", "jobs": [...]}
```

**Event Types**:
- `job.created`: Job was created and queued
- `job.running`: Job execution started
- `job.completed`: Job execution completed (includes result)
- `job.failed`: Job execution failed (includes error)
- `batch.completed`: All jobs in batch completed

**Job Completed Event Data**:
```json
{
  "job_uuid": "660e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "measurement_type": "expval",
    "value": 0.5
  }
}
```

**Batch Completed Event Data**:
```json
{
  "batch_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "jobs": [
    {
      "job_uuid": "660e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "result": {
        "measurement_type": "expval",
        "value": 0.5
      }
    }
  ]
}
```

**Error Responses**:

**404 Not Found**:
```json
{
  "detail": "Batch not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

**Connection Timeout**: SSE connection will close after `stream_timeout` seconds (default: 1800 seconds)

---

### 3. Poll Batch Results (HTTP)

**Endpoint**: `GET /api/batches/{batch_uuid}`

**Description**: Poll for batch job status and results (fallback for SSE)

**Path Parameters**:
- `batch_uuid` (string): UUID of the batch

**Request Headers**: None required

**Success Response (200 OK)**:
```json
{
  "batch_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-01-01T00:00:00.000000Z",
  "completed_at": "2025-01-01T00:01:30.000000Z",
  "jobs": [
    {
      "job_uuid": "660e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "created_at": "2025-01-01T00:00:00.000000Z",
      "completed_at": "2025-01-01T00:01:30.000000Z",
      "result": {
        "measurement_type": "expval",
        "value": 0.5
      }
    }
  ]
}
```

**Response Schema**:
```typescript
interface BatchStatusResponse {
  batch_uuid: string;
  status: "submitted" | "running" | "completed" | "failed";
  created_at: string;
  completed_at?: string | null;
  jobs: JobStatus[];
}

interface JobStatus {
  job_uuid: string;
  status: "created" | "running" | "completed" | "failed";
  created_at: string;
  completed_at?: string | null;
  result?: JobResult | null;
  error?: string | null;
}

interface JobResult {
  measurement_type: string;
  value: any;  // Type depends on measurement_type
}
```

**Status Values**:
- `submitted`: Batch/job received, waiting to be processed
- `running`: Batch/job is currently executing
- `completed`: Batch/job finished successfully
- `failed`: Batch/job failed with error

**Error Responses**:

**404 Not Found**:
```json
{
  "detail": "Batch not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 4. Health Check

**Endpoint**: `GET /api/health`

**Description**: Check API server health

**Request Headers**: None required

**Success Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00.000000Z"
}
```

---

## Result Formats

### Expectation Value (expval)

```json
{
  "measurement_type": "expval",
  "value": 0.5
}
```

**Type**: `float` (range: -1.0 to 1.0)

**PennyLane Result**: `float`

---

### Variance (var)

```json
{
  "measurement_type": "var",
  "value": 0.25
}
```

**Type**: `float` (range: 0.0 to 1.0)

**PennyLane Result**: `float`

---

### Samples (sample)

```json
{
  "measurement_type": "sample",
  "value": [1, -1, 1, 1, -1, ...]
}
```

**Type**: `array` of eigenvalues (typically ±1 for Pauli observables)

**Length**: Equal to `shots` parameter

**PennyLane Result**: `numpy.ndarray` of shape `(shots,)`

---

### Probabilities (probs)

```json
{
  "measurement_type": "probs",
  "value": [0.5, 0.0, 0.0, 0.5]
}
```

**Type**: `array` of floats (probabilities sum to 1.0)

**Length**: `2^n` where `n` is number of wires

**PennyLane Result**: `numpy.ndarray` of shape `(2^n,)`

---

### Counts (counts)

```json
{
  "measurement_type": "counts",
  "value": {
    "0x0": 512,
    "0x3": 512
  }
}
```

**Type**: `object` mapping state strings to counts

**State Format**: Hex strings (e.g., "0x0", "0x3") or binary strings (e.g., "00", "11")

**PennyLane Result**: `dict` mapping states to counts

**Note**: pennylane-kq automatically handles both hex and binary formats

---

## Error Codes

| Status Code | Meaning | When It Occurs |
|-------------|---------|----------------|
| 200 | OK | Successful GET request |
| 201 | Created | Successful POST (batch created) |
| 400 | Bad Request | Invalid request format |
| 404 | Not Found | Batch UUID not found |
| 422 | Unprocessable Entity | Pydantic validation error |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Server overloaded or down |

---

## Rate Limiting

**Current version**: No rate limiting

**Future versions**: May implement rate limiting with headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

---

## Best Practices

### 1. Prefer SSE Streaming

Use SSE streaming (`use_streaming=True`) for:
- Real-time status updates
- Long-running jobs
- Better user experience

Use HTTP polling (`use_streaming=False`) only when:
- RabbitMQ is unavailable
- SSE is blocked by firewall
- Simple debugging

### 2. Handle Timeouts Gracefully

Set appropriate timeouts:
```python
dev = qml.device('kq.cloudv2',
                 wires=2,
                 stream_timeout=3600.0,  # 1 hour for large circuits
                 poll_interval=1.0)      # Check every 1 second
```

### 3. Batch Multiple Circuits

Submit multiple circuits in one batch:
```python
# pennylane-kq automatically batches circuits from the same QNode
@qml.qnode(dev)
def circuit(theta):
    qml.RY(theta, wires=0)
    return qml.expval(qml.PauliZ(0))

# These will be batched into one API call
results = [circuit(theta) for theta in [0.0, 0.5, 1.0]]
```

### 4. Check Health Before Submission

```python
import requests

health = requests.get("http://localhost:8080/api/health")
if health.status_code == 200:
    # Submit jobs
    pass
else:
    # Server is down
    pass
```

### 5. Handle Connection Errors

```python
try:
    result = circuit()
except RuntimeError as e:
    if "Cannot connect" in str(e):
        # Server is unreachable
        pass
    elif "timed out" in str(e):
        # Job took too long
        pass
```

---

## Example: Complete Workflow

```python
import pennylane as qml
import requests

# 1. Check server health
health = requests.get("http://localhost:8080/api/health")
assert health.status_code == 200

# 2. Create device
dev = qml.device('kq.cloudv2',
                 wires=2,
                 shots=1024,
                 host="http://localhost:8080",
                 use_streaming=True)

# 3. Define circuit
@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# 4. Execute (device handles API calls internally)
result = circuit()

# 5. Use result
print(f"Expectation value: {result}")
```

---

## Related Documentation

- **Cloud API v2**: `/cloud_v2/CLAUDE.md` in parent project
- **Emulator API**: `/emulator_api/CLAUDE.md` in parent project
- **pennylane-kq Developer Guide**: [CLAUDE.md](../CLAUDE.md)

---

**API Version**: v2
**Document Version**: 1.0
**Last Updated**: 2025-11-06
