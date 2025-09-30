"""提供角色回复生成的抽象接口与本地实现。"""  # 模块级 docstring，说明用途

from __future__ import annotations  # 导入未来注释行为，允许前向引用类型

import logging  # 导入 logging 模块，用于输出调试信息
import random  # 导入 random 模块，生成可重复的伪随机文本
from typing import Iterable, Protocol  # 导入 Protocol 用于定义接口，Iterable 提供类型提示

logger = logging.getLogger(__name__)  # 创建模块级日志记录器，便于调试


class BaseRoleGenerator(Protocol):  # 定义协议类，描述角色生成器接口
    """角色回复生成器的接口定义。"""  # 类 docstring，说明用途

    def generate(self, role: str, prompt: str) -> str:  # 定义生成方法，声明参数与返回值类型
        """根据角色与提示词生成回复文本。"""  # 方法 docstring，描述行为


class LocalDeterministicGenerator:  # 定义本地可重复的生成器实现
    """使用固定随机种子生成确定性回复的本地实现。"""  # 类 docstring，说明用途

    def __init__(self, seed: int, templates: Iterable[str] | None = None) -> None:  # 定义构造函数，接收种子与模板
        """初始化生成器，构建内部随机数发生器与模板库。"""  # 方法 docstring，解释作用

        self._random = random.Random(seed)  # 创建 Random 实例，保证可重复
        source_templates = (  # 定义模板来源，可能来自外部或默认列表
            list(templates)  # 如果提供了自定义模板，转换为列表
            if templates is not None  # 判断是否存在自定义模板
            else [  # 否则使用默认模板列表
                "{role}经过深思熟虑后说：{prompt}的关键在于团队协作。",  # 模板一，强调协作
                "{role}分析道：围绕'{prompt}'我们需要拆解问题。",  # 模板二，强调拆解
                "{role}微笑回应：让我们针对{prompt}制定下一步计划。",  # 模板三，强调计划
            ]  # 结束默认模板列表
        )  # 结束条件表达式
        self._templates = list(source_templates)  # 存储模板列表，确保后续可索引
        logger.debug("初始化本地生成器，模板数量=%d", len(self._templates))  # 输出调试日志，标注模板数量

    def generate(self, role: str, prompt: str) -> str:  # 定义生成方法，实现接口
        """根据给定角色与提示词生成稳定的文本回复。"""  # 方法 docstring，说明行为

        template = self._random.choice(self._templates)  # 随机选择一个模板，保证多样性
        suffix = self._random.randint(1, 9999)  # 生成随机数字后缀，增加变化
        reply = template.format(role=role, prompt=prompt)  # 填充模板中的角色与提示词
        final_reply = f"{reply}（参考编号 {suffix}）"  # 拼接编号，提升可重复验证性
        logger.debug("角色=%s, 模板=%s, 编号=%d", role, template, suffix)  # 输出调试日志，记录生成细节
        return final_reply  # 返回最终生成的文本


def build_generator(seed: int) -> BaseRoleGenerator:  # 定义工厂函数，方便创建生成器实例
    """根据传入的种子构建默认的角色生成器。"""  # 函数 docstring，说明用途

    return LocalDeterministicGenerator(seed=seed)  # 返回本地确定性生成器实例
