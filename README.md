# OpenSearch MCP Server

MCP (Model Context Protocol) server for OpenSearch integration which is inspired by **[elasticsearch-mcp-server](https://github.com/cr7258/elasticsearch-mcp-server)**.

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

## Usage with Cursor

### Run the MCP server:

```bash
uv run opensearch-mcp-server --port=<port>
```
### Integrate with Cursor
```
{
  "mcpServers": {
    "opensearch": {
      "url": "http://<host>:<port>>/sse"
    }
  }
}
```
## Usage with Claude Desktop APP
```
{
  "mcpServers": {
    "opensearch": {
      "command": "uv",
      "args": [
          "--directory",
          "/absolute/path/to/opensearch-mcp-server",
          "run",
          "opensearch-mcp-server"
      ]
    }
  }
}
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
