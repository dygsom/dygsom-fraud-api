FROM python:3.11-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ curl postgresql-client && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .

FROM base AS development
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN prisma generate
EXPOSE 3000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]

FROM base AS production
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Create appuser and setup directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /home/appuser/.cache/prisma-python && \
    chown -R appuser:appuser /home/appuser && \
    chown -R appuser:appuser /app

# Switch to appuser for the rest
USER appuser

# Set HOME to appuser's home directory
ENV HOME=/home/appuser

# Generate Prisma client and download query engine
RUN prisma generate

# Ensure query engine binary has execute permissions
RUN find /home/appuser/.cache/prisma-python -name "*query-engine*" -type f -exec chmod +x {} \; 2>/dev/null || true

EXPOSE 3000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000", "--workers", "4"]
