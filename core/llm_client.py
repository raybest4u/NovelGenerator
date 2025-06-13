# core/llm_client.py
"""
LLM客户端封装
支持OpenAI兼容接口的自定义LLM
"""

import asyncio
import json
from typing import Dict, List, Optional, Union, AsyncGenerator, Callable
from dataclasses import dataclass
from openai import AsyncOpenAI
from loguru import logger
import time
from config.settings import get_settings


@dataclass
class Message:
    """消息类"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict] = None


@dataclass
class LLMResponse:
    """LLM响应类"""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    response_time: float


class LLMClient:
    """LLM客户端"""

    def __init__(self, config=None):
        self.config = config or get_settings().llm
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
            timeout=self.config.timeout
        )
        self.retry_count = 0

    async def chat_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        functions: Optional[List[Dict]] = None,
        function_call: Optional[Union[str, Dict]] = None
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """聊天补全"""

        model = model or self.config.model_name
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # 转换消息格式
        formatted_messages = [
            {
                "role": msg.role,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
                **({"function_call": msg.function_call} if msg.function_call else {})
            }
            for msg in messages
        ]

        request_params = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        if functions:
            request_params["functions"] = functions
        if function_call:
            request_params["function_call"] = function_call

        start_time = time.time()

        try:
            if stream:
                return self._stream_completion(request_params, start_time)
            else:
                return await self._single_completion(request_params, start_time)

        except Exception as e:
            logger.error(f"LLM请求失败: {e}")
            if self.retry_count < self.config.retry_times:
                self.retry_count += 1
                logger.info(f"重试第{self.retry_count}次...")
                await asyncio.sleep(1)
                return await self.chat_completion(
                    messages, model, temperature, max_tokens, stream, functions, function_call
                )
            else:
                self.retry_count = 0
                raise e

    async def _single_completion(self, params: Dict, start_time: float) -> LLMResponse:
        """单次完整响应"""
        response = await self.client.chat.completions.create(**params)

        end_time = time.time()
        response_time = end_time - start_time

        choice = response.choices[0]
        self.retry_count  = 0
        return LLMResponse(
            content=choice.message.content or "",
            usage=response.usage.model_dump() if response.usage else {},
            model=response.model,
            finish_reason=choice.finish_reason or "stop",
            response_time=response_time
        )

    async def _stream_completion(self, params: Dict, start_time: float) -> AsyncGenerator[str, None]:
        """流式响应"""
        stream = await self.client.chat.completions.create(**params)

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class PromptTemplate:
    """提示词模板"""

    def __init__(self, template: str, required_vars: List[str] = None):
        self.template = template
        self.required_vars = required_vars or []

    def format(self, **kwargs) -> str:
        """格式化模板"""
        # 检查必需变量
        missing_vars = [var for var in self.required_vars if var not in kwargs]
        if missing_vars:
            raise ValueError(f"缺少必需变量: {missing_vars}")

        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"模板变量错误: {e}")


class ConversationManager:
    """对话管理器"""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversations: Dict[str, List[Message]] = {}

    def add_message(self, session_id: str, message: Message):
        """添加消息"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        self.conversations[session_id].append(message)

        # 限制历史长度
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]

    def get_conversation(self, session_id: str) -> List[Message]:
        """获取对话历史"""
        return self.conversations.get(session_id, [])

    def clear_conversation(self, session_id: str):
        """清除对话历史"""
        if session_id in self.conversations:
            del self.conversations[session_id]


class FunctionCallHandler:
    """函数调用处理器"""

    def __init__(self):
        self.functions: Dict[str, Callable] = {}

    def register_function(self, name: str, func: Callable, description: str, parameters: Dict):
        """注册函数"""
        self.functions[name] = {
            "function": func,
            "definition": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }

    def get_function_definitions(self) -> List[Dict]:
        """获取函数定义"""
        return [func_info["definition"] for func_info in self.functions.values()]

    async def call_function(self, name: str, arguments: str) -> str:
        """调用函数"""
        if name not in self.functions:
            raise ValueError(f"未知函数: {name}")

        try:
            args = json.loads(arguments)
            func = self.functions[name]["function"]

            if asyncio.iscoroutinefunction(func):
                result = await func(**args)
            else:
                result = func(**args)

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            logger.error(f"函数调用失败 {name}: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)


class LLMService:
    """LLM服务层"""

    def __init__(self):
        self.client = LLMClient()
        self.conversation_manager = ConversationManager()
        self.function_handler = FunctionCallHandler()

    async def generate_text(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        use_history: bool = True,
        **kwargs
    ) -> LLMResponse:
        """生成文本"""

        messages = []

        # 添加系统提示
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))

        # 添加历史对话
        if use_history and session_id:
            history = self.conversation_manager.get_conversation(session_id)
            messages.extend(history)

        # 添加用户输入
        user_message = Message(role="user", content=prompt)
        messages.append(user_message)

        # 生成响应
        response = await self.client.chat_completion(messages, **kwargs)

        # logger.info(f">>生成基础世界设定 response: {response}")
        # 保存对话历史
        if session_id:
            self.conversation_manager.add_message(session_id, user_message)
            self.conversation_manager.add_message(
                session_id,
                Message(role="assistant", content=response.content)
            )

        return response

    async def generate_with_template(
        self,
        template: PromptTemplate,
        template_vars: Dict,
        session_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """使用模板生成文本"""

        prompt = template.format(**template_vars)
        return await self.generate_text(prompt, session_id, **kwargs)

    async def stream_generate(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式生成文本"""

        messages = []

        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))

        if session_id:
            history = self.conversation_manager.get_conversation(session_id)
            messages.extend(history)

        user_message = Message(role="user", content=prompt)
        messages.append(user_message)

        stream = await self.client.chat_completion(messages, stream=True, **kwargs)

        full_response = ""
        async for chunk in stream:
            full_response += chunk
            yield chunk

        # 保存完整对话
        if session_id:
            self.conversation_manager.add_message(session_id, user_message)
            self.conversation_manager.add_message(
                session_id,
                Message(role="assistant", content=full_response)
            )


# 全局LLM服务实例
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """获取LLM服务实例"""
    return llm_service


if __name__ == "__main__":
    async def test():
        service = get_llm_service()

        # 测试基本文本生成
        response = await service.generate_text("你好，请介绍一下自己")
        print(f"响应: {response.content}")
        print(f"用时: {response.response_time:.2f}秒")

        # 测试模板
        template = PromptTemplate(
            "请为我的{genre}小说创建一个{character_type}角色，名字叫{name}",
            required_vars=["genre", "character_type", "name"]
        )

        response = await service.generate_with_template(
            template,
            {"genre": "玄幻", "character_type": "主角", "name": "林风"}
        )
        print(f"模板响应: {response.content}")

    asyncio.run(test())
