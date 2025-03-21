import logging
from typing import Dict, Any
from ..opensearch_client import OpenSearchClient
from mcp.types import TextContent

class IndexTools(OpenSearchClient):
    def register_tools(self, mcp: Any):
        """Register index-related tools."""
        
        @mcp.tool(description="List all indices in OpenSearch cluster")
        async def list_indices() -> list[TextContent]:
            """List all indices in the OpenSearch cluster."""
            self.logger.info("Listing indices...")
            try:
                indices = self.os_client.cat.indices(format="json")
                return [TextContent(type="text", text=str(indices))]
            except Exception as e:
                self.logger.error(f"Error listing indices: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        @mcp.tool(description="Get index mapping")
        async def get_mapping(index: str) -> list[TextContent]:
            """
            Get the mapping for an index.
            
            Args:
                index: Name of the index
            """
            self.logger.info(f"Getting mapping for index: {index}")
            try:
                response = self.os_client.indices.get_mapping(index=index)
                return [TextContent(type="text", text=str(response))]
            except Exception as e:
                self.logger.error(f"Error getting mapping: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        @mcp.tool(description="Get index settings")
        async def get_settings(index: str) -> list[TextContent]:
            """
            Get the settings for an index.
            
            Args:
                index: Name of the index
            """
            self.logger.info(f"Getting settings for index: {index}")
            try:
                response = self.os_client.indices.get_settings(index=index)
                return [TextContent(type="text", text=str(response))]
            except Exception as e:
                self.logger.error(f"Error getting settings: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")] 