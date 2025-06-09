# config/settings.py
"""
配置管理模块
支持多环境配置和动态加载
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from pydantic.v1 import BaseSettings, Field


class LLMConfig(BaseSettings):
    """LLM配置"""
    api_base: str = Field(default="http://localhost:8000/v1", description="API基础URL")
    api_key: str = Field(default="your-api-key", description="API密钥")
    model_name: str = Field(default="qwen2.5-72b-instruct", description="模型名称")
    max_tokens: int = Field(default=4000, description="最大token数")
    temperature: float = Field(default=0.7, description="温度参数")
    timeout: int = Field(default=60, description="请求超时时间")
    retry_times: int = Field(default=3, description="重试次数")


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    url: str = Field(default="sqlite:///fantasy_novel.db", description="数据库URL")
    echo: bool = Field(default=False, description="是否打印SQL")
    pool_size: int = Field(default=10, description="连接池大小")


class RedisConfig(BaseSettings):
    """Redis配置"""
    host: str = Field(default="localhost", description="Redis主机")
    port: int = Field(default=6379, description="Redis端口")
    db: int = Field(default=0, description="数据库编号")
    password: Optional[str] = Field(default=None, description="密码")


class NovelConfig(BaseSettings):
    """小说生成配置"""
    default_genre: str = Field(default="玄幻", description="默认类型")
    chapter_word_count: int = Field(default=3000, description="章节字数")
    max_chapters: int = Field(default=100, description="最大章节数")
    auto_save: bool = Field(default=True, description="自动保存")
    consistency_check: bool = Field(default=True, description="一致性检查")


class MCPConfig(BaseSettings):
    """MCP服务器配置"""
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8080, description="服务器端口")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")


class AppSettings(BaseSettings):
    """应用程序主配置"""

    # 基础配置
    app_name: str = Field(default="Fantasy Novel MCP", description="应用名称")
    version: str = Field(default="1.0.0", description="版本号")
    debug: bool = Field(default=False, description="调试模式")

    # 子配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    novel: NovelConfig = Field(default_factory=NovelConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)

    # 文件路径
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    templates_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data" / "templates")
    generated_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data" / "generated")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


class PromptManager:
    """提示词管理器"""

    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self._prompts_cache: Dict[str, Dict[str, Any]] = {}

    def load_prompts(self, category: str) -> Dict[str, Any]:
        """加载指定类别的提示词"""
        if category in self._prompts_cache:
            return self._prompts_cache[category]

        prompt_file = self.prompts_dir / f"{category}.yaml"
        if not prompt_file.exists():
            raise FileNotFoundError(f"提示词文件不存在: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)

        self._prompts_cache[category] = prompts
        return prompts

    def get_prompt(self, category: str, key: str, **kwargs) -> str:
        """获取格式化的提示词"""
        prompts = self.load_prompts(category)
        template = prompts.get(key)

        if not template:
            raise KeyError(f"提示词不存在: {category}.{key}")

        if kwargs:
            from jinja2 import Template
            return Template(template).render(**kwargs)

        return template

    def reload_prompts(self):
        """重新加载所有提示词"""
        self._prompts_cache.clear()


# 全局配置实例
settings = AppSettings()
prompt_manager = PromptManager(settings.project_root / "config" / "prompts")


def get_settings() -> AppSettings:
    """获取应用配置"""
    return settings


def get_prompt_manager() -> PromptManager:
    """获取提示词管理器"""
    return prompt_manager


def update_settings(**kwargs):
    """动态更新配置"""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)


# 配置验证
def validate_config():
    """验证配置有效性"""
    # 检查必要的目录
    for dir_path in [settings.data_dir, settings.templates_dir, settings.generated_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # 验证LLM配置
    if not settings.llm.api_key or settings.llm.api_key == "your-api-key":
        print("警告: 请设置有效的LLM API密钥")

    print("配置验证完成")


if __name__ == "__main__":
    validate_config()
    print("当前配置:")
    print(f"- 应用名称: {settings.app_name}")
    print(f"- 版本: {settings.version}")
    print(f"- LLM模型: {settings.llm.model_name}")
    print(f"- 数据目录: {settings.data_dir}")
