"""定义世界编辑动作相关的数据模型与处理逻辑。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

from dataclasses import dataclass  # 导入 dataclass,用于内部临时结构
from typing import TYPE_CHECKING, Any  # 导入类型工具

from pydantic import BaseModel, Field, model_validator  # 导入 BaseModel 等工具

from .chunk import Chunk  # 导入区块模型
from .store import UsageLimitError, WorldStore  # 导入存储相关类型
from .tiles import TileType  # 导入瓦片类型枚举

if TYPE_CHECKING:  # 类型检查分支,避免循环导入
    from ..config import Settings  # 仅在类型检查时导入 Settings
    from .quests import QuestProgressor  # 仅在类型检查时导入 QuestProgressor


class WorldActionType(str):  # 定义动作类型,继承 str 便于序列化
    """动作类型枚举的字符串常量集合。"""  # 类 docstring,说明用途

    PLACE_TILE = "PLACE_TILE"  # 铺设基础地块
    PLACE_STRUCTURE = "PLACE_STRUCTURE"  # 放置结构基座
    PLANT_TREE = "PLANT_TREE"  # 种植树苗
    REMOVE_TILE = "REMOVE_TILE"  # 拆除瓦片或装饰
    FARM_TILL = "FARM_TILL"  # 翻耕土地

    @classmethod
    def list_all(cls) -> list[str]:  # 定义列举全部动作的类方法
        """返回所有动作类型字符串列表。"""  # 方法 docstring,说明用途

        return [  # 返回列表
            cls.PLACE_TILE,  # 铺设地块
            cls.PLACE_STRUCTURE,  # 放置结构
            cls.PLANT_TREE,  # 种树
            cls.REMOVE_TILE,  # 拆除
            cls.FARM_TILL,  # 翻土
        ]  # 结束列表


class ChunkCoord(BaseModel):  # 定义区块坐标模型
    """区块坐标数据结构。"""  # 类 docstring,说明用途

    cx: int = Field(..., description="区块 X 坐标")  # 区块横向坐标
    cy: int = Field(..., description="区块 Y 坐标")  # 区块纵向坐标


class Position(BaseModel):  # 定义格子坐标模型
    """格子坐标数据结构。"""  # 类 docstring,说明用途

    x: int = Field(..., ge=0, description="格子 X 坐标")  # 定义横向坐标
    y: int = Field(..., ge=0, description="格子 Y 坐标")  # 定义纵向坐标


class ActionRequest(BaseModel):  # 定义动作请求模型
    """描述一次世界编辑动作的输入参数。"""  # 类 docstring,说明用途

    actor: str = Field(..., description="执行动作的角色名称")  # 执行者
    type: str = Field(..., description="动作类型,使用 WorldActionType 枚举")  # 动作类型
    chunk: ChunkCoord = Field(..., description="目标区块坐标")  # 区块坐标
    pos: Position = Field(..., description="区块内的格子坐标")  # 格子坐标
    payload: dict[str, Any] | None = Field(  # 定义 payload 字段
        default=None,  # 默认无附加数据
        description="附加参数,如目标瓦片",  # 字段描述
    )  # 结束 Field 定义
    client_ts: int = Field(..., ge=0, description="客户端提供的毫秒时间戳")  # 时间戳

    @model_validator(mode="after")  # 定义模型验证器
    def _validate_type(self) -> ActionRequest:  # 定义验证方法
        """确保动作类型为已知枚举。"""  # 方法 docstring,说明用途

        if self.type not in WorldActionType.list_all():  # 检查类型是否合法
            raise ValueError(f"未知动作类型:{self.type}")  # 抛出错误
        return self  # 返回验证后的实例


class ActionChange(BaseModel):  # 定义动作变更摘要模型
    """描述一次动作对单个格子的影响。"""  # 类 docstring,说明用途

    chunk: ChunkCoord = Field(..., description="变更所在区块")  # 区块信息
    pos: Position = Field(..., description="变更所在格子")  # 格子信息
    before: dict[str, Any] = Field(..., description="修改前的格子数据")  # 修改前数据
    after: dict[str, Any] = Field(..., description="修改后的格子数据")  # 修改后数据


class ActionResponse(BaseModel):  # 定义动作响应模型
    """返回动作执行结果与摘要。"""  # 类 docstring,说明用途

    success: bool = Field(..., description="是否执行成功")  # 成功标记
    message: str = Field(..., description="动作执行结果描述")  # 描述信息
    changes: list[ActionChange] = Field(  # 变更列表
        default_factory=list,  # 默认空列表
        description="本次动作涉及的格子变更集合",  # 字段描述
    )  # 结束 Field 定义
    code: int = Field(default=0, description="错误码,成功时为 0")  # 错误码


class ForbiddenRegion(BaseModel):  # 定义禁区模型
    """描述角色无法操作的区块范围。"""  # 类 docstring,说明用途

    cx: int = Field(..., description="禁区所在区块 X 坐标")  # 区块横坐标
    cy: int = Field(..., description="禁区所在区块 Y 坐标")  # 区块纵坐标
    x_range: tuple[int, int] = Field(..., description="允许的 X 范围,含端点")  # X 范围
    y_range: tuple[int, int] = Field(..., description="允许的 Y 范围,含端点")  # Y 范围

    def contains(self, cx: int, cy: int, x: int, y: int) -> bool:  # 定义包含判断方法
        """判断给定坐标是否位于禁区内。"""  # 方法 docstring,说明用途

        if self.cx != cx or self.cy != cy:  # 首先比较区块坐标
            return False  # 不在同一区块则返回 False
        return (  # 返回范围判断
            self.x_range[0] <= x <= self.x_range[1] and self.y_range[0] <= y <= self.y_range[1]
        )


class RolePermission(BaseModel):  # 定义角色权限模型
    """描述角色对世界动作的限制规则。"""  # 类 docstring,说明用途

    allowed_actions: set[str] = Field(  # 定义允许动作字段
        default_factory=set,
        description="允许的动作类型集合",
    )
    tile_whitelist: dict[str, list[TileType]] = Field(  # 定义瓦片白名单
        default_factory=dict,  # 默认空字典
        description="动作对应的瓦片白名单",  # 字段描述
    )  # 结束 Field 定义
    forbidden_remove_bases: list[TileType] = Field(  # 定义拆除禁用的基础瓦片
        default_factory=list,  # 默认空列表
        description="禁止拆除的基础瓦片集合",  # 字段描述
    )  # 结束 Field 定义
    cooldown_seconds: dict[str, int] = Field(  # 定义动作冷却时间
        default_factory=dict,  # 默认空字典
        description="动作冷却秒数配置",  # 字段描述
    )  # 结束 Field 定义
    daily_quota: dict[str, int] = Field(  # 定义每日配额
        default_factory=dict,  # 默认空字典
        description="动作每日允许执行的次数",  # 字段描述
    )  # 结束 Field 定义
    forbidden_regions: list[ForbiddenRegion] = Field(  # 定义禁区列表
        default_factory=list,  # 默认空列表
        description="角色无法进行操作的坐标范围",  # 字段描述
    )  # 结束 Field 定义


class ActionError(Exception):  # 定义动作异常基类
    """动作执行失败时抛出的异常。"""  # 类 docstring,说明用途

    def __init__(self, message: str, code: int = 400) -> None:  # 定义构造函数
        """保存错误信息与错误码。"""  # 方法 docstring,说明用途

        super().__init__(message)  # 调用父类构造
        self.code = code  # 保存错误码
        self.message = message  # 保存错误消息


@dataclass
class UsageContext:  # 定义用量校验上下文的简单数据类
    """存储配额与冷却检查所需的参数。"""  # 类 docstring,说明用途

    quota: int | None  # 每日配额
    cooldown: int | None  # 冷却时间


class ActionProcessor:  # 定义动作处理器
    """协调权限校验、规则判断与持久化的核心类。"""  # 类 docstring,说明用途

    def __init__(  # 定义构造函数
        self,  # 传入实例自身
        store: WorldStore,  # 世界存储对象
        settings: Settings,  # 配置对象
        permissions: dict[str, RolePermission],  # 角色权限映射
        quest_progressor: QuestProgressor,  # 任务推进器
    ) -> None:  # 构造函数返回 None
        """保存依赖对象并准备处理动作。"""  # 方法 docstring,说明用途

        self._store = store  # 保存世界存储实例
        self._settings = settings  # 保存配置实例
        self._permissions = permissions  # 保存权限映射
        self._quest_progressor = quest_progressor  # 保存任务推进器

    def process(self, request: ActionRequest) -> ActionResponse:  # 定义处理动作的方法
        """执行单次动作并返回结果。"""  # 方法 docstring,说明用途

        permission = self._permissions.get(request.actor)  # 根据角色名称获取权限
        if permission is None:  # 如果没有权限配置
            raise ActionError(f"未知角色:{request.actor}", code=404)  # 抛出错误
        action_type = request.type  # 读取动作类型
        if action_type not in permission.allowed_actions:  # 校验动作是否被允许
            raise ActionError("动作未被授权", code=403)  # 抛出权限错误
        self._validate_forbidden_region(permission, request)  # 校验禁区
        usage_ctx = UsageContext(  # 构建用量上下文
            quota=permission.daily_quota.get(action_type),  # 获取配额
            cooldown=permission.cooldown_seconds.get(action_type),  # 获取冷却
        )  # 结束上下文构建
        try:  # 尝试执行用量校验
            self._store.ensure_usage(  # 调用存储校验配额与冷却
                actor=request.actor,  # 传入执行者
                action_type=action_type,  # 传入动作类型
                client_ts=request.client_ts,  # 传入时间戳
                quota=usage_ctx.quota,  # 传入配额
                cooldown=usage_ctx.cooldown,  # 传入冷却
            )  # 结束用量校验
        except UsageLimitError as exc:  # 捕获配额或冷却异常
            raise ActionError(exc.message, code=exc.code) from exc  # 转换为 ActionError
        chunk = self._store.load_chunk(  # 加载目标区块
            cx=request.chunk.cx,  # 区块 X 坐标
            cy=request.chunk.cy,  # 区块 Y 坐标
        )  # 结束加载
        self._validate_position(request.pos, chunk.size)  # 校验坐标范围
        handler = {  # 构建动作处理映射
            WorldActionType.PLACE_TILE: self._handle_place_tile,  # 铺设地块处理函数
            WorldActionType.PLACE_STRUCTURE: self._handle_place_structure,  # 放置结构处理函数
            WorldActionType.PLANT_TREE: self._handle_plant_tree,  # 种树处理函数
            WorldActionType.REMOVE_TILE: self._handle_remove_tile,  # 拆除处理函数
            WorldActionType.FARM_TILL: self._handle_farm_till,  # 翻土处理函数
        }  # 结束映射
        handler_fn = handler[action_type]  # 获取对应的处理函数
        changes = handler_fn(request=request, chunk=chunk, permission=permission)  # 执行动作
        self._store.save_chunk(chunk)  # 保存区块变更
        self._store.append_action_log(  # 记录审计日志
            actor=request.actor,  # 执行者
            action_type=action_type,  # 动作类型
            chunk=request.chunk.model_dump(),  # 区块信息
            pos=request.pos.model_dump(),  # 坐标信息
            payload=request.payload or {},  # 附加参数
        )  # 结束日志记录
        self._quest_progressor.on_action_success(  # 通知任务推进器
            actor=request.actor,  # 执行者
            request=request,  # 动作请求
            changes=changes,  # 变更列表
        )  # 结束任务更新
        return ActionResponse(  # 构造成功响应
            success=True,  # 标记成功
            message="动作执行成功",  # 返回提示消息
            changes=changes,  # 返回变更列表
        )  # 结束响应构造

    def _validate_forbidden_region(  # 定义禁区校验方法
        self,
        permission: RolePermission,  # 角色权限
        request: ActionRequest,  # 动作请求
    ) -> None:  # 方法返回 None
        """若目标坐标位于禁区则抛出异常。"""  # 方法 docstring,说明用途

        for region in permission.forbidden_regions:  # 遍历禁区列表
            if region.contains(  # 调用 contains 判断
                cx=request.chunk.cx,  # 区块 X
                cy=request.chunk.cy,  # 区块 Y
                x=request.pos.x,  # 格子 X
                y=request.pos.y,  # 格子 Y
            ):  # 判断结束
                raise ActionError("目标坐标位于禁区", code=403)  # 抛出错误

    def _validate_position(self, pos: Position, size: int) -> None:  # 定义坐标校验方法
        """保证坐标没有越界。"""  # 方法 docstring,说明用途

        if not 0 <= pos.x < size or not 0 <= pos.y < size:  # 判断范围
            raise ActionError("坐标越界", code=400)  # 抛出错误

    def _handle_place_tile(  # 定义铺设地块处理函数
        self,
        request: ActionRequest,  # 动作请求
        chunk: Chunk,  # 目标区块
        permission: RolePermission,  # 角色权限
    ) -> list[ActionChange]:  # 返回变更列表
        """处理基础地块铺设逻辑。"""  # 方法 docstring,说明用途

        tile_name = self._require_tile_name(request)  # 获取目标瓦片名称
        tile = TileType(tile_name)  # 转换为 TileType 枚举
        allowed_tiles = permission.tile_whitelist.get(WorldActionType.PLACE_TILE, [])  # 获取白名单
        if allowed_tiles and tile not in allowed_tiles:  # 如果存在白名单且不包含目标瓦片
            raise ActionError("瓦片类型未被授权", code=403)  # 抛出错误
        cell = chunk.cell_at(request.pos.x, request.pos.y)  # 获取当前格子
        before = cell.model_dump()  # 记录修改前数据
        new_cell = cell.model_copy(deep=True)  # 深拷贝为新格子
        new_cell.base = tile  # 更新基础瓦片
        if tile == TileType.WATER:  # 若新瓦片是水面
            new_cell.deco = None  # 清空装饰
            new_cell.growth_stage = None  # 清空成长数据
        change = ActionChange(  # 构造变更摘要
            chunk=request.chunk,  # 区块坐标
            pos=request.pos,  # 格子坐标
            before=before,  # 修改前
            after=new_cell.model_dump(),  # 修改后
        )  # 结束构造
        chunk.apply_cell(request.pos.x, request.pos.y, new_cell)  # 应用变更
        return [change]  # 返回变更列表

    def _handle_place_structure(  # 定义放置结构处理函数
        self,
        request: ActionRequest,  # 动作请求
        chunk: Chunk,  # 目标区块
        permission: RolePermission,  # 角色权限
    ) -> list[ActionChange]:  # 返回变更列表
        """处理结构放置逻辑,包括房基与法阵。"""  # 方法 docstring,说明用途

        tile_name = self._require_tile_name(request)  # 获取目标瓦片名称
        tile = TileType(tile_name)  # 转换为枚举
        allowed_tiles = permission.tile_whitelist.get(  # 获取白名单
            WorldActionType.PLACE_STRUCTURE,
            [],
        )
        if allowed_tiles and tile not in allowed_tiles:  # 检查白名单
            raise ActionError("结构类型未被授权", code=403)  # 抛出错误
        if not TileType.is_structure(tile):  # 确保瓦片属于结构类别
            raise ActionError("目标瓦片不是结构类型", code=400)  # 抛出错误
        cell = chunk.cell_at(request.pos.x, request.pos.y)  # 获取当前格子
        if cell.base == TileType.WATER and tile == TileType.HOUSE_BASE:  # 若在水面放置房基
            raise ActionError("水面需先铺设 WOODFLOOR 才能建造", code=400)  # 抛出规则错误
        before = cell.model_dump()  # 记录修改前
        new_cell = cell.model_copy(deep=True)  # 深拷贝格子
        new_cell.base = tile  # 将基础瓦片更新为结构瓦片
        change = ActionChange(  # 构造变更摘要
            chunk=request.chunk,  # 区块坐标
            pos=request.pos,  # 格子坐标
            before=before,  # 修改前数据
            after=new_cell.model_dump(),  # 修改后数据
        )  # 结束构造
        chunk.apply_cell(request.pos.x, request.pos.y, new_cell)  # 应用变更
        return [change]  # 返回变更列表

    def _handle_plant_tree(  # 定义种树处理函数
        self,
        request: ActionRequest,  # 动作请求
        chunk: Chunk,  # 目标区块
        permission: RolePermission,  # 角色权限
    ) -> list[ActionChange]:  # 返回变更列表
        """处理种植树苗的逻辑。"""  # 方法 docstring,说明用途

        cell = chunk.cell_at(request.pos.x, request.pos.y)  # 获取格子
        allowed_tiles = permission.tile_whitelist.get(WorldActionType.PLANT_TREE, [])  # 获取白名单
        if allowed_tiles and cell.base not in allowed_tiles:  # 判断基础瓦片是否可种植
            raise ActionError("当前地表不允许种树", code=400)  # 抛出错误
        if cell.deco is not None:  # 若已有装饰
            raise ActionError("装饰槽已被占用", code=400)  # 抛出错误
        before = cell.model_dump()  # 记录修改前
        new_cell = cell.model_copy(deep=True)  # 深拷贝格子
        new_cell.deco = TileType.TREE_SAPLING  # 放置树苗
        new_cell.growth_stage = 0  # 初始化成长阶段
        change = ActionChange(  # 构造变更摘要
            chunk=request.chunk,  # 区块坐标
            pos=request.pos,  # 格子坐标
            before=before,  # 修改前
            after=new_cell.model_dump(),  # 修改后
        )  # 结束构造
        chunk.apply_cell(request.pos.x, request.pos.y, new_cell)  # 应用变更
        return [change]  # 返回变更列表

    def _handle_remove_tile(  # 定义拆除处理函数
        self,
        request: ActionRequest,  # 动作请求
        chunk: Chunk,  # 目标区块
        permission: RolePermission,  # 角色权限
    ) -> list[ActionChange]:  # 返回变更列表
        """处理拆除或清除装饰的逻辑。"""  # 方法 docstring,说明用途

        cell = chunk.cell_at(request.pos.x, request.pos.y)  # 获取格子
        before = cell.model_dump()  # 记录修改前
        new_cell = cell.model_copy(deep=True)  # 深拷贝格子
        if new_cell.deco is not None:  # 如果存在装饰
            allowed = permission.tile_whitelist.get(WorldActionType.REMOVE_TILE, [])  # 获取白名单
            if allowed and new_cell.deco not in allowed:  # 若装饰不在白名单
                raise ActionError("无权移除此装饰", code=403)  # 抛出错误
            new_cell.deco = None  # 清空装饰
            new_cell.growth_stage = None  # 清空成长数据
        else:  # 若没有装饰则尝试拆除基础瓦片
            allowed = permission.tile_whitelist.get(WorldActionType.REMOVE_TILE, [])  # 获取白名单
            if allowed and new_cell.base not in allowed:  # 判断基础瓦片是否允许拆除
                raise ActionError("无权移除此地块", code=403)  # 抛出错误
            if new_cell.base in permission.forbidden_remove_bases:  # 判断是否在禁拆列表
                raise ActionError("该基础瓦片被保护,无法拆除", code=403)  # 抛出错误
            new_cell.base = TileType.GRASS  # 拆除后恢复为草地
        change = ActionChange(  # 构造变更摘要
            chunk=request.chunk,  # 区块坐标
            pos=request.pos,  # 格子坐标
            before=before,  # 修改前数据
            after=new_cell.model_dump(),  # 修改后数据
        )  # 结束构造
        chunk.apply_cell(request.pos.x, request.pos.y, new_cell)  # 应用变更
        return [change]  # 返回变更列表

    def _handle_farm_till(  # 定义翻土处理函数
        self,
        request: ActionRequest,  # 动作请求
        chunk: Chunk,  # 目标区块
        permission: RolePermission,  # 角色权限(未直接使用,保留以便扩展)
    ) -> list[ActionChange]:  # 返回变更列表
        """处理翻耕土地的逻辑。"""  # 方法 docstring,说明用途

        cell = chunk.cell_at(request.pos.x, request.pos.y)  # 获取格子
        allowed_tiles = permission.tile_whitelist.get(WorldActionType.FARM_TILL, [])  # 获取白名单
        if allowed_tiles and cell.base not in allowed_tiles:  # 判断是否允许翻土
            raise ActionError("当前地块无法翻土", code=400)  # 抛出错误
        if cell.base != TileType.SOIL:  # 只有土地方可翻耕
            raise ActionError("只有 SOIL 可以翻土", code=400)  # 抛出错误
        before = cell.model_dump()  # 记录修改前
        new_cell = cell.model_copy(deep=True)  # 深拷贝格子
        new_cell.base = TileType.FARM  # 更新为农田
        change = ActionChange(  # 构造变更摘要
            chunk=request.chunk,  # 区块坐标
            pos=request.pos,  # 格子坐标
            before=before,  # 修改前数据
            after=new_cell.model_dump(),  # 修改后数据
        )  # 结束构造
        chunk.apply_cell(request.pos.x, request.pos.y, new_cell)  # 应用变更
        return [change]  # 返回变更列表

    def _require_tile_name(self, request: ActionRequest) -> str:  # 定义提取瓦片名的工具方法
        """从请求 payload 中读取目标瓦片名称。"""  # 方法 docstring,说明用途

        if not request.payload or "tile" not in request.payload:  # 如果缺少 tile 字段
            raise ActionError("payload 需要包含 tile 字段", code=400)  # 抛出错误
        tile_name = request.payload["tile"]  # 读取瓦片名称
        if not isinstance(tile_name, str):  # 校验类型
            raise ActionError("tile 字段必须是字符串", code=400)  # 抛出错误
        return tile_name  # 返回瓦片名称
