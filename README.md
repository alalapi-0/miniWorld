本次骨架由 Codex 根据规范自动生成

# AI 群聊模拟器（后端原型）

## 1. 项目简介
本项目旨在提供一个“AI 角色群聊模拟器”的后端原型，支持多角色在本地环境中围绕用户输入自动生成回复。当前实现仅使用本地的确定性文本生成器，不会访问外部网络或真实的 LLM 服务，方便在离线或安全受限环境中验证业务流程。

## 2. 架构与目录结构
```
.
├─ src/
│  └─ ai_groupchat/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ models.py
│     ├─ main.py
│     ├─ app.py
│     └─ services/
│        ├─ __init__.py
│        └─ generator.py
├─ tests/
│  ├─ __init__.py
│  ├─ test_health.py
│  └─ test_chat.py
├─ .env.example
├─ .gitignore
├─ .editorconfig
├─ LICENSE
├─ Makefile
├─ pyproject.toml
├─ requirements.txt
└─ README.md
```
- `src/ai_groupchat/config.py`：使用 Pydantic Settings 管理环境配置，提供统一的参数入口。
- `src/ai_groupchat/models.py`：定义 FastAPI 输入输出数据模型，保证请求与响应结构清晰。
- `src/ai_groupchat/services/generator.py`：封装角色回复生成逻辑，当前提供可重复的本地实现，可替换为真实 LLM。
- `src/ai_groupchat/app.py`：构建 FastAPI 应用并注册路由，串联配置、模型与服务。
- `src/ai_groupchat/main.py`：提供命令行入口，便于使用 `python -m ai_groupchat.main` 启动服务。
- `tests/`：包含 pytest 单元测试，覆盖健康检查与群聊模拟核心流程。
- `pyproject.toml`、`requirements.txt`、`Makefile` 等文件统一管理依赖、工具与命令。

## 3. 快速开始
1. **前置要求**：已安装 Python 3.11，推荐使用虚拟环境隔离依赖。
2. **创建虚拟环境**：
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # Windows 请使用 .venv\\Scripts\\activate
   ```
3. **安装依赖**：
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **运行服务**：
   ```bash
   make run
   # 或
   uvicorn ai_groupchat.app:app --reload
   ```
5. **运行测试**：
   ```bash
   make test
   ```

## 4. 配置说明
- `.env.example` 提供所有可配置项，复制为 `.env` 后按需修改。
- `APP_NAME`：FastAPI 的标题与日志中展示的服务名。
- `DEBUG`：控制调试模式，影响日志级别与 uvicorn 热重载。
- `HOST`、`PORT`：服务监听地址与端口。
- `DEFAULT_ROLES`：以逗号分隔的角色列表，影响模拟输出角色数量与名称。
- `REPLY_SENTENCES_PER_ROLE`：指导生成器每个角色生成的句子数，当前实现以提示信息形式使用。
- `SEED`：随机种子，确保 `LocalDeterministicGenerator` 输出稳定，便于测试与回归。

## 5. API 文档
### GET /health
- **功能**：检查服务是否运行正常。
- **请求示例**：
  ```bash
  curl http://127.0.0.1:8000/health
  ```
- **响应示例**：
  ```json
  {"status": "ok"}
  ```

### POST /chat/simulate
- **功能**：根据用户输入模拟多个角色的回复。
- **请求体（MessageIn）**：
  ```json
  {"content": "你好，今天的议题是什么？"}
  ```
- **响应体（ChatSimulateResponse）**：
  ```json
  {
    "replies": [
      {"role": "贤者", "text": "贤者微笑回应：让我们针对你好，今天的议题是什么？（预计回复句数 2）制定下一步计划。（参考编号 1825）"},
      {"role": "剑士", "text": "剑士经过深思熟虑后说：你好，今天的议题是什么？（预计回复句数 2）的关键在于团队协作。（参考编号 4507）"}
    ]
  }
  ```
- **字段说明**：
  - `content`：用户提供的主题或问题。
  - `replies`：角色回复数组。
  - `role`：回复者的角色名。
  - `text`：生成的自然语言回复。

## 6. 本地“AI 生成器”说明
- `LocalDeterministicGenerator` 使用 Python `random.Random` 并结合固定模板生成文本。由于种子固定，同一输入会生成可预测的输出，有助于测试和调试。
- 要替换为真实 LLM，可在 `src/ai_groupchat/services/generator.py` 中新增实现，例如 `OpenAIGenerator`，实现 `BaseRoleGenerator` 的 `generate` 方法并在 `build_generator` 函数中根据配置返回不同实例。请通过环境变量传入 API Key，避免在仓库中硬编码，并注意添加超时、重试、异常处理与速率限制。

## 7. 开发规范
- **代码风格**：所有 Python 文件已提供中文注释与 docstring，保持类型标注齐全。
- **格式化与 Lint**：使用 `make format`（black）和 `make lint`（ruff）维持统一风格。
- **测试**：所有新增功能需配套 pytest 用例，遵循 Given-When-Then 或 Arrange-Act-Assert 的结构确保可读性。

## 8. 路线图（Roadmap）
- 集成真实的 LLM 服务提供商（如 OpenAI、Azure OpenAI、通义千问等）。
- 引入角色长期记忆、对话上下文管理与个性化话术配置。
- 提供多轮对话记录、回放与分析能力。
- 与微信小程序或 Web 前端对接，提供完整体验。
- 设计容器化与 Serverless 部署方案，考虑灰度发布与监控告警。

## 9. 常见问题（FAQ）
- **端口占用**：若 8000 端口被占用，可修改 `.env` 中的 `PORT` 或运行时传入 `--port` 参数。
- **虚拟环境问题**：确保激活虚拟环境后再执行 `pip install` 与 `make` 命令，Windows 用户需使用 `Scripts\\activate`。
- **平台差异**：在 Windows 上使用 `make` 可能需要安装 GNU Make，可改用对应的 Python 命令直接运行。

## 10. 许可证
本项目基于 MIT License 发布，详见 [LICENSE](LICENSE)。感谢所有潜在贡献者与使用者。

---

### 如何安全替换为真实 LLM 提供商
在接入真实 LLM 时，请遵循以下实践：
1. **密钥管理**：通过环境变量或专用密钥管理服务（如 Vault、AWS Secrets Manager）注入 API Key，避免明文写入仓库。
2. **超时与重试**：为外部请求设置合理的超时时间与指数回退重试策略，防止服务阻塞。
3. **速率限制**：在本地或网关处实现令牌桶/漏桶限流，避免触发供应商的限速策略。
4. **审计日志**：记录请求参数摘要、响应状态与错误信息，满足合规与问题排查需求，同时注意脱敏处理敏感数据。
