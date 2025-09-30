"""提供外部像素素材下载与占位生成功能的脚本。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 启用前向引用,便于类型标注

import argparse  # 导入 argparse,处理命令行参数
import hashlib  # 导入 hashlib,用于计算哈希
import json  # 导入 json,读取目录元数据
import logging  # 导入 logging,输出提示
import shutil  # 导入 shutil,执行文件移动
import sys  # 导入 sys,用于返回值
from pathlib import Path  # 导入 Path,统一文件路径
from tempfile import TemporaryDirectory  # 导入 TemporaryDirectory,存放临时下载文件
from typing import Any, Iterable  # 导入类型提示
from urllib.error import URLError  # 导入 URLError,处理下载异常
from urllib.request import urlopen  # 导入 urlopen,下载文件
import zipfile  # 导入 zipfile,解压压缩包

logger = logging.getLogger(__name__)  # 创建模块级日志记录器

CATALOG_PATH = Path(__file__).resolve().parents[1] / "assets" / "external_catalog.json"  # 定义元数据路径
LICENSE_PATH = Path(__file__).resolve().parents[1] / "assets" / "licenses" / "ASSETS_LICENSES.md"  # 定义许可证输出路径


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:  # 定义参数解析函数
    """解析命令行参数并返回命名空间。"""  # 函数 docstring,说明用途

    parser = argparse.ArgumentParser(description="miniWorld 外部素材拉取脚本")  # 创建参数解析器
    parser.add_argument("--only-cc0", action="store_true", help="仅处理 CC0 许可的素材源")  # 添加 only-cc0 选项
    parser.add_argument("--with-lpc", action="store_true", help="明确允许包含 LPC CC-BY-SA 素材")  # 添加 with-lpc 选项
    parser.add_argument("--dry-run", action="store_true", help="仅打印计划,不写入素材文件")  # 添加 dry-run 选项
    parser.add_argument("--dest", type=Path, default=Path(__file__).resolve().parents[1] / "assets" / "build", help="指定素材输出目录")  # 添加 dest 选项
    parser.add_argument("--allow-network", action="store_true", help="允许脚本尝试联网下载直链资源")  # 添加 allow-network 选项
    args = parser.parse_args(list(argv) if argv is not None else None)  # 解析参数
    return args  # 返回解析结果


def load_catalog(path: Path) -> dict[str, Any]:  # 定义元数据加载函数
    """读取外部素材目录 JSON 并返回字典。"""  # 函数 docstring,说明用途

    with path.open("r", encoding="utf-8") as fp:  # 打开 JSON 文件
        data = json.load(fp)  # 解析为字典
    return data  # 返回数据


def slugify(name: str) -> str:  # 定义名称转目录函数
    """将素材名称转换为小写短横线形式的目录名。"""  # 函数 docstring,说明用途

    safe = [ch.lower() if ch.isalnum() else "-" for ch in name]  # 将非字母数字替换为短横线
    slug = "".join(safe).strip("-")  # 拼接并去除首尾短横线
    return slug or "assets"  # 若结果为空则回退为默认


def ensure_directory(path: Path, dry_run: bool) -> None:  # 定义确保目录存在的函数
    """在非 dry-run 模式下创建目标目录。"""  # 函数 docstring,说明用途

    if dry_run:  # 判断是否 dry-run
        logger.info("dry-run: 预创建目录 %s", path)  # 打印提示
        return  # 直接返回
    path.mkdir(parents=True, exist_ok=True)  # 创建目录


def create_placeholder(path: Path, message: str, dry_run: bool) -> None:  # 定义占位文件创建函数
    """在指定目录写入占位文件以提示手动下载。"""  # 函数 docstring,说明用途

    ensure_directory(path.parent, dry_run)  # 确保目录存在
    placeholder = path.with_suffix(path.suffix + ".placeholder") if path.suffix else path / "MANUAL.placeholder"  # 计算占位文件名
    if dry_run:  # 判断是否 dry-run
        logger.info("dry-run: 将在 %s 写入占位提示: %s", placeholder, message)  # 输出提示
        return  # 返回
    with placeholder.open("w", encoding="utf-8") as fp:  # 打开占位文件
        fp.write(message)  # 写入提示文本


def write_license_report(sources: list[dict[str, Any]], license_path: Path, dry_run: bool, include_lpc: bool) -> None:  # 定义许可证文档生成函数
    """根据已处理的素材源生成许可证汇总文档。"""  # 函数 docstring,说明用途

    lines: list[str] = []  # 初始化行列表
    lines.append("# 外部素材许可证汇总")  # 写入标题
    lines.append("")  # 写入空行
    if dry_run:  # 若为 dry-run 模式
        lines.append("当前未拉取任何素材,以下内容仅供手动下载或正式执行时参考。")  # 写入提示
        lines.append("")  # 添加空行
    if not sources:  # 判断是否有素材
        lines.append("当前未拉取任何素材,请手动下载或执行脚本去除 --dry-run 选项。")  # 写入提示
        lines.append("需要素材时请参考 assets/external_catalog.json 中的 notes 字段。")  # 写入指引
    else:  # 存在素材
        cc0_only = all(src.get("license", "").upper() == "CC0" for src in sources)  # 判断是否全部 CC0
        if cc0_only:  # 若全部 CC0
            lines.append("全部素材均为 CC0 许可,无需额外署名,可自由在项目中使用。")  # 写入说明
        else:  # 存在非 CC0
            lines.append("存在非 CC0 素材,请在产品发行时附带以下署名段落。")  # 写入警告
        lines.append("")  # 插入空行
        for src in sources:  # 遍历素材
            lines.append(f"## {src.get('name', '未命名来源')}")  # 写入小标题
            lines.append("")  # 空行
            lines.append(f"- 许可: {src.get('license', '未知许可')}")  # 写入许可
            lines.append(f"- 官网: {src.get('homepage', '无')}")  # 写入官网
            download = src.get("download")  # 读取下载信息
            lines.append(f"- 下载: {download if download else '需手动下载或参考备注'}")  # 写入下载指引
            notes = src.get("notes")  # 读取备注
            if notes:  # 若存在备注
                lines.append(f"- 备注: {notes}")  # 写入备注
            attribution = src.get("attribution")  # 读取署名要求
            if attribution:  # 若存在署名要求
                lines.append(f"- 署名: {attribution}")  # 写入署名文本
            lines.append("")  # 添加空行
        if include_lpc:  # 若包含 LPC
            lines.append("### LPC 素材署名模板")  # 写入模板标题
            lines.append("")  # 空行
            lines.append("本项目使用了来自 OpenGameArt LPC 系列的素材,请在发布页面附上原作者及链接,并以 CC-BY-SA 3.0 共享衍生作品。")  # 写入模板
    content = "\n".join(lines) + "\n"  # 拼接内容
    if dry_run:  # 判断是否 dry-run
        logger.info("dry-run: 仍会写入许可证文档以便下游校验,内容如下:\n%s", content)  # 输出预览
    license_path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
    with license_path.open("w", encoding="utf-8") as fp:  # 打开文件写入
        fp.write(content)  # 写入内容


def save_binary_to_path(data: bytes, target: Path, dry_run: bool) -> None:  # 定义保存字节流的函数
    """保存下载内容到目标路径,遵循 dry-run 逻辑。"""  # 函数 docstring,说明用途

    ensure_directory(target.parent, dry_run)  # 确保目录存在
    if dry_run:  # 判断是否 dry-run
        logger.info("dry-run: 将在 %s 写入文件(长度 %s)", target, len(data))  # 输出提示
        return  # 返回
    with target.open("wb") as fp:  # 打开目标文件
        fp.write(data)  # 写入字节流


def maybe_download(url: str, allow_network: bool) -> bytes | None:  # 定义下载辅助函数
    """根据 allow-network 决定是否尝试下载指定 URL。"""  # 函数 docstring,说明用途

    if not allow_network:  # 若未允许联网
        logger.warning("未开启 --allow-network,跳过下载 %s", url)  # 输出警告
        return None  # 返回空
    try:  # 尝试下载
        with urlopen(url) as resp:  # 发起请求
            data = resp.read()  # 读取全部内容
        return data  # 返回字节
    except URLError as exc:  # 捕获下载异常
        logger.error("下载失败:%s", exc)  # 输出错误
        return None  # 返回空


def handle_source(source: dict[str, Any], args: argparse.Namespace, processed: list[dict[str, Any]]) -> None:  # 定义素材处理函数
    """根据参数处理单个素材来源,并将成功的源记录在 processed 中。"""  # 函数 docstring,说明用途

    license_name = source.get("license", "").upper()  # 读取许可名称
    if args.only_cc0 and license_name != "CC0":  # 判断 only-cc0
        logger.info("跳过 %s,因非 CC0", source.get("name"))  # 输出提示
        return  # 返回
    if license_name == "CC-BY-SA" and not args.with_lpc:  # 判断 LPC 许可
        logger.info("跳过 %s,需加 --with-lpc 才会处理", source.get("name"))  # 输出提示
        return  # 返回
    dest_root: Path = args.dest  # 读取目标根目录
    slug = slugify(source.get("name", "source"))  # 计算目录名
    dest_dir = dest_root / slug  # 组合目录
    download_url = source.get("download")  # 读取下载链接
    ensure_directory(dest_dir, args.dry_run)  # 确保目录存在
    if download_url and "example.com" in download_url:  # 若链接为示例链接
        logger.info("检测到示例链接 %s,改为生成占位文件", download_url)  # 输出提示
        download_url = None  # 将链接视为无效
    if download_url:  # 若存在可用链接
        data = maybe_download(download_url, args.allow_network)  # 尝试下载
        if data:  # 若成功下载
            with TemporaryDirectory() as tmp_dir_name:  # 创建临时目录
                tmp_dir = Path(tmp_dir_name)  # 转换为 Path
                archive_path = tmp_dir / "archive.bin"  # 定义临时文件
                save_binary_to_path(data, archive_path, args.dry_run)  # 保存文件
                if args.dry_run:  # 若 dry-run
                    logger.info("dry-run: 将检测下载内容是否为 zip")  # 输出提示
                else:  # 非 dry-run
                    if zipfile.is_zipfile(archive_path):  # 判断是否为 zip
                        with zipfile.ZipFile(archive_path) as zf:  # 打开压缩包
                            for member in zf.namelist():  # 遍历文件
                                zf.extract(member, tmp_dir)  # 解压文件
                        for child in tmp_dir.iterdir():  # 遍历解压内容
                            target = dest_dir / child.name  # 计算目标路径
                            if child.is_dir():  # 若为目录
                                if target.exists():  # 若目标存在
                                    shutil.rmtree(target)  # 删除旧目录
                                shutil.move(str(child), target)  # 移动目录
                            else:  # 普通文件
                                shutil.move(str(child), target)  # 直接移动
                    else:  # 非 zip 文件
                        target_file = dest_dir / archive_path.name  # 直接保存
                        shutil.move(str(archive_path), target_file)  # 移动到目标
                    hash_expected = source.get("sha256")  # 读取预期哈希
                    if hash_expected:  # 若提供哈希
                        hash_actual = hashlib.sha256(data).hexdigest()  # 计算实际哈希
                        if hash_actual.lower() != str(hash_expected).lower():  # 比较哈希
                            logger.warning("哈希不匹配: 预期 %s 实得 %s", hash_expected, hash_actual)  # 输出警告
                        else:  # 哈希匹配
                            logger.info("哈希校验通过:%s", hash_actual)  # 输出确认
                    else:  # 没有哈希
                        logger.warning("源 %s 未提供哈希校验,请人工确认文件完整性", source.get("name"))  # 输出警告
            processed.append(source)  # 记录已处理来源
            return  # 返回
        logger.warning("未能下载 %s,将创建占位文件", source.get("name"))  # 下载失败提示
    message = source.get("notes", "请参考 external_catalog.json 中的 notes 手动下载。")  # 读取提示信息
    placeholder_target = dest_dir / "README.txt"  # 设置占位路径
    create_placeholder(placeholder_target, message, args.dry_run)  # 创建占位文件
    processed.append(source)  # 即便是占位也视作已处理,便于许可证记录


def main(argv: Iterable[str] | None = None) -> int:  # 定义主函数
    """执行素材拉取流程,返回退出码。"""  # 函数 docstring,说明用途

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")  # 初始化日志
    args = parse_args(argv)  # 解析参数
    catalog = load_catalog(CATALOG_PATH)  # 加载目录
    sources: list[dict[str, Any]] = catalog.get("sources", [])  # 提取来源列表
    processed: list[dict[str, Any]] = []  # 初始化已处理列表
    for source in sources:  # 遍历来源
        handle_source(source, args, processed)  # 处理素材
    write_license_report(processed, LICENSE_PATH, args.dry_run, args.with_lpc)  # 生成许可证文档
    logger.info("处理完成,共记录 %s 个素材源", len(processed))  # 输出总结
    return 0  # 返回成功码


if __name__ == "__main__":  # 判断脚本是否直接执行
    sys.exit(main())  # 调用主函数并退出
