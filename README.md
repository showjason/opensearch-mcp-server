# OpenSearch MCP Server

MCP (Machine Coding Protocol) server for OpenSearch integration.

## Features

- Index Management Tools:
  - List all indices in OpenSearch cluster
  - Get index mapping
  - Get index settings
- Cluster Management Tools:
  - Get cluster health status
  - Get cluster statistics
- Document Tools:
  - Search documents

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/opensearch-mcp-server.git
cd opensearch-mcp-server

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install uv
uv pip install -e .
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```
OPENSEARCH_HOST=https://localhost:9200
OPENSEARCH_USERNAME=xxxx
OPENSEARCH_PASSWORD=xxxx
```

Adjust the values to match your OpenSearch configuration.

## Usage

Run the MCP server:

```bash
uv run opensearch-mcp-server --transport=sse --port=8004
```

## Development

```bash
# Install dependencies
uv pip install -e .

# Run tests
uv run pytest -vv -s test_opensearch.py
```

## License

[MIT](LICENSE) 