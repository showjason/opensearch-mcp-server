FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install uv && \
    uv pip install --system -e .

# Copy source code
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the server
CMD ["opensearch-mcp-server"] 