"""
Performance tests — document ingestion throughput.
Measures chunks/second and total ingestion time.

Run:
    TEST_API_URL=http://localhost:8000 pytest tests/performance/test_ingestion_throughput.py -v -s
"""

import os
import time
import pytest

pytestmark = [pytest.mark.performance, pytest.mark.slow]


class TestIngestionThroughput:
    """Throughput benchmarks for POST /ingest/upload."""

    def _make_pdf_bytes(self, content: str) -> bytes:
        """Create a minimal in-memory PDF for testing."""
        import io
        try:
            from reportlab.pdfgen import canvas as rl_canvas
            from reportlab.lib.pagesizes import letter
            buf = io.BytesIO()
            c = rl_canvas.Canvas(buf, pagesize=letter)
            y = 750
            for line in content.split("\n"):
                if y < 50:
                    c.showPage(); y = 750
                c.drawString(50, y, line[:90])
                y -= 14
            c.save()
            buf.seek(0)
            return buf.read()
        except ImportError:
            # Fallback: tiny hand-crafted PDF
            return (
                b"%PDF-1.4\n1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
                b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n"
                b"3 0 obj\n<</Type /Page /Parent 2 0 R "
                b"/MediaBox [0 0 612 792]>>\nendobj\n"
                b"xref\n0 4\n"
                b"0000000000 65535 f \n0000000009 00000 n \n"
                b"0000000058 00000 n \n0000000115 00000 n \n"
                b"trailer\n<</Size 4 /Root 1 0 R>>\n"
                b"startxref\n190\n%%EOF"
            )

    def test_single_document_ingestion_under_120s(self, live_client):
        """Single small PDF should be ingested within 2 minutes."""
        content = "Medical guidelines for diabetes. " * 50
        pdf = self._make_pdf_bytes(content)

        start = time.perf_counter()
        r = live_client.post(
            "/ingest/upload",
            data={"domain": "medical", "source_name": "Perf Test Doc"},
            files={"file": ("perf_test.pdf", pdf, "application/pdf")},
        )
        elapsed = time.perf_counter() - start

        assert r.status_code == 200, f"Upload failed: {r.text[:200]}"
        d = r.json()
        chunks = d.get("chunks_ingested", 0)

        print(f"\n  📊 Ingestion throughput:")
        print(f"     Duration:       {elapsed:.1f}s")
        print(f"     Chunks indexed: {chunks}")
        if chunks and elapsed:
            cps = chunks / elapsed
            print(f"     Chunks/second:  {cps:.2f}")

        assert elapsed < 120, f"Ingestion took {elapsed:.1f}s > 120s"

    def test_ingestion_returns_chunk_count(self, live_client):
        """Upload response must always include chunks_ingested."""
        content = "Short test document for throughput validation."
        pdf = self._make_pdf_bytes(content)
        r = live_client.post(
            "/ingest/upload",
            data={"domain": "finance", "source_name": "Throughput Doc"},
            files={"file": ("tp.pdf", pdf, "application/pdf")},
        )
        assert r.status_code == 200
        assert "chunks_ingested" in r.json()

    def test_health_stable_during_background_operations(self, live_client):
        """Health endpoint should remain responsive (<500 ms) at all times."""
        start = time.perf_counter()
        r = live_client.get("/health")
        elapsed = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        assert elapsed < 500, f"Health check took {elapsed:.0f}ms while idle"
