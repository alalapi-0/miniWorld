"""针对世界状态接口的单元测试。"""  # 模块级 docstring,说明用途

from fastapi.testclient import TestClient  # 导入 TestClient,用于模拟 HTTP 请求

from ai_groupchat.app import app  # 导入 FastAPI 应用实例

client = TestClient(app)  # 创建测试客户端


def test_get_world_state_returns_current_state() -> None:  # 定义测试函数,验证查询接口
    """确保 /world/state 返回有效的世界状态。"""  # 函数 docstring,说明测试目标

    response = client.get("/world/state")  # 发送 GET 请求
    assert response.status_code == 200  # 断言状态码为 200
    payload = response.json()  # 解析 JSON 数据
    assert payload["season"] in {"春", "夏", "秋", "冬"}  # 断言季节字段有效
    assert isinstance(payload["major_events"], list)  # 断言重大事件为列表


def test_update_world_state_when_debug_enabled() -> None:  # 定义测试函数,验证更新接口
    """确保在调试模式下可以修改世界状态并恢复原状。"""  # 函数 docstring,说明测试目标

    original = client.get("/world/state").json()  # 记录原始状态
    try:  # 使用 try/finally 确保最终恢复
        response = client.post(  # 发送 POST 请求更新世界状态
            "/world/state",  # 指定路径
            json={  # 构造新的世界状态
                "year": 2048,  # 设置新的年份
                "season": "冬",  # 设置新的季节
                "major_events": ["测试事件"],  # 设置新的事件列表
                "location": "单元测试临时营地",  # 设置新的地点
            },  # 结束 JSON 构造
        )  # 结束请求发送
        assert response.status_code == 200  # 断言状态码为 200
        updated = response.json()  # 解析更新结果
        assert updated["year"] == 2048  # 断言年份更新成功
        assert updated["location"] == "单元测试临时营地"  # 断言地点更新成功
    finally:  # 无论成功与否都执行恢复
        client.post("/world/state", json=original)  # 调用接口恢复原始世界状态
