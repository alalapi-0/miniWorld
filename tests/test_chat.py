"""针对聊天模拟接口的单元测试。"""  # 模块级 docstring,说明用途

from fastapi.testclient import TestClient  # 导入 TestClient,用于发送请求

from ai_groupchat.app import app  # 导入 FastAPI 应用实例

client = TestClient(app)  # 创建测试客户端,执行 HTTP 请求


def test_chat_simulate_returns_persona_aware_replies() -> None:  # 定义测试函数,验证人设融合输出
    """确保聊天模拟接口返回包含世界观提示的人设化文本。"""  # 函数 docstring,说明测试目标

    response = client.post(  # 发送 POST 请求到模拟接口
        "/chat/simulate",  # 指定路径
        json={"content": "今日战术"},  # 提供示例输入内容
    )  # 结束请求发送
    assert response.status_code == 200  # 断言状态码为 200
    data = response.json()  # 解析响应 JSON
    replies = data["replies"]  # 提取回复列表
    assert len(replies) == 6  # 断言默认返回六位角色
    sample_text = replies[0]["text"]  # 获取首条回复文本
    assert "近期事件" in sample_text  # 断言文本包含世界事件提示
    assert "以" in sample_text and "身份" in sample_text  # 断言文本提及角色身份


def test_chat_simulate_filters_role_and_location() -> None:  # 定义测试函数,验证角色筛选与地点覆盖
    """确保接口可按角色筛选并在提示中反映临时地点。"""  # 函数 docstring,说明测试目标

    response = client.post(  # 发送带筛选的请求
        "/chat/simulate",  # 指定路径
        json={  # 指定角色与临时地点
            "content": "勘察地形",  # 用户输入内容
            "roles": ["盗贼"],  # 指定只生成盗贼
            "location": "隐匿峡谷",  # 指定临时地点
        },  # 结束 JSON 构造
    )  # 结束请求发送
    assert response.status_code == 200  # 断言状态码为 200
    payload = response.json()  # 解析响应 JSON
    replies = payload["replies"]  # 提取回复列表
    assert replies[0]["role"] == "盗贼"  # 断言仅返回盗贼角色
    assert "隐匿峡谷" in replies[0]["text"]  # 断言文本包含覆盖后的地点
