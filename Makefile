.PHONY: setup lint format test run

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
