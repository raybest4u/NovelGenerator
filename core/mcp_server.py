# core/mcp_server.py
"""
MCP服务器实现
提供RESTful API接口和工具调用能力
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

from config.settings import get_settings
from core.base_tools import ToolRegistry, ToolCall
from core.llm_client import get_llm_service


class MCPRequest(BaseModel):
    """MCP请求基类"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ChatRequest(MCPRequest):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    system_prompt: Optional[str] = Field(None, description="系统提示")
    model: Optional[str] = Field(None, description="模型名称")
    temperature: Optional[float] = Field(None, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    stream: bool = Field(False, description="是否流式响应")
    use_tools: bool = Field(True, description="是否使用工具")


class NovelGenerationRequest(MCPRequest):
    """小说生成请求"""
    title: str = Field(..., description="小说标题")
    genre: str = Field("玄幻", description="小说类型")
    outline: Optional[str] = Field(None, description="大纲")
    character_count: int = Field(3, description="主要角色数量")
    chapter_count: int = Field(10, description="章节数量")
    word_count_per_chapter: int = Field(3000, description="每章字数")
    auto_generate: bool = Field(False, description="是否自动生成全文")


class ToolCallRequest(MCPRequest):
    """工具调用请求"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(..., description="工具参数")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")


class MCPResponse(BaseModel):
    """MCP响应基类"""
    id: str
    success: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None


class ChatResponse(MCPResponse):
    """聊天响应"""
    content: str
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    session_id: Optional[str] = None
    tools_used: List[str] = Field(default_factory=list)


class NovelResponse(MCPResponse):
    """小说生成响应"""
    novel_id: str
    title: str
    status: str  # "planning", "generating", "completed", "error"
    progress: float = 0.0
    current_step: str = ""
    chapters: List[Dict[str, Any]] = Field(default_factory=list)


class MCPServer:
    """MCP服务器"""

    def __init__(self):
        self.app = FastAPI(
            title="Fantasy Novel MCP Server",
            description="玄幻小说自动生成MCP服务器",
            version="1.0.0"
        )
        self.settings = get_settings()
        self.llm_service = get_llm_service()
        self.tool_registry = ToolRegistry()

        # 活跃任务追踪
        self.active_tasks: Dict[str, Dict] = {}

        self._setup_middleware()
        self._setup_routes()
        self._register_default_tools()

    def _setup_middleware(self):
        """设置中间件"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/")
        async def root():
            return {
                "message": "Fantasy Novel MCP Server",
                "version": "1.0.0",
                "status": "running"
            }

        @self.app.get("/tools")
        async def list_tools():
            """列出所有可用工具"""
            return {
                "tools": self.tool_registry.list_tools(),
                "count": len(self.tool_registry.tools)
            }

        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest):
            """聊天接口"""
            try:
                if request.stream:
                    return StreamingResponse(
                        self._stream_chat(request),
                        media_type="text/plain"
                    )
                else:
                    return await self._handle_chat(request)
            except Exception as e:
                logger.error(f"聊天处理失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/novel/generate", response_model=NovelResponse)
        async def generate_novel(request: NovelGenerationRequest, background_tasks: BackgroundTasks):
            """生成小说"""
            try:
                novel_id = str(uuid.uuid4())

                # 创建任务
                task_info = {
                    "id": novel_id,
                    "title": request.title,
                    "status": "planning",
                    "progress": 0.0,
                    "current_step": "初始化",
                    "chapters": [],
                    "created_at": datetime.now()
                }

                self.active_tasks[novel_id] = task_info

                if request.auto_generate:
                    # 后台异步生成
                    background_tasks.add_task(self._generate_novel_background, novel_id, request)

                return NovelResponse(
                    id=request.id,
                    success=True,
                    novel_id=novel_id,
                    title=request.title,
                    status="planning",
                    current_step="任务已创建"
                )

            except Exception as e:
                logger.error(f"小说生成失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/novel/{novel_id}/status")
        async def get_novel_status(novel_id: str):
            """获取小说生成状态"""
            if novel_id not in self.active_tasks:
                raise HTTPException(status_code=404, detail="任务不存在")

            task = self.active_tasks[novel_id]
            return NovelResponse(
                id=str(uuid.uuid4()),
                success=True,
                novel_id=novel_id,
                title=task["title"],
                status=task["status"],
                progress=task["progress"],
                current_step=task["current_step"],
                chapters=task["chapters"]
            )

        @self.app.post("/tools/call")
        async def call_tool(request: ToolCallRequest):
            """调用工具"""
            try:
                tool_call = ToolCall(
                    id=request.id,
                    name=request.tool_name,
                    parameters=request.parameters
                )

                response = await self.tool_registry.execute_tool(tool_call, request.context)

                return {
                    "id": request.id,
                    "success": response.success,
                    "result": response.result,
                    "error": response.error,
                    "execution_time": response.execution_time
                }

            except Exception as e:
                logger.error(f"工具调用失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health")
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "timestamp": datetime.now(),
                "active_tasks": len(self.active_tasks),
                "available_tools": len(self.tool_registry.tools)
            }

    async def _handle_chat(self, request: ChatRequest) -> ChatResponse:
        """处理聊天请求"""
        tools_used = []

        # 如果启用工具使用，先尝试识别是否需要调用工具
        if request.use_tools:
            tool_calls = await self._detect_tool_calls(request.message)
            for tool_call in tool_calls:
                tool_response = await self.tool_registry.execute_tool(tool_call)
                tools_used.append(tool_call.name)

                # 将工具结果添加到对话中
                if tool_response.success:
                    request.message += f"\n\n工具({tool_call.name})执行结果: {tool_response.result}"

        # 生成LLM响应
        response = await self.llm_service.generate_text(
            prompt=request.message,
            session_id=request.session_id,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return ChatResponse(
            id=request.id,
            success=True,
            content=response.content,
            usage=response.usage,
            model=response.model,
            session_id=request.session_id,
            tools_used=tools_used
        )

    async def _stream_chat(self, request: ChatRequest):
        """流式聊天处理"""
        stream = await self.llm_service.stream_generate(
            prompt=request.message,
            session_id=request.session_id,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    async def _detect_tool_calls(self, message: str) -> List[ToolCall]:
        """检测消息中是否需要调用工具"""
        # 简单的工具调用检测逻辑
        # 实际项目中可以使用更复杂的NLP或规则匹配
        tool_calls = []

        # 示例：检测生成角色的请求
        if "生成角色" in message or "创建角色" in message:
            tool_calls.append(ToolCall(
                id=str(uuid.uuid4()),
                name="character_generator",
                parameters={"message": message}
            ))

        # 检测世界观设定请求
        if "世界观" in message or "设定背景" in message:
            tool_calls.append(ToolCall(
                id=str(uuid.uuid4()),
                name="world_builder",
                parameters={"message": message}
            ))

        return tool_calls

    async def _generate_novel_background(self, novel_id: str, request: NovelGenerationRequest):
        """后台生成小说"""
        try:
            task = self.active_tasks[novel_id]

            # 1. 规划阶段
            task["status"] = "planning"
            task["current_step"] = "生成大纲"

            # 调用大纲生成工具
            outline_call = ToolCall(
                id=str(uuid.uuid4()),
                name="story_planner",
                parameters={
                    "title": request.title,
                    "genre": request.genre,
                    "chapter_count": request.chapter_count
                }
            )

            outline_response = await self.tool_registry.execute_tool(outline_call)
            if not outline_response.success:
                task["status"] = "error"
                task["current_step"] = f"大纲生成失败: {outline_response.error}"
                return

            task["progress"] = 0.2

            # 2. 角色生成阶段
            task["current_step"] = "生成角色"

            character_call = ToolCall(
                id=str(uuid.uuid4()),
                name="character_creator",
                parameters={
                    "count": request.character_count,
                    "genre": request.genre
                }
            )

            character_response = await self.tool_registry.execute_tool(character_call)
            task["progress"] = 0.4

            # 3. 章节生成阶段
            task["status"] = "generating"
            task["current_step"] = "生成章节"

            chapters = []
            for i in range(request.chapter_count):
                chapter_call = ToolCall(
                    id=str(uuid.uuid4()),
                    name="chapter_writer",
                    parameters={
                        "chapter_number": i + 1,
                        "word_count": request.word_count_per_chapter,
                        "outline": outline_response.result if outline_response.success else "",
                        "characters": character_response.result if character_response.success else ""
                    }
                )

                chapter_response = await self.tool_registry.execute_tool(chapter_call)
                if chapter_response.success:
                    chapters.append({
                        "number": i + 1,
                        "title": f"第{i+1}章",
                        "content": chapter_response.result,
                        "word_count": len(chapter_response.result)
                    })

                task["progress"] = 0.4 + (0.6 * (i + 1) / request.chapter_count)
                task["current_step"] = f"已完成第{i+1}章"
                task["chapters"] = chapters

                # 短暂延迟，避免过度占用资源
                await asyncio.sleep(0.1)

            # 4. 完成
            task["status"] = "completed"
            task["progress"] = 1.0
            task["current_step"] = "生成完成"

            logger.info(f"小说生成完成: {novel_id}")

        except Exception as e:
            logger.error(f"后台小说生成失败: {e}")
            task["status"] = "error"
            task["current_step"] = f"生成失败: {str(e)}"

    def _register_default_tools(self):
        """注册默认工具"""
        # 这里会注册各个模块的工具
        # 实际的工具实现在对应的模块中
        # registry = get_tool_registry()
        # registry.register(EnhancedStoryGeneratorTool())
        pass

    def run(self, host: str = None, port: int = None, debug: bool = None):
        """运行服务器"""
        import uvicorn

        host = host or self.settings.mcp.host
        port = port or self.settings.mcp.port
        debug = debug or self.settings.mcp.debug

        logger.info(f"启动MCP服务器: {host}:{port}")

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            log_level=self.settings.mcp.log_level.lower()
        )


# 创建全局服务器实例
mcp_server = MCPServer()


def get_mcp_server() -> MCPServer:
    """获取MCP服务器实例"""
    return mcp_server


if __name__ == "__main__":
    mcp_server.run()
