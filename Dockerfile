FROM python:3.11-slim

# Accept version as build argument
ARG VERSION=1.0.0
ENV VERSION=$VERSION

# Set working directory
WORKDIR /app

# Set environment variables for K8s optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=UTC

# Install system dependencies for health checks and security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with proper signal handling and logging
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--access-log", "--log-level", "info"]