# 玄幻小说自动生成MCP工程

## 项目简介

这是一个基于大型语言模型（LLM）的玄幻小说自动生成系统，采用模块化架构设计，支持从世界观设定到完整小说的全自动生成。项目使用MCP（Model Context Protocol）架构，提供灵活的工具调用和扩展能力。


"""
玄幻小说自动生成MCP工程
项目结构设计
"""

# 项目目录结构
```
fantasy_novel_mcp/
├── config/
│   ├── __init__.py
│   ├── settings.py           # 配置管理
│   └── prompts/             # 提示词模板
│       ├── worldbuilding.yaml
│       ├── character.yaml
│       ├── plot.yaml
│       └── writing.yaml
├── core/
│   ├── __init__.py
│   ├── llm_client.py        # LLM客户端封装
│   ├── mcp_server.py        # MCP服务器
│   └── base_tools.py        # 基础工具类
├── modules/
│   ├── __init__.py
│   ├── worldbuilding/       # 世界观构建模块
│   │   ├── __init__.py
│   │   ├── world_generator.py
│   │   ├── magic_system.py
│   │   └── geography.py
│   ├── character/           # 角色管理模块
│   │   ├── __init__.py
│   │   ├── character_creator.py
│   │   ├── relationship.py
│   │   └── development.py
│   ├── plot/                # 情节规划模块
│   │   ├── __init__.py
│   │   ├── story_planner.py
│   │   ├── conflict_generator.py
│   │   └── arc_manager.py
│   ├── writing/             # 写作模块
│   │   ├── __init__.py
│   │   ├── chapter_writer.py
│   │   ├── scene_generator.py
│   │   ├── dialogue_writer.py
│   │   └── description_writer.py
│   └── tools/               # 工具集合
│       ├── __init__.py
│       ├── name_generator.py
│       ├── timeline_manager.py
│       └── consistency_checker.py
├── data/
│   ├── templates/           # 模板数据
│   ├── references/          # 参考资料
│   └── generated/           # 生成的小说
├── tests/
│   ├── __init__.py
│   ├── test_worldbuilding.py
│   ├── test_character.py
│   ├── test_plot.py
│   └── test_writing.py
├── requirements.txt
├── setup.py
├── README.md
└── main.py                  # 主入口
```

# setup.py
```
setup_py_content = '''
from setuptools import setup, find_packages

setup(
    name="fantasy-novel-mcp",
    version="1.0.0",
    description="自动玄幻小说生成MCP工程",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "pyyaml>=6.0",
        "jinja2>=3.0.0",
        "sqlalchemy>=2.0.0",
        "redis>=4.0.0",
        "aiofiles>=23.0.0",
        "loguru>=0.7.0",
    ],
    python_requires=">=3.9",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automatic Fantasy Novel Generation MCP Project",
)
```

# requirements.txt
requirements_txt = 
```
openai>=1.0.0
pydantic>=2.0.0
fastapi>=0.100.0
uvicorn>=0.20.0
pyyaml>=6.0
jinja2>=3.0.0
sqlalchemy>=2.0.0
redis>=4.0.0
aiofiles>=23.0.0
loguru>=0.7.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```


## 功能特色

### 🌍 世界观构建
- **智能世界生成**：自动创建复杂的玄幻世界设定
- **魔法体系设计**：生成完整的修炼等级和技能体系
- **地理环境规划**：创建大陆、城市、自然奇观等地理要素
- **势力关系网络**：建立王国、门派、种族间的复杂关系

### 👥 角色管理系统
- **多维角色创建**：从外貌、性格到背景的全方位角色设定
- **关系网络管理**：自动分析和维护角色间的复杂关系
- **角色成长弧线**：规划角色的发展路径和实力提升
- **智能角色一致性**：确保角色在不同章节中的表现一致

### 📖 情节规划引擎
- **多结构支持**：支持三幕式、英雄之旅等多种故事结构
- **冲突生成器**：自动创建内外冲突和矛盾对立
- **弧线管理**：统筹主线和支线的发展节奏
- **智能情节连接**：确保章节间的逻辑连贯性

### ✍️ 智能写作系统
- **分层写作**：从章节到场景再到具体描述的层次化生成
- **风格控制**：支持古典、现代、诗意等多种写作风格
- **对话生成**：创造符合角色特点的自然对话
- **描写专精**：专业的人物、环境、动作描写生成

### 🛠️ 辅助工具集
- **名称生成器**：为角色、地点、功法、法宝生成合适名称
- **时间线管理**：维护复杂的时间线和事件序列
- **一致性检查**：全面检查故事的逻辑一致性
- **质量评估**：自动分析和评估生成内容的质量

## 技术架构

### 核心架构
```
fantasy_novel_mcp/
├── config/          # 配置管理
├── core/           # 核心组件
├── modules/        # 功能模块
│   ├── worldbuilding/  # 世界观构建
│   ├── character/      # 角色管理
│   ├── plot/          # 情节规划
│   ├── writing/       # 写作系统
│   └── tools/         # 辅助工具
├── data/           # 数据存储
└── tests/          # 测试代码
```

