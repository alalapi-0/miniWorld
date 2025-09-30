"""对主要 API 端点进行冒烟测试。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

from fastapi.testclient import TestClient  # 导入 TestClient,用于模拟 HTTP 请求

from miniWorld.app import app  # 导入 FastAPI 应用实例

client = TestClient(app)  # 创建测试客户端


def test_world_state_and_chunk_endpoints() -> None:  # 定义测试函数,验证世界状态与区块接口
    """确保世界状态与区块接口均能返回有效数据。"""  # 函数 docstring,说明测试目标

    state_response = client.get("/world/state")  # 请求世界状态
    assert state_response.status_code == 200  # 断言成功
    state = state_response.json()  # 解析 JSON
    assert {"year", "season", "location"}.issubset(state.keys())  # 断言关键字段存在

    chunk_response = client.get("/world/chunk", params={"cx": 0, "cy": 0})  # 请求区块数据
    assert chunk_response.status_code == 200  # 断言成功
    chunk = chunk_response.json()  # 解析 JSON
    assert len(chunk["grid"]) == 32  # 断言行数为 32
    assert len(chunk["grid"][0]) == 32  # 断言列数为 32


def test_world_quests_and_personas() -> None:  # 定义测试函数,验证任务与人设接口
    """确保任务列表与角色权限接口返回结构化数据。"""  # 函数 docstring,说明测试目标

    quests_response = client.get("/world/quests")  # 请求任务列表
    assert quests_response.status_code == 200  # 断言成功
    quests = quests_response.json()  # 解析 JSON
    assert isinstance(quests, list)  # 断言返回列表

    personas_response = client.get("/personas")  # 请求人设列表
    assert personas_response.status_code == 200  # 断言成功
    personas = personas_response.json()  # 解析 JSON
    assert "personas" in personas  # 断言顶层键存在
    assert personas["personas"]  # 断言至少存在一个角色


def test_action_error_and_tick_endpoint() -> None:  # 定义测试函数,验证错误分支与 tick 接口
    """未知角色触发错误,世界 tick 返回摘要。"""  # 函数 docstring,说明测试目标

    response = client.post(  # 使用未知角色调用动作接口
        "/world/action",  # 指定路径
        json={  # 构建请求体
            "actor": "未知角色",  # 不存在的角色
            "type": "PLACE_TILE",  # 动作类型
            "chunk": {"cx": 5, "cy": 5},  # 区块坐标
            "pos": {"x": 0, "y": 0},  # 格子坐标
            "payload": {"tile": "ROAD"},  # 指定瓦片
            "client_ts": 12345,  # 时间戳
        },  # 结束 JSON
    )  # 结束请求
    assert response.status_code == 404  # 断言返回 404
    assert response.json()["code"] == 404  # 断言错误码一致

    tick_response = client.post("/world/tick")  # 调用世界时间推进接口
    assert tick_response.status_code == 200  # 断言成功
    tick_payload = tick_response.json()  # 解析 JSON
    assert "message" in tick_payload  # 断言包含消息
    assert "changes" in tick_payload  # 断言包含变更列表
