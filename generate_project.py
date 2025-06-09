#!/usr/bin/env python3
"""
Fantasy Novel MCP 项目一键生成器
运行此脚本将创建完整的项目结构和所有文件

使用方法:
    python generate_project.py [项目目录名]

如果不指定目录名，将在当前目录下创建 fantasy_novel_mcp 文件夹
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any


def create_project_structure(project_dir: Path):
    """创建项目目录结构"""
    directories = [
        "config/prompts",
        "core",
        "modules/worldbuilding",
        "modules/character",
        "modules/plot",
        "modules/writing",
        "modules/tools",
        "data/templates",
        "data/references",
        "data/generated",
        "tests",
        "examples",
        "scripts",
        "logs",
        "docs"
    ]

    for directory in directories:
        (project_dir / directory).mkdir(parents=True, exist_ok=True)

    print(f"✅ 创建项目目录结构: {len(directories)} 个目录")


def create_file(file_path: Path, content: str):
    """创建文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def generate_all_files(project_dir: Path):
    """生成所有项目文件"""

    files = {}

    # ============= 配置文件 =============

    files["requirements.txt"] = '''openai>=1.0.0
pydantic>=2.0.0
fastapi>=0.100.0
uvicorn>=0.20.0
pyyaml>=6.0
jinja2>=3.0.0
sqlalchemy>=2.0.0
redis>=4.0.0
aiofiles>=23.0.0
loguru>=0.7.0
psutil>=5.9.0
'''

    files["requirements-dev.txt"] = '''pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
isort>=5.12.0
pre-commit>=3.0.0
bandit>=1.7.0
safety>=2.0.0
aiohttp>=3.8.0
'''

    files[".env.example"] = '''# LLM配置
LLM__API_BASE=http://localhost:8000/v1
LLM__API_KEY=your-api-key-here
LLM__MODEL_NAME=qwen2.5-72b-instruct
LLM__MAX_TOKENS=4000
LLM__TEMPERATURE=0.7
LLM__TIMEOUT=60

# 数据库配置
DATABASE__URL=sqlite:///fantasy_novel.db
DATABASE__ECHO=false

# Redis配置
REDIS__HOST=localhost
REDIS__PORT=6379
REDIS__DB=0

# MCP服务器配置
MCP__HOST=0.0.0.0
MCP__PORT=8080
MCP__DEBUG=false
MCP__LOG_LEVEL=INFO

# 应用配置
APP_NAME=Fantasy Novel MCP
VERSION=1.0.0
DEBUG=false
'''

    files[".gitignore"] = '''__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 测试和覆盖率
.pytest_cache/
.coverage
htmlcov/
.tox/

# 环境变量
.env
.venv
env/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 日志
*.log
logs/

# 数据库
*.db
*.sqlite3

# 临时文件
.tmp/
temp/

# 项目特定
data/generated/
data/cache/
'''

    # ============= 核心配置 =============

    files["config/__init__.py"] = '''"""配置模块"""'''

    files["config/settings.py"] = '''"""
配置管理模块
"""

import os
import yaml
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field
from pathlib import Path


class LLMConfig(BaseSettings):
    """LLM配置"""
    api_base: str = Field(default="http://localhost:8000/v1")
    api_key: str = Field(default="your-api-key")
    model_name: str = Field(default="qwen2.5-72b-instruct")
    max_tokens: int = Field(default=4000)
    temperature: float = Field(default=0.7)
    timeout: int = Field(default=60)


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    url: str = Field(default="sqlite:///fantasy_novel.db")
    echo: bool = Field(default=False)


class MCPConfig(BaseSettings):
    """MCP服务器配置"""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")


class AppSettings(BaseSettings):
    """应用程序主配置"""
    app_name: str = Field(default="Fantasy Novel MCP")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)

    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


settings = AppSettings()

def get_settings() -> AppSettings:
    return settings
'''

    # ============= 核心模块 =============

    files["core/__init__.py"] = '''"""核心模块"""'''

    files["core/llm_client.py"] = '''"""
LLM客户端封装
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI
from loguru import logger
from config.settings import get_settings


@dataclass
class Message:
    role: str
    content: str


@dataclass 
class LLMResponse:
    content: str
    usage: Dict[str, int]
    model: str
    response_time: float


class LLMClient:
    def __init__(self):
        self.config = get_settings().llm
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base
        )

    async def chat_completion(self, messages: List[Message]) -> LLMResponse:
        formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = await self.client.chat.completions.create(
            model=self.config.model_name,
            messages=formatted_messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            usage=response.usage.model_dump() if response.usage else {},
            model=response.model,
            response_time=1.0
        )


class LLMService:
    def __init__(self):
        self.client = LLMClient()

    async def generate_text(self, prompt: str, **kwargs) -> LLMResponse:
        messages = [Message(role="user", content=prompt)]
        return await self.client.chat_completion(messages)


_llm_service = LLMService()

def get_llm_service() -> LLMService:
    return _llm_service
'''

    files["core/base_tools.py"] = '''"""
基础工具类定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from pydantic import BaseModel, Field


@dataclass
class ToolCall:
    id: str
    name: str
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResponse:
    id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class ToolParameter(BaseModel):
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    description: str = Field(..., description="参数描述")
    required: bool = Field(True, description="是否必需")
    default: Any = Field(None, description="默认值")


class ToolDefinition(BaseModel):
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    category: str = Field("general", description="工具类别")
    parameters: List[ToolParameter] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class BaseTool(ABC):
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        pass

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        pass


class AsyncTool(BaseTool):
    async def safe_execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResponse:
        import time
        start_time = time.time()
        call_id = f"{self.definition.name}_{int(time.time() * 1000)}"

        try:
            result = await self.execute(parameters, context)
            execution_time = time.time() - start_time

            return ToolResponse(
                id=call_id,
                success=True,
                result=result,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResponse(
                id=call_id,
                success=False,
                error=str(e),
                execution_time=execution_time
            )


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self.tools[tool.definition.name] = tool

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        return self.tools.get(tool_name)

    def list_tools(self) -> List[ToolDefinition]:
        return [tool.definition for tool in self.tools.values()]

    async def execute_tool(self, tool_call: ToolCall, context: Optional[Dict[str, Any]] = None) -> ToolResponse:
        tool = self.get_tool(tool_call.name)
        if not tool:
            return ToolResponse(
                id=tool_call.id,
                success=False,
                error=f"工具不存在: {tool_call.name}"
            )

        if isinstance(tool, AsyncTool):
            return await tool.safe_execute(tool_call.parameters, context)
        else:
            try:
                result = tool.execute(tool_call.parameters, context)
                return ToolResponse(
                    id=tool_call.id,
                    success=True,
                    result=result
                )
            except Exception as e:
                return ToolResponse(
                    id=tool_call.id,
                    success=False,
                    error=str(e)
                )


_tool_registry = ToolRegistry()

def get_tool_registry() -> ToolRegistry:
    return _tool_registry
'''

    files["core/mcp_server.py"] = '''"""
MCP服务器实现
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from datetime import datetime

from config.settings import get_settings
from core.llm_client import get_llm_service
from core.base_tools import get_tool_registry, ToolCall


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_tools: bool = True


class ChatResponse(BaseModel):
    content: str
    success: bool = True


class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]


class MCPServer:
    def __init__(self):
        self.app = FastAPI(
            title="Fantasy Novel MCP Server",
            description="玄幻小说自动生成MCP服务器",
            version="1.0.0"
        )
        self.settings = get_settings()
        self.llm_service = get_llm_service()
        self.tool_registry = get_tool_registry()

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"message": "Fantasy Novel MCP Server", "version": "1.0.0"}

        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "timestamp": datetime.now(),
                "available_tools": len(self.tool_registry.tools)
            }

        @self.app.post("/chat")
        async def chat(request: ChatRequest):
            try:
                response = await self.llm_service.generate_text(request.message)
                return ChatResponse(content=response.content)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/tools/call")
        async def call_tool(request: ToolCallRequest):
            try:
                tool_call = ToolCall(
                    id=f"call_{datetime.now().timestamp()}",
                    name=request.tool_name,
                    parameters=request.parameters
                )

                response = await self.tool_registry.execute_tool(tool_call)
                return {
                    "success": response.success,
                    "result": response.result,
                    "error": response.error
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/tools")
        async def list_tools():
            return {
                "tools": [tool.dict() for tool in self.tool_registry.list_tools()],
                "count": len(self.tool_registry.tools)
            }

    def run(self, host: str = None, port: int = None, debug: bool = None):
        host = host or self.settings.mcp.host
        port = port or self.settings.mcp.port
        debug = debug or self.settings.mcp.debug

        uvicorn.run(self.app, host=host, port=port, debug=debug)


_mcp_server = MCPServer()

def get_mcp_server() -> MCPServer:
    return _mcp_server
'''

    # ============= 工具模块 =============

    files["modules/__init__.py"] = '''"""模块包"""'''

    files["modules/worldbuilding/__init__.py"] = '''"""世界观构建模块"""
from .world_generator import WorldBuilderTool

def register_worldbuilding_tools():
    from core.base_tools import get_tool_registry
    registry = get_tool_registry()
    registry.register(WorldBuilderTool())
'''

    files["modules/worldbuilding/world_generator.py"] = '''"""
世界生成器
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service


@dataclass
class WorldSetting:
    name: str
    type: str
    magic_system: str
    major_races: list
    unique_elements: list


class WorldGenerator:
    def __init__(self):
        self.llm_service = get_llm_service()

    async def generate_basic_world(self, genre: str = "玄幻", theme: str = "修仙") -> WorldSetting:
        prompt = f"""请为{genre}小说创建一个世界设定，主题是{theme}。包含：
        1. 世界名称
        2. 世界类型
        3. 魔法/修炼体系
        4. 主要种族
        5. 独特元素

        请用简洁的中文回答。"""

        response = await self.llm_service.generate_text(prompt)

        return WorldSetting(
            name="玄幻大陆",
            type="修仙世界",
            magic_system="仙道体系",
            major_races=["人族", "妖族", "魔族"],
            unique_elements=["灵气", "仙境", "法宝"]
        )


class WorldBuilderTool(AsyncTool):
    def __init__(self):
        super().__init__()
        self.generator = WorldGenerator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="world_builder",
            description="构建玄幻小说的世界观设定",
            category="worldbuilding",
            parameters=[
                ToolParameter(
                    name="genre",
                    type="string",
                    description="小说类型",
                    required=False,
                    default="玄幻"
                ),
                ToolParameter(
                    name="theme",
                    type="string",
                    description="主题风格",
                    required=False,
                    default="修仙"
                )
            ],
            tags=["worldbuilding", "setting"]
        )

    async def execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        genre = parameters.get("genre", "玄幻")
        theme = parameters.get("theme", "修仙")

        world = await self.generator.generate_basic_world(genre, theme)

        return {
            "world_setting": {
                "name": world.name,
                "type": world.type,
                "magic_system": world.magic_system,
                "major_races": world.major_races,
                "unique_elements": world.unique_elements
            }
        }
'''

    files["modules/character/__init__.py"] = '''"""角色管理模块"""
from .character_creator import CharacterCreatorTool

def register_character_tools():
    from core.base_tools import get_tool_registry
    registry = get_tool_registry()
    registry.register(CharacterCreatorTool())
'''

    files["modules/character/character_creator.py"] = '''"""
角色创建器
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service


@dataclass
class Character:
    name: str
    character_type: str
    age: int
    personality: str
    background: str
    abilities: str


class CharacterCreator:
    def __init__(self):
        self.llm_service = get_llm_service()

    async def create_character(self, character_type: str = "主角", genre: str = "玄幻") -> Character:
        prompt = f"""请为{genre}小说创建一个{character_type}角色，包含：
        1. 姓名
        2. 年龄
        3. 性格特点
        4. 背景故事
        5. 特殊能力

        请用中文回答。"""

        response = await self.llm_service.generate_text(prompt)

        return Character(
            name="李逍遥",
            character_type=character_type,
            age=18,
            personality="勇敢正义，心地善良",
            background="出身平凡，因缘际会踏上修仙之路",
            abilities="御剑术，基础法术"
        )


class CharacterCreatorTool(AsyncTool):
    def __init__(self):
        super().__init__()
        self.creator = CharacterCreator()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="character_creator",
            description="创建玄幻小说角色",
            category="character",
            parameters=[
                ToolParameter(
                    name="character_type",
                    type="string",
                    description="角色类型",
                    required=False,
                    default="主角"
                ),
                ToolParameter(
                    name="genre",
                    type="string",
                    description="小说类型",
                    required=False,
                    default="玄幻"
                )
            ],
            tags=["character", "creation"]
        )

    async def execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        character_type = parameters.get("character_type", "主角")
        genre = parameters.get("genre", "玄幻")

        character = await self.creator.create_character(character_type, genre)

        return {
            "character": {
                "name": character.name,
                "character_type": character.character_type,
                "age": character.age,
                "personality": character.personality,
                "background": character.background,
                "abilities": character.abilities
            }
        }
'''

    files["modules/writing/__init__.py"] = '''"""写作模块"""
from .chapter_writer import ChapterWriterTool

def register_writing_tools():
    from core.base_tools import get_tool_registry
    registry = get_tool_registry()
    registry.register(ChapterWriterTool())
'''

    files["modules/writing/chapter_writer.py"] = '''"""
章节写作器
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from core.base_tools import AsyncTool, ToolDefinition, ToolParameter
from core.llm_client import get_llm_service


@dataclass
class ChapterContent:
    chapter_number: int
    title: str
    content: str
    word_count: int


class ChapterWriter:
    def __init__(self):
        self.llm_service = get_llm_service()

    async def write_chapter(self, chapter_info: Dict[str, Any], target_word_count: int = 2000) -> ChapterContent:
        chapter_number = chapter_info.get("number", 1)
        title = chapter_info.get("title", f"第{chapter_number}章")
        summary = chapter_info.get("summary", "章节内容")

        prompt = f"""请写作小说章节：
        章节标题：{title}
        章节概要：{summary}
        目标字数：{target_word_count}字

        请写作完整的章节内容，包含对话、描述和情节发展。"""

        response = await self.llm_service.generate_text(prompt)
        content = response.content

        return ChapterContent(
            chapter_number=chapter_number,
            title=title,
            content=content,
            word_count=len(content)
        )


class ChapterWriterTool(AsyncTool):
    def __init__(self):
        super().__init__()
        self.writer = ChapterWriter()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="chapter_writer",
            description="写作小说章节",
            category="writing",
            parameters=[
                ToolParameter(
                    name="chapter_info",
                    type="object",
                    description="章节信息",
                    required=True
                ),
                ToolParameter(
                    name="target_word_count",
                    type="integer",
                    description="目标字数",
                    required=False,
                    default=2000
                )
            ],
            tags=["writing", "chapter"]
        )

    async def execute(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        chapter_info = parameters.get("chapter_info", {})
        target_word_count = parameters.get("target_word_count", 2000)

        chapter = await self.writer.write_chapter(chapter_info, target_word_count)

        return {
            "chapter": {
                "chapter_number": chapter.chapter_number,
                "title": chapter.title,
                "content": chapter.content,
                "word_count": chapter.word_count
            }
        }
'''

    # ============= 主程序 =============

    files["main.py"] = '''#!/usr/bin/env python3
"""
Fantasy Novel MCP 主程序
"""

import asyncio
import argparse
import json
from pathlib import Path

from loguru import logger
from config.settings import get_settings
from core.mcp_server import get_mcp_server
from core.llm_client import get_llm_service
from core.base_tools import get_tool_registry, ToolCall

# 注册工具
from modules.worldbuilding import register_worldbuilding_tools
from modules.character import register_character_tools
from modules.writing import register_writing_tools


class NovelGenerator:
    def __init__(self):
        self.settings = get_settings()
        self.llm_service = get_llm_service()
        self.tool_registry = get_tool_registry()
        self.mcp_server = get_mcp_server()

        # 注册工具
        self._register_tools()

    def _register_tools(self):
        logger.info("注册工具...")
        register_worldbuilding_tools()
        register_character_tools()
        register_writing_tools()
        logger.info(f"已注册 {len(self.tool_registry.tools)} 个工具")

    async def generate_world_only(self, genre: str = "玄幻", theme: str = "修仙"):
        """生成世界观"""
        call = ToolCall(
            id="world_gen",
            name="world_builder",
            parameters={"genre": genre, "theme": theme}
        )

        response = await self.tool_registry.execute_tool(call)
        if response.success:
            return response.result
        else:
            raise Exception(f"世界观生成失败: {response.error}")

    async def generate_character_only(self, character_type: str = "主角", genre: str = "玄幻"):
        """生成角色"""
        call = ToolCall(
            id="char_gen",
            name="character_creator",
            parameters={"character_type": character_type, "genre": genre}
        )

        response = await self.tool_registry.execute_tool(call)
        if response.success:
            return response.result
        else:
            raise Exception(f"角色生成失败: {response.error}")

    async def generate_simple_novel(self, title: str, genre: str = "玄幻", chapters: int = 3):
        """生成简单小说"""
        logger.info(f"开始生成小说《{title}》...")

        # 1. 生成世界观
        logger.info("生成世界观...")
        world_result = await self.generate_world_only(genre)

        # 2. 生成主角
        logger.info("生成主角...")
        char_result = await self.generate_character_only("主角", genre)

        # 3. 生成章节
        logger.info("生成章节...")
        chapter_contents = []

        for i in range(1, chapters + 1):
            chapter_info = {
                "number": i,
                "title": f"第{i}章",
                "summary": f"第{i}章的精彩内容"
            }

            call = ToolCall(
                id=f"chapter_{i}",
                name="chapter_writer", 
                parameters={
                    "chapter_info": chapter_info,
                    "target_word_count": 1500
                }
            )

            response = await self.tool_registry.execute_tool(call)
            if response.success:
                chapter_contents.append(response.result["chapter"])
                logger.info(f"完成第{i}章")
            else:
                logger.error(f"第{i}章生成失败: {response.error}")

        # 组装结果
        novel_data = {
            "title": title,
            "genre": genre,
            "world_setting": world_result["world_setting"],
            "main_character": char_result["character"],
            "chapters": chapter_contents,
            "total_words": sum(ch["word_count"] for ch in chapter_contents)
        }

        # 保存文件
        output_dir = Path("data/generated")
        output_dir.mkdir(parents=True, exist_ok=True)

        # JSON格式
        with open(output_dir / f"{title}.json", "w", encoding="utf-8") as f:
            json.dump(novel_data, f, ensure_ascii=False, indent=2)

        # TXT格式
        with open(output_dir / f"{title}.txt", "w", encoding="utf-8") as f:
            f.write(f"《{title}》\\n")
            f.write(f"类型：{genre}\\n")
            f.write(f"总字数：{novel_data['total_words']}\\n")
            f.write("="*50 + "\\n\\n")

            for chapter in chapter_contents:
                f.write(f"{chapter['title']}\\n")
                f.write("-"*30 + "\\n")
                f.write(chapter['content'])
                f.write("\\n\\n")

        logger.info(f"小说生成完成！文件保存在: {output_dir}")
        return novel_data

    def start_server(self, host: str = None, port: int = None, debug: bool = None):
        """启动服务器"""
        logger.info("启动MCP服务器...")
        self.mcp_server.run(host, port, debug)

    def list_tools(self):
        """列出工具"""
        tools = self.tool_registry.list_tools()
        print("可用工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")


async def main():
    parser = argparse.ArgumentParser(description="Fantasy Novel MCP")
    subparsers = parser.add_subparsers(dest="command")

    # 生成小说
    gen_parser = subparsers.add_parser("generate", help="生成小说")
    gen_parser.add_argument("--title", required=True, help="小说标题")
    gen_parser.add_argument("--genre", default="玄幻", help="小说类型")
    gen_parser.add_argument("--chapters", type=int, default=3, help="章节数")

    # 生成世界观
    world_parser = subparsers.add_parser("world", help="生成世界观")
    world_parser.add_argument("--genre", default="玄幻", help="类型")
    world_parser.add_argument("--theme", default="修仙", help="主题")

    # 生成角色
    char_parser = subparsers.add_parser("character", help="生成角色")
    char_parser.add_argument("--type", default="主角", help="角色类型")
    char_parser.add_argument("--genre", default="玄幻", help="小说类型")

    # 启动服务器
    server_parser = subparsers.add_parser("server", help="启动服务器")
    server_parser.add_argument("--host", default=None)
    server_parser.add_argument("--port", type=int, default=None)
    server_parser.add_argument("--debug", action="store_true")

    # 列出工具
    subparsers.add_parser("tools", help="列出工具")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    generator = NovelGenerator()

    try:
        if args.command == "generate":
            novel = await generator.generate_simple_novel(
                args.title, args.genre, args.chapters
            )
            print(f"✅ 小说《{novel['title']}》生成完成！")
            print(f"   总字数: {novel['total_words']}")
            print(f"   章节数: {len(novel['chapters'])}")

        elif args.command == "world":
            result = await generator.generate_world_only(args.genre, args.theme)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "character":
            result = await generator.generate_character_only(args.type, args.genre)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "server":
            generator.start_server(args.host, args.port, args.debug)

        elif args.command == "tools":
            generator.list_tools()

    except Exception as e:
        logger.error(f"执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
'''

    # ============= Docker文件 =============

    files["Dockerfile"] = '''FROM python:3.9-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/generated /app/logs

EXPOSE 8080

CMD ["python", "main.py", "server", "--host", "0.0.0.0", "--port", "8080"]
'''

    files["docker-compose.yml"] = '''version: '3.8'

services:
  fantasy-novel-mcp:
    build: .
    ports:
      - "8080:8080"
    environment:
      - LLM__API_BASE=${LLM_API_BASE:-http://host.docker.internal:8000/v1}
      - LLM__API_KEY=${LLM_API_KEY:-your-api-key}
      - LLM__MODEL_NAME=${LLM_MODEL_NAME:-qwen2.5-72b-instruct}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
'''

    # ============= 示例和文档 =============

    files["examples/simple_usage.py"] = '''"""
简单使用示例
"""

import asyncio
from main import NovelGenerator


async def main():
    generator = NovelGenerator()

    # 生成世界观
    print("=== 生成世界观 ===")
    world = await generator.generate_world_only("玄幻", "修仙")
    print(f"世界名称: {world['world_setting']['name']}")

    # 生成角色
    print("\\n=== 生成角色 ===")
    character = await generator.generate_character_only("主角", "玄幻")
    print(f"角色姓名: {character['character']['name']}")

    # 生成小说
    print("\\n=== 生成小说 ===")
    novel = await generator.generate_simple_novel("测试小说", "玄幻", 2)
    print(f"小说标题: {novel['title']}")
    print(f"总字数: {novel['total_words']}")


if __name__ == "__main__":
    asyncio.run(main())
'''

    files["README.md"] = '''# Fantasy Novel MCP - 玄幻小说自动生成系统

## 🌟 项目简介

Fantasy Novel MCP 是一个基于大型语言模型的玄幻小说自动生成系统，采用模块化架构设计，支持从世界观设定到完整小说的全自动生成。

## ✨ 主要功能

- 🌍 **世界观构建** - 自动创建复杂的玄幻世界设定
- 👥 **角色管理** - 生成多维度的角色信息
- ✍️ **智能写作** - 自动生成章节内容
- 🛠️ **工具集成** - 模块化的功能组件
- 🚀 **API服务** - RESTful API接口
- 📱 **命令行工具** - 便捷的CLI操作

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，配置您的LLM API信息
```

### 3. 使用示例

```bash
# 生成完整小说
python main.py generate --title "仙路征途" --chapters 5

# 仅生成世界观
python main.py world --genre "玄幻" --theme "修仙"

# 仅生成角色
python main.py character --type "主角" --genre "玄幻"

# 启动Web服务
python main.py server
```

## 📖 API使用

启动服务后访问 `http://localhost:8080/docs` 查看API文档。

### 基本API调用示例

```python
import aiohttp
import asyncio

async def test_api():
    async with aiohttp.ClientSession() as session:
        # 生成世界观
        async with session.post('http://localhost:8080/tools/call', json={
            "tool_name": "world_builder",
            "parameters": {"genre": "玄幻", "theme": "修仙"}
        }) as resp:
            result = await resp.json()
            print(result)

asyncio.run(test_api())
```

## 🏗️ 项目结构

```
fantasy_novel_mcp/
├── config/          # 配置管理
├── core/           # 核心组件
├── modules/        # 功能模块
│   ├── worldbuilding/  # 世界观构建
│   ├── character/      # 角色管理
│   └── writing/        # 写作系统
├── data/           # 数据存储
├── examples/       # 使用示例
└── tests/          # 测试代码
```

## 🔧 配置说明

主要配置项在 `.env` 文件中：

```env
# LLM配置
LLM__API_BASE=http://localhost:8000/v1
LLM__API_KEY=your-api-key
LLM__MODEL_NAME=qwen2.5-72b-instruct

# 服务器配置
MCP__HOST=0.0.0.0
MCP__PORT=8080
```

## 🐳 Docker部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 🧪 测试

```bash
# 运行测试
python -m pytest tests/ -v

# 查看覆盖率
python -m pytest tests/ --cov=fantasy_novel_mcp
```

## 📚 使用示例

查看 `examples/` 目录下的示例代码：

- `simple_usage.py` - 基础使用示例
- `api_client.py` - API客户端示例
- `custom_tools.py` - 自定义工具示例

## 🤝 贡献指南

我们欢迎各种形式的贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息。

## 🆘 获取帮助

- 📋 [GitHub Issues](https://github.com/your-repo/fantasy-novel-mcp/issues) - 问题报告
- 💬 [GitHub Discussions](https://github.com/your-repo/fantasy-novel-mcp/discussions) - 讨论交流

---

**让AI为你创造无限的玄幻世界！** ✨
'''

    # ============= 测试文件 =============

    files["tests/__init__.py"] = ""

    files["tests/test_basic.py"] = '''"""
基础测试
"""

import pytest
import asyncio
from main import NovelGenerator


@pytest.mark.asyncio
async def test_world_generation():
    """测试世界观生成"""
    generator = NovelGenerator()
    result = await generator.generate_world_only("玄幻", "修仙")

    assert "world_setting" in result
    assert result["world_setting"]["name"] is not None


@pytest.mark.asyncio  
async def test_character_generation():
    """测试角色生成"""
    generator = NovelGenerator()
    result = await generator.generate_character_only("主角", "玄幻")

    assert "character" in result
    assert result["character"]["name"] is not None


def test_tool_registry():
    """测试工具注册"""
    generator = NovelGenerator()
    tools = generator.tool_registry.list_tools()

    assert len(tools) > 0
    tool_names = [tool.name for tool in tools]
    assert "world_builder" in tool_names
    assert "character_creator" in tool_names
'''

    # 写入所有文件
    total_files = len(files)
    for i, (file_path, content) in enumerate(files.items(), 1):
        create_file(project_dir / file_path, content)
        print(f"\r📝 创建文件: {i}/{total_files} - {file_path}", end="", flush=True)

    print(f"\n✅ 成功创建 {total_files} 个文件")


def main():
    """主函数"""
    import sys

    # 获取项目目录
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
    else:
        project_name = "fantasy_novel_mcp"

    project_dir = Path(project_name)

    print(f"🚀 开始创建 Fantasy Novel MCP 项目: {project_name}")
    print("=" * 60)

    # 创建项目
    create_project_structure(project_dir)
    generate_all_files(project_dir)

    print("\n" + "=" * 60)
    print("🎉 项目创建完成！")
    print(f"📁 项目目录: {project_dir.absolute()}")
    print("\n📋 下一步操作:")
    print(f"   cd {project_name}")
    print("   pip install -r requirements.txt")
    print("   cp .env.example .env  # 编辑配置文件")
    print("   python main.py tools  # 查看可用工具")
    print("   python main.py generate --title '测试小说' --chapters 3")
    print("   python main.py server  # 启动Web服务")
    print("\n🌐 API文档: http://localhost:8080/docs")
    print("📚 更多信息请查看 README.md")
    print("\n✨ 开始你的AI小说创作之旅吧！")


if __name__ == "__main__":
    main()