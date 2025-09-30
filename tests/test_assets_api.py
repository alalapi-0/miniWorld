"""测试素材映射相关 API 的行为。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 启用前向引用,便于类型标注

import json  # 导入 json,用于写入测试文件
from pathlib import Path  # 导入 Path,构造临时路径

import pytest  # 导入 pytest,组织测试
from fastapi.testclient import TestClient  # 导入 TestClient,调用 API

from src.miniWorld import assets_api  # 导入素材 API 模块
from src.miniWorld.app import app  # 导入应用实例

client = TestClient(app)  # 创建测试客户端


@pytest.fixture()  # 声明 pytest 固件
def temp_mapping_dir(tmp_path: Path) -> Path:  # 定义临时映射目录固件
    """创建并返回用于测试的临时映射目录。"""  # 函数 docstring,说明用途

    mapping_dir = tmp_path / "mapping"  # 组合目录
    mapping_dir.mkdir()  # 创建目录
    return mapping_dir  # 返回目录


def test_assets_api_returns_mappings(monkeypatch: pytest.MonkeyPatch, temp_mapping_dir: Path) -> None:  # 定义测试函数
    """当映射文件存在时,API 应返回完整 JSON。"""  # 函数 docstring,说明用途

    tileset_path = temp_mapping_dir / "tileset_binding.json"  # 组合瓦片映射路径
    personas_path = temp_mapping_dir / "personas_binding.json"  # 组合角色映射路径
    tileset_data = {  # 构造瓦片数据
        "tile_size": 16,  # 指定瓦片尺寸
        "bindings": {"GRASS": {"atlas": "assets/build/demo.png", "id": 1}},  # 定义映射
    }  # 结束字典
    personas_data = {"勇者": {"avatar": "assets/build/hero.png"}}  # 构造角色数据
    tileset_path.write_text(json.dumps(tileset_data), encoding="utf-8")  # 写入瓦片文件
    personas_path.write_text(json.dumps(personas_data), encoding="utf-8")  # 写入角色文件
    monkeypatch.setattr(assets_api, "_MAPPING_DIR", temp_mapping_dir)  # 覆盖映射目录
    response_tiles = client.get("/assets/tilesets")  # 调用瓦片接口
    response_personas = client.get("/assets/personas")  # 调用角色接口
    assert response_tiles.status_code == 200  # 断言状态码
    assert response_personas.status_code == 200  # 断言状态码
    assert response_tiles.json()["bindings"]["GRASS"]["id"] == 1  # 校验返回内容
    assert response_personas.json()["勇者"]["avatar"] == "assets/build/hero.png"  # 校验返回内容


def test_assets_api_handles_missing_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:  # 定义缺失文件测试
    """当映射缺失时,API 应返回降级提示而不是错误。"""  # 函数 docstring,说明用途

    monkeypatch.setattr(assets_api, "_MAPPING_DIR", tmp_path)  # 将映射目录指向空目录
    tiles_response = client.get("/assets/tilesets")  # 调用瓦片接口
    personas_response = client.get("/assets/personas")  # 调用角色接口
    assert tiles_response.status_code == 200  # 断言状态码
    assert personas_response.status_code == 200  # 断言状态码
    assert tiles_response.json()["bindings"] == {}  # 降级结构应为空绑定
    assert "message" in tiles_response.json()  # 应包含提示信息
    assert personas_response.json()["personas"] == {}  # 降级结构应为空角色映射
    assert "message" in personas_response.json()  # 应包含提示信息
