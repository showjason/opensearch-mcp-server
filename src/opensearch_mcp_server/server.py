#!/usr/bin/env python3
import logging
import argparse
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from mcp.server.streamable_http import StreamableHttpServerTransport
import uvicorn

from .tools.index import IndexTools
from .tools.cluster import ClusterTools
from .tools.document import DocumentTools
from .opensearch_client import OpenSearchClient


class OpenSearchMCPServer:
    """OpenSearch MCP Server with Streamable HTTP transport"""
    
    def __init__(self):
        self.name = "opensearch_mcp_server"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)
        
        # Create FastMCP instance
        self.mcp = FastMCP(self.name)
        
        # Initialize OpenSearch client
        self.os_client = OpenSearchClient(self.logger).os_client
        
        # Initialize tools
        self._register_tools()
        
        # Create Streamable HTTP transport
        self.transport = StreamableHttpServerTransport()
        
        # Session management
        self.sessions: Dict[str, Any] = {}

    
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
        
        self.logger.info("All MCP tools registered successfully")
    
    async def handle_mcp_request(self, request: Request) -> JSONResponse | StreamingResponse:
        """Handle MCP requests via Streamable HTTP"""
        try:
            # Get session ID from headers
            session_id = request.headers.get("Mcp-Session-Id")
            
            if request.method == "POST":
                # Handle JSON-RPC request
                body = await request.json()
                self.logger.info(f"Received MCP request: {body.get('method', 'unknown')}")
                
                # Process the request through MCP server
                async with self.transport.connect_http(
                    request.scope, 
                    request.receive, 
                    request._send
                ) as streams:
                    # Initialize session if needed
                    if body.get("method") == "initialize" and not session_id:
                        session_id = self._generate_session_id()
                        self.sessions[session_id] = {}
                        self.logger.info(f"Created new session: {session_id}")
                    
                    # Run MCP server
                    await self.mcp._mcp_server.run(
                        streams[0],
                        streams[1],
                        self.mcp._mcp_server.create_initialization_options(),
                    )
                
                # Return appropriate response (handled by transport)
                return JSONResponse({"status": "processed"})
                
            elif request.method == "GET":
                # Optional: Support server-initiated SSE streams
                return await self._handle_sse_stream(request, session_id)
                
            elif request.method == "DELETE":
                # Handle session termination
                if session_id and session_id in self.sessions:
                    del self.sessions[session_id]
                    self.logger.info(f"Terminated session: {session_id}")
                    return JSONResponse({"status": "session_terminated"})
                
                return JSONResponse({"error": "Session not found"}, status_code=404)
                
        except Exception as e:
            self.logger.error(f"Error handling MCP request: {e}", exc_info=True)
            return JSONResponse(
                {"error": f"Internal server error: {str(e)}"}, 
                status_code=500
            )
    
    async def _handle_sse_stream(self, request: Request, session_id: Optional[str]) -> StreamingResponse:
        """Handle server-initiated SSE streams"""
        async def event_generator():
            try:
                # Send initial connection event
                yield f"data: {{'event': 'connected', 'session_id': '{session_id}'}}\n\n"
                
                # Keep connection alive and send periodic heartbeats
                while True:
                    await asyncio.sleep(30)  # 30 second heartbeat
                    yield f"data: {{'event': 'heartbeat', 'timestamp': '{asyncio.get_event_loop().time()}'}}\n\n"
                    
            except asyncio.CancelledError:
                self.logger.info("SSE stream cancelled")
                yield f"data: {{'event': 'disconnected'}}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Mcp-Session-Id": session_id or "",
            }
        )
    
    def _generate_session_id(self) -> str:
        """Generate a secure session ID"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def create_app(self) -> Starlette:
        """Create Starlette application with Streamable HTTP support"""
        
        async def health_check(request: Request) -> JSONResponse:
            """Health check endpoint"""
            return JSONResponse({
                "status": "healthy",
                "server": self.name,
                "transport": "streamable-http"
            })
        
        # Create Starlette application
        app = Starlette(
            debug=False,
            routes=[
                Route("/health", endpoint=health_check, methods=["GET"]),
                Route("/mcp", endpoint=self.handle_mcp_request, methods=["POST", "GET", "DELETE"]),
            ],
        )
        
        # Add CORS middleware for web clients
        @app.middleware("http")
        async def cors_middleware(request: Request, call_next):
            response = await call_next(request)
            
            # Add CORS headers
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Mcp-Session-Id, Last-Event-ID"
            response.headers["Access-Control-Expose-Headers"] = "Mcp-Session-Id"
            
            return response
        
        # Add error handling middleware
        @app.middleware("http")
        async def error_handling_middleware(request: Request, call_next):
            self.logger.info(f"Processing request: {request.method} {request.url.path}")
            try:
                response = await call_next(request)
                self.logger.info(f"Request completed: {request.url.path}, status: {response.status_code}")
                return response
            except Exception as e:
                self.logger.error(f"Request failed: {str(e)}", exc_info=True)
                return JSONResponse(
                    {"error": f"Internal server error: {str(e)}"}, 
                    status_code=500
                )
        
        return app
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the MCP server with Streamable HTTP transport"""
        self.logger.info(f"Starting OpenSearch MCP Server with Streamable HTTP transport")
        self.logger.info(f"Server will listen on {host}:{port}")
        self.logger.info(f"MCP endpoint: http://{host}:{port}/mcp")
        
        # Create and run the application
        app = self.create_app()
        
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )
        
        server = uvicorn.Server(config)
        asyncio.run(server.serve())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='OpenSearch MCP Server with Streamable HTTP')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on (default: 8000)')
    args = parser.parse_args()
    
    # Create and run the server
    server = OpenSearchMCPServer()
    server.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()