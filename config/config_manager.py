# config/config_manager.py
"""
统一配置管理系统 - 增强版
集成enhanced_story_generator的配置需求
"""
import os
import yaml
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Type, Union, List
from pydantic import BaseModel, Field
from loguru import logger


class ConfigLoader(ABC):
    """配置加载器基类"""

    @abstractmethod
    def load(self, file_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        pass

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """检查是否能处理该文件"""
        pass


class YamlConfigLoader(ConfigLoader):
    """YAML配置加载器"""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.yaml', '.yml']

    def load(self, file_path: Path) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"YAML配置加载失败 {file_path}: {e}")
            return {}


class JsonConfigLoader(ConfigLoader):
    """JSON配置加载器"""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.json'

    def load(self, file_path: Path) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSON配置加载失败 {file_path}: {e}")
            return {}


class EnvConfigLoader(ConfigLoader):
    """环境变量配置加载器"""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.env'

    def load(self, file_path: Path) -> Dict[str, Any]:
        try:
            config = {}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()

            # 覆盖环境变量
            config.update(os.environ)
            return config
        except Exception as e:
            logger.error(f"环境变量配置加载失败 {file_path}: {e}")
            return {}


class ConfigManager:
    """统一配置管理器"""

    def __init__(self, config_dir: Union[str, Path] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.loaders = [
            YamlConfigLoader(),
            JsonConfigLoader(),
            EnvConfigLoader()
        ]
        self._configs: Dict[str, Any] = {}
        self._schemas: Dict[str, Type[BaseModel]] = {}

    def register_schema(self, name: str, schema_class: Type[BaseModel]):
        """注册配置模式"""
        self._schemas[name] = schema_class

    def load_config(self, name: str, schema_class: Type[BaseModel] = None) -> Any:
        """加载配置"""
        if name in self._configs:
            return self._configs[name]

        # 尝试不同的加载器和文件扩展名
        config_data = {}

        for loader in self.loaders:
            for ext in ['.yaml', '.yml', '.json', '.env']:
                config_file = self.config_dir / f"{name}{ext}"
                if config_file.exists() and loader.can_handle(config_file):
                    file_data = loader.load(config_file)
                    config_data.update(file_data)
                    logger.debug(f"加载配置文件: {config_file}")

        if not config_data:
            logger.warning(f"配置文件未找到: {name}")
            config_data = {}

        # 应用模式验证
        schema_class = schema_class or self._schemas.get(name)
        if schema_class:
            try:
                config = schema_class(**config_data)
                self._configs[name] = config
                logger.info(f"配置加载成功: {name}")
                return config
            except Exception as e:
                logger.error(f"配置验证失败 {name}: {e}")
                # 返回原始数据作为备选
                self._configs[name] = config_data
                return config_data
        else:
            self._configs[name] = config_data
            return config_data

    def get_config(self, name: str) -> Any:
        """获取已加载的配置"""
        return self._configs.get(name)

    def reload_config(self, name: str):
        """重新加载配置"""
        if name in self._configs:
            del self._configs[name]
        return self.load_config(name)

    def set_config(self, name: str, config: Any):
        """直接设置配置"""
        self._configs[name] = config

    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._configs.copy()


# ============================================================================
# 简化的配置数据类
# ============================================================================

class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = Field(default="openai", description="LLM提供商")
    model_name: str = Field(default="gpt-3.5-turbo", description="模型名称")
    api_key: str = Field(default="", description="API密钥")
    api_base: Optional[str] = Field(default=None, description="API基础URL")
    max_tokens: int = Field(default=2000, description="最大令牌数")
    temperature: float = Field(default=0.7, description="温度参数")
    timeout: int = Field(default=30, description="超时时间")


class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: str = Field(default="sqlite", description="数据库类型")
    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=5432, description="端口号")
    database: str = Field(default="novel_generator", description="数据库名")
    username: str = Field(default="", description="用户名")
    password: str = Field(default="", description="密码")
    pool_size: int = Field(default=10, description="连接池大小")


class MCPConfig(BaseModel):
    """MCP服务器配置"""
    host: str = Field(default="localhost", description="服务器地址")
    port: int = Field(default=8080, description="端口号")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    cors_origins: list = Field(default=["*"], description="CORS允许的源")


