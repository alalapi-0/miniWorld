"""定义世界状态模型与辅助函数。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

from pydantic import BaseModel, Field  # 导入 BaseModel 与 Field,用于数据建模


class WorldState(BaseModel):  # 定义世界状态模型
    """描述世界时间线、地点以及数据版本。"""  # 类 docstring,说明用途

    version: str = Field(default="v1", description="世界状态数据版本")  # 数据版本
    year: int = Field(..., description="当前年份")  # 年份
    season: str = Field(..., description="当前季节")  # 季节
    location: str = Field(..., description="当前地点描述")  # 地点
    major_events: list[str] = Field(  # 定义重大事件字段
        default_factory=list,  # 默认空列表
        description="正在发生的重大事件列表",  # 字段描述
    )  # 结束 Field 定义
    seed: int = Field(default=42, description="随机种子,用于确定性生成")  # 随机种子

    class Config:  # 定义内部配置
        """配置项用于保持字段顺序。"""  # Config docstring

        frozen = True  # 将模型设为不可变,便于缓存

    def describe(self) -> str:  # 定义描述方法
        """返回用于提示词的世界概况字符串。"""  # 方法 docstring,说明用途

        events = "、".join(self.major_events) if self.major_events else "暂无重大事件"  # 拼接事件
        return f"{self.year}年{self.season},{self.location},事件:{events}"  # 返回格式化字符串
