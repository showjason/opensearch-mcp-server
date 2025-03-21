#!/usr/bin/env python3
import logging
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

    def run(self):
        """Run the MCP server."""
        self.mcp.run()

def main():
    server = OpenSearchMCPServer()
    server.run() 