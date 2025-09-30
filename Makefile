.PHONY: setup lint format test run assets check

# 创建虚拟环境并安装依赖
setup:
	python3.11 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# 运行 ruff 进行静态检查
lint:
	ruff check src tests

# 使用 black 格式化代码
format:
	black src tests

# 运行 pytest 执行单元测试
test:
	pytest

# 启动本地开发服务器
run:
	uvicorn ai_groupchat.app:app --reload

# 本地生成像素占位资源（请勿提交 assets/build/ 内容）
assets:
	@echo "[提示] 本命令将在本地生成占位 PNG 到 assets/build/，请勿提交到仓库"
	python assets/generators/generate_sample_tiles.py
	python assets/generators/generate_sample_sprites.py

# 一键执行静态检查与测试
check:
	ruff check src tests
	black --check src tests
	pytest
