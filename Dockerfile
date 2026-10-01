FROM python:3.14-slim

WORKDIR /app

# Install dependencies (assuming pip install via requirements.txt or pyproject.toml)
COPY pyproject.toml .
# If requirements.txt exists, we could use it, but pip install . covers pyproject.toml
RUN pip install --no-cache-dir . || pip install uv && uv pip install --system -r requirements.txt || true

COPY . .

# Cloud Run provides the PORT environment variable
ENV PORT=8080

# Production ASGI server configuration
CMD uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers --forwarded-allow-ips='*'
