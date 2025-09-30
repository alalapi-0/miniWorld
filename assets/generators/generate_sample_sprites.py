"""生成六位角色像素头像的占位图脚本。"""  # 模块级 docstring,说明用途

from __future__ import annotations  # 导入未来注解,保持兼容性

from pathlib import Path  # 导入 Path,处理文件路径

from PIL import Image, ImageDraw  # 导入 Pillow,用于绘制头像

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "build" / "sprites"  # 定义输出目录
CHARACTER_NAMES = ["勇者", "剑士", "魔导师", "神官", "盗贼", "公主"]  # 定义角色名称列表


def generate_placeholder_sprites() -> None:  # 定义函数,生成占位头像
    """创建 48x48 像素头像,标注角色首字和阵营色。"""  # 函数 docstring,说明用途

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)  # 确保输出目录存在
    palette = [  # 定义六种代表色
        (255, 163, 67),  # 勇者橙色
        (120, 193, 255),  # 剑士蓝色
        (180, 167, 214),  # 魔导师紫色
        (255, 229, 153),  # 神官金色
        (163, 73, 164),  # 盗贼深紫
        (255, 174, 201),  # 公主粉色
    ]  # 结束调色板
    for index, name in enumerate(CHARACTER_NAMES):  # 遍历角色列表
        image = Image.new("RGB", (48, 48), palette[index])  # 创建背景
        draw = ImageDraw.Draw(image)  # 创建画笔
        draw.ellipse((4, 4, 44, 44), outline=(0, 0, 0), width=2)  # 绘制外圈
        draw.text((16, 18), name[0], fill=(0, 0, 0))  # 绘制角色首字
        output_path = OUTPUT_DIR / f"persona_{index+1:02d}_{name}.png"  # 计算输出路径
        image.save(output_path)  # 保存 PNG 文件


def main() -> None:  # 定义主函数,提示使用方式
    """运行脚本并提醒开发者不要提交生成产物。"""  # 函数 docstring,说明用途

    print("[提示] 正在本地生成角色头像占位图,请勿将 assets/build/ 提交到仓库。")  # 输出提醒
    generate_placeholder_sprites()  # 调用生成函数


if __name__ == "__main__":  # 判断是否直接执行脚本
    main()  # 调用主函数
