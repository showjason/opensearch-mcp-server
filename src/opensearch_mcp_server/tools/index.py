import logging
from typing import Dict, Any

class IndexTools:
    def __init__(self, logger=None, os_client=None):
        """
        Initialize IndexTools with logger and OpenSearch client.
        
        Args:
            logger: Logger instance
            os_client: OpenSearch client instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.os_client = os_client
        
    def register_tools(self, mcp: Any):
        """Register index-related tools."""
        
        @mcp.tool(description="List all indices in OpenSearch cluster")
        async def list_indices() -> str:
            """List all indices in the OpenSearch cluster."""
            self.logger.info("Listing indices...")
            try:
                indices = self.os_client.cat.indices(format="json")
                return str(indices)
            except Exception as e:
                self.logger.error(f"Error listing indices: {e}")
                return f"Error: {str(e)}"

        @mcp.tool(description="Get index mapping")
        async def get_mapping(index: str) -> str:
            """
            Get the mapping for an index.
            
            Args:
                index: Name of the index
            """
            self.logger.info(f"Getting mapping for index: {index}")
            try:
                response = self.os_client.indices.get_mapping(index=index)
                return str(response)
            except Exception as e:
                self.logger.error(f"Error getting mapping: {e}")
                return f"Error: {str(e)}"

        @mcp.tool(description="Get index settings")
        async def get_settings(index: str) -> str:
            """
            Get the settings for an index.
            
            Args:
                index: Name of the index
            """
            self.logger.info(f"Getting settings for index: {index}")
            try:
                response = self.os_client.indices.get_settings(index=index)
                return str(response)
            except Exception as e:
                self.logger.error(f"Error getting settings: {e}")
                return f"Error: {str(e)}"