### 技术栈
- **Python 3.9+**：主要开发语言
- **FastAPI**：高性能Web框架
- **OpenAI API兼容**：支持各种LLM后端
- **Pydantic**：数据验证和序列化
- **SQLAlchemy**：数据库ORM
- **Redis**：缓存和会话管理
- **Docker**：容器化部署

## 快速开始

### 环境要求
- Python 3.9+
- 支持OpenAI API格式的LLM服务
- Redis（可选，用于缓存）
- SQLite/PostgreSQL（可选，用于数据持久化）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-repo/fantasy-novel-mcp.git
cd fantasy-novel-mcp
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
cp .env.example .env
# 编辑.env文件，配置LLM API信息
```

4. **验证配置**
```bash
python main.py config
```

### 环境配置

创建 `.env` 文件：
```env
# LLM配置
LLM__API_BASE=http://localhost:8000/v1
LLM__API_KEY=your-api-key
LLM__MODEL_NAME=qwen2.5-72b-instruct

# 服务器配置
MCP__HOST=0.0.0.0
MCP__PORT=8080
MCP__DEBUG=false

# 数据库配置（可选）
DATABASE__URL=sqlite:///fantasy_novel.db

# Redis配置（可选）
REDIS__HOST=localhost
REDIS__PORT=6379
```

## 使用指南

### 命令行使用

#### 生成完整小说
```bash
python main.py generate --title "仙路征途" --genre "玄幻" --chapters 20 --theme "修仙"
```

#### 仅生成世界观
```bash
python main.py world --genre "玄幻" --theme "修仙"
```

#### 仅生成角色
```bash
python main.py characters --count 5 --genre "玄幻"
```

#### 启动Web服务
```bash
python main.py server --host 0.0.0.0 --port 8080
```

#### 查看可用工具
```bash
python main.py tools
```

### API使用

启动服务后，可通过HTTP API调用各种功能：

#### 聊天接口
```http
POST /chat
Content-Type: application/json

{
  "message": "请为我创建一个修仙世界的设定",
  "session_id": "user_123",
  "use_tools": true
}
```

#### 小说生成接口
```http
POST /novel/generate
Content-Type: application/json

{
  "title": "仙路征途",
  "genre": "玄幻",
  "chapter_count": 20,
  "auto_generate": true
}
```

#### 工具调用接口
```http
POST /tools/call
Content-Type: application/json

{
  "tool_name": "world_builder",
  "parameters": {
    "genre": "玄幻",
    "theme": "修仙",
    "detail_level": "detailed"
  }
}
```

### Python API使用

```python
from main import NovelGenerator
import asyncio

async def main():
    generator = NovelGenerator()
    
    # 生成完整小说
    novel = await generator.generate_novel_complete(
        title="仙路征途",
        genre="玄幻",
        chapter_count=10,
        theme="修仙"
    )
    
    print(f"生成小说：{novel['title']}")
    print(f"总字数：{novel['total_word_count']}")

