"""针对区块加载与持久化行为的测试用例。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

from pathlib import Path  # 导入 Path,用于定位文件

from miniWorld.config import get_settings  # 导入配置获取函数
from miniWorld.world.store import WorldStore  # 导入世界存储
from miniWorld.world.tiles import TileType  # 导入瓦片类型


def test_chunk_creation_and_bounds(tmp_path: Path) -> None:  # 定义测试函数,验证默认创建与越界校验
    """确保新建区块填充草地且坐标越界会抛出异常。"""  # 函数 docstring,说明测试目标

    settings = get_settings()  # 加载配置
    store = WorldStore(  # 创建临时世界存储
        root=tmp_path,  # 使用 pytest 提供的临时目录
        chunk_size=settings.chunk_size,  # 传入区块尺寸
        default_world_state=settings.world_state,  # 传入默认世界状态
        tick_tree_grow_steps=settings.tick_tree_grow_steps,  # 传入树苗成长步数
    )  # 结束存储初始化
    chunk = store.load_chunk(cx=5, cy=6)  # 加载一个新建区块
    assert chunk.cell_at(0, 0).base == TileType.GRASS  # 断言默认格子为草地
    try:  # 尝试访问越界坐标
        chunk.cell_at(chunk.size, 0)  # 调用 cell_at 使用非法坐标
    except ValueError:  # 捕获越界异常
        pass  # 表示测试通过
    else:  # 若未抛出异常
        raise AssertionError("越界访问应当抛出 ValueError")  # 手动失败测试


def test_chunk_persistence_roundtrip(tmp_path: Path) -> None:  # 定义测试函数,验证持久化一致性
    """修改区块后保存并重新加载,应保持数据一致。"""  # 函数 docstring,说明测试目标

    settings = get_settings()  # 加载配置
    store = WorldStore(  # 创建临时世界存储
        root=tmp_path,  # 使用临时目录
        chunk_size=settings.chunk_size,  # 传入区块尺寸
        default_world_state=settings.world_state,  # 传入默认世界状态
        tick_tree_grow_steps=settings.tick_tree_grow_steps,  # 传入树苗成长步数
    )  # 结束存储初始化
    chunk = store.load_chunk(cx=2, cy=3)  # 加载目标区块
    cell = chunk.cell_at(1, 1)  # 获取目标格子
    new_cell = cell.model_copy(deep=True)  # 深拷贝格子
    new_cell.base = TileType.ROAD  # 修改为石路
    chunk.apply_cell(1, 1, new_cell)  # 应用修改
    store.save_chunk(chunk)  # 保存到磁盘
    fresh_store = WorldStore(  # 创建新的存储实例,确保从磁盘重新加载
        root=tmp_path,  # 使用相同目录
        chunk_size=settings.chunk_size,  # 传入区块尺寸
        default_world_state=settings.world_state,  # 传入默认世界状态
        tick_tree_grow_steps=settings.tick_tree_grow_steps,  # 传入树苗成长步数
    )  # 结束新存储初始化
    reloaded = fresh_store.load_chunk(cx=2, cy=3)  # 重新加载区块
    assert reloaded.cell_at(1, 1).base == TileType.ROAD  # 断言修改被持久化
