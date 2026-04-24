FROM python:3.11-slim

# System dependencies for pdfplumber (poppler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpoppler-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command (overridden by docker-compose.yml per service)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
