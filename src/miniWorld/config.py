"""应用配置模块,负责加载环境变量并提供默认设定。"""  # 模块级 docstring,说明模块功能

from __future__ import annotations  # 导入未来注解特性,支持前向引用类型

import json  # 导入 json 模块,用于解析覆盖配置
from functools import lru_cache  # 导入 lru_cache,用于缓存配置实例

from pydantic import Field, ValidationError  # 导入 Field 与 ValidationError,声明字段并处理错误
from pydantic_settings import (  # 导入 pydantic_settings 中的类
    BaseSettings,  # BaseSettings 用于读取环境变量
    SettingsConfigDict,  # SettingsConfigDict 用于定义模型配置
)

from .models import Persona  # 导入 Persona 模型,用于人设信息
from .world.actions import RolePermission  # 导入 RolePermission,用于权限配置
from .world.tiles import TileType  # 导入 TileType,在默认权限中引用瓦片类型
from .world.world_state import WorldState  # 导入 WorldState,构建世界状态


class Settings(BaseSettings):  # 定义 Settings 类,继承 BaseSettings
    """miniWorld 应用的配置对象,封装运行期所需参数。"""  # 类 docstring,描述用途

    app_name: str = Field(  # 定义应用名称字段
        default="miniWorld",  # 设置默认应用名称
        description="FastAPI 应用展示名称",  # 字段描述
        alias="APP_NAME",  # 指定环境变量名称
    )  # 结束 Field 定义
    debug: bool = Field(  # 定义调试模式字段
        default=True,  # 默认开启调试
        description="是否启用调试日志",  # 字段描述
        alias="DEBUG",  # 指定环境变量名称
    )  # 结束 Field 定义
    host: str = Field(  # 定义主机地址字段
        default="127.0.0.1",  # 默认监听地址
        description="服务器监听地址",  # 字段描述
        alias="HOST",  # 指定环境变量名称
    )  # 结束 Field 定义
    port: int = Field(  # 定义端口字段
        default=8000,  # 默认监听端口
        description="服务器监听端口",  # 字段描述
        alias="PORT",  # 指定环境变量名称
    )  # 结束 Field 定义
    seed: int = Field(  # 定义随机种子字段
        default=42,  # 默认随机种子
        description="本地生成器使用的随机种子",  # 字段描述
        alias="SEED",  # 指定环境变量名称
    )  # 结束 Field 定义
    reply_sentences_per_role: int = Field(  # 定义角色回复建议句数
        default=2,  # 默认两句
        description="建议的角色回复句数提示",  # 字段描述
    )  # 结束 Field 定义
    world_year: int = Field(  # 定义世界年份字段
        default=302,  # 默认年份
        description="世界观当前年份",  # 字段描述
        alias="WORLD_YEAR",  # 指定环境变量名称
    )  # 结束 Field 定义
    world_season: str = Field(  # 定义世界季节字段
        default="春",  # 默认季节
        description="世界观当前季节",  # 字段描述
        alias="WORLD_SEASON",  # 指定环境变量名称
    )  # 结束 Field 定义
    default_location: str = Field(  # 定义默认地点字段
        default="王都近郊",  # 默认地点
        description="队伍当前活动区域",  # 字段描述
        alias="DEFAULT_LOCATION",  # 指定环境变量名称
    )  # 结束 Field 定义
    seed_events: list[str] = Field(  # 定义重大事件列表字段
        default_factory=lambda: [  # 使用默认工厂生成列表
            "圣印遗失导致王国动荡",  # 事件一
            "边境魔导炉持续紊乱",  # 事件二
        ],  # 结束默认列表
        description="影响剧情的重大事件列表",  # 字段描述
    )  # 结束 Field 定义
    personas_json: str | None = Field(  # 定义可选人设覆盖字段
        default=None,  # 默认不覆盖
        description="通过 JSON 字符串覆盖默认人设",  # 字段描述
        alias="PERSONAS_JSON",  # 指定环境变量名称
    )  # 结束 Field 定义
    role_permissions_json: str | None = Field(  # 定义可选权限覆盖字段
        default=None,  # 默认不覆盖
        description="通过 JSON 字符串覆盖角色权限",  # 字段描述
        alias="ROLE_PERMISSIONS_JSON",  # 指定环境变量名称
    )  # 结束 Field 定义
    chunk_size: int = Field(  # 定义区块尺寸字段
        default=32,  # 默认 32
        description="单个区块的边长",  # 字段描述
        alias="CHUNK_SIZE",  # 指定环境变量名称
    )  # 结束 Field 定义
    tick_tree_grow_steps: int = Field(  # 定义树苗成长步数字段
        default=3,  # 默认三步成长
        description="树苗成长为成树所需 tick 数",  # 字段描述
        alias="TICK_TREE_GROW_STEPS",  # 指定环境变量名称
    )  # 结束 Field 定义
    use_external_llm: bool = Field(  # 定义外部 LLM 开关
        default=False,  # 默认关闭
        description="是否启用外部大模型",  # 字段描述
        alias="USE_EXTERNAL_LLM",  # 指定环境变量名称
    )  # 结束 Field 定义
    llm_provider: str = Field(  # 定义外部 LLM 提供商
        default="openai",  # 默认提供商
        description="外部 LLM 提供商标识",  # 字段描述
        alias="LLM_PROVIDER",  # 指定环境变量名称
    )  # 结束 Field 定义
    openai_api_key: str | None = Field(  # 定义 OpenAI API Key 字段
        default=None,  # 默认无密钥
        description="OpenAI API Key,启用外部 LLM 时必填",  # 字段描述
        alias="OPENAI_API_KEY",  # 指定环境变量名称
    )  # 结束 Field 定义
    openai_base_url: str | None = Field(  # 定义 OpenAI 基础地址字段
        default=None,  # 默认无地址
        description="OpenAI API Base URL",  # 字段描述
        alias="OPENAI_BASE_URL",  # 指定环境变量名称
    )  # 结束 Field 定义
    model_config = SettingsConfigDict(  # 定义模型配置
        env_file=".env",  # 指定环境变量文件
        env_file_encoding="utf-8",  # 指定文件编码
        populate_by_name=True,  # 支持通过字段名或别名赋值
    )  # 结束模型配置

    @property
    def world_state(self) -> WorldState:  # 定义 world_state 属性
        """根据配置构造默认世界状态对象。"""  # 属性 docstring,说明用途

        return WorldState(  # 返回 WorldState 实例
            year=self.world_year,  # 传入年份
            season=self.world_season,  # 传入季节
            location=self.default_location,  # 传入地点
            major_events=self.seed_events,  # 传入重大事件列表
            version="v1",  # 设置世界状态版本号
            seed=self.seed,  # 传入随机种子
        )  # 结束 WorldState 构造

    @property
    def personas(self) -> list[Persona]:  # 定义 personas 属性
        """返回六位核心角色的人设信息。"""  # 属性 docstring,说明用途

        if self.personas_json:  # 如果提供了覆盖 JSON
            try:  # 尝试解析 JSON 字符串
                payload = json.loads(self.personas_json)  # 将字符串解析为 Python 对象
            except json.JSONDecodeError as exc:  # 捕获解析异常
                raise ValueError("PERSONAS_JSON 必须是有效 JSON") from exc  # 抛出友好错误
            return [  # 将解析结果转换为 Persona 列表
                Persona.model_validate(item)  # 验证并构建 Persona
                for item in payload  # 遍历 JSON 数组
            ]  # 结束列表推导
        return self._default_personas()  # 若未覆盖则返回默认人设

    @property
    def role_permissions(self) -> dict[str, RolePermission]:  # 定义 role_permissions 属性
        """返回六位角色的权限配置映射。"""  # 属性 docstring,说明用途

        if self.role_permissions_json:  # 如果提供了覆盖 JSON
            try:  # 尝试解析 JSON
                payload = json.loads(self.role_permissions_json)  # 解析字符串
            except json.JSONDecodeError as exc:  # 捕获解析错误
                raise ValueError("ROLE_PERMISSIONS_JSON 必须是有效 JSON") from exc  # 抛出错误
            return {  # 返回解析后的权限映射
                name: RolePermission.model_validate(data)  # 将每个条目转换为 RolePermission
                for name, data in payload.items()  # 遍历 JSON 中的角色配置
            }  # 结束字典推导
        return self._default_role_permissions()  # 若未覆盖则使用默认权限

    def _default_personas(self) -> list[Persona]:  # 定义内部方法,构建默认人设
        """提供六位核心角色的预置人设信息。"""  # 方法 docstring,说明用途

        return [  # 返回 Persona 列表
            Persona(  # 勇者人设
                name="勇者",  # 角色名称
                archetype="来自异世界的勇者",  # 角色原型
                speaking_style="直率真诚,偶尔带现代语汇",  # 说话风格
                knowledge_tags=["现代科技", "冒险经验"],  # 知识标签
                moral_axis="守序善良",  # 道德阵营
                goal="修复圣印并守护伙伴",  # 角色目标
            ),  # 结束 Persona
            Persona(  # 剑士人设
                name="剑士",  # 角色名称
                archetype="王国禁卫军剑士",  # 角色原型
                speaking_style="简洁有力,常带军语",  # 说话风格
                knowledge_tags=["军事战术", "道路构建"],  # 知识标签
                moral_axis="守序中立",  # 道德阵营
                goal="巩固防线并保障交通",  # 角色目标
            ),  # 结束 Persona
            Persona(  # 魔导师人设
                name="魔导师",  # 角色名称
                archetype="高塔研究者",  # 角色原型
                speaking_style="术语丰富,理性分析",  # 说话风格
                knowledge_tags=["魔力导管", "元素生态"],  # 知识标签
                moral_axis="中立善良",  # 道德阵营
                goal="复原魔导网络并探索新魔法",  # 角色目标
            ),  # 结束 Persona
            Persona(  # 神官人设
                name="神官",  # 角色名称
                archetype="教会巡礼者",  # 角色原型
                speaking_style="温柔劝勉,引用经文",  # 说话风格
                knowledge_tags=["神圣仪式", "农作物疗养"],  # 知识标签
                moral_axis="守序善良",  # 道德阵营
                goal="治疗瘟潮并赐福土地",  # 角色目标
            ),  # 结束 Persona
            Persona(  # 盗贼人设
                name="盗贼",  # 角色名称
                archetype="潜行情报员",  # 角色原型
                speaking_style="轻佻风趣,暗语频繁",  # 说话风格
                knowledge_tags=["暗道", "陷阱拆解"],  # 知识标签
                moral_axis="混乱中立",  # 道德阵营
                goal="排除机关并收集情报",  # 角色目标
            ),  # 结束 Persona
            Persona(  # 公主人设
                name="公主",  # 角色名称
                archetype="复国者与建设发起人",  # 角色原型
                speaking_style="礼貌庄重,注重号召",  # 说话风格
                knowledge_tags=["城市规划", "外交事务"],  # 知识标签
                moral_axis="中立善良",  # 道德阵营
                goal="重建王都并安置民众",  # 角色目标
            ),  # 结束 Persona
        ]  # 结束列表

    def _default_role_permissions(self) -> dict[str, RolePermission]:  # 定义内部方法,构建默认权限
        """返回六位角色的默认权限矩阵。"""  # 方法 docstring,说明用途

        return {  # 返回角色到权限的映射
            "勇者": RolePermission(  # 勇者权限
                allowed_actions={"PLACE_TILE", "PLANT_TREE", "FARM_TILL"},  # 允许的动作集合
                tile_whitelist={  # 定义瓦片白名单
                    "PLACE_TILE": [  # 对 PLACE_TILE 指定允许瓦片
                        TileType.GRASS,  # 草地
                        TileType.ROAD,  # 石路
                        TileType.SOIL,  # 土地
                        TileType.WOODFLOOR,  # 木地板
                    ],  # 结束列表
                    "PLANT_TREE": [  # 可种树的基础瓦片
                        TileType.GRASS,
                        TileType.SOIL,
                        TileType.FARM,
                    ],
                },  # 结束白名单
                daily_quota={"PLANT_TREE": 20},  # 设置每日种树配额
            ),  # 结束勇者权限
            "剑士": RolePermission(  # 剑士权限
                allowed_actions={"PLACE_TILE", "REMOVE_TILE"},  # 允许铺路与清障
                tile_whitelist={  # 定义瓦片白名单
                    "PLACE_TILE": [TileType.ROAD, TileType.WOODFLOOR],  # 剑士主要负责道路与防御铺设
                    "REMOVE_TILE": [TileType.TREE, TileType.TREE_SAPLING],  # 可移除树木障碍
                },  # 结束白名单
                forbidden_remove_bases=[TileType.HOUSE_BASE],  # 禁止拆除房基
                cooldown_seconds={"REMOVE_TILE": 30},  # 拆除动作需要冷却
            ),  # 结束剑士权限
            "魔导师": RolePermission(  # 魔导师权限
                allowed_actions={  # 允许铺设魔法基底与结构
                    "PLACE_TILE",
                    "PLANT_TREE",
                    "PLACE_STRUCTURE",
                },
                tile_whitelist={  # 定义瓦片白名单
                    "PLACE_TILE": [TileType.SOIL, TileType.WATER, TileType.WOODFLOOR],  # 魔法基底
                    "PLACE_STRUCTURE": [TileType.HOUSE_BASE, TileType.WOODFLOOR],  # 魔导基座
                    "PLANT_TREE": [TileType.GRASS, TileType.WATER],  # 魔法林可覆盖草地与水面
                },  # 结束白名单
            ),  # 结束魔导师权限
            "神官": RolePermission(  # 神官权限
                allowed_actions={"PLANT_TREE", "FARM_TILL"},  # 允许种圣树与翻土
                tile_whitelist={  # 定义瓦片白名单
                    "PLANT_TREE": [TileType.GRASS, TileType.SOIL, TileType.FARM],  # 圣树适宜地
                    "FARM_TILL": [TileType.SOIL],  # 仅能翻土
                },  # 结束白名单
                daily_quota={"FARM_TILL": 50},  # 每日翻土配额
            ),  # 结束神官权限
            "盗贼": RolePermission(  # 盗贼权限
                allowed_actions={"REMOVE_TILE", "PLACE_TILE"},  # 允许拆除陷阱并铺设隐匿地板
                tile_whitelist={  # 定义瓦片白名单
                    "PLACE_TILE": [TileType.WOODFLOOR, TileType.GRASS],  # 隐匿地板
                    "REMOVE_TILE": [  # 可拆除的障碍
                        TileType.TREE,
                        TileType.TREE_SAPLING,
                        TileType.WOODFLOOR,
                    ],
                },  # 结束白名单
                cooldown_seconds={"REMOVE_TILE": 60},  # 拆除有冷却
                daily_quota={"REMOVE_TILE": 30},  # 拆除每日配额
            ),  # 结束盗贼权限
            "公主": RolePermission(  # 公主权限
                allowed_actions={"PLACE_STRUCTURE", "PLACE_TILE"},  # 负责基建与主干道路
                tile_whitelist={  # 定义瓦片白名单
                    "PLACE_STRUCTURE": [TileType.HOUSE_BASE, TileType.WOODFLOOR],  # 公共设施基座
                    "PLACE_TILE": [TileType.ROAD, TileType.WOODFLOOR],  # 主干道路
                },  # 结束白名单
                forbidden_remove_bases=[TileType.HOUSE_BASE],  # 公主不可拆除任何地基
            ),  # 结束公主权限
        }  # 结束映射


@lru_cache  # 使用 lru_cache 缓存配置实例
def get_settings() -> Settings:  # 定义获取配置的函数
    """返回单例配置对象,避免重复解析环境变量。"""  # 函数 docstring,说明用途

    try:  # 尝试创建配置实例
        return Settings()  # 返回 Settings 实例
    except ValidationError as exc:  # 捕获验证错误
        raise RuntimeError(f"配置加载失败: {exc}") from exc  # 抛出运行时错误以终止启动
