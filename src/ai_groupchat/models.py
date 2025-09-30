"""定义 FastAPI 接口使用的数据模型。"""  # 模块级 docstring,说明用途

from pydantic import BaseModel, Field  # 导入 BaseModel 和 Field,用于声明数据模型


class WorldState(BaseModel):  # 定义世界观状态模型,继承 BaseModel
    """描述王道异世界当前的时间线与事件。"""  # 类 docstring,说明模型用途

    year: int = Field(..., description="世界年份,体现时间线进度")  # 定义年份字段,记录年代
    season: str = Field(..., description="当前季节,例如春夏秋冬")  # 定义季节字段,标记四季
    major_events: list[str] = Field(  # 定义重大事件字段,为字符串列表
        ...,  # 该字段必须提供,不允许缺失
        description="近期发生的关键事件列表",  # 字段描述,说明用途
    )  # 结束 Field 配置
    location: str = Field(..., description="队伍当前所在的主要地点")  # 定义地点字段,记录坐标


class Persona(BaseModel):  # 定义角色人设模型,继承 BaseModel
    """描述群聊角色的设定与动机。"""  # 类 docstring,说明模型用途

    name: str = Field(..., description="角色名称,用于展示与标识")  # 定义名称字段
    archetype: str = Field(..., description="角色原型或身份")  # 定义 archetype 字段
    speaking_style: str = Field(..., description="角色的口吻与表达风格")  # 定义说话风格字段
    knowledge_tags: list[str] = Field(  # 定义知识标签字段
        ...,  # 该字段必填
        description="角色熟悉的知识标签列表",  # 字段描述说明
    )  # 结束 Field 配置
    moral_axis: str = Field(..., description="角色的道德阵营定位")  # 定义道德阵营字段
    goal: str = Field(..., description="角色在当前剧情中的目标")  # 定义目标字段


class MessageIn(BaseModel):  # 定义输入消息模型,继承 BaseModel
    """用户输入消息的数据结构。"""  # 类 docstring,说明模型意义

    content: str = Field(..., description="用户输入的消息内容")  # 定义消息正文字段
    roles: list[str] | None = Field(  # 定义可选的角色筛选字段
        default=None,  # 默认值为 None 表示使用全部默认角色
        description="可选角色名称列表,为空时使用默认人设",  # 字段描述
    )  # 结束 Field 配置
    location: str | None = Field(  # 定义可选的场景位置字段
        default=None,  # 默认值为 None 表示使用当前世界地点
        description="可覆盖世界观的临时场景位置",  # 字段描述
    )  # 结束 Field 配置


class RoleReply(BaseModel):  # 定义角色回复模型,继承 BaseModel
    """单个角色的回复数据结构。"""  # 类 docstring,说明模型用途

    role: str = Field(..., description="生成回复的角色名称")  # 定义角色名称字段
    text: str = Field(..., description="角色生成的回复文本")  # 定义回复文本字段


class ChatSimulateResponse(BaseModel):  # 定义群聊模拟响应模型
    """群聊模拟响应的数据结构。"""  # 类 docstring,说明模型用途

    replies: list[RoleReply] = Field(  # 定义 replies 字段,为 RoleReply 列表
        ...,  # 指定字段为必填
        description="所有角色的回复列表",  # 字段描述,帮助理解
    )  # 结束 Field 定义
