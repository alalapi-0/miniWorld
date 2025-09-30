"""生成像素 RPG 瓦片占位图的示例脚本。"""  # 模块级 docstring,说明用途

from __future__ import annotations  # 导入未来注解,保持兼容性

from pathlib import Path  # 导入 Path,处理文件路径

from PIL import Image, ImageDraw  # 导入 Pillow 的 Image 与 ImageDraw,用于绘图

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "build" / "tiles"  # 定义输出目录


def generate_placeholder_tiles() -> None:  # 定义函数,生成占位瓦片
    """创建若干 32x32/16 色的 PNG 文件作为占位资源。"""  # 函数 docstring,说明用途

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)  # 确保输出目录存在
    palette = [  # 定义占位调色板
        (34, 177, 76),  # 草地绿色
        (185, 122, 87),  # 土路棕色
        (112, 146, 190),  # 水面蓝色
        (195, 195, 195),  # 石块灰色
        (136, 0, 21),  # 旗帜红色
    ]  # 结束调色板
    names = ["grass", "road", "river", "rock", "banner"]  # 定义瓦片名称顺序
    for index, name in enumerate(names, start=1):  # 遍历要生成的瓦片名称
        image = Image.new("RGB", (32, 32), palette[(index - 1) % len(palette)])  # 创建单色背景
        draw = ImageDraw.Draw(image)  # 创建画笔对象
        draw.rectangle((0, 0, 31, 31), outline=(0, 0, 0))  # 绘制黑色边框
        draw.text((4, 12), name[0].upper(), fill=(255, 255, 255))  # 在中心绘制首字母
        output_path = OUTPUT_DIR / f"tile_{index:03d}_{name}.png"  # 计算输出文件路径
        image.save(output_path)  # 保存 PNG 文件


def main() -> None:  # 定义主函数,提供命令行入口
    """运行脚本并提示开发者不要提交生成产物。"""  # 函数 docstring,说明用途

    print("[提示] 正在本地生成瓦片占位图,请勿将 assets/build/ 提交到仓库。")  # 输出提醒信息
    generate_placeholder_tiles()  # 调用生成函数


if __name__ == "__main__":  # 判断是否直接执行脚本
    main()  # 调用主函数
