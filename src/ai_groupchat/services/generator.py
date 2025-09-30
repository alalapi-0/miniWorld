"""提供角色回复生成的抽象接口与本地实现。"""  # 模块级 docstring,说明用途

from __future__ import annotations  # 导入未来注释行为,允许前向引用类型

import logging  # 导入 logging 模块,用于输出调试信息
import random  # 导入 random 模块,生成可重复的伪随机文本
from collections.abc import Iterable  # 导入 Iterable,用于描述可迭代模板集合
from typing import Protocol  # 导入 Protocol,用于定义生成器接口协议

from ..config import Settings  # 导入 Settings 类型,支持根据配置构建生成器
from ..models import Persona, WorldState  # 导入 Persona 与 WorldState,用于情境化生成

logger = logging.getLogger(__name__)  # 创建模块级日志记录器,便于调试


class BaseRoleGenerator(Protocol):  # 定义协议类,描述角色生成器接口
    """角色回复生成器的接口定义。"""  # 类 docstring,说明用途

    def generate(self, role: str, prompt: str) -> str:  # 定义生成方法,声明参数与返回值类型
        """根据角色与提示词生成回复文本。"""  # 方法 docstring,描述行为


class LocalDeterministicGenerator:  # 定义本地可重复的生成器实现
    """使用固定随机种子生成确定性回复的本地实现。"""  # 类 docstring,说明用途

    def __init__(  # 定义构造函数,接收种子与模板
        self,  # 传入实例自身
        seed: int,  # 随机种子参数
        templates: Iterable[str] | None = None,  # 可选模板集合
    ) -> None:  # 构造函数返回 None
        """初始化生成器,构建内部随机数发生器与模板库。"""  # 方法 docstring,解释作用

        self._random = random.Random(seed)  # 创建 Random 实例,保证可重复
        source_templates = (  # 定义模板来源,可能来自外部或默认列表
            list(templates)  # 如果提供了自定义模板,转换为列表
            if templates is not None  # 判断是否存在自定义模板
            else [  # 否则使用默认模板列表
                "{role}经过深思熟虑后说:{prompt}的关键在于团队协作。",  # 模板一,强调协作
                "{role}分析道:围绕'{prompt}'我们需要拆解问题。",  # 模板二,强调拆解
                "{role}微笑回应:让我们针对{prompt}制定下一步计划。",  # 模板三,强调计划
            ]  # 结束默认模板列表
        )  # 结束条件表达式
        self._templates = list(source_templates)  # 存储模板列表,确保后续可索引
        logger.debug(  # 输出调试日志,标注模板数量
            "初始化本地生成器,模板数量=%d",  # 日志模板
            len(self._templates),  # 模板数量
        )  # 结束日志调用

    def generate(self, role: str, prompt: str) -> str:  # 定义生成方法,实现接口
        """根据给定角色与提示词生成稳定的文本回复。"""  # 方法 docstring,说明行为

        template = self._random.choice(self._templates)  # 随机选择一个模板,保证多样性
        suffix = self._random.randint(1, 9999)  # 生成随机数字后缀,增加变化
        reply = template.format(role=role, prompt=prompt)  # 填充模板中的角色与提示词
        final_reply = f"{reply}(参考编号 {suffix})"  # 拼接编号,提升可重复验证性
        logger.debug(  # 输出调试日志,记录生成细节
            "角色=%s, 模板=%s, 编号=%d",  # 日志模板
            role,  # 角色名称
            template,  # 使用的模板字符串
            suffix,  # 生成的编号
        )  # 结束日志调用
        return final_reply  # 返回最终生成的文本


