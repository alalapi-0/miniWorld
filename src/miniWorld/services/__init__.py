"""服务层包的初始化模块。"""  # 模块级 docstring,说明用途  # noqa: N999

from .generator import (  # 从生成器模块导入公开类
    BaseRoleGenerator,  # 生成器协议接口
    ExternalLLMGenerator,  # 预留的外部 LLM 生成器
    LocalDeterministicGenerator,  # 基础本地生成器
    PersonaAwareGenerator,  # 融合世界观的人设生成器
)  # 结束导入列表

__all__ = [  # 定义模块导出的符号列表
    "BaseRoleGenerator",  # 导出生成器协议
    "ExternalLLMGenerator",  # 导出外部生成器占位实现
    "LocalDeterministicGenerator",  # 导出本地生成器
    "PersonaAwareGenerator",  # 导出人设生成器
]  # 结束导出列表
