FROM python:3.12-slim

# LibreOffice (headless) + font dibutuhkan untuk export PDF 1:1 dari docx.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer fonts-dejavu fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV CORS_ORIGINS=http://localhost:3000 \
    CACHE_TTL_SECONDS=300 \
    SOFFICE_BIN=/usr/bin/soffice

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
