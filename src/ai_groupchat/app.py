"""FastAPI 应用实例定义模块。"""  # 模块级 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,确保类型前向引用可用

import json  # 导入 json 模块,用于加载像素元数据
import logging  # 导入 logging 模块,用于记录调试信息
from pathlib import Path  # 导入 Path 对象,便于处理路径

from fastapi import FastAPI, HTTPException  # 导入 FastAPI 与 HTTPException,用于构建应用与错误处理

from .config import get_settings  # 导入配置获取函数,用于访问环境配置
from .models import (  # 导入数据模型,描述请求与响应
    ChatSimulateResponse,  # 聊天响应模型
    MessageIn,  # 聊天输入模型
    Persona,  # 人设模型
    RoleReply,  # 角色回复模型
    WorldState,  # 世界状态模型
)
from .services.generator import build_generator  # 导入生成器工厂函数,构建回复生成器

logger = logging.getLogger(__name__)  # 创建模块级日志记录器,方便追踪请求

settings = get_settings()  # 获取全局配置实例,供应用使用
app = FastAPI(  # 创建 FastAPI 应用,使用配置中的名称与调试开关
    title=settings.app_name,  # 指定应用标题
    debug=settings.debug,  # 指定调试模式
)  # 结束 FastAPI 构造

_runtime_world_state = settings.world_state.model_copy(  # 初始化运行期世界状态,允许后续更新
    deep=True,  # 深拷贝配置中的默认状态
)  # 结束 world_state 拷贝
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 解析工程根目录,方便定位资源
_PIXEL_META_DIR = _PROJECT_ROOT / "assets" / "pixel_meta"  # 定义像素元数据目录


@app.get("/health", tags=["system"], summary="健康检查")  # 注册健康检查路由,包含标签与摘要
async def health() -> dict[str, str]:  # 定义异步健康检查处理函数,返回字典
    """返回服务健康状态,供监控与测试使用。"""  # 函数 docstring,说明用途

    logger.debug("健康检查被调用")  # 输出调试日志,记录调用
    return {"status": "ok"}  # 返回固定的健康状态


@app.get(  # 注册世界状态查询路由
    "/world/state",  # 设置路由路径
    response_model=WorldState,  # 指定返回模型
    tags=["world"],  # 分配标签
    summary="获取当前世界状态",  # 设置摘要
)
async def get_world_state() -> WorldState:  # 定义获取世界状态的异步函数
    """返回运行期缓存的世界状态。"""  # 函数 docstring,说明用途

    return _runtime_world_state  # 返回当前世界状态


@app.post(  # 注册世界状态更新路由
    "/world/state",  # 设置路由路径
    response_model=WorldState,  # 指定返回模型
    tags=["world"],  # 分配标签
    summary="更新当前世界状态",  # 设置摘要
)
async def update_world_state(new_state: WorldState) -> WorldState:  # 定义更新世界状态的异步函数
    """在调试模式下更新世界状态,生产环境禁止。"""  # 函数 docstring,说明用途

    if not settings.debug:  # 检查是否处于调试模式
        raise HTTPException(  # 抛出 HTTP 异常
            status_code=403,  # 指定状态码
            detail="生产环境禁止修改世界状态",  # 指定错误信息
        )  # 结束异常构造
    global _runtime_world_state  # 声明使用模块级可变状态
    _runtime_world_state = new_state  # 更新运行期世界状态
    logger.info("世界状态已更新:%s", new_state.model_dump())  # 记录更新日志
    return _runtime_world_state  # 返回最新世界状态


@app.get(  # 注册人设查询路由
    "/personas",  # 设置路由路径
    response_model=list[Persona],  # 指定返回列表模型
    tags=["world"],  # 分配标签
    summary="获取默认人设",  # 设置摘要
)
async def get_personas() -> list[Persona]:  # 定义获取人设的异步函数
    """返回用于生成的所有默认角色人设。"""  # 函数 docstring,说明用途

    return settings.personas  # 返回配置中的人设列表


