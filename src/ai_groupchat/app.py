"""FastAPI 应用实例定义模块。"""  # 模块级 docstring，说明用途

import logging  # 导入 logging 模块，用于记录调试信息
from fastapi import FastAPI  # 导入 FastAPI 类，用于创建应用实例

from .config import get_settings  # 导入配置获取函数，用于访问环境配置
from .models import ChatSimulateResponse, MessageIn, RoleReply  # 导入数据模型，描述请求与响应
from .services.generator import build_generator  # 导入生成器工厂函数，构建回复生成器

logger = logging.getLogger(__name__)  # 创建模块级日志记录器，方便追踪请求

settings = get_settings()  # 获取全局配置实例，供应用使用
app = FastAPI(title=settings.app_name, debug=settings.debug)  # 创建 FastAPI 应用，使用配置中的名称与调试开关


@app.get("/health", tags=["system"], summary="健康检查")  # 注册健康检查路由，包含标签与摘要
async def health() -> dict[str, str]:  # 定义异步健康检查处理函数，返回字典
    """返回服务健康状态，供监控与测试使用。"""  # 函数 docstring，说明用途

    logger.debug("健康检查被调用")  # 输出调试日志，记录调用
    return {"status": "ok"}  # 返回固定的健康状态


@app.post(  # 注册聊天模拟路由，处理 POST 请求
    "/chat/simulate",  # 指定路径为 /chat/simulate
    response_model=ChatSimulateResponse,  # 指定响应模型，确保返回结构
    tags=["chat"],  # 添加标签，便于文档分类
    summary="模拟多角色群聊",  # 设置摘要，说明功能
)
async def chat_simulate(message: MessageIn) -> ChatSimulateResponse:  # 定义异步处理函数，接收 MessageIn
    """根据用户输入模拟多个角色的回复。"""  # 函数 docstring，说明用途

    logger.debug("开始模拟群聊，输入=%s", message.content)  # 输出调试日志，记录输入内容
    generator = build_generator(seed=settings.seed)  # 构建确定性生成器，确保回复可预测
    replies: list[RoleReply] = []  # 初始化回复列表，收集每个角色的回复
    for role in settings.default_roles:  # 遍历配置中的角色列表
        combined_prompt = f"{message.content}（预计回复句数 {settings.reply_sentences_per_role}）"  # 构造提示词，提供上下文
        text = generator.generate(role=role, prompt=combined_prompt)  # 调用生成器产生文本
        replies.append(RoleReply(role=role, text=text))  # 将角色与文本封装为模型并加入列表
        logger.debug("角色=%s 已生成回复", role)  # 输出调试日志，标记角色完成
    logger.info("群聊模拟完成，共生成 %d 条回复", len(replies))  # 输出信息日志，总结数量
    return ChatSimulateResponse(replies=replies)  # 返回响应模型实例
