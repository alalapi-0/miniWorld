"""针对健康检查接口的单元测试。"""  # 模块级 docstring，说明用途

from fastapi.testclient import TestClient  # 导入 TestClient，用于模拟 HTTP 请求

from ai_groupchat.app import app  # 导入 FastAPI 应用实例，供测试调用

client = TestClient(app)  # 创建测试客户端，复用应用实例


def test_health_endpoint_returns_ok() -> None:  # 定义测试函数，验证健康检查
    """确保健康检查接口返回 200 与正确的 JSON。"""  # 函数 docstring，说明测试目标

    response = client.get("/health")  # 发送 GET 请求到 /health
    assert response.status_code == 200  # 断言状态码为 200
    assert response.json() == {"status": "ok"}  # 断言返回的 JSON 与预期一致
