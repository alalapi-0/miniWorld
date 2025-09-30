> ⚠️ 当前项目默认运行在“离线本地生成”模式，外部 LLM 接入仅作为可选增强功能。

# AI 群聊模拟器（后端原型）

## 1. 项目简介
本项目提供一个围绕“王道异世界像素 RPG”世界观构建的多角色群聊模拟后端。默认使用纯本地的确定性生成器，结合世界时间轴与角色人设，在离线或安全受限环境中也能稳定复现对话流程。若需连接真实的 LLM 服务，可通过配置开关在后续阶段接入，但默认保持断网与本地模式以便开发调试。

## 2. 架构与目录结构
```
.
├─ assets/
│  ├─ pixel_meta/                # 世界地图、城镇、角色与 UI 的像素规格元数据
│  └─ generators/                # 占位 PNG 生成脚本（默认不执行，不提交产物）
├─ src/
│  └─ ai_groupchat/
│     ├─ __init__.py
│     ├─ app.py                  # FastAPI 应用与接口
│     ├─ config.py               # 环境配置（含世界状态与人设）
│     ├─ models.py               # Pydantic 数据模型
│     ├─ main.py                 # 命令行启动入口
│     └─ services/
│        ├─ __init__.py
│        └─ generator.py         # 本地/人设感知/预留外部 LLM 生成器
├─ tests/                        # pytest 覆盖所有接口
├─ Makefile                      # 常用命令（含 make assets / make check）
├─ requirements.txt              # 运行与脚本依赖（含 Pillow）
└─ README.md
```

## 3. 世界观与时间轴
- 默认世界状态 `WorldState` 包含年份（1024 年）、季节（春季）、地点（格兰王都）与关键事件（圣印遗失、魔导回路紊乱）。
- 可在 `.env` 中通过 `WORLD_YEAR`、`WORLD_SEASON`、`DEFAULT_LOCATION` 覆盖上述设定；在开发环境可调用 `POST /world/state` 动态调整。
- 世界事件会被嵌入 Prompt：生成器会自动拼接 `年份/季节/地点/重大事件`，让角色回复紧贴时间线变化。
- 示例：
  ```text
  地点：隐匿峡谷｜季节：春｜年份：1024｜事件：王都圣印遗失引发王国震动、边境魔导回路出现紊乱
  ```
  该文本会与用户消息组合后传入生成器，产出符合异世界背景的回复。

## 4. 六角色人设一览
| 名称 | Archetype | 说话风格 | 知识标签 | 道德阵营 | 目标 |
| --- | --- | --- | --- | --- | --- |
| 勇者 | 勇者/外来者 | 直白乐观、略带现代梗、尊重同伴 | 现代常识；基础魔物图鉴 | 守序善良 | 找回失落的圣印，守护新伙伴 |
| 剑士 | 王都禁卫/骑士 | 简练、重承诺、常以军语行文 | 王国律法；军事礼仪 | 守序中立 | 维持秩序，护送队伍穿越边境 |
| 魔导师 | 高塔学者/元素研究者 | 术语密集、好引用典籍、理性克制 | 元素学；古代魔法史 | 中立善良 | 修复湮灭的魔导回路，验证理论 |
| 神官 | 巡礼者/教会使徒 | 温柔劝勉、偶有经文比喻 | 神学仪式；医疗药理 | 守序善良 | 追寻“光明遗器”，治疗瘟潮 |
| 盗贼 | 城底斥候/情报客 | 俏皮挖苦、擅用暗号、避免正面承诺 | 黑市流通；陷阱与机关 | 混乱中立 | 替老友赎罪，追查幕后商会 |
| 公主 | 流亡王女/谈判者 | 礼貌端庄、善外交辞令、偶露真情 | 封疆史；礼仪与条约 | 中立善良 | 重建同盟，避免战端再起 |

如需自定义角色，可在 `.env` 中配置 `PERSONAS_JSON`（JSON 数组），其字段需与上表保持一致。

## 5. 像素资源与美术规范
- `assets/pixel_meta/**.meta.json` 保存像素规格元数据，包含瓦片尺寸、色板标签、索引语义等；这些文件只含文本，便于版本管理。
- `assets/generators/*.py` 使用 Pillow 程序化生成占位 PNG（32x32 瓦片、48x48 头像），默认不执行。
- 运行 `make assets` 可在本地生成资源到 `assets/build/`，**请勿将该目录提交到仓库**。
- 调色板遵循 16 色 Game Boy Color 风格，瓦片命名使用三位数索引（如 `001 grass`、`100 roof`）。

## 6. 配置说明
- `.env.example` 列出了所有配置项。
- 关键环境变量：
  - `APP_NAME`、`HOST`、`PORT`、`DEBUG`：FastAPI 基本设置。
  - `WORLD_YEAR`、`WORLD_SEASON`、`DEFAULT_LOCATION`：覆盖默认世界状态。
  - `PERSONAS_JSON`：以 JSON 字符串覆盖默认六人设。
  - `REPLY_SENTENCES_PER_ROLE`、`SEED`：控制本地生成器行为。
  - `USE_EXTERNAL_LLM`、`LLM_PROVIDER`、`OPENAI_API_KEY`、`OPENAI_BASE_URL`：预留给未来接入外部 LLM。

