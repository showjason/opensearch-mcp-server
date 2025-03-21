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

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/opensearch-mcp-server.git
cd opensearch-mcp-server

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

## Configuration

Create a `.env` file in the root directory with the following variables:

```
OPENSEARCH_HOST=https://localhost:9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin
```

Adjust the values to match your OpenSearch configuration.

## Usage

Run the MCP server:

```bash
opensearch-mcp-server
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

[MIT](LICENSE) 