# job 제출 OpenAPI API 명세서

## 1. 작업 제출
HTTP Method : POST
Path: kriss/batch-jobs
Headers: 
    {Content-Type: application/json
    QCC-API-KEY: API Key
    QCC-TARGET: Device Code}
Request Body: 
이름 | 형식 | 필수 여부 | 설명
jobs | List[Object] | 필수 | Job 정보의 Object 데이터
jobs.circuit | String | 필수 | 회로 정보
jobs.shots | Integer | 필수 | shot 수
jobs.type | Integer | 필수 | 포맷 타입
### 예시
POST {{host}}/kriss/batch-jobs
Content-Type: application/json
QCC-API-KEY: 7UQdc67W4G-7-i5ux6tT1dSG3IdU7NXQorsHUBgWQ8
QCC-TARGET: kisti.sim1

{
  "jobs": [
    {
      "circuit": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;",
      "shots": 1024,
      "type": "qasm"
    },
    {
      "circuit": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;",
      "shots": 1024,
      "type": "qasm"
    }
  ]
}
### 응답
HTTP Response code: 20
Response Body: 
    이름 | 형식 | 설명
    batch_uuid | String | 작업의 batch uuid 값
    status | String | 작업의 상태
    total_count | Integer | 제출한 작업 수
    completed_count | Integer | 완료된 작업 수
    failed_count | Integer | 실패한 작업 수
    pending_count | Integer | 대기 작업 수
    running_count | Integer | 실행 작업 수
    created_at | String | 제출 시간
    completed_at | String | 완료 시간
    jobs | List[Object] | 작업 정보의 Object 데이터
    jobs.job_uuid | String | 작업 uuid
    jobs.batch_uuid | String | 작업의 batch uuid
    jobs.sequence_number | Integer | 작업 인식 번호
    jobs.status | String | 작업의 상태
    jobs.type | String | 작업 유형
    jobs.shots | Integer | 작업 shot 정보
    jobs.backend | String | 작업의 backend
    jobs.created_at | String | 작업 생성시간
    jobs.started_at | String | 작업 처리 시작 시간
    jobs.completed_at | String | 작업 완료 시간
    jobs.result | Object | 작업 결과의 Object 데이터
    jobs.result.counts | Object | 작업 결과 데이터
    jobs.error_message | String | 작업의 에러 메시지
    jobs.execution_time | String | 작업 실행 시간
### 응답 예시
Status Code: 200
Response Body:
{
  "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
  "status": "PENDING",
  "jobs": [
    {
      "job_uuid": "e2c44f1e-7789-4048-a8a7-b25dc39ba87f",
      "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
      "sequence_number": 1,
      "status": "CREATED",
      "type": "qasm",
      "shots": 1024,
      "backend": "default.qubit",
      "created_at": "2026-01-30T03:03:29",
      "started_at": null,
      "completed_at": null,
      "result": null,
      "error_message": null,
      "execution_time": null
    },
    {
      "job_uuid": "9b85d9a0-50b3-4681-831d-a493f44b0c2a",
      "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
      "sequence_number": 2,
      "status": "CREATED",
      "type": "qasm",
      "shots": 1024,
      "backend": "default.qubit",
      "created_at": "2026-01-30T03:03:29",
      "started_at": null,
      "completed_at": null,
      "result": null,
      "error_message": null,
      "execution_time": null
    },
    {
      "job_uuid": "916e9812-1a6e-44da-9b78-728c689637a5",
      "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
      "sequence_number": 3,
      "status": "CREATED",
      "type": "qasm",
      "shots": 1024,
      "backend": "default.qubit",
      "created_at": "2026-01-30T03:03:29",
      "started_at": null,
      "completed_at": null,
      "result": null,
      "error_message": null,
      "execution_time": null
    },
    {
      "job_uuid": "60d23b5f-9196-45b3-8201-fb54d51838ac",
      "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
      "sequence_number": 4,
      "status": "CREATED",
      "type": "qasm",
      "shots": 1024,
      "backend": "default.qubit",
      "created_at": "2026-01-30T03:03:29",
      "started_at": null,
      "completed_at": null,
      "result": null,
      "error_message": null,
      "execution_time": null
    }
  ],
  "total_count": 4,
  "completed_count": 0,
  "failed_count": 0,
  "pending_count": 4,
  "running_count": 0,
  "created_at": "2026-01-30T03:03:29",
  "completed_at": null
}

