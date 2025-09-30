"""定义 FastAPI 应用与世界相关接口。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

import logging  # 导入 logging,用于输出调试信息
from pathlib import Path  # 导入 Path,定位工程目录
from typing import Any  # 导入 Any,用于注解 payload

from fastapi import FastAPI, HTTPException, Request  # 导入 FastAPI 相关类
from fastapi.responses import JSONResponse  # 导入 JSONResponse,自定义错误响应

from .config import get_settings  # 导入配置加载函数
from .models import (  # 导入数据模型
    ChatSimulateResponse,  # 聊天响应模型
    ErrorResponse,  # 错误响应模型
    MessageIn,  # 聊天输入模型
    PersonaPermissionSummary,  # 人设权限摘要
    PersonasResponse,  # 人设列表响应
    RoleReply,  # 角色回复模型
)  # 结束导入
from .services.generator import (  # 导入生成器与任务生成器
    QuestGenerator,  # 任务生成器
    build_generator,  # 文本生成器工厂
)  # 结束导入
from .world.actions import (  # 导入动作相关类型
    ActionChange,  # 动作变更摘要
    ActionError,  # 动作异常
    ActionProcessor,  # 动作处理器
    ActionRequest,  # 动作请求模型
    ActionResponse,  # 动作响应模型
    ChunkCoord,  # 区块坐标模型
    Position,  # 坐标模型
)  # 结束导入
from .world.quests import QuestProgressor  # 导入任务推进器
from .world.store import WorldStore  # 导入世界存储
from .world.tiles import TileType  # 导入瓦片类型
from .world.world_state import WorldState  # 导入世界状态模型

logger = logging.getLogger(__name__)  # 创建模块级日志记录器

settings = get_settings()  # 读取全局配置
app = FastAPI(title=settings.app_name, debug=settings.debug)  # 创建 FastAPI 应用实例

_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 计算工程根目录
_DATA_ROOT = _PROJECT_ROOT / "data"  # 定义数据目录
_store = WorldStore(  # 初始化世界存储
    root=_DATA_ROOT,  # 指定数据根目录
    chunk_size=settings.chunk_size,  # 传入区块尺寸
    default_world_state=settings.world_state,  # 传入默认世界状态
    tick_tree_grow_steps=settings.tick_tree_grow_steps,  # 传入树苗成长步数
)  # 结束存储初始化
_progressor = QuestProgressor(_store)  # 创建任务推进器
_quest_generator = QuestGenerator(progressor=_progressor, settings=settings)  # 创建任务生成器
_quest_generator.ensure_seed_quests(_store.load_world_state())  # 确保存在初始任务
_action_processor = ActionProcessor(  # 创建动作处理器
    store=_store,  # 注入世界存储
    settings=settings,  # 注入配置
    permissions=settings.role_permissions,  # 注入角色权限
    quest_progressor=_progressor,  # 注入任务推进器
)  # 结束处理器初始化


@app.exception_handler(ActionError)  # 注册动作异常处理器
async def handle_action_error(request: Request, exc: ActionError) -> JSONResponse:  # 定义处理函数
    """将 ActionError 转换为统一的 JSON 响应。"""  # 函数 docstring,说明用途

    logger.warning("动作执行失败:%s", exc.message)  # 记录警告日志
    return JSONResponse(  # 返回 JSON 响应
        status_code=exc.code,  # 使用异常中的状态码
        content=ErrorResponse(code=exc.code, msg=exc.message).model_dump(),  # 构造错误响应
    )  # 结束响应


@app.get("/health", tags=["system"], summary="健康检查")  # 注册健康检查接口
async def health() -> dict[str, str]:  # 定义异步处理函数
    """返回服务的健康状态。"""  # 函数 docstring,说明用途

    return {"status": "ok"}  # 返回固定状态


@app.get("/world/state", tags=["world"], summary="获取世界状态")  # 注册世界状态查询接口
async def get_world_state() -> WorldState:  # 定义处理函数
    """返回当前的世界状态对象。"""  # 函数 docstring,说明用途

    return _store.load_world_state()  # 从存储加载世界状态


@app.get("/world/chunk", tags=["world"], summary="获取区块数据")  # 注册区块查询接口
async def get_chunk(cx: int, cy: int):  # 定义处理函数
    """返回指定区块的 32x32 瓦片网格。"""  # 函数 docstring,说明用途

    chunk = _store.load_chunk(cx=cx, cy=cy)  # 加载区块
    return chunk  # FastAPI 会自动序列化 Pydantic 模型


@app.get("/world/quests", tags=["world"], summary="获取任务列表")  # 注册任务查询接口
async def get_world_quests():  # 定义处理函数
    """返回当前存储中的所有任务。"""  # 函数 docstring,说明用途

    return _progressor.get_quests()  # 使用任务推进器读取任务


@app.post("/world/action", tags=["world"], summary="执行世界编辑动作")  # 注册动作接口
async def post_world_action(request: ActionRequest) -> ActionResponse:  # 定义处理函数
    """执行一次世界编辑动作并返回变更摘要。"""  # 函数 docstring,说明用途

    response = _action_processor.process(request=request)  # 调用处理器执行动作
    return response  # 返回动作响应


@app.post("/world/tick", tags=["world"], summary="推进世界时间")  # 注册时间推进接口
async def post_world_tick() -> dict[str, Any]:  # 定义处理函数
    """让世界时间前进一个单位,同时处理树苗成长。"""  # 函数 docstring,说明用途

    changes: list[ActionChange] = []  # 初始化变更列表
    for chunk in _store.iter_chunks():  # 遍历所有区块
        chunk_changed = False  # 标记区块是否修改
        for y in range(chunk.size):  # 遍历行
            for x in range(chunk.size):  # 遍历列
                cell = chunk.cell_at(x, y)  # 获取当前格子
                if cell.deco != TileType.TREE_SAPLING:  # 若不是树苗
                    continue  # 跳过
                new_cell = cell.model_copy(deep=True)  # 深拷贝格子
                next_stage = (new_cell.growth_stage or 0) + 1  # 计算下一成长阶段
                if next_stage >= _store.tick_tree_grow_steps:  # 若达到成熟阶段
                    new_cell.deco = TileType.TREE  # 将装饰替换为成树
                    new_cell.growth_stage = None  # 清空成长数据
                else:  # 尚未成熟
                    new_cell.growth_stage = next_stage  # 更新成长阶段
                chunk.apply_cell(x, y, new_cell)  # 写入新格子
                changes.append(  # 记录变更摘要
                    ActionChange(  # 创建 ActionChange
                        chunk=ChunkCoord(cx=chunk.cx, cy=chunk.cy),  # 区块坐标
                        pos=Position(x=x, y=y),  # 格子坐标
                        before=cell.model_dump(),  # 修改前数据
                        after=new_cell.model_dump(),  # 修改后数据
                    ),  # 结束 ActionChange
                )  # 结束 append
                chunk_changed = True  # 标记区块已修改
        if chunk_changed:  # 若区块被修改
            _store.save_chunk(chunk)  # 写回磁盘
    if changes:  # 若存在变更
        first = changes[0]  # 取出首条变更
        _store.append_action_log(  # 记录审计日志
            actor="系统",  # 日志执行者
            action_type="WORLD_TICK",  # 日志类型
            chunk={"cx": first.chunk.cx, "cy": first.chunk.cy},  # 记录区块
            pos={"x": first.pos.x, "y": first.pos.y},  # 记录坐标
            payload={"change_count": len(changes)},  # 附带变更数量
        )  # 结束日志记录
    return {  # 构造响应字典
        "message": "世界时间推进完成",  # 返回提示语
        "changes": [change.model_dump() for change in changes],  # 返回本次变更列表
    }  # 结束返回


@app.get("/personas", tags=["world"], summary="获取角色与权限摘要")  # 注册人设查询接口
async def get_personas() -> PersonasResponse:  # 定义处理函数
    """返回六位核心角色及其权限摘要。"""  # 函数 docstring,说明用途

    summaries: list[PersonaPermissionSummary] = []  # 初始化列表
    permission_map = settings.role_permissions  # 读取权限映射
    for persona in settings.personas:  # 遍历角色人设
        permission = permission_map.get(persona.name)  # 获取权限配置
        if permission is None:  # 若缺少权限
            logger.warning("角色 %s 缺少权限配置", persona.name)  # 输出警告日志
            continue  # 跳过
        whitelist_summary = {  # 构建瓦片白名单摘要
            action: [tile.value for tile in tiles]  # 将枚举转换为字符串
            for action, tiles in permission.tile_whitelist.items()  # 遍历白名单
        }  # 结束字典推导
        summaries.append(  # 添加摘要
            PersonaPermissionSummary(  # 构造摘要模型
                persona=persona,  # 角色人设
                allowed_actions=sorted(permission.allowed_actions),  # 允许的动作
                tile_whitelist=whitelist_summary,  # 瓦片白名单
                cooldown_seconds=permission.cooldown_seconds,  # 冷却配置
                daily_quota=permission.daily_quota,  # 配额配置
            ),  # 结束 PersonaPermissionSummary
        )  # 结束 append
    return PersonasResponse(personas=summaries)  # 返回响应模型


@app.post("/chat/simulate", tags=["chat"], summary="模拟群聊")  # 注册聊天模拟接口
async def chat_simulate(message: MessageIn) -> ChatSimulateResponse:  # 定义处理函数
    """根据用户输入与世界状态生成多角色回复。"""  # 函数 docstring,说明用途

    world_state = _store.load_world_state()  # 加载世界状态
    if message.location:  # 若请求覆盖地点
        world_state = WorldState(  # 创建新的世界状态实例
            version=world_state.version,  # 继承版本
            year=world_state.year,  # 继承年份
            season=world_state.season,  # 继承季节
            location=message.location,  # 使用覆盖地点
            major_events=world_state.major_events,  # 保留事件
            seed=world_state.seed,  # 保留种子
        )  # 结束 WorldState 构造
    personas = settings.personas  # 获取默认角色列表
    if message.roles:  # 若指定角色子集
        persona_lookup = {persona.name: persona for persona in personas}  # 构建名称映射
        try:  # 尝试按照请求顺序筛选角色
            personas = [persona_lookup[name] for name in message.roles]  # 根据名称选择
        except KeyError as exc:  # 捕获未知角色
            raise HTTPException(  # 抛出 400 错误
                status_code=400,  # 指定状态码
                detail=f"未知角色:{exc.args[0]}",  # 提供错误详情
            ) from exc  # 保留原始异常
    quests = _quest_generator.ensure_seed_quests(world_state)  # 获取当前任务
    generator = build_generator(  # 构建角色生成器
        settings=settings,  # 传入配置
        world_state=world_state,  # 传入世界状态
        personas=personas,  # 传入角色列表
        quests=quests,  # 传入任务列表
    )  # 结束生成器构建
    replies: list[RoleReply] = []  # 初始化回复列表
    event_text = "、".join(world_state.major_events)  # 合并重大事件
    prompt_prefix = "|".join(  # 构建统一提示前缀
        [
            f"地点:{world_state.location}",  # 地点信息
            f"季节:{world_state.season}",  # 季节信息
            f"事件:{event_text}",  # 事件信息
        ]
    )  # 结束 join
    for persona in personas:  # 遍历角色
        prompt = f"{message.content}|{prompt_prefix}"  # 组合提示词
        text = generator.generate(role=persona.name, prompt=prompt)  # 生成回复文本
        replies.append(RoleReply(role=persona.name, text=text))  # 添加回复
    return ChatSimulateResponse(replies=replies)  # 返回响应