asyncio.run(main())
```

## 工具详解

### 世界观构建工具

#### world_builder
创建完整的玄幻世界设定
```python
{
  "tool_name": "world_builder",
  "parameters": {
    "genre": "玄幻",        # 小说类型
    "theme": "修仙",        # 主题风格
    "scale": "大陆",        # 世界规模
    "detail_level": "detailed"  # 详细程度
  }
}
```

#### magic_system_generator
生成魔法/修炼体系
```python
{
  "tool_name": "magic_system_generator",
  "parameters": {
    "world_type": "修仙",   # 世界类型
    "complexity": "medium"  # 复杂程度
  }
}
```

### 角色管理工具

#### character_creator
创建角色
```python
{
  "tool_name": "character_creator",
  "parameters": {
    "character_type": "主角",    # 角色类型
    "genre": "玄幻",           # 小说类型
    "count": 1,               # 创建数量
    "world_setting": {}       # 世界设定
  }
}
```

#### relationship_manager
管理角色关系
```python
{
  "tool_name": "relationship_manager",
  "parameters": {
    "action": "create",       # 操作类型
    "character1": {},         # 角色1信息
    "character2": {},         # 角色2信息
    "relationship_type": "友谊关系"
  }
}
```

### 情节规划工具

#### story_planner
创建故事大纲
```python
{
  "tool_name": "story_planner",
  "parameters": {
    "title": "仙路征途",      # 故事标题
    "genre": "玄幻",         # 故事类型
    "chapter_count": 20,     # 章节数量
    "structure": "三幕式"     # 情节结构
  }
}
```

#### conflict_generator
生成故事冲突
```python
{
  "tool_name": "conflict_generator",
  "parameters": {
    "conflict_type": "central",  # 冲突类型
    "protagonist": "主角",       # 主要角色
    "antagonist": "反派"        # 对立角色
  }
}
```

### 写作工具

#### chapter_writer
写作章节
```python
{
  "tool_name": "chapter_writer",
  "parameters": {
    "chapter_info": {         # 章节信息
      "number": 1,
      "title": "初入江湖",
      "summary": "主角开始修仙之路"
    },
    "story_context": {},      # 故事上下文
    "writing_style": "traditional",  # 写作风格
    "target_word_count": 3000        # 目标字数
  }
}
```

#### dialogue_writer
写作对话
```python
{
  "tool_name": "dialogue_writer",
  "parameters": {
    "dialogue_type": "exchange",     # 对话类型
    "participants": ["角色1", "角色2"], # 参与者
    "topic": "重要决定",             # 对话主题
    "emotional_goal": "紧张"         # 情感目标
  }
}
```

### 辅助工具

#### name_generator
生成名称
```python
{
  "tool_name": "name_generator",
  "parameters": {
    "name_type": "character",    # 名称类型
    "count": 5,                 # 生成数量
    "cultural_style": "中式古典", # 文化风格
    "gender": "male"            # 性别
  }
}
```

#### consistency_checker
一致性检查
```python
{
  "tool_name": "consistency_checker",
  "parameters": {
    "check_type": "full",       # 检查类型
    "story_data": {}           # 故事数据
  }
}
```

## 配置说明

### 基础配置
在 `config/settings.py` 中可以配置：
- LLM连接参数
- 数据库设置
- Redis缓存
- 小说生成参数
- MCP服务器设置

### 提示词模板
在 `config/prompts/` 目录下可以自定义：
- 世界观生成提示词
- 角色创建提示词
- 情节规划提示词
- 写作风格提示词

## 扩展开发

### 添加新工具

1. **创建工具类**
```python
from core.base_tools import AsyncTool, ToolDefinition

class MyCustomTool(AsyncTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="my_tool",
            description="我的自定义工具",
            category="custom",
            parameters=[...]
        )
    
    async def execute(self, parameters, context=None):
        # 实现工具逻辑
        return result
```

2. **注册工具**
```python
from core.base_tools import get_tool_registry

registry = get_tool_registry()
registry.register(MyCustomTool())
```

### 添加新模块

1. 在 `modules/` 下创建新目录
2. 实现模块功能和工具
3. 在主程序中注册模块工具

### 自定义写作风格

在提示词模板中添加新的写作风格：
```yaml
my_style: |
  请使用我的自定义风格写作：
  - 特点1
  - 特点2
  - 特点3
```

## API文档

启动服务后访问 `http://localhost:8080/docs` 查看完整的API文档。

## 部署指南

### Docker部署

1. **构建镜像**
```bash
docker build -t fantasy-novel-mcp .
```

2. **运行容器**
```bash
docker run -d \
  -p 8080:8080 \
  -e LLM__API_KEY=your-api-key \
  -v $(pwd)/data:/app/data \
  fantasy-novel-mcp
```

### 生产环境部署

1. **使用Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker core.mcp_server:app
```

2. **Nginx反向代理**
```nginx
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
```

## 性能优化

### 缓存策略
- 启用Redis缓存常用生成结果
- 使用 `@cached` 装饰器缓存工具执行结果
- 配置合适的缓存过期时间

### 并发控制
- 使用连接池管理LLM连接
- 实现请求排队和限流
- 优化生成任务的批处理

### 资源管理
- 监控内存使用情况
- 定期清理临时文件
- 优化提示词长度

## 故障排除

### 常见问题

**1. LLM连接失败**
- 检查API密钥和基础URL
- 确认网络连接正常
- 验证模型名称正确

**2. 生成质量不佳**
- 调整温度参数
- 优化提示词模板
- 检查上下文信息完整性

**3. 内存占用过高**
- 减少并发请求数
- 清理缓存数据
- 优化数据结构

**4. 生成速度慢**
- 启用缓存机制
- 调整批处理大小
- 使用更快的LLM模型

### 日志分析
启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 贡献指南

### 开发流程
1. Fork项目
2. 创建特性分支
3. 提交代码
4. 创建Pull Request

### 代码规范
- 遵循PEP 8代码风格
- 添加完整的类型注解
- 编写单元测试
- 更新文档

### 测试要求
```bash
# 运行测试
pytest tests/

# 代码覆盖率
pytest --cov=fantasy_novel_mcp tests/
```

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 更新日志

### v1.0.0 (2024-12-19)
- 初始版本发布
- 完整的MCP架构实现
- 全模块功能支持
- Web API接口
- 命令行工具

## 联系方式

- 项目地址：https://github.com/your-repo/fantasy-novel-mcp
- 问题反馈：https://github.com/your-repo/fantasy-novel-mcp/issues
- 技术交流：your-email@example.com

## 致谢

感谢所有为本项目做出贡献的开发者和测试者！

---

**让AI为你创造无限的玄幻世界！** 🌟
