"""
HTTP Client for Cloud API v2
============================

HTTP communication functions for batch job submission, SSE streaming, and polling.
"""

import json
import time
import random
import logging
from typing import Dict, Any, List, Tuple, Optional, Callable

import requests

logger = logging.getLogger(__name__)


def request_with_retry(
    request_func: Callable,
    max_retries: int = 3,
    retry_on_status: Optional[List[int]] = None,
):
    """
    Execute HTTP request with exponential backoff retry logic.

    Args:
        request_func: Function that performs the HTTP request
        max_retries: Maximum number of retries (default: 3)
        retry_on_status: HTTP status codes to retry on (default: 5xx errors)

    Returns:
        Response from request_func

    Raises:
        RuntimeError: If all retries fail
    """
    if retry_on_status is None:
        retry_on_status = list(range(500, 600))  # 5xx errors

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            response = request_func()

            # Check if status code should trigger retry
            if hasattr(response, "status_code"):
                if response.status_code in retry_on_status:
                    if attempt < max_retries:
                        wait_time = (2**attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"Request failed with status {response.status_code}. "
                            f"Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise RuntimeError(
                            f"Request failed after {max_retries} retries: "
                            f"{response.status_code} {response.text}"
                        )

            # Success
            return response

        except (requests.ConnectionError, requests.Timeout) as e:
            last_exception = e

            if attempt < max_retries:
                wait_time = (2**attempt) + random.uniform(0, 1)
                logger.warning(
                    f"Request failed: {type(e).__name__}: {e}. "
                    f"Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
            else:
                raise RuntimeError(
                    f"Request failed after {max_retries} retries: {type(e).__name__}: {e}"
                )

        except Exception as e:
            # Don't retry on unexpected exceptions
            logger.error(f"Unexpected error during request: {e}")
            raise RuntimeError(f"Request failed: {type(e).__name__}: {e}")

    # Should never reach here, but just in case
    raise RuntimeError(f"Request failed after {max_retries} retries: {last_exception}")


def submit_batch(
    host: str,
    jobs_data: Dict[str, Any],
    api_key: str,
    target: str,
    max_retries: int = 3,
    verify_ssl: bool = True,
) -> Tuple[str, List[str]]:
    """
    Submit batch of jobs to KRISS API with automatic retry.

    Args:
        host: API host URL (e.g., "http://localhost:8080")
        jobs_data: Jobs data in API format
        api_key: QCC-API-KEY header value
        target: QCC-TARGET header value
        max_retries: Maximum number of retries (default: 3)
        verify_ssl: Whether to verify SSL certificates (default: True)

    Returns:
        Tuple of (batch_uuid, list of job_uuids)

    Raises:
        RuntimeError: If submission fails after all retries
    """
    url = f"{host}/kriss/batch-jobs"
    headers = {
        "Content-Type": "application/json",
        "QCC-API-KEY": api_key,
        "QCC-TARGET": target,
    }

    def submit_request():
        return requests.post(
            url, json=jobs_data, headers=headers, timeout=30.0, verify=verify_ssl
        )

    try:
        response = request_with_retry(submit_request, max_retries=max_retries)

        if response.status_code != 200:
            error_msg = (
                f"Batch submission failed: {response.status_code} {response.text}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        result = response.json()
        batch_uuid = result["batch_uuid"]
        job_uuids = [job["job_uuid"] for job in result["jobs"]]

        return batch_uuid, job_uuids

    except Exception as e:
        error_msg = f"Batch submission error: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def stream_batch_results(
    host: str, batch_uuid: str, stream_timeout: float = 1800.0, verify_ssl: bool = True
) -> List[Dict[str, Any]]:
    """
    Stream batch results via SSE.

    Args:
        host: Cloud API v2 host URL (e.g., "http://localhost:8080")
        batch_uuid: Batch UUID
        stream_timeout: SSE timeout in seconds (default: 1800.0)
        verify_ssl: Whether to verify SSL certificates (default: True)

    Returns:
        List of job results

    Raises:
        RuntimeError: If SSE stream fails
    """
    url = f"{host}/api/stream/batch/{batch_uuid}"
    headers = {"Accept": "text/event-stream"}

    logger.info(f"Starting SSE stream: {url}")

    try:
        response = requests.get(
            url, stream=True, headers=headers, timeout=stream_timeout, verify=verify_ssl
        )

        if response.status_code != 200:
            error_msg = f"SSE stream failed: {response.status_code} {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Parse SSE events
        event_type = None
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue

            # SSE format: "event: <type>\ndata: <json>"
            if line.startswith("event: "):
                event_type = line[7:]  # Remove "event: "
                continue

            if line.startswith("data: "):
                event_data_str = line[6:]  # Remove "data: "

                try:
                    event_data = json.loads(event_data_str)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in SSE data: {event_data_str}")
                    continue

                # Handle different event types
                if event_type == "connected":
                    logger.debug(f"SSE connected: {event_data}")

                elif event_type == "progress":
                    # Job progress update
                    logger.debug(f"Progress update: {event_data}")

                elif event_type == "completed":
                    # Batch completed - extract all results
                    logger.info("Batch completed")

                    # Cloud API v2 returns data in nested structure
                    batch_data = event_data.get("data", {})
                    jobs = batch_data.get("jobs", [])

                    if not jobs:
                        # Try alternative format
                        jobs = event_data.get("jobs", [])

                    logger.info(f"Received {len(jobs)} job results")
                    return jobs

                elif event_type == "error":
                    error_msg = event_data.get("error", "Unknown error")
                    logger.error(f"SSE error event: {error_msg}")
                    raise RuntimeError(f"SSE stream error: {error_msg}")

                elif event_type == "timeout":
                    logger.error("SSE stream timeout")
                    raise RuntimeError("SSE stream timeout")

                elif event_type == "keepalive":
                    # Ignore keepalive events
                    pass

        # If we reach here, stream ended without completion
        error_msg = "SSE stream ended without completion event"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    except requests.Timeout as e:
        error_msg = f"SSE stream timeout after {stream_timeout}s: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    except requests.ConnectionError as e:
        error_msg = f"SSE connection lost: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during SSE streaming: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def poll_batch_results(
    host: str,
    batch_uuid: str,
    api_key: str,
    target: str,
    poll_interval: float = 2.0,
    max_wait: float = 1800.0,
    max_retries: int = 3,
    verify_ssl: bool = True,
) -> List[Dict[str, Any]]:
    """
    Poll batch results via HTTP GET (two-phase: status check then results fetch).

    Phase 1: Poll GET /kriss/batch-jobs/{uuid} until status == "COMPLETED"
    Phase 2: Fetch GET /kriss/batch-jobs/{uuid}/results and return sorted results

    Args:
        host: API host URL (e.g., "http://localhost:8080")
        batch_uuid: Batch UUID
        api_key: QCC-API-KEY header value
        target: QCC-TARGET header value
        poll_interval: Time between polls in seconds (default: 2.0)
        max_wait: Maximum wait time in seconds (default: 1800.0)
        max_retries: Maximum retries per request (default: 3)
        verify_ssl: Whether to verify SSL certificates (default: True)

    Returns:
        List of job results sorted by sequence_number

    Raises:
        RuntimeError: If polling fails or times out
    """
    status_url = f"{host}/kriss/batch-jobs/{batch_uuid}"
    results_url = f"{host}/kriss/batch-jobs/{batch_uuid}/results"
    headers = {
        "QCC-API-KEY": api_key,
        "QCC-TARGET": target,
    }

    logger.info(f"Starting HTTP polling: {status_url}")

    start_time = time.time()

    # Phase 1: Poll until COMPLETED
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            raise RuntimeError(f"Polling timeout after {max_wait}s")

        try:

            def status_request():
                return requests.get(
                    status_url, headers=headers, timeout=30.0, verify=verify_ssl
                )

            response = request_with_retry(status_request, max_retries=max_retries)

            if response.status_code == 404:
                logger.debug(
                    f"Batch not yet available (404), retrying in {poll_interval}s"
                )
                time.sleep(poll_interval)
                continue

            if response.status_code != 200:
                error_msg = (
                    f"Batch status query failed: {response.status_code} {response.text}"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            batch_data = response.json()
            status = batch_data.get("status")
            completed = batch_data.get("completed_count", 0)
            total = batch_data.get("total_count", 0)

            logger.debug(f"Poll status: {status} ({completed}/{total} completed)")

            if status == "COMPLETED":
                logger.info("Batch completed, fetching results")
                break

            elif status == "FAILED":
                error_msg = batch_data.get("error_message", "Batch failed")
                logger.error(f"Batch failed: {error_msg}")
                raise RuntimeError(f"Batch failed: {error_msg}")

            time.sleep(poll_interval)

        except RuntimeError:
            raise

        except Exception as e:
            error_msg = f"Unexpected error during polling: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    # Phase 2: Fetch results
    try:

        def results_request():
            return requests.get(
                results_url, headers=headers, timeout=30.0, verify=verify_ssl
            )

        response = request_with_retry(results_request, max_retries=max_retries)

        if response.status_code != 200:
            error_msg = f"Results fetch failed: {response.status_code} {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        results_data = response.json()
        results = results_data.get("results", [])

        # Sort by sequence_number to guarantee submission order
        results = sorted(results, key=lambda r: r["sequence_number"])

        logger.info(f"Received {len(results)} job results")
        return results

    except RuntimeError:
        raise

    except Exception as e:
        error_msg = f"Unexpected error fetching results: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
