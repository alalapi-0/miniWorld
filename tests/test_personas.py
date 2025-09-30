"""针对人设与像素元数据接口的单元测试。"""  # 模块级 docstring,说明用途

from fastapi.testclient import TestClient  # 导入 TestClient,用于模拟 HTTP 请求

from ai_groupchat.app import app  # 导入 FastAPI 应用实例供测试使用

client = TestClient(app)  # 创建测试客户端


def test_get_personas_returns_all_roles() -> None:  # 定义测试函数,验证人设接口
    """确保 /personas 返回六位角色并包含核心字段。"""  # 函数 docstring,说明测试目标

    response = client.get("/personas")  # 发送 GET 请求获取人设
    assert response.status_code == 200  # 断言状态码为 200
    personas = response.json()  # 解析 JSON 响应
    assert len(personas) == 6  # 断言返回六位角色
    first = personas[0]  # 取第一位角色
    required_keys = [  # 定义必须存在的字段列表
        "name",  # 角色名称
        "archetype",  # 原型说明
        "speaking_style",  # 说话风格
        "knowledge_tags",  # 知识标签
        "moral_axis",  # 道德阵营
        "goal",  # 角色目标
    ]  # 结束字段列表
    for key in required_keys:  # 遍历必需字段
        assert key in first  # 断言每个字段存在


def test_get_pixel_meta_collects_files() -> None:  # 定义测试函数,验证像素元数据接口
    """确保 /pixel/meta 汇总目录下的元数据文件。"""  # 函数 docstring,说明测试目标

    response = client.get("/pixel/meta")  # 发送 GET 请求获取元数据
    assert response.status_code == 200  # 断言状态码为 200
    payload = response.json()  # 解析 JSON 响应
    assert "files" in payload  # 断言响应包含 files 字段
    files = payload["files"]  # 提取文件映射
    assert "tilesets/overworld_tileset.meta.json" in files  # 断言包含世界地图瓦片元数据
    assert "sprites/personas.meta.json" in files  # 断言包含角色像素规格元数据