class PersonaAwareGenerator:  # 定义具备世界观意识的生成器实现
    """在本地模板基础上融合世界观与角色设定。"""  # 类 docstring,说明用途

    def __init__(  # 定义构造函数,接收所需上下文
        self,  # 传入实例自身
        seed: int,  # 随机种子,用于内部本地生成器
        world_state: WorldState,  # 当前世界观状态
        personas: list[Persona],  # 角色设定列表
    ) -> None:  # 构造函数返回 None
        """保存世界观上下文并初始化内部生成器。"""  # 方法 docstring,说明用途

        self._world_state = world_state  # 存储世界观状态,供生成时引用
        self._personas = {persona.name: persona for persona in personas}  # 将人设列表转换为名称映射
        self._fallback = LocalDeterministicGenerator(  # 初始化内部本地生成器
            seed=seed,  # 传入随机种子
            templates=[  # 定义更贴合冒险语气的模板
                "{role}整理装备后回应:围绕{prompt}我们需协调行动。",  # 模板一
                "{role}眺望远方:若按{prompt}推进,得兼顾队伍安全。",  # 模板二
                "{role}低声商议:此刻{prompt}必须考虑盟友心情。",  # 模板三
            ],  # 结束模板列表
        )  # 完成内部生成器初始化

    def generate(self, role: str, prompt: str) -> str:  # 定义生成方法,实现接口
        """综合世界状态与角色设定生成文本。"""  # 方法 docstring,说明用途

        persona = self._personas.get(role)  # 根据角色名称获取对应人设
        base_reply = self._fallback.generate(role=role, prompt=prompt)  # 使用本地生成器产生基础文本
        if persona is None:  # 判断人设是否存在
            logger.warning("角色 %s 缺少人设,返回基础文本", role)  # 输出警告日志
            return f"【设定缺失】{base_reply}"  # 返回带提示的基础文本
        events = "、".join(self._world_state.major_events)  # 将重大事件拼接成字符串
        scene_prefix = (  # 构建世界状态前缀
            f"{self._world_state.year} 年{self._world_state.season}季"  # 表示年份与季节
            f",{self._world_state.location}。"  # 表示地点
            f"近期事件:{events}。"  # 描述重大事件
        )  # 结束字符串拼接
        persona_hint = (  # 构建角色提示文本
            f"{persona.name}以{persona.archetype}的身份,"  # 标明身份
            f"目标是{persona.goal},"  # 提及目标
            f"口吻应{persona.speaking_style},"  # 描述口吻
            f"熟悉领域:{'、'.join(persona.knowledge_tags)}。"  # 列举知识标签
        )  # 结束字符串拼接
        final_reply = f"{scene_prefix}{persona_hint}回复:{base_reply}"  # 组合所有片段形成最终文本
        logger.debug("角色=%s 使用人设生成回复", role)  # 输出调试日志
        return final_reply  # 返回最终文本


class ExternalLLMGenerator:  # 定义预留的外部 LLM 生成器占位实现
    """预留的外部 LLM 调用接口,默认不启用。"""  # 类 docstring,说明用途

    def __init__(self, settings: Settings) -> None:  # 定义构造函数,接收配置对象
        """保存配置用于未来接入真实 LLM。"""  # 方法 docstring,说明用途

        self._settings = settings  # 存储配置,未来可用于初始化客户端

    def generate(self, role: str, prompt: str) -> str:  # 定义生成方法,与协议保持一致
        """伪代码:占位描述外部 LLM 调用并提醒需要超时与审计。"""  # 方法 docstring,描述未来逻辑

        raise NotImplementedError(  # 抛出未实现异常,提醒调用者
            "外部 LLM 生成尚未启用,请保持 USE_EXTERNAL_LLM=false。",  # 提示安全默认策略
        )  # 结束异常抛出


def build_generator(  # 定义生成器工厂函数
    settings: Settings,  # 传入配置对象,读取开关与种子
    world_state: WorldState,  # 传入当前世界状态
    personas: list[Persona],  # 传入角色人设列表
) -> BaseRoleGenerator:  # 返回实现协议的生成器实例
    """根据配置开关选择离线或外部 LLM 生成器。"""  # 函数 docstring,说明用途

    if settings.use_external_llm and settings.openai_api_key:  # 当启用外部 LLM 且提供密钥时
        logger.info("启用外部 LLM 生成器,提供商=%s", settings.llm_provider)  # 记录选择信息
        return ExternalLLMGenerator(settings=settings)  # 返回外部 LLM 生成器占位实现
    logger.debug("使用 PersonaAwareGenerator 进行离线生成")  # 记录使用离线生成器
    return PersonaAwareGenerator(  # 返回具备人设意识的本地生成器
        seed=settings.seed,  # 传入随机种子
        world_state=world_state,  # 传入世界状态
        personas=personas,  # 传入角色人设
    )  # 结束 PersonaAwareGenerator 初始化
