#!/usr/bin/env python3
import logging
import argparse
import traceback
from fastmcp import FastMCP
from .tools.index import IndexTools
from .tools.cluster import ClusterTools
from .tools.document import DocumentTools
from .opensearch_client import OpenSearchClient

# 自定义SSE响应类
class DebugEventSourceResponse:
    """重载SSE响应类以添加调试日志"""
    
    @staticmethod
    def patch_sse_starlette():
        """通过猴子补丁方式修改SSE Starlette库"""
        try:
            from sse_starlette.sse import EventSourceResponse
            import anyio
            
            # 保存原始的__call__方法
            original_call = EventSourceResponse.__call__
            logger = logging.getLogger("opensearch_mcp_server")
            
            # 重写__call__方法
            async def patched_call(self, scope, receive, send):
                logger.info(f"EventSourceResponse.__call__ 开始，send类型: {type(send)}, ID: {id(send)}")
                try:
                    async with anyio.create_task_group() as task_group:
                        # 复制代码，添加日志
                        async def cancel_on_finish(coro, coro_name):
                            logger.info(f"开始运行任务: {coro_name}")
                            try:
                                await coro()
                                logger.info(f"任务 {coro_name} 完成")
                            except Exception as e:
                                logger.error(f"任务 {coro_name} 出现异常: {e}")
                                logger.error(traceback.format_exc())
                            finally:
                                logger.info(f"取消作用域: {coro_name}")
                                task_group.cancel_scope.cancel()

                        # 检查send是否是可调用的
                        if not callable(send):
                            logger.error(f"错误: send 对象不可调用! 类型: {type(send)}")
                            # 如果send不可调用，创建一个占位符
                            async def dummy_send(message):
                                logger.info(f"调用替代send: {message}")
                            send = dummy_send

                        # 启动任务
                        task_group.start_soon(cancel_on_finish, lambda: self._stream_response(send), "_stream_response")
                        task_group.start_soon(cancel_on_finish, lambda: self._ping(send), "_ping")
                        task_group.start_soon(cancel_on_finish, self._listen_for_exit_signal, "_listen_for_exit_signal")

                        if self.data_sender_callable:
                            task_group.start_soon(cancel_on_finish, self.data_sender_callable, "data_sender_callable")

                        # 监听断开连接
                        await cancel_on_finish(lambda: self._listen_for_disconnect(receive), "_listen_for_disconnect")

                    # 运行背景任务
                    if self.background is not None:
                        logger.info("运行背景任务")
                        await self.background()
                        
                except Exception as e:
                    logger.error(f"EventSourceResponse.__call__ 出现异常: {e}")
                    logger.error(traceback.format_exc())
                    raise
                finally:
                    logger.info("EventSourceResponse.__call__ 结束")
            
            # 应用补丁
            EventSourceResponse.__call__ = patched_call
            logger.info("成功应用SSE响应类补丁")
            
            # 记录重要方法的类型和ID
            logger.info(f"原始__call__方法: {type(original_call)}, ID: {id(original_call)}")
            logger.info(f"补丁后__call__方法: {type(EventSourceResponse.__call__)}, ID: {id(EventSourceResponse.__call__)}")
            
            return True
        except Exception as e:
            logging.getLogger("opensearch_mcp_server").error(f"应用SSE补丁失败: {e}")
            logging.getLogger("opensearch_mcp_server").error(traceback.format_exc())
            return False

class CustomFastMCP(FastMCP):
    """扩展FastMCP以自定义SSE处理"""
    
    def __init__(self, name, logger=None, **kwargs):
        super().__init__(name, **kwargs)
        self.logger = logger or logging.getLogger(name)
    
    async def run_sse_async(self) -> None:
        """重载SSE异步运行方法，添加日志记录与错误处理"""
        # 应用SSE补丁
        DebugEventSourceResponse.patch_sse_starlette()
        
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        from mcp.server.sse import SseServerTransport

        self.logger.info("准备启动SSE服务")
        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            self.logger.info(f"收到SSE连接请求: {request}")
            try:
                # 在发生错误的地方添加详细日志
                self.logger.info(f"Request attributes: {dir(request)}")
                self.logger.info(f"Request _send type: {type(request._send)}, ID: {id(request._send)}")
                
                async with sse.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    self.logger.info(f"SSE连接成功建立")
                    await self._mcp_server.run(
                        streams[0],
                        streams[1],
                        self._mcp_server.create_initialization_options(),
                    )
            except Exception as e:
                self.logger.error(f"SSE处理过程中出现异常: {e}", exc_info=True)
                raise

        # 创建Starlette应用
        starlette_app = Starlette(
            debug=self.settings.debug,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        # 添加中间件监控
        @starlette_app.middleware("http")
        async def log_responses(request, call_next):
            self.logger.info(f"处理请求: {request.url.path}")
            try:
                response = await call_next(request)
                self.logger.info(f"响应状态: {response.status_code}, 类型: {type(response)}, ID: {id(response)}")
                if response is None:
                    self.logger.error("警告: 响应对象为None!")
                return response
            except Exception as e:
                self.logger.error(f"中间件捕获异常: {e}", exc_info=True)
                raise

        import uvicorn
        config = uvicorn.Config(
            starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            log_level=self.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        self.logger.info("正在启动uvicorn服务器...")
        try:
            await server.serve()
        except Exception as e:
            self.logger.error(f"uvicorn服务器启动异常: {e}", exc_info=True)
            raise

class OpenSearchMCPServer:
    def __init__(self):
        self.name = "opensearch_mcp_server"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)
        
        # 使用自定义FastMCP类
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