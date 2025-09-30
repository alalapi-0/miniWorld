"""生成用户角色三面图的工具脚本。"""

from __future__ import annotations  # 启用未来注解行为，兼容较旧解释器

import os  # 导入 os 模块，用于读取环境变量
from pathlib import Path  # 导入 Path 类，便于处理文件路径
from typing import Iterable, Tuple  # 导入类型注解，增强可读性

from PIL import Image, ImageDraw, ImageFont  # 引入 Pillow 库的核心组件

# 读取环境变量，允许在测试或自定义环境中重定向素材目录
CUSTOM_ROOT = os.environ.get("USER_CHARACTER_ROOT")  # 读取自定义根路径
if CUSTOM_ROOT:  # 如果用户指定了目录
    ASSETS_ROOT = Path(CUSTOM_ROOT).resolve()  # 直接使用该目录
else:  # 否则使用仓库默认路径
    ASSETS_ROOT = (
        Path(__file__).resolve().parents[1]  # 仓库根目录
        / "assets"
        / "sprites"
        / "user_character"
    )  # 完整的素材目录
DESCRIPTION_FILE = ASSETS_ROOT / "description.txt"  # 角色描述文件路径
FRONT_IMAGE = ASSETS_ROOT / "front.png"  # 正面图片路径
SIDE_IMAGE = ASSETS_ROOT / "side.png"  # 侧面图片路径
BACK_IMAGE = ASSETS_ROOT / "back.png"  # 背面图片路径
SHEET_IMAGE = ASSETS_ROOT / "sheet.png"  # 拼接输出路径


def read_description() -> str:
    """读取自然语言描述文本。"""  # 说明函数用途

    if not DESCRIPTION_FILE.exists():  # 若描述文件缺失
        raise FileNotFoundError("缺少 description.txt，请先编写角色描述。")  # 抛出明确异常
    return DESCRIPTION_FILE.read_text(encoding="utf-8").strip()  # 返回去除首尾空白的描述


def request_ai_images(description: str) -> dict[str, str]:
    """预留的 AI 生成接口，默认返回空结果。"""  # 提示该函数占位

    print("[提示] 未配置外部 AI 接口，将生成占位图。")  # 输出提示信息
    return {}  # 返回空字典，表示未生成外部资源


def ensure_placeholder(image_path: Path, label: str, size: Tuple[int, int]) -> None:
    """生成带有标签文字的占位图，便于手动替换。"""  # 说明函数目的

    if image_path.exists():  # 如果文件已存在
        return  # 不再重复生成

    image = Image.new("RGBA", size, (200, 200, 200, 255))  # 创建灰色底图
    draw = ImageDraw.Draw(image)  # 构建绘图对象
    text = f"{label}\nplaceholder"  # 准备显示的标签文字

    try:  # 尝试加载系统字体
        font = ImageFont.truetype("DejaVuSans.ttf", 14)  # 使用常见字体渲染文字
    except OSError:  # 若字体不可用
        font = ImageFont.load_default()  # 回退到默认字体

    text_bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")  # 计算文字包围盒
    text_width = text_bbox[2] - text_bbox[0]  # 计算文字宽度
    text_height = text_bbox[3] - text_bbox[1]  # 计算文字高度
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)  # 求出居中位置
    draw.multiline_text(position, text, fill=(30, 30, 30), font=font, align="center")  # 在图片中绘制文字
    image.save(image_path)  # 保存占位图
    print(f"[生成] {image_path.name} 占位图已创建。")  # 打印生成结果


def load_image(image_path: Path) -> Image.Image:
    """载入图像并确保为 RGBA 模式。"""  # 函数说明

    image = Image.open(image_path)  # 打开目标图像
    if image.mode != "RGBA":  # 如果模式不是 RGBA
        image = image.convert("RGBA")  # 转换为带透明通道
    return image  # 返回处理后的图像对象


def stitch_images(images: Iterable[Image.Image]) -> Image.Image:
    """将多张同尺寸图像横向拼接为一张。"""  # 函数说明

    image_list = list(images)  # 将迭代器转为列表
    if not image_list:  # 若列表为空
        raise ValueError("没有可拼接的图像。")  # 抛出异常提醒

    widths = {img.width for img in image_list}  # 收集宽度集合
    heights = {img.height for img in image_list}  # 收集高度集合
    if len(widths) != 1 or len(heights) != 1:  # 检查尺寸是否一致
        raise ValueError("所有图像必须尺寸一致，请先调整 front/side/back。")  # 抛出错误提示

    width = next(iter(widths))  # 取出统一宽度
    height = next(iter(heights))  # 取出统一高度
    sheet = Image.new("RGBA", (width * len(image_list), height))  # 创建目标拼接画布

    for index, image in enumerate(image_list):  # 枚举每张图片
        sheet.paste(image, (width * index, 0))  # 根据顺序贴到画布上

    return sheet  # 返回拼接结果


def main() -> None:
    """执行角色素材生成流程。"""  # 函数说明

    description = read_description()  # 读取角色描述
    print("[信息] 当前角色描述:\n" + description)  # 输出描述内容

    _ = request_ai_images(description)  # 调用占位的 AI 接口，当前结果未使用

    placeholder_size = (128, 128)  # 约定默认占位图尺寸
    ensure_placeholder(FRONT_IMAGE, "front", placeholder_size)  # 确保正面占位图存在
    ensure_placeholder(SIDE_IMAGE, "side", placeholder_size)  # 确保侧面占位图存在
    ensure_placeholder(BACK_IMAGE, "back", placeholder_size)  # 确保背面占位图存在

    front = load_image(FRONT_IMAGE)  # 载入正面图像
    side = load_image(SIDE_IMAGE)  # 载入侧面图像
    back = load_image(BACK_IMAGE)  # 载入背面图像

    sheet = stitch_images([front, side, back])  # 拼接三视图
    sheet.save(SHEET_IMAGE)  # 保存为 spritesheet
    print(f"[完成] 已生成 {SHEET_IMAGE}。")  # 输出完成提示


if __name__ == "__main__":  # 当脚本直接执行时
    main()  # 调用主流程
