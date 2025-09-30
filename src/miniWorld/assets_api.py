"""提供素材映射读取接口的 FastAPI 路由模块。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 启用前向引用,便于类型标注

import json  # 导入 json,读取映射文件
import logging  # 导入 logging,记录警告
from pathlib import Path  # 导入 Path,定位文件
from typing import Any  # 导入 Any,用于类型标注

from fastapi import APIRouter  # 导入 APIRouter,注册子路由

logger = logging.getLogger(__name__)  # 创建模块级日志记录器

_ROUTER = APIRouter(prefix="/assets", tags=["assets"])  # 创建带前缀的路由器
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 计算项目根目录
_MAPPING_DIR = _PROJECT_ROOT / "assets" / "mapping"  # 定义映射目录


def _load_json(path: Path) -> dict[str, Any]:  # 定义内部 JSON 读取函数
    """尝试从给定路径加载 JSON 文件,若失败则抛出异常。"""  # 函数 docstring,说明用途

    with path.open("r", encoding="utf-8") as fp:  # 打开文件
        return json.load(fp)  # 返回解析结果


@_ROUTER.get("/tilesets", summary="获取瓦片图集映射", response_model=dict[str, Any])  # 注册瓦片映射接口
async def get_tileset_bindings() -> dict[str, Any]:  # 定义异步处理函数
    """返回瓦片与外部图集的映射 JSON,缺失时提供降级结构。"""  # 函数 docstring,说明用途

    path = _MAPPING_DIR / "tileset_binding.json"  # 组合文件路径
    if not path.exists():  # 检查文件存在
        logger.warning("tileset_binding.json 缺失,返回降级提示")  # 输出警告
        return {"bindings": {}, "message": "尚未准备外部瓦片素材,请执行 fetch_assets.py。"}  # 返回降级结构
    try:  # 捕获潜在解析错误
        data = _load_json(path)  # 尝试读取文件
        return data  # 返回文件内容
    except (OSError, json.JSONDecodeError) as exc:  # 捕获异常
        logger.warning("读取 tileset_binding.json 失败:%s", exc)  # 记录警告
        return {"bindings": {}, "message": "瓦片映射解析失败,请检查 JSON 格式。"}  # 返回降级结构


@_ROUTER.get("/personas", summary="获取角色头像映射", response_model=dict[str, Any])  # 注册角色头像接口
async def get_persona_bindings() -> dict[str, Any]:  # 定义异步处理函数
    """返回角色头像映射 JSON,缺失时返回降级结构。"""  # 函数 docstring,说明用途

    path = _MAPPING_DIR / "personas_binding.json"  # 组合文件路径
    if not path.exists():  # 检查文件存在
        logger.warning("personas_binding.json 缺失,返回降级提示")  # 输出警告
        return {"personas": {}, "message": "尚未准备角色头像素材,请执行 fetch_assets.py。"}  # 返回降级结构
    try:  # 捕获潜在错误
        data = _load_json(path)  # 尝试读取文件
        return data  # 返回文件内容
    except (OSError, json.JSONDecodeError) as exc:  # 捕获异常
        logger.warning("读取 personas_binding.json 失败:%s", exc)  # 记录警告
        return {"personas": {}, "message": "角色头像映射解析失败,请检查 JSON 格式。"}  # 返回降级结构


router = _ROUTER  # 暴露路由对象供应用挂载
