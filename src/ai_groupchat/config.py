"""应用配置模块,负责加载与缓存运行所需的环境变量。"""  # 模块级 docstring,说明功能

from __future__ import annotations  # 导入未来注解特性,支持前向引用

import json  # 导入 json 模块,用于解析人设覆盖配置
from functools import lru_cache  # 从 functools 导入 lru_cache,用于缓存设置实例

from pydantic import Field  # 导入 Field,处理字段声明
from pydantic_settings import (  # 从 pydantic_settings 导入所需类
    BaseSettings,  # 导入 BaseSettings,用于定义配置类
    SettingsConfigDict,  # 导入 SettingsConfigDict,用于声明模型配置
)

from .models import Persona, WorldState  # 导入 Persona 与 WorldState,用于构建默认数据


class Settings(BaseSettings):  # 定义 Settings 类,继承 BaseSettings 以加载环境变量
    """应用的配置对象,集中描述运行参数。"""  # 类 docstring,概述用途

    app_name: str = Field(  # 定义应用名称字段
        default="AI GroupChat Simulator",  # 设置默认名称
        description="FastAPI 应用展示名称",  # 字段描述
    )  # 结束 Field 配置
    debug: bool = Field(default=True, description="是否启用调试模式")  # 定义调试模式字段
    host: str = Field(default="127.0.0.1", description="服务器监听地址")  # 定义监听地址字段
    port: int = Field(default=8000, description="服务器监听端口")  # 定义端口字段
    seed: int = Field(default=42, description="生成器随机种子")  # 定义随机种子字段
    reply_sentences_per_role: int = Field(  # 定义每个角色句子数量字段
        default=2,  # 默认每个角色输出两句
        description="角色回复的句子数量提示",  # 字段描述
    )  # 结束 Field 配置
    default_location: str = Field(  # 定义默认地点字段
        default="格兰王都",  # 设置默认地点
        description="王道异世界当前默认地点",  # 字段描述
        alias="DEFAULT_LOCATION",  # 指定环境变量名称
    )  # 结束 Field 配置
    world_year: int = Field(  # 定义世界年份字段
        default=1024,  # 设定默认年份
        description="王道异世界当前年份",  # 字段描述
        alias="WORLD_YEAR",  # 指定环境变量名称
    )  # 结束 Field 配置
    world_season: str = Field(  # 定义世界季节字段
        default="春",  # 默认季节设为春
        description="王道异世界当前季节",  # 字段描述
        alias="WORLD_SEASON",  # 指定环境变量名称
    )  # 结束 Field 配置
    world_major_events: list[str] = Field(  # 定义重大事件列表字段
        default_factory=lambda: [  # 使用默认工厂提供列表
            "王都圣印遗失引发王国震动",  # 事件一,描述剧情背景
            "边境魔导回路出现紊乱",  # 事件二,描述世界危机
        ],  # 结束列表
        description="影响世界局势的关键事件列表",  # 字段描述
    )  # 结束 Field 配置
    personas_json: str | None = Field(  # 定义可选的人设覆盖 JSON 字段
        default=None,  # 默认不覆盖
        description="使用 JSON 字符串覆盖默认人设",  # 字段描述
        alias="PERSONAS_JSON",  # 指定环境变量名称
    )  # 结束 Field 配置
    use_external_llm: bool = Field(  # 定义外部 LLM 开关字段
        default=False,  # 默认关闭,保持离线
        description="是否启用外部 LLM 生成",  # 字段描述
        alias="USE_EXTERNAL_LLM",  # 指定环境变量名称
    )  # 结束 Field 配置
    llm_provider: str = Field(  # 定义 LLM 服务提供商字段
        default="openai",  # 默认提供商标签
        description="外部 LLM 服务提供商标识",  # 字段描述
        alias="LLM_PROVIDER",  # 指定环境变量名称
    )  # 结束 Field 配置
    openai_api_key: str | None = Field(  # 定义 OpenAI API Key 字段
        default=None,  # 默认为空
        description="OpenAI API 密钥,可在启用外部 LLM 时提供",  # 字段描述
        alias="OPENAI_API_KEY",  # 指定环境变量名称
    )  # 结束 Field 配置
    openai_base_url: str | None = Field(  # 定义 OpenAI Base URL 字段
        default=None,  # 默认不指定代理地址
        description="OpenAI API 代理地址或自定义 Base URL",  # 字段描述
        alias="OPENAI_BASE_URL",  # 指定环境变量名称
    )  # 结束 Field 配置
    model_config = SettingsConfigDict(  # 定义模型配置,替代旧的 Config 类
        env_file=".env",  # 指定默认环境变量文件
        env_file_encoding="utf-8",  # 指定文件编码,保障中文安全
        populate_by_name=True,  # 允许通过字段名与别名同时赋值
    )  # 结束模型配置定义

    @property
    def world_state(self) -> WorldState:  # 定义 world_state 只读属性,返回世界状态实例
        """构造当前王道异世界的世界状态。"""  # 属性 docstring,说明用途

        return WorldState(  # 返回 WorldState 实例
            year=self.world_year,  # 使用配置中的年份
            season=self.world_season,  # 使用配置中的季节
            major_events=self.world_major_events,  # 使用配置中的重大事件列表
            location=self.default_location,  # 使用配置中的默认地点
        )  # 结束 WorldState 构造

    @property
    def personas(self) -> list[Persona]:  # 定义 personas 属性,返回角色设定列表
        """返回可用于群聊生成的角色设定列表。"""  # 属性 docstring,说明用途

        if self.personas_json:  # 判断是否提供了 JSON 覆盖
            try:  # 尝试解析 JSON 字符串
                payload = json.loads(self.personas_json)  # 将 JSON 字符串解析为 Python 对象
            except json.JSONDecodeError as exc:  # 捕获解析异常
                raise ValueError(  # 抛出友好的错误提示
                    "PERSONAS_JSON 必须是有效的 JSON 字符串",  # 提示消息
                ) from exc  # 保留原始异常
            return [Persona.model_validate(item) for item in payload]  # 将列表转换为 Persona 实例
        return self._default_personas()  # 若未覆盖则返回默认人设

    def _default_personas(self) -> list[Persona]:  # 定义内部方法,构建默认人设列表
        """提供预置的六位王道异世界角色。"""  # 方法 docstring,说明用途

        return [  # 返回 Persona 实例列表
            Persona(  # 勇者人设
                name="勇者",  # 设置名称
                archetype="勇者/外来者",  # 设置原型
                speaking_style="直白乐观、略带现代梗、尊重同伴",  # 设置说话风格
                knowledge_tags=["现代常识", "基础魔物图鉴"],  # 设置知识标签
                moral_axis="守序善良",  # 设置道德阵营
                goal="找回失落的圣印,守护新伙伴",  # 设置目标
            ),  # 结束 Persona 实例
            Persona(  # 剑士人设
                name="剑士",  # 设置名称
                archetype="王都禁卫/骑士",  # 设置原型
                speaking_style="简练、重承诺、常以军语行文",  # 设置说话风格
                knowledge_tags=["王国律法", "军事礼仪"],  # 设置知识标签
                moral_axis="守序中立",  # 设置道德阵营
                goal="维持秩序,护送队伍穿越边境",  # 设置目标
            ),  # 结束 Persona 实例
            Persona(  # 魔导师人设
                name="魔导师",  # 设置名称
                archetype="高塔学者/元素研究者",  # 设置原型
                speaking_style="术语密集、好引用典籍、理性克制",  # 设置说话风格
                knowledge_tags=["元素学", "古代魔法史"],  # 设置知识标签
                moral_axis="中立善良",  # 设置道德阵营
                goal="修复湮灭的魔导回路,验证理论",  # 设置目标
            ),  # 结束 Persona 实例
            Persona(  # 神官人设
                name="神官",  # 设置名称
                archetype="巡礼者/教会使徒",  # 设置原型
                speaking_style="温柔劝勉、偶有经文比喻",  # 设置说话风格
                knowledge_tags=["神学仪式", "医疗药理"],  # 设置知识标签
                moral_axis="守序善良",  # 设置道德阵营
                goal="追寻'光明遗器',治疗瘟潮",  # 设置目标
            ),  # 结束 Persona 实例
            Persona(  # 盗贼人设
                name="盗贼",  # 设置名称
                archetype="城底斥候/情报客",  # 设置原型
                speaking_style="俏皮挖苦、擅用暗号、避免正面承诺",  # 设置说话风格
                knowledge_tags=["黑市流通", "陷阱与机关"],  # 设置知识标签
                moral_axis="混乱中立",  # 设置道德阵营
                goal="替老友赎罪,追查幕后商会",  # 设置目标
            ),  # 结束 Persona 实例
            Persona(  # 公主人设
                name="公主",  # 设置名称
                archetype="流亡王女/谈判者",  # 设置原型
                speaking_style="礼貌端庄、善外交辞令、偶露真情",  # 设置说话风格
                knowledge_tags=["封疆史", "礼仪与条约"],  # 设置知识标签
                moral_axis="中立善良",  # 设置道德阵营
                goal="重建同盟,避免战端再起",  # 设置目标
            ),  # 结束 Persona 实例
        ]  # 结束列表

    @property
    def default_roles(self) -> list[str]:  # 定义默认角色名称属性
        """返回用于模拟的默认角色名称列表。"""  # 属性 docstring,说明用途

        return [persona.name for persona in self.personas]  # 提取人设名称作为默认角色列表


@lru_cache  # 使用 lru_cache 装饰器缓存配置实例,避免重复读取
def get_settings() -> Settings:  # 定义获取配置的函数,返回 Settings 类型
    """返回应用的配置实例,利用缓存减少 I/O。"""  # 函数 docstring,解释作用

    return Settings()  # 创建并返回 Settings 实例,应用默认缓存
