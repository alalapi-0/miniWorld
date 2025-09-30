"""验证世界编辑动作的权限与规则约束。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

from fastapi.testclient import TestClient  # 导入 TestClient,用于请求接口

from miniWorld.app import app  # 导入 FastAPI 应用实例

client = TestClient(app)  # 创建测试客户端


def test_road_building_and_tree_planting() -> None:  # 定义测试函数,验证修路与种树动作
    """勇者应能铺路,神官应能种树。"""  # 函数 docstring,说明测试目标

    response = client.post(  # 调用动作接口铺设石路
        "/world/action",  # 指定路径
        json={  # 构建请求体
            "actor": "勇者",  # 执行动作的角色
            "type": "PLACE_TILE",  # 动作类型
            "chunk": {"cx": 20, "cy": 20},  # 目标区块
            "pos": {"x": 0, "y": 0},  # 目标坐标
            "payload": {"tile": "ROAD"},  # 指定瓦片
            "client_ts": 1_000_000,  # 时间戳
        },  # 结束 JSON
    )  # 结束请求
    assert response.status_code == 200  # 断言请求成功
    payload = response.json()  # 解析响应数据
    assert payload["success"] is True  # 断言动作成功

    response = client.post(  # 调用动作接口种植树苗
        "/world/action",  # 指定路径
        json={  # 构建请求体
            "actor": "神官",  # 执行动作的角色
            "type": "PLANT_TREE",  # 动作类型
            "chunk": {"cx": 20, "cy": 20},  # 同一区块
            "pos": {"x": 1, "y": 0},  # 邻近坐标
            "payload": {},  # 种树无需额外 payload
            "client_ts": 1_000_100,  # 时间戳
        },  # 结束 JSON
    )  # 结束请求
    assert response.status_code == 200  # 断言请求成功
    assert response.json()["success"] is True  # 断言动作成功


def test_structure_rules_and_invalid_action() -> None:  # 定义测试函数,验证造屋与非法放置
    """验证水面建屋受限以及剑士不能放置结构。"""  # 函数 docstring,说明测试目标

    response = client.post(  # 使用魔导师将地块改为水面
        "/world/action",  # 指定路径
        json={  # 构建请求体
            "actor": "魔导师",  # 执行动作
            "type": "PLACE_TILE",  # 动作类型
            "chunk": {"cx": 21, "cy": 21},  # 目标区块
            "pos": {"x": 0, "y": 0},  # 目标坐标
            "payload": {"tile": "WATER"},  # 设置瓦片为水面
            "client_ts": 1_001_000,  # 时间戳
        },  # 结束 JSON
    )  # 结束请求
    assert response.status_code == 200  # 断言修改成功

    response = client.post(  # 尝试在水面放置房基
        "/world/action",  # 指定路径
        json={  # 构建请求体
            "actor": "公主",  # 执行动作的角色
            "type": "PLACE_STRUCTURE",  # 动作类型
            "chunk": {"cx": 21, "cy": 21},  # 同一区块
            "pos": {"x": 0, "y": 0},  # 同一坐标
            "payload": {"tile": "HOUSE_BASE"},  # 房屋地基
            "client_ts": 1_001_500,  # 时间戳
        },  # 结束 JSON
    )  # 结束请求
    assert response.status_code == 400  # 断言触发规则限制
    assert response.json()["code"] == 400  # 断言错误码一致

    response = client.post(  # 剑士尝试放置结构
        "/world/action",  # 指定路径
        json={  # 构建请求体
            "actor": "剑士",  # 执行动作
            "type": "PLACE_STRUCTURE",  # 动作类型
            "chunk": {"cx": 22, "cy": 22},  # 另一区块
            "pos": {"x": 0, "y": 0},  # 目标坐标
            "payload": {"tile": "HOUSE_BASE"},  # 房基
            "client_ts": 1_002_000,  # 时间戳
        },  # 结束 JSON
    )  # 结束请求
    assert response.status_code == 403  # 断言权限不足
    assert response.json()["code"] == 403  # 断言错误码一致
