"""测试任务生成与进度推进的流程。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

import time  # 导入 time,用于生成时间戳

from fastapi.testclient import TestClient  # 导入 TestClient,用于调用接口

from miniWorld.app import _progressor, _store, app  # 导入应用、任务推进器与存储
from miniWorld.world.actions import ChunkCoord  # 导入区块坐标模型
from miniWorld.world.quests import ActionRequirement, Quest, QuestStatus  # 导入任务模型
from miniWorld.world.tiles import TileType  # 导入瓦片类型

client = TestClient(app)  # 创建测试客户端


def test_quest_progression() -> None:  # 定义测试函数,验证任务推进
    """通过执行动作推动任务状态从 OPEN 到 DONE。"""  # 函数 docstring,说明测试目标

    original = [quest.model_dump(mode="json") for quest in _progressor.get_quests()]  # 备份原任务
    chunk_path = _store._chunk_dir / "40_40.json"  # 计算测试区块文件路径
    try:  # 使用 try/finally 确保恢复现场
        timestamp = int(time.time() * 1000)  # 生成时间戳
        quest = Quest(  # 构建测试任务
            id="quest_test_progress",  # 任务 ID
            title="测试修路任务",  # 标题
            desc="铺设两格道路以验证任务进度。",  # 描述
            giver="公主",  # 发布者
            assignee=["勇者"],  # 执行角色
            status=QuestStatus.OPEN,  # 初始状态
            requirements=[  # 需求列表
                ActionRequirement(  # 单个需求
                    action_type="PLACE_TILE",  # 动作类型
                    target_tile=TileType.ROAD,  # 目标瓦片
                    chunk=ChunkCoord(cx=40, cy=40),  # 目标区块
                    target_count=2,  # 需要铺设的数量
                ),  # 结束需求
            ],  # 结束需求列表
            rewards=["测试奖励"],  # 奖励描述
            created_at=timestamp,  # 创建时间
            updated_at=timestamp,  # 更新时间
        )  # 结束 Quest 构造
        _progressor.save_quests([quest])  # 写入测试任务

        response = client.post(  # 执行第一次铺路
            "/world/action",  # 指定路径
            json={  # 构建请求体
                "actor": "勇者",  # 执行动作的角色
                "type": "PLACE_TILE",  # 动作类型
                "chunk": {"cx": 40, "cy": 40},  # 目标区块
                "pos": {"x": 0, "y": 0},  # 坐标
                "payload": {"tile": "ROAD"},  # 指定瓦片
                "client_ts": timestamp + 1,  # 时间戳
            },  # 结束 JSON
        )  # 结束请求
        assert response.status_code == 200  # 断言成功
        quests_after_first = _progressor.get_quests()  # 读取任务列表
        assert quests_after_first[0].status == QuestStatus.IN_PROGRESS  # 断言状态更新
        assert quests_after_first[0].requirements[0].progress == 1  # 断言进度为 1

        response = client.post(  # 执行第二次铺路
            "/world/action",  # 指定路径
            json={  # 构建请求体
                "actor": "勇者",  # 执行动作
                "type": "PLACE_TILE",  # 动作类型
                "chunk": {"cx": 40, "cy": 40},  # 目标区块
                "pos": {"x": 1, "y": 0},  # 坐标
                "payload": {"tile": "ROAD"},  # 指定瓦片
                "client_ts": timestamp + 2,  # 时间戳
            },  # 结束 JSON
        )  # 结束请求
        assert response.status_code == 200  # 断言成功
        quests_after_second = _progressor.get_quests()  # 重新读取任务
        assert quests_after_second[0].status == QuestStatus.DONE  # 断言任务完成
        assert quests_after_second[0].requirements[0].progress == 2  # 断言进度达到目标
    finally:  # 无论成功与否均执行
        _progressor.save_quests([Quest.model_validate(item) for item in original])  # 恢复原任务
        if chunk_path.exists():  # 若测试区块文件存在
            chunk_path.unlink()  # 删除以避免污染
