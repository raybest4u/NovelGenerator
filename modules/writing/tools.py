# modules/writing/tools.py
"""
写作工具模块 - 使用新的抽象基类
"""
import time
from typing import Dict, Any, Optional
from core.abstract_tools import ContentGeneratorTool
from core.base_tools import ToolDefinition, ToolParameter
from core.cache_manager import cached
from core.llm_client import get_llm_service
from config.settings import get_prompt_manager


class ChapterWriterTool(ContentGeneratorTool):
    """章节写作工具 - 重构版本"""

    def __init__(self):
        super().__init__()
        self.llm_service = get_llm_service()
        self.prompt_manager = get_prompt_manager()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="chapter_writer",
            description="生成章节内容，支持多种写作风格和结构",
            category="writing",
            version="2.0.0",
            parameters=self.common_parameters + [
                ToolParameter(
                    name="chapter_info",
                    type="object",
                    description="章节信息（标题、摘要、角色等）",
                    required=True
                ),
                ToolParameter(
                    name="plot_context",
                    type="object",
                    description="情节上下文",
                    required=False,
                    default={}
                ),
                ToolParameter(
                    name="characters",
                    type="array",
                    description="涉及的角色列表",
                    required=False,
                    default=[]
                )
            ],
            examples=[
                {
                    "parameters": {
                        "content_type": "chapter",
                        "chapter_info": {
                            "title": "初入仙门",
                            "summary": "主角通过考验进入仙门",
                            "chapter_number": 1
                        },
                        "style": "traditional",
                        "word_count": 2000
                    },
                    "result": "生成的章节内容..."
                }
            ],
            tags=["writing", "chapter", "novel"]
        )

    @cached("chapter_writer", expire_seconds=1800)  # 使用统一缓存
    async def generate_content(self, content_type: str, context: Dict[str, Any],
                               style: str, word_count: int) -> Dict[str, Any]:
        """生成章节内容 - 使用缓存避免重复生成"""

        # 提取章节信息
        chapter_info = context.get("chapter_info", {})
        plot_context = context.get("plot_context", {})
        characters = context.get("characters", [])

        # 构建提示词
        prompt = self._build_chapter_prompt(
            chapter_info, plot_context, characters, style, word_count
        )

        # 调用LLM生成内容
        response = await self.llm_service.generate_text(
            prompt=prompt,
            max_tokens=word_count * 2,  # 预留空间
            temperature=0.7
        )

        # 处理生成结果
        chapter_content = self._process_generated_content(response, chapter_info)

        return chapter_content

    def _build_chapter_prompt(self, chapter_info: Dict, plot_context: Dict,
                              characters: list, style: str, word_count: int) -> str:
        """构建章节生成提示词"""

        # 获取风格模板
        style_template = self.prompt_manager.get_prompt("writing_styles", style)

        # 构建角色信息
        character_info = "\n".join([
            f"- {char.get('name', '未知')}: {char.get('description', '暂无描述')}"
            for char in characters
        ])

        prompt = f"""
请根据以下信息生成一个章节内容：

章节信息：
- 标题：{chapter_info.get('title', '未命名')}
- 章节号：{chapter_info.get('chapter_number', 1)}
- 摘要：{chapter_info.get('summary', '暂无摘要')}

情节背景：
{plot_context.get('background', '暂无背景')}

主要角色：
{character_info or '暂无角色信息'}

写作要求：
- 风格：{style_template}
- 目标字数：{word_count}字
- 保持情节连贯性
- 突出角色特点

请生成完整的章节内容：
"""

        return prompt

    def _process_generated_content(self, response: str, chapter_info: Dict) -> Dict[str, Any]:
        """处理生成的内容"""

        # 基本清理
        content = response.strip()

        # 统计信息
        word_count = len(content)
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])

        # 构建返回结果
        result = {
            "chapter_number": chapter_info.get("chapter_number", 1),
            "title": chapter_info.get("title", "未命名"),
            "content": content,
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "generation_time": time.time(),
            "metadata": {
                "style": "processed",
                "quality_score": self._calculate_quality_score(content)
            }
        }

        return result

    def _calculate_quality_score(self, content: str) -> float:
        """简单的质量评分"""

        # 基础评分指标
        score = 0.0

        # 长度合理性
        if 500 <= len(content) <= 5000:
            score += 0.3

        # 段落结构
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        if 3 <= len(paragraphs) <= 20:
            score += 0.3

        # 对话比例
        dialogue_lines = len([line for line in content.split('\n') if '"' in line or '"' in line])
        total_lines = len([line for line in content.split('\n') if line.strip()])
        if total_lines > 0:
            dialogue_ratio = dialogue_lines / total_lines
            if 0.1 <= dialogue_ratio <= 0.6:
                score += 0.4

        return min(score, 1.0)


# ============================================================================
# 工具注册函数
# ============================================================================

def register_writing_tools(registry):
    """注册写作工具"""
    registry.register(ChapterWriterTool())
    # 其他写作工具...


# ============================================================================
# 使用示例
# ============================================================================

async def example_usage():
    """使用示例"""

    # 创建工具实例
    chapter_tool = ChapterWriterTool()

    # 准备参数
    parameters = {
        "content_type": "chapter",
        "chapter_info": {
            "title": "踏入修仙路",
            "chapter_number": 1,
            "summary": "少年林云意外获得仙缘，踏上修仙之路"
        },
        "context": {
            "plot_context": {
                "background": "现代都市修仙背景，灵气复苏的时代"
            },
            "characters": [
                {
                    "name": "林云",
                    "description": "18岁高中生，意外获得修仙传承"
                }
            ]
        },
        "style": "modern",
        "word_count": 2000
    }

    # 执行工具
    result = await chapter_tool.execute(parameters)

    print(f"生成章节：{result['title']}")
    print(f"字数：{result['word_count']}")
    print(f"质量评分：{result['metadata']['quality_score']}")

    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
