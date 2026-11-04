"""Offline HTTP contract tests; no remote jobs are submitted."""

import unittest
from unittest.mock import Mock, call, patch

from pennylane_kq.utils.http_client import poll_batch_results, submit_batch


class HTTPHeaderTests(unittest.TestCase):
    def test_submission_uses_qc_headers(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "batch_uuid": "batch",
            "jobs": [{"job_uuid": "job"}],
        }
        jobs = {"jobs": [{"type": "qasm", "circuit": "test", "shots": 100}]}

        with patch(
            "pennylane_kq.utils.http_client.requests.post", return_value=response
        ) as post:
            result = submit_batch(
                "https://example.invalid", jobs, "test-key", "test-target"
            )

        self.assertEqual(result, ("batch", ["job"]))
        post.assert_called_once_with(
            "https://example.invalid/kriss/batch-jobs",
            json=jobs,
            headers={
                "Content-Type": "application/json",
                "QC-API-KEY": "test-key",
                "QC-TARGET": "test-target",
            },
            timeout=30.0,
            verify=True,
        )

    def test_polling_and_results_use_qc_headers(self):
        pending = Mock(status_code=200)
        pending.json.return_value = {"status": "RUNNING"}
        completed = Mock(status_code=200)
        completed.json.return_value = {"status": "COMPLETED"}
        results = Mock(status_code=200)
        jobs = [{"sequence_number": 1}, {"sequence_number": 0}]
        results.json.return_value = {"results": jobs}

        with patch(
            "pennylane_kq.utils.http_client.requests.get",
            side_effect=[pending, completed, results],
        ) as get, patch("pennylane_kq.utils.http_client.time.sleep"):
            result = poll_batch_results(
                "https://example.invalid", "batch", "test-key", "test-target"
            )

        self.assertEqual(result, [jobs[1], jobs[0]])
        headers = {"QC-API-KEY": "test-key", "QC-TARGET": "test-target"}
        status_call = call(
            "https://example.invalid/kriss/batch-jobs/batch",
            headers=headers,
            timeout=30.0,
            verify=True,
        )
        self.assertEqual(
            get.call_args_list,
            [
                status_call,
                status_call,
                call(
                    "https://example.invalid/kriss/batch-jobs/batch/results",
                    headers=headers,
                    timeout=30.0,
                    verify=True,
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