## 7. 生成管线与 Prompt 拼装策略
- `LocalDeterministicGenerator`：基础模板生成器，用于产出稳定的段落。
- `PersonaAwareGenerator`：在本地模板基础上嵌入 `WorldState` 与 `Persona` 信息，输出形如：
  ```text
  1024 年春季，格兰王都。近期事件：王都圣印遗失引发王国震动、边境魔导回路出现紊乱。勇者以勇者/外来者的身份，目标是找回失落的圣印，口吻应直白乐观、略带现代梗、尊重同伴，熟悉领域：现代常识、基础魔物图鉴。回复：勇者整理装备后回应：...
  ```
- Prompt 拼装模板：
  ```text
  {用户输入}｜地点：{location}｜季节：{season}｜年份：{year}｜事件：{events}｜角色风格：{speaking_style}｜目标：{goal}｜建议句数：{N}
  ```
- `ExternalLLMGenerator`：占位实现，仅定义方法与安全说明，默认抛出未实现异常，提醒保持离线模式。

## 8. API 文档
### GET /health
- **用途**：健康检查。
- **响应**：`{"status": "ok"}`。

### GET /world/state
- **用途**：查看当前世界状态。
- **响应示例**：
  ```json
  {
    "year": 1024,
    "season": "春",
    "major_events": ["王都圣印遗失引发王国震动", "边境魔导回路出现紊乱"],
    "location": "格兰王都"
  }
  ```

### POST /world/state
- **用途**：在调试模式下更新世界状态，生产环境会返回 403。
- **请求体**：`WorldState` JSON。
- **响应**：返回更新后的 `WorldState`。

### GET /personas
- **用途**：获取六位默认角色的人设元数据，用于前端展示头像/名牌。
- **响应**：`Persona` 数组。

### GET /pixel/meta
- **用途**：汇总 `assets/pixel_meta/**.meta.json` 内容，前端可用来构建瓦片与 UI。
- **响应**：
  ```json
  {
    "files": {
      "tilesets/overworld_tileset.meta.json": {"tile_size": 32, ...},
      "sprites/personas.meta.json": {"sprite_spec": {...}},
      "sprites/ui.meta.json": {...},
      "tilesets/town_tileset.meta.json": {...}
    }
  }
  ```

### POST /chat/simulate
- **用途**：基于世界状态与选定角色生成群聊回复。
- **请求体（MessageIn）**：
  ```json
  {
    "content": "请汇报前线情报",
    "roles": ["勇者", "盗贼"],
    "location": "隐匿峡谷"
  }
  ```
- **响应体（ChatSimulateResponse）**：`replies` 数组，每位角色会根据 `Persona` 与 `WorldState` 生成 `REPLY_SENTENCES_PER_ROLE` 条语义的文本段落。

## 9. 快速开始
1. **创建虚拟环境**：
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```
2. **安装依赖**：
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **运行服务**：
   ```bash
   make run
   # 或
   uvicorn ai_groupchat.app:app --reload
   ```
4. **运行测试与检查**：
   ```bash
   make check
   ```
5. **（可选）生成像素占位图**：
   ```bash
   make assets
   # 产物位于 assets/build/，请勿提交
   ```

## 10. 开发规范
- Python 代码使用中文逐行注释与完整 docstring，便于团队沟通设定。
- 统一使用 `ruff` 与 `black` 维护代码风格，`pytest` 覆盖所有接口。
- `make check` 会依次执行 `ruff`、`black --check` 与 `pytest`。

## 11. 从本地到真·API 的迁移路径
1. 将 `.env` 中的 `USE_EXTERNAL_LLM` 设为 `true`，配置 `LLM_PROVIDER`、`OPENAI_API_KEY`、`OPENAI_BASE_URL`（如需代理）。
2. 在 `ExternalLLMGenerator` 中实现实际的 API 调用：需增加超时、指数退避重试、速率限制与错误日志，并确保脱敏处理。
3. 将调用与响应写入审计日志，遵守公司安全策略；密钥必须通过环境变量或安全密钥管理服务注入。
4. 在切换到生产时，保持 `POST /world/state` 禁用（`DEBUG=false`），并监控外部 API 的速率与费用。

## 12. 路线图（Roadmap）
- 接入真实 LLM（OpenAI、Azure OpenAI、通义千问等），完善 `ExternalLLMGenerator`。
- 引入角色长期记忆、对话上下文管理与个性化话术配置。
- 记录多轮对话日志，支持回放与分析。
- 与 Web/小程序前端集成，展示像素场景与角色头像。
- 设计容器化与 Serverless 部署方案，完善监控与告警。

## 13. 常见问题（FAQ）
- **端口占用**：若 8000 端口被占用，可修改 `.env` 中的 `PORT`。
- **虚拟环境问题**：确保激活虚拟环境后再执行 `pip install` 与 `make`。
- **像素资源缺失**：仓库不包含二进制图片，可使用 `make assets` 在本地生成占位图。
- **角色/世界设定扩展**：通过 `PERSONAS_JSON` 和 `POST /world/state` 快速调整设定，便于迭代剧情。

## 14. 许可证
项目基于 MIT License 发布，详见 [LICENSE](LICENSE)。

## 15. 变更日志 / Changelog
- 2024-08-30：引入王道异世界世界观、六位默认人设、PersonaAwareGenerator、世界状态接口、像素元数据与占位图脚本，README 同步说明并新增 make assets / make check。
