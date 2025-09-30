"""针对聊天模拟接口的单元测试。"""  # 模块级 docstring，说明用途

from fastapi.testclient import TestClient  # 导入 TestClient，用于发送请求

from ai_groupchat.app import app  # 导入 FastAPI 应用实例
from ai_groupchat.config import get_settings  # 导入配置函数，便于读取种子

client = TestClient(app)  # 创建测试客户端，执行 HTTP 请求


def test_chat_simulate_returns_role_replies() -> None:  # 定义测试函数，验证模拟接口
    """确保聊天模拟接口返回包含角色回复的稳定结果。"""  # 函数 docstring，说明测试目标

    response = client.post(  # 发送 POST 请求到模拟接口
        "/chat/simulate",  # 指定路径
        json={"content": "你好，今天的议题是什么？"},  # 提供示例输入内容
    )  # 结束请求发送
    assert response.status_code == 200  # 断言状态码为 200
    data = response.json()  # 解析响应 JSON
    assert "replies" in data  # 断言返回包含 replies 字段
    replies = data["replies"]  # 提取回复列表
    assert isinstance(replies, list)  # 断言 replies 为列表
    assert replies  # 断言列表非空
    first_reply = replies[0]  # 获取首条回复
    assert "role" in first_reply  # 断言首条回复包含 role 字段
    assert "text" in first_reply  # 断言首条回复包含 text 字段
    assert "制定下一步计划" in first_reply["text"]  # 断言首条回复文本包含可预测的关键词
    settings = get_settings()  # 读取配置，确保种子与默认值可用
    assert settings.seed == 42  # 断言种子为固定值 42，保障可重复