## 2. 배치 작업 상태 조회
HTTP Method : GET
Path: kriss/batch-jobs/{batch-id}
Path Variables:
    이름 | 값
    batch-id | batch의 uuid
Headers: 
    이름 | 값
    QCC-API-KEY | API Key
    QCC-TARGET | Device Code
### 예시
GET {{host}}/kriss/batch-jobs/60ea39f1-d3a3-4d40-8716-a610540c4f68
QCC-API-KEY: 7UQdc67W4G-7-i5ux6tT1dSG3IdU7NXQors_HUBgWQ8
QCC-TARGET: kisti.sim1
### 응답
HTTP Response Code: 200
Response Body:
    이름 | 형식 | 설명
    --- | --- | ---
    batch_uuid | String | 작업의 batch uuid 값
    status | String | 작업의 상태
    total_count | Integer | 제출한 작업 수
    completed_count | Integer | 완료된 작업 수
    failed_count | Integer | 실패한 작업 수
    pending_count | Integer | 대기 작업 수
    running_count | Integer | 실행 작업 수
    created_at | String | 제출 시간
    completed_at | String | 완료 시간
    jobs | List[Object] | 작업 정보의 Object 데이터
    jobs.job_uuid | String | 작업 uuid
    jobs.batch_uuid | String | 작업의 batch uuid
    jobs.sequence_number | Integer | 작업 인식 번호
    jobs.status | String | 작업의 상태
    jobs.type | String | 작업 유형
    jobs.shots | Integer | 작업 shot 정보
    jobs.backend | String | 작업의 backend
    jobs.created_at | String | 작업 생성시간
    jobs.started_at | String | 작업 처리 시작 시간
    jobs.completed_at | String | 작업 완료 시간
    jobs.result | Object | 작업 결과의 Object 데이터
    jobs.result.counts | Object | 작업 결과 데이터
    jobs.error_message | String | 작업의 에러 메시지
    jobs.execution_time | String | 작업 실행 시간
### 응답 예시
Status Code: 200
Response Body:
{
  "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
  "status": "COMPLETED",
  "jobs": [
    {
      "job_uuid": "e2c44f1e-7789-4048-a8a7-b25dc39ba87f",
      "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
      "sequence_number": 1,
      "status": "SUCCESS",
      "type": "qasm",
      "shots": 1024,
      "backend": "default.qubit",
      "created_at": "2026-01-30T03:03:29",
      "started_at": "2026-01-30T03:03:29.957277",
      "completed_at": "2026-01-30T03:03:30.368776",
      "result": {
        "counts": {
          "11": 529,
          "00": 495
        }
      },
      "error_message": null,
      "execution_time": 0.408785
    },
    {
      "job_uuid": "9b85d9a0-50b3-4681-831d-a493f44b0c2a",
      "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
      "sequence_number": 2,
      "status": "SUCCESS",
      "type": "qasm",
      "shots": 1024,
      "backend": "default.qubit",
      "created_at": "2026-01-30T03:03:29",
      "started_at": "2026-01-30T03:03:30.375385",
      "completed_at": "2026-01-30T03:03:30.748309",
      "result": {
        "counts": {
          "00": 489,
          "11": 535
        }
      },
      "error_message": null,
      "execution_time": 0.370496
    },
    {
      "job_uuid": "916e9812-1a6e-44da-9b78-728c689637a5",
      "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
      "sequence_number": 3,
      "status": "SUCCESS",
      "type": "qasm",
      "shots": 1024,
      "backend": "default.qubit",
      "created_at": "2026-01-30T03:03:29",
      "started_at": "2026-01-30T03:03:30.752434",
      "completed_at": "2026-01-30T03:03:31.131268",
      "result": {
        "counts": {
          "11": 526,
          "00": 498
        }
      },
      "error_message": null,
      "execution_time": 0.377547
    },
    {
      "job_uuid": "60d23b5f-9196-45b3-8201-fb54d51838ac",
      "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
      "sequence_number": 4,
      "status": "SUCCESS",
      "type": "qasm",
      "shots": 1024,
      "backend": "default.qubit",
      "created_at": "2026-01-30T03:03:29",
      "started_at": "2026-01-30T03:03:31.141937",
      "completed_at": "2026-01-30T03:03:31.521637",
      "result": {
        "counts": {
          "11": 509,
          "00": 515
        }
      },
      "error_message": null,
      "execution_time": 0.377258
    }
  ],
  "total_count": 4,
  "completed_count": 4,
  "failed_count": 0,
  "pending_count": 0,
  "running_count": 0,
  "created_at": "2026-01-30T03:03:29",
  "completed_at": "2026-01-30T03:03:31.526797"
}

