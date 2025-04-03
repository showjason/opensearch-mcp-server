#!/usr/bin/env python3
import logging
import argparse
# import asyncio
from fastmcp import FastMCP
from .tools.index import IndexTools
from .tools.cluster import ClusterTools
from .tools.document import DocumentTools
from .opensearch_client import OpenSearchClient

class CustomFastMCP(FastMCP):
    """Custom FastMCP to fix SSE issues"""
    
    def __init__(self, name, logger=None, **kwargs):
        super().__init__(name, **kwargs)
        self.logger = logger or logging.getLogger(name)
    
    async def run_sse_async(self) -> None:
        """Fixed SSE run method, directly rewrites the process of creating Starlette application"""
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        from starlette.responses import Response
        from mcp.server.sse import SseServerTransport
        import uvicorn

        self.logger.info("Initializing SSE service using custom method")
        sse = SseServerTransport("/messages/")

        # Create SSE handler function
        async def handle_sse(request):
            self.logger.info(f"Received SSE connection request: {request}")
            try:
                async with sse.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    self.logger.info("SSE connection established")
                    await self._mcp_server.run(
                        streams[0],
                        streams[1],
                        self._mcp_server.create_initialization_options(),
                    )
            except Exception as e:
                self.logger.error(f"SSE handling error: {e}", exc_info=True)
                raise

        # Create secure POST message handler function
        async def safe_handle_post_message(scope, receive, send):
            """Secure wrapper function for handling POST messages"""
            self.logger.info("Processing POST message request")
            try:
                # Call original handler function
                await sse.handle_post_message(scope, receive, send)
                # Note: original function has already sent response but has no return value
                self.logger.info("POST message processing completed")
            except Exception as e:
                self.logger.error(f"Error processing POST message: {e}", exc_info=True)
                # If error occurs, try to send error response
                try:
                    response = Response(f"Error: {str(e)}", status_code=500)
                    await response(scope, receive, send)
                except Exception:
                    pass
                raise

        # Create Starlette application
        starlette_app = Starlette(
            debug=self.settings.debug,
            routes=[
                Route("/sse", endpoint=handle_sse),
                # Use our secure wrapper function instead of the original
                Mount("/messages", app=safe_handle_post_message),
            ],
        )
        
        # Add middleware to capture request-level errors
        @starlette_app.middleware("http")
        async def error_handling_middleware(request, call_next):
            self.logger.info(f"Starting request processing: {request.url.path}")
            try:
                response = await call_next(request)
                self.logger.info(f"Request processing completed: {request.url.path}, status code: {getattr(response, 'status_code', 'unknown')}")
                return response
            except Exception as e:
                self.logger.error(f"Request processing exception: {str(e)}", exc_info=True)
                return Response(
                    f"Internal server error: {str(e)}", status_code=500
                )

        # Start server
        config = uvicorn.Config(
            starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            log_level=self.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        self.logger.info(f"Starting server, listening on {self.settings.host}:{self.settings.port}")
        await server.serve()

class OpenSearchMCPServer:
    def __init__(self):
        self.name = "opensearch_mcp_server"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)
        
        # Use custom FastMCP
        self.mcp = CustomFastMCP(self.name, logger=self.logger)
        
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
        
    def run(self, port=None):
        """Run the MCP server with SSE transport.
        
        Args:
            port: Optional port number, if specified it will override the default port
        """
        if port is not None:
            self.mcp.settings.port = port
            self.logger.info(f"OpenSearch MCP service will start on port {port}")
            
        self.mcp.run(transport="sse")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='OpenSearch MCP Server')
    parser.add_argument('--port', type=int, help='Service listening port (default: 8000)')
    args = parser.parse_args()
    
    # Create and run the server
    server = OpenSearchMCPServer()
    server.run(port=args.port)