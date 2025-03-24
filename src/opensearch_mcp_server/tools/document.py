import logging
from typing import Dict, Any
from mcp.types import TextContent

class DocumentTools:
    def __init__(self, logger=None, os_client=None):
        """
        Initialize DocumentTools with logger and OpenSearch client.
        
        Args:
            logger: Logger instance
            os_client: OpenSearch client instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.os_client = os_client
        
    def register_tools(self, mcp: Any):
        """Register document-related tools."""
        
        @mcp.tool(description="Search documents in an index with a custom query")
        async def search_documents(index: str, body: dict) -> list[TextContent]:
            """
            Search documents in a specified index using a custom query.

            Args:
                index: Name of the index to search
                body: OpenSearch query DSL
            """
            self.logger.info(f"Searching in index: {index} with query: {body}")
            try:
                response = self.os_client.search(index=index, body=body)
                return [TextContent(type="text", text=str(response))]
            except Exception as e:
                self.logger.error(f"Error searching documents: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
                