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
    """自定义FastMCP修复SSE问题"""
    
    def __init__(self, name, logger=None, **kwargs):
        super().__init__(name, **kwargs)
        self.logger = logger or logging.getLogger(name)
    
    async def run_sse_async(self) -> None:
        """修复的SSE运行方法，直接重写创建Starlette应用的过程"""
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        from starlette.responses import Response
        from mcp.server.sse import SseServerTransport
        import uvicorn

        self.logger.info("通过自定义方法初始化SSE服务")
        sse = SseServerTransport("/messages/")

        # 创建SSE处理函数
        async def handle_sse(request):
            self.logger.info(f"接收到SSE连接请求: {request}")
            try:
                async with sse.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    self.logger.info("SSE连接已建立")
                    await self._mcp_server.run(
                        streams[0],
                        streams[1],
                        self._mcp_server.create_initialization_options(),
                    )
            except Exception as e:
                self.logger.error(f"SSE处理错误: {e}", exc_info=True)
                raise

        # 创建安全的POST消息处理函数
        async def safe_handle_post_message(scope, receive, send):
            """安全处理POST消息的包装函数"""
            self.logger.info("处理POST消息请求")
            try:
                # 调用原始处理函数
                await sse.handle_post_message(scope, receive, send)
                # 注意:原始函数已经发送了响应，但没有返回值
                self.logger.info("POST消息处理完成")
            except Exception as e:
                self.logger.error(f"处理POST消息时出错: {e}", exc_info=True)
                # 如果出错，尝试发送错误响应
                try:
                    response = Response(f"Error: {str(e)}", status_code=500)
                    await response(scope, receive, send)
                except Exception:
                    pass
                raise

        # 创建Starlette应用
        starlette_app = Starlette(
            debug=self.settings.debug,
            routes=[
                Route("/sse", endpoint=handle_sse),
                # 使用我们的安全包装函数代替原始函数
                Mount("/messages", app=safe_handle_post_message),
            ],
        )
        
        # 增加中间件来捕获请求级别错误
        @starlette_app.middleware("http")
        async def error_handling_middleware(request, call_next):
            self.logger.info(f"开始处理请求: {request.url.path}")
            try:
                response = await call_next(request)
                self.logger.info(f"请求处理完成: {request.url.path}, 状态码: {getattr(response, 'status_code', '未知')}")
                return response
            except Exception as e:
                self.logger.error(f"请求处理异常: {str(e)}", exc_info=True)
                return Response(
                    f"服务器内部错误: {str(e)}", status_code=500
                )

        # 启动服务器
        config = uvicorn.Config(
            starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            log_level=self.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        self.logger.info(f"开始启动服务器，监听 {self.settings.host}:{self.settings.port}")
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
        
        # 使用自定义FastMCP
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