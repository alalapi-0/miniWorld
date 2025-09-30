"""服务层包的初始化模块。"""  # 模块级 docstring，说明用途

from .generator import BaseRoleGenerator, LocalDeterministicGenerator  # 导入生成器接口与实现，便于包外直接使用

__all__ = ["BaseRoleGenerator", "LocalDeterministicGenerator"]  # 导出生成器相关类，方便外部引用
