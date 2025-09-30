"""提供角色回复生成与任务生成的本地实现。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

import logging  # 导入 logging,输出调试信息
import random  # 导入 random,用于确定性生成
from collections.abc import Iterable  # 导入 Iterable,用于类型注解
from typing import Protocol  # 导入 Protocol,定义接口

from ..config import Settings  # 导入 Settings,读取配置
from ..models import Persona  # 导入 Persona,用于人设信息
from ..world.actions import ChunkCoord  # 导入 ChunkCoord,指定任务区块
from ..world.quests import (  # 导入任务相关类型
    ActionRequirement,  # 动作需求
    Quest,  # 任务模型
    QuestProgressor,  # 任务推进器
    QuestStatus,  # 任务状态
)  # 结束导入
from ..world.tiles import TileType  # 导入 TileType,用于任务目标
from ..world.world_state import WorldState  # 导入 WorldState,用于世界描述

logger = logging.getLogger(__name__)  # 创建模块级日志记录器


class BaseRoleGenerator(Protocol):  # 定义生成器协议
    """角色回复生成器需要实现的接口。"""  # 类 docstring,说明用途

    def generate(self, role: str, prompt: str) -> str:  # 定义生成方法
        """根据角色与提示词生成回复文本。"""  # 方法 docstring,说明用途


class LocalDeterministicGenerator:  # 定义本地伪随机生成器
    """通过固定种子提供稳定输出的文本生成器。"""  # 类 docstring,说明用途

    def __init__(self, seed: int, templates: Iterable[str]) -> None:  # 定义构造函数
        """根据给定模板列表初始化随机序列。"""  # 方法 docstring,说明用途

        self._random = random.Random(seed)  # 创建随机对象
        self._templates = list(templates)  # 将模板转换为列表
        if not self._templates:  # 若模板为空
            raise ValueError("至少需要一个模板字符串")  # 抛出错误

    def generate(self, role: str, prompt: str) -> str:  # 实现生成方法
        """从模板中选择一个句式并替换变量。"""  # 方法 docstring,说明用途

        template = self._random.choice(self._templates)  # 随机选择模板
        token = self._random.randint(100, 999)  # 生成编号
        return template.format(role=role, prompt=prompt, token=token)  # 返回填充后的文本


class PersonaAwareGenerator:  # 定义具备世界上下文的生成器
    """在本地模板基础上融合世界与任务概况。"""  # 类 docstring,说明用途

    def __init__(  # 定义构造函数
        self,
        seed: int,  # 随机种子
        world_state: WorldState,  # 世界状态
        personas: list[Persona],  # 人设列表
        quest_digest: str,  # 任务摘要字符串
    ) -> None:  # 构造函数返回 None
        """保存上下文并构建基础生成器。"""  # 方法 docstring,说明用途

        self._world_state = world_state  # 保存世界状态
        self._personas = {persona.name: persona for persona in personas}  # 创建名称到人设的映射
        self._quest_digest = quest_digest  # 保存任务摘要
        self._fallback = LocalDeterministicGenerator(  # 初始化本地生成器
            seed=seed,  # 使用外部提供的种子
            templates=[  # 定义模板列表
                "{role}整理装备道:在{prompt}下我们需配合推进({token})。",  # 模板一
                "{role}目视远方说:围绕{prompt}的目标得兼顾后勤({token})。",  # 模板二
                "{role}微笑补充:落实{prompt}时别忘记互相通报({token})。",  # 模板三
            ],  # 结束模板列表
        )  # 完成本地生成器初始化

    def generate(self, role: str, prompt: str) -> str:  # 定义生成方法
        """结合世界状态与任务摘要生成文本。"""  # 方法 docstring,说明用途

        persona = self._personas.get(role)  # 根据角色名称获取人设
        base_reply = self._fallback.generate(role=role, prompt=prompt)  # 获取基础文本
        if persona is None:  # 若未找到人设
            logger.warning("缺少人设:%s", role)  # 输出警告
            return f"【设定缺失】{base_reply}"  # 返回带提示的文本
        world_hint = self._world_state.describe()  # 构建世界提示
        persona_hint = (  # 构建角色提示
            f"{persona.name}作为{persona.archetype},目标是{persona.goal},"  # 标明身份与目标
            f"口吻应当{persona.speaking_style},"  # 指定口吻
            f"熟悉领域:{'、'.join(persona.knowledge_tags)}。"  # 指定知识
        )  # 结束字符串
        quest_hint = (  # 构建任务提示
            f"当前任务:{self._quest_digest}。" if self._quest_digest else "当前暂无活跃任务。"
        )
        return f"{world_hint}|{quest_hint}|{persona_hint}{base_reply}"  # 返回组合文本


class ExternalLLMGenerator:  # 定义预留的外部 LLM 生成器
    """当启用外部 LLM 时使用的占位实现。"""  # 类 docstring,说明用途

    def __init__(self, settings: Settings) -> None:  # 定义构造函数
        """保存配置,未来可扩展真实调用。"""  # 方法 docstring,说明用途

        self._settings = settings  # 保存配置

    def generate(self, role: str, prompt: str) -> str:  # 定义生成方法
        """暂未实现外部调用,直接抛出异常。"""  # 方法 docstring,说明用途

        raise NotImplementedError(  # 抛出未实现异常
            "外部 LLM 未启用,请保持 USE_EXTERNAL_LLM=false",  # 提示信息
        )  # 结束异常


class QuestGenerator:  # 定义任务生成器
    """基于世界状态与角色目标生成初始任务列表。"""  # 类 docstring,说明用途

    def __init__(self, progressor: QuestProgressor, settings: Settings) -> None:  # 定义构造函数
        """保存依赖,以便生成确定性的任务。"""  # 方法 docstring,说明用途

        self._progressor = progressor  # 保存任务推进器
        self._settings = settings  # 保存配置对象
        logger.debug("QuestGenerator 初始化,种子=%s", settings.seed)  # 输出调试信息

    def ensure_seed_quests(self, world_state: WorldState) -> list[Quest]:  # 生成或返回初始任务
        """若任务列表为空则生成默认任务并写回存储。"""  # 方法 docstring,说明用途

        quests = self._progressor.get_quests()  # 读取现有任务
        if quests:  # 若已存在任务
            return quests  # 直接返回
        timestamp = world_state.seed * 1000  # 使用世界种子生成确定性时间戳
        seed_quests = [  # 构建默认任务列表
            Quest(  # 道路建设任务
                id="quest_main_road",  # 任务 ID
                title="铺设主干道路",  # 标题
                desc="在王都近郊修建 40 格石路,确保补给畅通。",  # 描述
                giver="公主",  # 发布者
                assignee=["勇者", "剑士"],  # 执行角色
                status=QuestStatus.OPEN,  # 初始状态
                requirements=[  # 任务需求
                    ActionRequirement(  # 定义动作需求
                        action_type="PLACE_TILE",  # 动作类型
                        target_tile=TileType.ROAD,  # 目标瓦片
                        chunk=ChunkCoord(cx=0, cy=0),  # 目标区块
                        target_count=40,  # 需要铺设数量
                    ),  # 结束需求
                ],  # 结束需求列表
                rewards=["道路通行效率提升", "声望+10"],  # 任务奖励
                created_at=timestamp,  # 创建时间
                updated_at=timestamp,  # 更新时间
            ),  # 结束任务
            Quest(  # 种树任务
                id="quest_forest_ring",  # 任务 ID
                title="栽种护城树林",  # 标题
                desc="在王都周围种下 20 棵树苗,构建天然防护。",  # 描述
                giver="神官",  # 发布者
                assignee=["神官", "勇者"],  # 执行角色
                status=QuestStatus.OPEN,  # 初始状态
                requirements=[  # 需求列表
                    ActionRequirement(  # 树苗需求
                        action_type="PLANT_TREE",  # 动作类型
                        target_tile=TileType.TREE_SAPLING,  # 目标瓦片
                        chunk=ChunkCoord(cx=0, cy=0),  # 区块
                        target_count=20,  # 树苗数量
                        layer="deco",  # 检测装饰槽
                    ),  # 结束需求
                ],  # 结束需求列表
                rewards=["自然恩泽加持", "治愈术效率提升"],  # 奖励
                created_at=timestamp,  # 创建时间
                updated_at=timestamp,  # 更新时间
            ),  # 结束任务
            Quest(  # 农田任务
                id="quest_farmland",  # 任务 ID
                title="开垦农田",  # 标题
                desc="在近郊翻耕 30 格土地成为农田,储备粮食。",  # 描述
                giver="公主",  # 发布者
                assignee=["神官", "勇者"],  # 执行角色
                status=QuestStatus.OPEN,  # 初始状态
                requirements=[  # 需求列表
                    ActionRequirement(  # 翻土需求
                        action_type="FARM_TILL",  # 动作类型
                        target_tile=TileType.FARM,  # 目标瓦片
                        chunk=ChunkCoord(cx=1, cy=0),  # 选定区块
                        target_count=30,  # 目标数量
                    ),  # 结束需求
                ],  # 结束需求列表
                rewards=["粮仓储备提升", "居民满意度上升"],  # 奖励
                created_at=timestamp,  # 创建时间
                updated_at=timestamp,  # 更新时间
            ),  # 结束任务
        ]  # 结束任务列表
        self._progressor.save_quests(seed_quests)  # 将任务写入存储
        logger.info("已生成默认任务列表,共 %d 条", len(seed_quests))  # 输出日志
        return seed_quests  # 返回任务列表


def build_generator(  # 定义生成器工厂函数
    settings: Settings,  # 配置对象
    world_state: WorldState,  # 世界状态
    personas: list[Persona],  # 角色人设
    quests: list[Quest],  # 当前任务列表
) -> BaseRoleGenerator:  # 返回生成器实例
    """根据配置选择合适的文本生成器实现。"""  # 函数 docstring,说明用途

    quest_digest = _summarize_quests(quests)  # 生成任务摘要
    if settings.use_external_llm and settings.openai_api_key:  # 若启用外部 LLM
        logger.info("启用外部 LLM 生成,提供商=%s", settings.llm_provider)  # 输出日志
        return ExternalLLMGenerator(settings=settings)  # 返回占位实现
    logger.debug("使用离线 PersonaAwareGenerator 生成文本")  # 输出调试日志
    return PersonaAwareGenerator(  # 返回本地生成器
        seed=settings.seed,  # 传入种子
        world_state=world_state,  # 传入世界状态
        personas=personas,  # 传入人设
        quest_digest=quest_digest,  # 传入任务摘要
    )  # 结束构造


def _summarize_quests(quests: Iterable[Quest]) -> str:  # 定义任务摘要函数
    """将任务列表压缩为适合提示词的描述。"""  # 函数 docstring,说明用途

    parts: list[str] = []  # 初始化字符串列表
    for quest in quests:  # 遍历任务
        remaining = sum(  # 计算剩余次数
            req.target_count - req.progress  # 单条需求剩余
            for req in quest.requirements  # 遍历任务需求
        )
        parts.append(  # 添加摘要
            f"{quest.title}(状态:{quest.status},剩余:{remaining})",  # 拼接信息
        )  # 结束 append
    return " | ".join(parts)  # 返回组合字符串