class EnhancedGenerationConfig(BaseModel):
    """增强生成配置"""
    # 随机化和多样性
    default_randomization_level: float = Field(default=0.8, description="默认随机化程度(0-1)")
    enable_diversity: bool = Field(default=True, description="启用多样性增强")
    avoid_recent_elements: bool = Field(default=True, description="避免最近使用的元素")
    constraint_adherence: float = Field(default=0.7, description="约束遵循度(0-1)")

    # 创新因子配置
    default_innovation_factors: List[str] = Field(
        default=["叙述技法", "角色创新", "情节转折"],
        description="默认创新因子"
    )
    innovation_intensity: str = Field(default="medium", description="创新强度: low/medium/high")

    # 故事结构偏好
    preferred_story_structures: List[str] = Field(
        default=["英雄之旅", "多线并行", "时间循环"],
        description="偏好的故事结构"
    )
    preferred_character_archetypes: List[str] = Field(
        default=["不羁浪子", "天才少年", "复仇使者"],
        description="偏好的角色原型"
    )
    preferred_world_flavors: List[str] = Field(
        default=["古典仙侠", "现代都市", "蒸汽朋克"],
        description="偏好的世界风味"
    )

    # 内容生成偏好
    avoid_cliches: bool = Field(default=True, description="避免俗套情节")
    enable_plot_twists: bool = Field(default=True, description="启用情节转折")
    narrative_complexity: str = Field(default="medium",
                                      description="叙述复杂度: simple/medium/complex")

    # 主题偏好
    preferred_themes: List[str] = Field(
        default=["修仙", "都市", "科幻", "奇幻"],
        description="偏好的主题类型"
    )
    forbidden_themes: List[str] = Field(default=[], description="禁用的主题类型")


class NovelConfig(BaseModel):
    """小说生成配置 - 增强版"""
    # 基础生成配置
    default_chapter_count: int = Field(default=20, description="默认章节数")
    default_word_count: int = Field(default=2000, description="默认章节字数")
    max_characters: int = Field(default=50, description="最大角色数")
    cache_generated_content: bool = Field(default=True, description="缓存生成内容")

    # 集成增强生成配置
    enhanced: EnhancedGenerationConfig = Field(default_factory=EnhancedGenerationConfig)

    # 生成质量配置
    quality_threshold: float = Field(default=0.7, description="质量阈值")
    auto_revision: bool = Field(default=True, description="自动修订")
    consistency_check: bool = Field(default=True, description="一致性检查")


class AppSettings(BaseModel):
    """应用主配置"""
    app_name: str = Field(default="Novel Generator", description="应用名称")
    version: str = Field(default="2.0.0", description="版本号")
    debug: bool = Field(default=False, description="调试模式")

    # 子配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    novel: NovelConfig = Field(default_factory=NovelConfig)

    # 路径配置
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    templates_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data" / "templates")
    generated_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data" / "generated")


# ============================================================================
# 全局配置管理
# ============================================================================

# 创建全局配置管理器
_config_manager = ConfigManager()

# 注册配置模式
_config_manager.register_schema("app", AppSettings)
_config_manager.register_schema("llm", LLMConfig)
_config_manager.register_schema("database", DatabaseConfig)
_config_manager.register_schema("mcp", MCPConfig)
_config_manager.register_schema("novel", NovelConfig)
_config_manager.register_schema("enhanced", EnhancedGenerationConfig)


def get_config_manager() -> ConfigManager:
    """获取配置管理器"""
    return _config_manager


def load_app_config() -> AppSettings:
    """加载应用配置"""
    return _config_manager.load_config("app", AppSettings)


# 便捷函数
def get_novel_config() -> NovelConfig:
    """获取小说配置"""
    app_config = load_app_config()
    return app_config.novel


def get_enhanced_config() -> EnhancedGenerationConfig:
    """获取增强生成配置"""
    novel_config = get_novel_config()
    return novel_config.enhanced


if __name__ == "__main__":
    # 测试配置加载
    config = load_app_config()
    print("配置加载成功:")
    print(f"- 应用名称: {config.app_name}")
    print(f"- 默认章节数: {config.novel.default_chapter_count}")
    print(f"- 随机化程度: {config.novel.enhanced.default_randomization_level}")
    print(f"- 启用多样性: {config.novel.enhanced.enable_diversity}")