## 3. 배치 작업 결과 조회
HTTP Method: GET
Path: kriss/batch-jobs/{batch-id}/results
Path Variables
    이름 | 값
    batch-id | batch의 uuid
Headers:
    이름 | 값
    QCC-API-KEY | API Key
    QCC-TARGET | Device Code
### 예시
GET {{host}}/kriss/batch-jobs/60ea39f1-d3a3-4d40-8716-a610540c4f68/results
QCC-API-KEY: 7UQdc67W4G-7-i5ux6tT1dSG3IdU7NXQors_HUBgWQ8
QCC-TARGET: kisti.sim1

### 응답
HTTP Response Code: 200
Response Body:
    이름 | 형식 | 설명
    --- | --- | ---
    batch_uuid | String | 작업의 batch uuid 값
    total_count | Integer | 제출한 작업 수
    completed_count | Integer | 완료된 작업 수
    failed_count | Integer | 실패한 작업 수
    completed_at | String | 완료 시간
    results | List[Object] | 작업 결과 Object 데이터
    results.job_uuid | String | 작업 uuid
    results.sequence_number | Integer | 작업 인식 번호
    results.status | String | 작업 상태
    results.type | String | 포맷 타입
    results.result | Object | 작업 결과
    results.result.counts | Object | 작업의 결과 데이터
    results.error_message | String | 작업 에러 메시지
    results.execution_time | Float | 작업 실행 시간

### 응답 예시
Status Code: 200
Response Body:
{
  "batch_uuid": "60ea39f1-d3a3-4d40-8716-a610540c4f68",
  "total_count": 4,
  "completed_count": 4,
  "failed_count": 0,
  "completed_at": "2026-01-30T03:03:31.526797",
  "results": [
    {
      "job_uuid": "e2c44f1e-7789-4048-a8a7-b25dc39ba87f",
      "sequence_number": 1,
      "status": "SUCCESS",
      "type": "qasm",
      "result": {
        "counts": {
          "11": 529,
          "00": 495
        }
      },
      "error_message": null,
      "execution_time": 0.408785
    },
    {
      "job_uuid": "9b85d9a0-50b3-4681-831d-a493f44b0c2a",
      "sequence_number": 2,
      "status": "SUCCESS",
      "type": "qasm",
      "result": {
        "counts": {
          "00": 489,
          "11": 535
        }
      },
      "error_message": null,
      "execution_time": 0.370496
    },
    {
      "job_uuid": "916e9812-1a6e-44da-9b78-728c689637a5",
      "sequence_number": 3,
      "status": "SUCCESS",
      "type": "qasm",
      "result": {
        "counts": {
          "11": 526,
          "00": 498
        }
      },
      "error_message": null,
      "execution_time": 0.377547
    },
    {
      "job_uuid": "60d23b5f-9196-45b3-8201-fb54d51838ac",
      "sequence_number": 4,
      "status": "SUCCESS",
      "type": "qasm",
      "result": {
        "counts": {
          "11": 509,
          "00": 515
        }
      },
      "error_message": null,
      "execution_time": 0.377258
    }
  ]
}