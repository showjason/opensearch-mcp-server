#!/usr/bin/env python3
import logging
import argparse
from fastmcp import FastMCP
from .tools.index import IndexTools
from .tools.cluster import ClusterTools

class OpenSearchMCPServer:
    def __init__(self):
        self.name = "opensearch_mcp_server"
        self.mcp = FastMCP(self.name)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)
        
        # Initialize tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools."""
        # Initialize tool classes
        index_tools = IndexTools(self.logger)
        cluster_tools = ClusterTools(self.logger)
        
        # Register tools from each module
        index_tools.register_tools(self.mcp)
        cluster_tools.register_tools(self.mcp)

    def run(self, port=None, transport="stdio"):
        """Run the MCP server.
        
        Args:
            port: Optional port number, if specified it will override the default port
            transport: Transport protocol, either "stdio" or "sse"
        """
        if port is not None:
            self.mcp.settings.port = port
            self.logger.info(f"OpenSearch MCP service will start on port {port}")
            
        self.mcp.run(transport=transport)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='OpenSearch MCP Server')
    parser.add_argument('--port', type=int, help='Service listening port (default: 8000)')
    parser.add_argument('--transport', default="stdio", choices=["stdio", "sse"], 
                        help='Transport protocol (default: stdio)')
    args = parser.parse_args()
    
    # Create and run the server
    server = OpenSearchMCPServer()
    server.run(port=args.port, transport=args.transport) 