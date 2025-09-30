"""定义 FastAPI 接口所需的数据模型。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

from pydantic import BaseModel, Field  # 导入 BaseModel 与 Field,用于数据建模


class WorldState(BaseModel):  # 定义世界状态模型
    """描述世界时间线与当前事件。"""  # 类 docstring,说明用途

    year: int = Field(..., description="世界年份")  # 年份
    season: str = Field(..., description="当前季节")  # 季节
    major_events: list[str] = Field(  # 定义重大事件字段
        default_factory=list,  # 默认空列表
        description="重大事件列表",  # 字段描述
    )  # 结束 Field 定义
    location: str = Field(..., description="当前地点描述")  # 地点


class Persona(BaseModel):  # 定义角色人设模型
    """描述角色设定、语气与目标。"""  # 类 docstring,说明用途

    name: str = Field(..., description="角色名称")  # 名称
    archetype: str = Field(..., description="角色原型或身份")  # 原型
    speaking_style: str = Field(..., description="说话风格")  # 说话风格
    knowledge_tags: list[str] = Field(  # 知识标签
        default_factory=list,  # 默认空列表
        description="角色擅长的知识标签",  # 字段描述
    )  # 结束 Field 定义
    moral_axis: str = Field(..., description="道德阵营")  # 阵营
    goal: str = Field(..., description="当前目标")  # 目标


class MessageIn(BaseModel):  # 定义聊天输入模型
    """描述 /chat/simulate 的请求体。"""  # 类 docstring,说明用途

    content: str = Field(..., description="用户输入文本")  # 输入内容
    roles: list[str] | None = Field(  # 可选角色字段
        default=None,  # 默认使用全部角色
        description="限定参与对话的角色名称列表",  # 字段描述
    )  # 结束 Field 定义
    location: str | None = Field(  # 可选地点字段
        default=None,  # 默认不覆盖
        description="临时覆盖的对话地点",  # 字段描述
    )  # 结束 Field 定义


class RoleReply(BaseModel):  # 定义角色回复模型
    """描述单个角色在群聊中的回答。"""  # 类 docstring,说明用途

    role: str = Field(..., description="角色名称")  # 角色名称
    text: str = Field(..., description="角色回复文本")  # 回复内容


class ChatSimulateResponse(BaseModel):  # 定义聊天响应模型
    """描述 /chat/simulate 的响应结构。"""  # 类 docstring,说明用途

    replies: list[RoleReply] = Field(  # 回复列表
        default_factory=list,  # 默认空列表
        description="所有角色的回复集合",  # 字段描述
    )  # 结束 Field 定义


class ErrorResponse(BaseModel):  # 定义统一错误响应模型
    """描述错误码、错误信息与可选详情。"""  # 类 docstring,说明用途

    code: int = Field(..., description="错误码")  # 错误码
    msg: str = Field(..., description="错误信息")  # 错误信息
    detail: dict | None = Field(  # 可选详情字段
        default=None,  # 默认无详情
        description="附加错误详情",  # 字段描述
    )  # 结束 Field 定义


class PersonaPermissionSummary(BaseModel):  # 定义人设权限摘要模型
    """组合角色人设与权限信息供前端展示。"""  # 类 docstring,说明用途

    persona: Persona = Field(..., description="角色人设数据")  # 人设数据
    allowed_actions: list[str] = Field(  # 定义允许动作字段
        default_factory=list,  # 默认空列表
        description="角色被授权的动作类型列表",  # 字段描述
    )  # 结束 Field 定义
    tile_whitelist: dict[str, list[str]] = Field(  # 定义瓦片白名单摘要
        default_factory=dict,  # 默认空字典
        description="动作到瓦片列表的映射",  # 字段描述
    )  # 结束 Field 定义
    cooldown_seconds: dict[str, int] = Field(  # 定义冷却时间摘要
        default_factory=dict,  # 默认空字典
        description="动作冷却秒数字典",  # 字段描述
    )  # 结束 Field 定义
    daily_quota: dict[str, int] = Field(  # 定义配额摘要
        default_factory=dict,  # 默认空字典
        description="动作每日配额字典",  # 字段描述
    )  # 结束 Field 定义


class PersonasResponse(BaseModel):  # 定义 /personas 的响应模型
    """将所有角色与权限摘要封装为统一结构。"""  # 类 docstring,说明用途

    personas: list[PersonaPermissionSummary] = Field(  # 定义 personas 字段
        default_factory=list,  # 默认空列表
        description="角色权限摘要列表",  # 字段描述
    )  # 结束 Field 定义
