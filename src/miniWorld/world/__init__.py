"""miniWorld 世界模型包的初始化模块。"""  # 模块级 docstring,说明包作用  # noqa: N999

from .actions import (  # 导入动作相关类型,供外部使用
    ActionRequest,  # 动作请求模型
    ActionResponse,  # 动作响应模型
    RolePermission,  # 权限模型
    WorldActionType,  # 动作类型枚举
)
from .chunk import Chunk, TileCell  # 导入 Chunk 与 TileCell,供外部使用
from .tiles import TileType  # 导入 TileType 枚举,供外部使用
from .world_state import WorldState  # 导入 WorldState,供外部使用

__all__ = [  # 定义导出列表,控制 from package import * 行为
    "ActionRequest",  # 导出动作请求
    "ActionResponse",  # 导出动作响应
    "Chunk",  # 导出区块模型
    "RolePermission",  # 导出角色权限
    "TileCell",  # 导出格子模型
    "TileType",  # 导出瓦片类型
    "WorldActionType",  # 导出动作枚举
    "WorldState",  # 导出世界状态
]
