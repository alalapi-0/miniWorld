"""应用配置模块，负责加载与缓存运行所需的环境变量。"""  # 模块级 docstring，说明功能

from functools import lru_cache  # 从 functools 导入 lru_cache，用于缓存设置实例
from typing import List  # 导入 List 类型注解，方便声明列表类型

from pydantic_settings import (  # 从 pydantic_settings 导入所需类
    BaseSettings,  # 导入 BaseSettings，用于定义配置类
    SettingsConfigDict,  # 导入 SettingsConfigDict，用于声明模型配置
)


class Settings(BaseSettings):  # 定义 Settings 类，继承 BaseSettings 以加载环境变量
    """应用的配置对象，集中描述运行参数。"""  # 类 docstring，概述用途

    app_name: str = "AI GroupChat Simulator"  # 应用名称字段，提供默认值
    debug: bool = True  # 调试模式开关，默认启用便于开发
    host: str = "127.0.0.1"  # 本地服务器监听地址，默认回环
    port: int = 8000  # 服务监听端口，默认 8000
    default_roles: List[str] = ["贤者", "剑士", "魔导师"]  # 默认角色列表，提供示例角色
    reply_sentences_per_role: int = 2  # 每个角色生成的句子数量，控制回复长度
    seed: int = 42  # 随机种子，确保生成器可重复
    model_config = SettingsConfigDict(  # 定义模型配置，替代旧的 Config 类
        env_file=".env",  # 指定默认环境变量文件
        env_file_encoding="utf-8",  # 指定文件编码，保障中文安全
    )  # 结束模型配置定义


@lru_cache  # 使用 lru_cache 装饰器缓存配置实例，避免重复读取
def get_settings() -> Settings:  # 定义获取配置的函数，返回 Settings 类型
    """返回应用的配置实例，利用缓存减少 I/O。"""  # 函数 docstring，解释作用

    return Settings()  # 创建并返回 Settings 实例，应用默认缓存
