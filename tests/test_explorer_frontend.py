"""验证前端探索页面的关键结构。"""

from __future__ import annotations

from pathlib import Path


HTML_FILE = Path("frontend/explorer.html")
JS_FILE = Path("frontend/explorer.js")


def test_explorer_files_exist():
    """HTML/JS 应存在并包含核心标记与函数。"""

    assert HTML_FILE.exists(), "缺少 explorer.html"
    html_text = HTML_FILE.read_text(encoding="utf-8")
    assert "world-canvas" in html_text
    assert "explorer.js" in html_text

    assert JS_FILE.exists(), "缺少 explorer.js"
    js_text = JS_FILE.read_text(encoding="utf-8")
    for snippet in [
        "async function initExplorer",
        "function setupControls",
        "function drawPlayer",
        "/world/chunk",
    ]:
        assert snippet in js_text, f"未找到预期片段: {snippet}"
