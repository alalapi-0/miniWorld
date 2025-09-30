"""定义 FastAPI 接口使用的数据模型。"""  # 模块级 docstring，说明用途

from pydantic import BaseModel, Field  # 导入 BaseModel 和 Field，用于声明数据模型


class MessageIn(BaseModel):  # 定义输入消息模型，继承 BaseModel
    """用户输入消息的数据结构。"""  # 类 docstring，说明模型意义

    content: str = Field(..., description="用户输入的消息内容")  # 定义 content 字段，包含描述


class RoleReply(BaseModel):  # 定义角色回复模型，继承 BaseModel
    """单个角色的回复数据结构。"""  # 类 docstring，说明模型用途

    role: str = Field(..., description="生成回复的角色名称")  # 定义角色名称字段
    text: str = Field(..., description="角色生成的回复文本")  # 定义回复文本字段


class ChatSimulateResponse(BaseModel):  # 定义群聊模拟响应模型
    """群聊模拟响应的数据结构。"""  # 类 docstring，说明模型用途

    replies: list[RoleReply] = Field(  # 定义 replies 字段，为 RoleReply 列表
        ...,  # 指定字段为必填
        description="所有角色的回复列表",  # 字段描述，帮助理解
    )  # 结束 Field 定义
