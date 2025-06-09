
# tests/test_core.py
"""
核心模块测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from core.base_tools import ToolRegistry, ToolBuilder, BaseTool, ToolDefinition, ToolParameter
from core.llm_client import LLMService, Message, PromptTemplate


class TestToolRegistry:
    """工具注册表测试"""

    def test_register_tool(self, tool_registry):
        """测试工具注册"""

        # 创建测试工具
        tool = (ToolBuilder()
                .name("test_tool")
                .description("测试工具")
                .parameter("input", "string", "输入参数")
                .execute(lambda params, context: "test result")
                .build())

        tool_registry.register(tool)

        assert "test_tool" in tool_registry.tools
        assert len(tool_registry.list_tools()) == 1

    @pytest.mark.asyncio
    async def test_execute_tool(self, tool_registry):
        """测试工具执行"""

        # 创建测试工具
        async def test_func(params, context=None):
            return f"Hello {params.get('name', 'World')}"

        tool = (ToolBuilder()
                .name("hello_tool")
                .description("问候工具")
                .parameter("name", "string", "姓名", required=False)
                .execute(test_func)
                .build())

        tool_registry.register(tool)

        from core.base_tools import ToolCall
        call = ToolCall(
            id="test_call",
            name="hello_tool",
            parameters={"name": "Alice"}
        )

        response = await tool_registry.execute_tool(call)

        assert response.success
        assert "Hello Alice" in response.result


class TestPromptTemplate:
    """提示词模板测试"""

    def test_format_template(self):
        """测试模板格式化"""
        template = PromptTemplate(
            "请为{genre}小说创建{count}个角色",
            required_vars=["genre", "count"]
        )

        result = template.format(genre="玄幻", count=3)

        assert "请为玄幻小说创建3个角色" == result

    def test_missing_variables(self):
        """测试缺少变量的情况"""
        template = PromptTemplate(
            "请创建{genre}小说",
            required_vars=["genre", "theme"]
        )

        with pytest.raises(ValueError):
            template.format(genre="玄幻")  # 缺少theme


class TestMessage:
    """消息类测试"""

    def test_create_message(self):
        """测试创建消息"""
        message = Message(
            role="user",
            content="请帮我写一个故事"
        )

        assert message.role == "user"
        assert message.content == "请帮我写一个故事"
        assert message.name is None

