# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION=1.0.0
ARG VCS_REF

# Add labels
LABEL org.opencontainers.image.title="Smart File Search"
LABEL org.opencontainers.image.description="Intelligent file search system with semantic capabilities"
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.revision=$VCS_REF
LABEL org.opencontainers.image.licenses="MIT"

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/home/appuser/.local/bin:$PATH

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app directory and set ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Copy Python packages from builder stage
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create data directory
RUN mkdir -p /app/data /app/sample_data && \
    chown -R appuser:appuser /app/data /app/sample_data

# Switch to non-root user
USER appuser

# Create health check script
RUN echo '#!/bin/sh\n\
curl -f http://localhost:9000/health || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/health')" || exit 1

# Expose port
EXPOSE 9000

# Start the application
CMD ["python", "mcp_server/server.py"]
