"""验证群聊接口是否融入世界与任务上下文。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

from fastapi.testclient import TestClient  # 导入 TestClient,用于请求接口

from miniWorld.app import app  # 导入 FastAPI 应用实例

client = TestClient(app)  # 创建测试客户端


def test_chat_simulate_contains_world_and_quest() -> None:  # 定义测试函数,验证回复内容
    """回复文本应包含地点与任务摘要信息。"""  # 函数 docstring,说明测试目标

    response = client.post(  # 调用聊天模拟接口
        "/chat/simulate",  # 指定路径
        json={"content": "汇报施工进度"},  # 发送简单请求
    )  # 结束请求
    assert response.status_code == 200  # 断言接口成功
    payload = response.json()  # 解析响应体
    assert payload["replies"], "接口应返回至少一条回复"  # 断言存在回复
    first_reply = payload["replies"][0]["text"]  # 取出首条回复文本
    assert "地点:" in first_reply  # 断言包含地点提示
    assert "当前任务" in first_reply or "暂无活跃任务" in first_reply  # 断言包含任务摘要
