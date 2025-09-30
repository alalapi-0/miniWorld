"""定义任务与进度推进相关的数据模型。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

from collections.abc import Iterable  # 导入 Iterable,用于类型注解
from enum import Enum  # 导入 Enum,用于定义状态枚举

from pydantic import BaseModel, Field, model_validator  # 导入 BaseModel 等工具

from .actions import ActionChange, ActionRequest, ChunkCoord  # 导入动作相关类型
from .store import WorldStore  # 导入 WorldStore,用于读写数据
from .tiles import TileType  # 导入 TileType,用于瓦片约束


class QuestStatus(str, Enum):  # 定义任务状态枚举
    """描述任务当前的推进状态。"""  # 类 docstring,说明用途

    OPEN = "OPEN"  # 未开始
    IN_PROGRESS = "IN_PROGRESS"  # 进行中
    DONE = "DONE"  # 已完成


class ActionRequirement(BaseModel):  # 定义动作需求模型
    """描述达成任务所需的特定动作条件。"""  # 类 docstring,说明用途

    action_type: str = Field(..., description="目标动作类型")  # 动作类型
    target_tile: TileType | None = Field(  # 定义目标瓦片字段
        default=None,  # 默认不限瓦片
        description="需要达成的目标瓦片类型,可为空",  # 字段描述
    )  # 结束 Field 定义
    chunk: ChunkCoord = Field(..., description="任务所在区块")  # 目标区块
    x_range: tuple[int, int] = Field(  # 定义 X 范围
        default=(0, 31),  # 默认覆盖整个区块
        description="X 坐标范围,闭区间",  # 字段描述
    )  # 结束 Field 定义
    y_range: tuple[int, int] = Field(  # 定义 Y 范围
        default=(0, 31),  # 默认覆盖整个区块
        description="Y 坐标范围,闭区间",  # 字段描述
    )  # 结束 Field 定义
    target_count: int = Field(..., ge=1, description="需要完成的次数")  # 目标次数
    progress: int = Field(default=0, ge=0, description="当前已完成次数")  # 当前进度
    layer: str = Field(  # 定义监控层级
        default="base",  # 默认关注基础瓦片
        description="检测变更的层级,可为 base 或 deco",  # 字段描述
    )  # 结束 Field 定义

    @model_validator(mode="after")  # 定义验证器
    def _validate_layer(self) -> ActionRequirement:  # 定义验证方法
        """确保 layer 字段合法。"""  # 方法 docstring,说明用途

        if self.layer not in {"base", "deco"}:  # 判断 layer 是否合法
            raise ValueError("layer 仅支持 base 或 deco")  # 抛出错误
        if self.progress > self.target_count:  # 如果进度超过目标
            self.progress = self.target_count  # 自动截断
        return self  # 返回自身

    def matches(self, change: ActionChange, action_type: str) -> bool:  # 定义匹配判定方法
        """判断给定变更是否满足需求基本条件。"""  # 方法 docstring,说明用途

        if action_type != self.action_type:  # 判断动作类型
            return False  # 不匹配
        if change.chunk.cx != self.chunk.cx or change.chunk.cy != self.chunk.cy:  # 判断区块
            return False  # 不匹配
        if not (self.x_range[0] <= change.pos.x <= self.x_range[1]):  # 判断 X 范围
            return False  # 不匹配
        return self.y_range[0] <= change.pos.y <= self.y_range[1]  # 返回最终判断

    def apply_change(self, change: ActionChange) -> bool:  # 定义应用变更的方法
        """根据变更更新进度,返回是否发生变化。"""  # 方法 docstring,说明用途

        target_layer = change.after.get(self.layer)  # 获取目标层的值
        if (  # 判断瓦片是否匹配
            self.target_tile is not None and target_layer != self.target_tile.value
        ):
            return False  # 未匹配
        if self.progress >= self.target_count:  # 若已完成
            return False  # 不再增加
        self.progress += 1  # 增加进度
        if self.progress > self.target_count:  # 防止超过目标
            self.progress = self.target_count  # 截断进度
        return True  # 返回发生变化

    def is_completed(self) -> bool:  # 定义完成状态判断方法
        """判断该需求是否已完成。"""  # 方法 docstring,说明用途

        return self.progress >= self.target_count  # 返回布尔值


class Quest(BaseModel):  # 定义任务模型
    """描述一项世界建设任务的完整信息。"""  # 类 docstring,说明用途

    id: str = Field(..., description="任务唯一标识")  # 任务 ID
    title: str = Field(..., description="任务标题")  # 标题
    desc: str = Field(..., description="任务描述")  # 描述
    giver: str = Field(..., description="发布者或自驱角色")  # 发布者
    assignee: list[str] = Field(default_factory=list, description="任务执行角色列表")  # 执行者
    status: QuestStatus = Field(default=QuestStatus.OPEN, description="任务状态")  # 状态
    requirements: list[ActionRequirement] = Field(  # 定义需求列表
        default_factory=list,  # 默认空列表
        description="完成任务所需的动作条件集合",  # 字段描述
    )  # 结束 Field 定义
    rewards: list[str] = Field(default_factory=list, description="任务奖励描述")  # 奖励
    created_at: int = Field(..., description="创建时间戳(毫秒)")  # 创建时间
    updated_at: int = Field(..., description="更新时间戳(毫秒)")  # 更新时间

    def is_completed(self) -> bool:  # 定义任务完成判定方法
        """判断任务是否所有需求均已完成。"""  # 方法 docstring,说明用途

        return all(req.is_completed() for req in self.requirements)  # 返回布尔值


class QuestProgressor:  # 定义任务推进器
    """负责读写任务数据并在动作成功后更新进度。"""  # 类 docstring,说明用途

    def __init__(self, store: WorldStore) -> None:  # 定义构造函数
        """保存世界存储实例,供进度同步使用。"""  # 方法 docstring,说明用途

        self._store = store  # 保存世界存储

    def get_quests(self) -> list[Quest]:  # 定义获取任务列表的方法
        """从存储中读取并解析所有任务。"""  # 方法 docstring,说明用途

        raw_list = self._store.load_quests_raw()  # 读取原始数据
        return [Quest.model_validate(item) for item in raw_list]  # 转换为 Quest 实例列表

    def save_quests(self, quests: Iterable[Quest]) -> None:  # 定义保存任务列表的方法
        """将任务列表序列化回磁盘。"""  # 方法 docstring,说明用途

        payload = [quest.model_dump(mode="json") for quest in quests]  # 序列化数据
        self._store.save_quests_raw(payload)  # 写入磁盘

    def on_action_success(  # 定义动作成功回调方法
        self,
        actor: str,  # 执行动作的角色
        request: ActionRequest,  # 动作请求
        changes: list[ActionChange],  # 变更列表
    ) -> None:  # 方法返回 None
        """根据动作结果推进任务进度。"""  # 方法 docstring,说明用途

        quests = self.get_quests()  # 读取任务列表
        updated = False  # 标记是否有任务更新
        for quest in quests:  # 遍历任务
            if quest.status == QuestStatus.DONE:  # 若任务已完成
                continue  # 跳过
            quest_changed = False  # 标记单个任务是否更新
            for requirement in quest.requirements:  # 遍历需求
                for change in changes:  # 遍历变更
                    if not requirement.matches(change, request.type):  # 判断是否匹配
                        continue  # 不匹配则跳过
                    if requirement.apply_change(change):  # 应用变更并检查是否更新
                        quest_changed = True  # 标记需求更新
            if quest_changed:  # 若本任务有进度变化
                quest.updated_at = request.client_ts  # 更新任务时间
                if quest.status == QuestStatus.OPEN:  # 若之前为 OPEN
                    quest.status = QuestStatus.IN_PROGRESS  # 切换为进行中
                if quest.is_completed():  # 若任务全部完成
                    quest.status = QuestStatus.DONE  # 标记完成
                    self._store.append_action_log(  # 写入审计日志
                        actor="系统",  # 使用系统作为记录者
                        action_type="QUEST_DONE",  # 日志类型
                        chunk={"cx": request.chunk.cx, "cy": request.chunk.cy},  # 复用动作位置
                        pos={"x": request.pos.x, "y": request.pos.y},  # 复用坐标
                        payload={"quest_id": quest.id, "actor": actor},  # 附带任务信息
                    )  # 结束日志写入
                updated = True  # 标记总体更新
        if updated:  # 若存在更新
            self.save_quests(quests)  # 将任务写回磁盘
