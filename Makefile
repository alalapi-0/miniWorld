.PHONY: setup lint format test run assets assets-cc0-lpc assets-verify check

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
	uvicorn miniWorld.app:app --reload

# 一键仅处理 CC0 来源,本地创建占位或下载素材(不会提交到仓库)
assets:
	# 调用素材拉取脚本,仅处理 CC0 许可
	python scripts/fetch_assets.py --only-cc0

# 包含 CC0 与 LPC 资源,会在许可证文档写入署名提示
assets-cc0-lpc:
	# 调用素材拉取脚本,允许包含 LPC CC-BY-SA 资源
	python scripts/fetch_assets.py --only-cc0 --with-lpc

# 校验映射 JSON 与本地素材文件是否一致
assets-verify:
	# 执行校验脚本,确保映射与文件存在
	python scripts/verify_bindings.py

# 一键执行静态检查与测试
check:
	ruff check src tests
	black --check src tests
	pytest
