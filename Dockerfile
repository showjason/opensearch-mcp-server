FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock* ./
# 分开执行各个命令以避免 /bin/sh -c 问题
RUN pip install --no-cache-dir --upgrade pip & pip install -e .

# Copy source code
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
# OpenSearch connection parameters
ENV OPENSEARCH_HOST="https://localhost:9200"
ENV OPENSEARCH_USERNAME="admin"
ENV OPENSEARCH_PASSWORD="admin"
# These can be overridden at runtime with docker run --env

# Expose the port the server is running on
EXPOSE 8000

# Run the server
# Default port is 8000
CMD ["opensearch-mcp-server"]