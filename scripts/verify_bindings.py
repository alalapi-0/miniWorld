"""校验素材映射 JSON 与本地素材文件是否完备的脚本。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 启用前向引用,便于类型标注

import argparse  # 导入 argparse,处理命令行参数
import json  # 导入 json,解析映射文件
import sys  # 导入 sys,控制退出码
from pathlib import Path  # 导入 Path,统一路径操作
from typing import Any  # 导入 Any,用于类型标注

DEFAULT_ROOT = Path(__file__).resolve().parents[1]  # 计算仓库根目录
DEFAULT_MAPPING_DIR = DEFAULT_ROOT / "assets" / "mapping"  # 默认映射目录
DEFAULT_BUILD_DIR = DEFAULT_ROOT / "assets" / "build"  # 默认素材生成目录


def parse_args() -> argparse.Namespace:  # 定义参数解析函数
    """解析命令行参数以支持自定义目录。"""  # 函数 docstring,说明用途

    parser = argparse.ArgumentParser(description="校验素材映射与文件存在性")  # 创建解析器
    parser.add_argument("--mapping-dir", type=Path, default=DEFAULT_MAPPING_DIR, help="指定映射 JSON 所在目录")  # 映射目录参数
    parser.add_argument("--asset-root", type=Path, default=DEFAULT_ROOT, help="指定素材路径解析的根目录")  # 素材根目录参数
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR, help="指定素材实际存放目录")  # build 目录参数
    return parser.parse_args()  # 返回解析结果


def load_json(path: Path) -> Any:  # 定义 JSON 读取函数
    """读取给定路径的 JSON 文件并返回解析后的对象。"""  # 函数 docstring,说明用途

    with path.open("r", encoding="utf-8") as fp:  # 打开文件
        return json.load(fp)  # 返回解析后的对象


def validate_tilesets(mapping_dir: Path, asset_root: Path) -> list[str]:  # 定义瓦片映射校验函数
    """校验瓦片图集映射结构与引用路径是否存在,返回错误消息列表。"""  # 函数 docstring,说明用途

    tileset_path = mapping_dir / "tileset_binding.json"  # 组合瓦片映射路径
    if not tileset_path.exists():  # 检查文件是否存在
        return ["缺少 tileset_binding.json,需要先执行素材拉取脚本或手动创建映射。"]  # 返回错误
    data = load_json(tileset_path)  # 读取 JSON
    errors: list[str] = []  # 初始化错误列表
    if "bindings" not in data:  # 检查键是否存在
        errors.append("tileset_binding.json 缺少 bindings 字段。")  # 追加错误
        return errors  # 直接返回
    for tile_type, binding in data["bindings"].items():  # 遍历每个绑定
        if not isinstance(binding, dict):  # 检查结构
            errors.append(f"瓦片 {tile_type} 的绑定不是对象。")  # 追加错误
            continue  # 继续下一项
        atlas = binding.get("atlas")  # 读取图集路径
        tile_id = binding.get("id")  # 读取瓦片编号
        if not atlas:  # 检查 atlas
            errors.append(f"瓦片 {tile_type} 缺少 atlas 字段。")  # 追加错误
            continue  # 继续
        if tile_id is None:  # 检查 id
            errors.append(f"瓦片 {tile_type} 缺少 id 字段。")  # 追加错误
        atlas_path = (asset_root / atlas).resolve() if not Path(atlas).is_absolute() else Path(atlas)  # 解析路径
        if not atlas_path.exists():  # 检查文件存在
            errors.append(f"瓦片 {tile_type} 引用的图集不存在: {atlas_path}")  # 追加错误
    return errors  # 返回错误列表


def validate_personas(mapping_dir: Path, asset_root: Path) -> list[str]:  # 定义角色头像校验函数
    """校验角色头像映射结构与文件存在性,返回错误消息列表。"""  # 函数 docstring,说明用途

    persona_path = mapping_dir / "personas_binding.json"  # 组合头像映射路径
    if not persona_path.exists():  # 判断文件存在
        return ["缺少 personas_binding.json,需要先执行素材拉取脚本或手动创建映射。"]  # 返回错误
    data = load_json(persona_path)  # 读取 JSON
    errors: list[str] = []  # 初始化错误列表
    for persona, meta in data.items():  # 遍历映射
        if persona.startswith("_"):  # 跳过注释键
            continue  # 跳过
        if not isinstance(meta, dict):  # 检查结构
            errors.append(f"角色 {persona} 的配置不是对象。")  # 追加错误
            continue  # 下一项
        avatar = meta.get("avatar")  # 读取头像路径
        if not avatar:  # 检查路径存在
            errors.append(f"角色 {persona} 缺少 avatar 字段。")  # 追加错误
            continue  # 下一项
        avatar_path = (asset_root / avatar).resolve() if not Path(avatar).is_absolute() else Path(avatar)  # 解析路径
        if not avatar_path.exists():  # 检查文件存在
            errors.append(f"角色 {persona} 的头像文件不存在: {avatar_path}")  # 追加错误
    return errors  # 返回错误列表


def main() -> int:  # 定义主函数
    """执行完整校验流程并返回退出码。"""  # 函数 docstring,说明用途

    args = parse_args()  # 解析命令行参数
    if not args.build_dir.exists():  # 检查素材输出目录是否存在
        print(f"[提示] 素材输出目录 {args.build_dir} 尚未创建,校验将继续但可能出现缺失文件提示。")  # 打印提示
    errors: list[str] = []  # 初始化错误列表
    errors.extend(validate_tilesets(args.mapping_dir, args.asset_root))  # 校验瓦片映射
    errors.extend(validate_personas(args.mapping_dir, args.asset_root))  # 校验头像映射
    if errors:  # 判断是否存在错误
        for message in errors:  # 遍历错误
            print(f"[校验失败] {message}")  # 打印提示
        print("需要先执行 fetch_assets.py 或将素材放入 assets/build/ 对应位置。")  # 打印总结
        return 1  # 返回失败码
    print("素材映射校验通过,所有引用的文件均已就绪。")  # 打印成功消息
    return 0  # 返回成功码


if __name__ == "__main__":  # 判断是否直接执行
    sys.exit(main())  # 调用主函数并退出
