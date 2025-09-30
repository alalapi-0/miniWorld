"""测试素材下载脚本与校验脚本的核心行为。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 启用前向引用,便于类型标注

import json  # 导入 json,构造伪元数据
import sys  # 导入 sys,以便修改 argv
from pathlib import Path  # 导入 Path,构造临时路径

import pytest  # 导入 pytest,组织测试

from scripts import fetch_assets, verify_bindings  # 导入待测脚本


def test_fetch_assets_dry_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:  # 定义 dry-run 测试
    """dry-run 模式下脚本应生成许可证文档并提示手动下载。"""  # 函数 docstring,说明用途

    catalog = {"sources": [{"name": "Test CC0", "license": "CC0", "download": None, "notes": "手动"}]}  # 构造目录数据
    catalog_path = tmp_path / "catalog.json"  # 定义目录文件路径
    license_path = tmp_path / "licenses.md"  # 定义许可证文件路径
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")  # 写入目录文件
    monkeypatch.setattr(fetch_assets, "CATALOG_PATH", catalog_path)  # 覆盖目录路径
    monkeypatch.setattr(fetch_assets, "LICENSE_PATH", license_path)  # 覆盖许可证路径
    exit_code = fetch_assets.main(["--dry-run", "--only-cc0", "--dest", str(tmp_path / "build")])  # 执行脚本
    assert exit_code == 0  # 断言成功
    content = license_path.read_text(encoding="utf-8")  # 读取许可证内容
    assert "当前未拉取任何素材" in content  # 断言包含提示
    assert "notes" in catalog_path.read_text(encoding="utf-8")  # 确认目录仍可被读取


def test_verify_bindings_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:  # 定义校验成功测试
    """当映射与文件匹配时,校验脚本应返回成功。"""  # 函数 docstring,说明用途

    root = tmp_path / "project"  # 定义根目录
    mapping_dir = root / "assets" / "mapping"  # 定义映射目录
    build_dir = root / "assets" / "build" / "kenney"  # 定义素材目录
    mapping_dir.mkdir(parents=True)  # 创建映射目录
    build_dir.mkdir(parents=True)  # 创建素材目录
    atlas_path = build_dir / "tilesheet.png"  # 定义图集文件
    persona_path = root / "assets" / "build" / "kenney" / "hero.png"  # 定义头像文件
    atlas_path.write_text("", encoding="utf-8")  # 创建空文件
    persona_path.write_text("", encoding="utf-8")  # 创建空文件
    tileset_data = {"tile_size": 32, "bindings": {"GRASS": {"atlas": "assets/build/kenney/tilesheet.png", "id": 1}}}  # 构造瓦片映射
    personas_data = {"勇者": {"avatar": "assets/build/kenney/hero.png"}}  # 构造角色映射
    (mapping_dir / "tileset_binding.json").write_text(json.dumps(tileset_data), encoding="utf-8")  # 写入瓦片文件
    (mapping_dir / "personas_binding.json").write_text(json.dumps(personas_data), encoding="utf-8")  # 写入角色文件
    monkeypatch.setattr(sys, "argv", ["verify", "--mapping-dir", str(mapping_dir), "--asset-root", str(root), "--build-dir", str(root / "assets" / "build")])  # 设置命令行参数
    exit_code = verify_bindings.main()  # 执行脚本
    captured = capsys.readouterr()  # 捕获输出
    assert exit_code == 0  # 断言成功
    assert "校验通过" in captured.out  # 确认输出


def test_verify_bindings_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:  # 定义缺失文件测试
    """当映射缺失时,校验脚本应返回非零并输出提示。"""  # 函数 docstring,说明用途

    mapping_dir = tmp_path / "mapping"  # 定义映射目录
    mapping_dir.mkdir()  # 创建目录
    monkeypatch.setattr(sys, "argv", ["verify", "--mapping-dir", str(mapping_dir), "--asset-root", str(tmp_path), "--build-dir", str(tmp_path / "build")])  # 设置命令行参数
    exit_code = verify_bindings.main()  # 执行脚本
    captured = capsys.readouterr()  # 捕获输出
    assert exit_code == 1  # 断言失败码
    assert "缺少" in captured.out  # 检查输出包含提示
