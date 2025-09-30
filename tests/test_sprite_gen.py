"""验证 gen_sprite.py 能在自定义目录内生成占位素材并拼接 spritesheet。"""

from __future__ import annotations

import subprocess
import sys

from PIL import Image


def test_gen_sprite_creates_sheet(tmp_path, monkeypatch):
    """运行脚本后应生成 front/side/back 以及 sheet.png,并保证尺寸一致。"""

    user_dir = tmp_path / "user_character"
    user_dir.mkdir()
    (user_dir / "description.txt").write_text("测试角色描述", encoding="utf-8")

    monkeypatch.setenv("USER_CHARACTER_ROOT", str(user_dir))

    subprocess.run([sys.executable, "scripts/gen_sprite.py"], check=True)

    front = Image.open(user_dir / "front.png")
    side = Image.open(user_dir / "side.png")
    back = Image.open(user_dir / "back.png")
    sheet = Image.open(user_dir / "sheet.png")

    assert front.size == side.size == back.size
    expected_sheet_size = (front.width * 3, front.height)
    assert sheet.size == expected_sheet_size