@app.get(  # 注册像素元数据路由
    "/pixel/meta",  # 设置路由路径
    tags=["assets"],  # 分配标签
    summary="获取像素资源元数据",  # 设置摘要
)
async def get_pixel_meta() -> dict[str, dict]:  # 定义获取像素元数据的异步函数
    """汇总 assets/pixel_meta 下的所有元数据文件。"""  # 函数 docstring,说明用途

    files: dict[str, dict] = {}  # 初始化字典,用于存储文件与内容
    for json_path in sorted(_PIXEL_META_DIR.rglob("*.meta.json")):  # 遍历所有元数据文件
        relative_key = str(json_path.relative_to(_PIXEL_META_DIR))  # 计算相对路径作为键
        with json_path.open("r", encoding="utf-8") as handle:  # 打开文件读取内容
            files[relative_key] = json.load(handle)  # 将解析后的 JSON 写入字典
    return {"files": files}  # 返回封装后的结果


@app.post(  # 注册聊天模拟路由,处理 POST 请求
    "/chat/simulate",  # 指定路径为 /chat/simulate
    response_model=ChatSimulateResponse,  # 指定响应模型,确保返回结构
    tags=["chat"],  # 添加标签,便于文档分类
    summary="模拟多角色群聊",  # 设置摘要,说明功能
)
async def chat_simulate(  # 定义异步处理函数,接收 MessageIn
    message: MessageIn,  # 请求体模型
) -> ChatSimulateResponse:  # 返回群聊模拟结果
    """根据用户输入模拟多个角色的回复。"""  # 函数 docstring,说明用途

    logger.debug("开始模拟群聊,输入=%s", message.content)  # 输出调试日志,记录输入内容
    world_state = _runtime_world_state  # 取出当前世界状态
    if message.location:  # 如果请求中提供了临时场景
        world_state = world_state.model_copy(  # 生成覆盖地点的新状态
            update={"location": message.location},  # 指定要更新的地点
        )  # 结束 model_copy 调用
    personas = settings.personas  # 获取默认人设列表
    if message.roles:  # 若请求指定角色列表
        persona_lookup = {persona.name: persona for persona in personas}  # 构建名称索引
        try:  # 尝试按照请求顺序获取对应人设
            personas = [persona_lookup[name] for name in message.roles]  # 根据名称筛选人设
        except KeyError as exc:  # 捕获缺少人设的情况
            raise HTTPException(  # 抛出 400 错误
                status_code=400,  # 设置错误码
                detail=f"未知角色:{exc.args[0]}",  # 设置错误详情
            ) from exc  # 保留原始异常上下文
    generator = build_generator(  # 构建生成器实例
        settings=settings,  # 传入全局配置
        world_state=world_state,  # 传入本次请求的世界状态
        personas=personas,  # 传入目标人设列表
    )  # 结束生成器构建
    replies: list[RoleReply] = []  # 初始化回复列表,收集每个角色的回复
    world_context_parts = [  # 构建世界上下文提示语片段
        f"地点:{world_state.location}",  # 描述地点
        f"季节:{world_state.season}",  # 描述季节
        f"年份:{world_state.year}",  # 描述年份
        f"事件:{'、'.join(world_state.major_events)}",  # 描述重大事件
    ]  # 结束片段列表
    world_context = "|".join(world_context_parts)  # 组合完整的上下文提示
    for persona in personas:  # 遍历每个人设
        prompt = "|".join(  # 构建完整提示词
            [  # 组装提示片段
                message.content,  # 用户输入内容
                world_context,  # 世界上下文提示
                f"角色风格:{persona.speaking_style}",  # 角色说话风格
                f"目标:{persona.goal}",  # 角色目标
                f"建议句数:{settings.reply_sentences_per_role}",  # 建议句数
            ]  # 结束片段列表
        )  # 结束 join 构建
        text = generator.generate(role=persona.name, prompt=prompt)  # 调用生成器产生文本
        replies.append(RoleReply(role=persona.name, text=text))  # 将角色与文本封装为模型并加入列表
        logger.debug("角色=%s 已生成回复", persona.name)  # 输出调试日志,标记角色完成
    logger.info("群聊模拟完成,共生成 %d 条回复", len(replies))  # 输出信息日志,总结数量
    return ChatSimulateResponse(replies=replies)  # 返回响应模型实例
