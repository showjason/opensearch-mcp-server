#!/usr/bin/env python3
import logging
import argparse
from fastmcp import FastMCP
from .tools.index import IndexTools
from .tools.cluster import ClusterTools
from .tools.document import DocumentTools
from .opensearch_client import OpenSearchClient

class OpenSearchMCPServer:
    def __init__(self):
        self.name = "opensearch_mcp_server"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)
        
        self.mcp = FastMCP(self.name)

        # Initialize OpenSearch client
        self.os_client = OpenSearchClient(self.logger).os_client
        
        # Initialize tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools."""
        # Initialize tool classes with shared OpenSearch client
        index_tools = IndexTools(self.logger, self.os_client)
        cluster_tools = ClusterTools(self.logger, self.os_client)
        document_tools = DocumentTools(self.logger, self.os_client)
        
        # Register tools from each module
        index_tools.register_tools(self.mcp)
        cluster_tools.register_tools(self.mcp)
        document_tools.register_tools(self.mcp)
        
    def run(self, host=None, port=None):
        """Run the MCP server with SSE transport.
        
        Args:
            host: Optional host address, defaults to 127.0.0.1
            port: Optional port number, defaults to 8000
        """
        host = host or "127.0.0.1"
        port = port or 8000
        
        self.logger.info(f"OpenSearch MCP service will start on {host}:{port}")
        self.mcp.run(transport="streamable-http", host=host, port=port)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='OpenSearch MCP Server')
    parser.add_argument('--host', type=str, default="127.0.0.1", help='Service listening host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='Service listening port (default: 8000)')
    args = parser.parse_args()
    
    # Create and run the server
    server = OpenSearchMCPServer()
    server.run(host=args.host, port=args.port)