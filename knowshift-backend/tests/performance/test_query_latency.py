"""
Performance tests — query endpoint latency benchmarks.
Measures P50 / P95 / P99 latencies against a live API.

Run:
    TEST_API_URL=http://localhost:8000 pytest tests/performance/test_query_latency.py -v -s
"""

import os
import time
import statistics
import pytest

pytestmark = [pytest.mark.performance, pytest.mark.slow]

QUESTIONS = {
    "medical":   "What is the first-line treatment for Type 2 Diabetes?",
    "finance":   "What is the tax rate for income between Rs 10-12 lakhs?",
    "ai_policy": "What obligations do high-risk AI system providers have?",
}


class TestQueryLatency:
    """Latency benchmarks for /query/ask."""

    def test_single_query_under_15_seconds(self, live_client):
        start = time.perf_counter()
        r = live_client.post(
            "/query/ask",
            json={"question": QUESTIONS["medical"], "domain": "medical"},
        )
        elapsed = time.perf_counter() - start
        assert r.status_code == 200
        assert elapsed < 15.0, f"Query took {elapsed:.2f}s, expected < 15s"
        print(f"\n  Single query latency: {elapsed*1000:.0f}ms")

    def test_p95_latency_under_12_seconds(self, live_client):
        """Run 5 queries and ensure P95 ≤ 12 s (Gemini free-tier budget)."""
        latencies_ms: list[float] = []
        N = 5

        for i in range(N):
            start = time.perf_counter()
            live_client.post(
                "/query/ask",
                json={"question": f"What treats Type 2 Diabetes? ({i})", "domain": "medical"},
            )
            latencies_ms.append((time.perf_counter() - start) * 1000)
            time.sleep(1.5)  # respect Gemini free-tier rate limit

        latencies_ms.sort()
        p50 = statistics.median(latencies_ms)
        p95 = latencies_ms[max(0, int(N * 0.95) - 1)]
        p99 = latencies_ms[max(0, int(N * 0.99) - 1)]

        print(f"\n  📊 Query latency ({N} requests):")
        print(f"     P50 = {p50:.0f}ms")
        print(f"     P95 = {p95:.0f}ms")
        print(f"     P99 = {p99:.0f}ms")
        print(f"     Max = {max(latencies_ms):.0f}ms")

        assert p95 < 12_000, f"P95 latency {p95:.0f}ms > 12 000ms"

    def test_health_endpoint_under_500ms(self, live_client):
        times_ms = []
        for _ in range(10):
            start = time.perf_counter()
            live_client.get("/health")
            times_ms.append((time.perf_counter() - start) * 1000)

        avg = statistics.mean(times_ms)
        print(f"\n  Health endpoint avg latency: {avg:.0f}ms")
        assert avg < 500, f"Health avg {avg:.0f}ms > 500ms"

    def test_dashboard_endpoint_under_2_seconds(self, live_client):
        start = time.perf_counter()
        live_client.get("/freshness/dashboard/medical")
        elapsed = (time.perf_counter() - start) * 1000
        print(f"\n  Dashboard latency: {elapsed:.0f}ms")
        assert elapsed < 2_000, f"Dashboard took {elapsed:.0f}ms > 2 000ms"

    def test_stats_endpoint_under_2_seconds(self, live_client):
        start = time.perf_counter()
        live_client.get("/stats")
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 2_000

    def test_processing_time_header_present(self, live_client):
        r = live_client.post(
            "/query/ask",
            json={"question": QUESTIONS["finance"], "domain": "finance"},
        )
        # Middleware should inject X-Process-Time-Ms
        header_present = "x-process-time-ms" in r.headers
        body_present = "processing_time_ms" in r.json()
        assert header_present or body_present, (
            "Expected X-Process-Time-Ms header or processing_time_ms in body"
        )
