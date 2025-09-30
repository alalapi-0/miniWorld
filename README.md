> ⚠️ 当前项目默认运行在“离线本地生成”模式,外部 LLM 接入仅作为可选增强功能。

# miniWorld —— 六角色协作的像素世界建设后端

## 目录
1. [项目概述](#项目概述)
2. [架构与目录结构](#架构与目录结构)
3. [世界模型设计](#世界模型设计)
4. [角色与权限矩阵](#角色与权限矩阵)
5. [任务系统](#任务系统)
6. [API 文档](#api-文档)
7. [前端协作契约](#前端协作契约)
8. [用户角色生成与操控](#用户角色生成与操控)
9. [素材接入与许可](#素材接入与许可)
10. [外部 LLM 接入说明](#外部-llm-接入说明)
11. [开发规范](#开发规范)
12. [路线图](#路线图)
13. [Changelog](#changelog)

## 项目概述
miniWorld 以“王都近郊重建”为核心背景,提供一个可离线运行的世界建设与角色群聊后端。系统内置六位角色(勇者、剑士、魔导师、神官、盗贼、公主),每位角色拥有独特的人设、权限与目标。服务在本地使用确定性模板生成器响应对话,同时提供区块化的世界地形、结构编辑、树木生长与任务推进等能力,便于像素 RPG 前端或小程序快速接入。

## 架构与目录结构
```
.
├─ assets/
│  ├─ external_catalog.json      # 外部素材目录与许可说明
│  ├─ mapping/                   # 前端渲染映射(JSON)
│  ├─ licenses/                  # 自动生成的许可证汇总
│  ├─ pixel_meta/                # 像素元数据,纯文本描述瓦片规格
│  └─ generators/                # 占位 PNG 生成脚本(默认不执行)
├─ data/
│  ├─ world/chunks/              # 区块 JSON(运行期生成)
│  ├─ world/world_state.json     # 世界状态持久化
│  ├─ world/quests.json          # 任务存档
│  └─ logs/actions.log           # 审计日志
├─ src/miniWorld/
│  ├─ app.py                     # FastAPI 应用与路由
│  ├─ main.py                    # 命令行启动入口
│  ├─ config.py                  # Pydantic Settings,加载人设与权限
│  ├─ models.py                  # 公共 Pydantic 模型
│  ├─ services/
│  │  └─ generator.py            # 本地回复生成器 + 任务生成器
│  └─ world/
│     ├─ __init__.py             # 世界模型汇总导出
│     ├─ actions.py              # 动作请求/响应、权限校验
│     ├─ chunk.py                # 32×32 区块与 TileCell 数据结构
│     ├─ quests.py               # 任务模型与 QuestProgressor
│     ├─ store.py                # JSON 存储、配额冷却与日志
│     ├─ tiles.py                # TileType 枚举与辅助方法
│     └─ world_state.py          # 不可变世界状态模型
├─ scripts/                      # 本地素材拉取与校验脚本
├─ tests/                        # pytest 用例,覆盖世界模型/动作/任务/API
├─ Makefile                      # 常用命令(make check/ make run 等)
├─ pyproject.toml                # 包配置、lint/test 设置
└─ README.md
```

## 世界模型设计
- **区块尺寸**: 固定为 32×32,支持高度、高度装饰、成长阶段字段。
- **瓦片定义**: `TileType` 枚举包含 GRASS、ROAD、WATER、SOIL、WOODFLOOR、HOUSE_BASE、TREE_SAPLING、TREE、FARM、ROCK、SHRUB、MAGIC_SIGIL 等地表/装饰类型。`TileType.is_structure()` 可判断结构基座, `TileType.can_be_decor()` 判断是否可放入装饰槽。
- **TileCell**: 记录 `base` 基础瓦片、`deco` 装饰槽、`height` 高度差、`growth_stage` 树苗成长阶段。
- **Chunk**: 包含 `cx/cy` 坐标、`size`、`grid` 二维数组,提供 `cell_at`/`apply_cell`/`to_summary` 等方法,确保越界安全。
- **世界状态**: `WorldState` 包含 `version`、`year`、`season`、`location`、`major_events`、`seed`,默认值来自 `.env` 或配置文件。`WorldState.describe()` 输出 `年-季-地点-事件` 文本,用于 Prompt 拼装。
- **持久化策略**: `WorldStore` 将区块写入 `data/world/chunks/{cx}_{cy}.json`,世界状态写入 `data/world/world_state.json`,任务存储在 `data/world/quests.json`,配额信息存于 `actor_usage.json`,审计日志追加至 `data/logs/actions.log`。
- **成长逻辑**: `POST /world/tick` 遍历区块,将 `TREE_SAPLING` 根据 `TICK_TREE_GROW_STEPS` 自动成长为 `TREE`,并记录变更。

## 角色与权限矩阵
角色权限通过 `RolePermission` 定义,支持动作白名单、瓦片白名单、冷却时间、每日配额与禁区。默认策略如下:

| 角色 | 允许动作 | 关键白名单 | 冷却/配额 | 备注 |
| --- | --- | --- | --- | --- |
| 勇者 | PLACE_TILE, PLANT_TREE, FARM_TILL | 道路/草地/木地板、草地种树 | 种树每日上限 20 | 负责日常建设与植树 |
| 剑士 | PLACE_TILE, REMOVE_TILE | 道路铺设、移除树木 | 拆除冷却 30s | 维护道路、防御设施 |
| 魔导师 | PLACE_TILE, PLANT_TREE, PLACE_STRUCTURE | 水面/木地板/魔法基座 | - | 可在特殊地形铺设魔导阵 |
| 神官 | PLANT_TREE, FARM_TILL | 圣树种植、翻土 | 翻土每日 50 次 | 负责土地赐福与农田建设 |
| 盗贼 | REMOVE_TILE, PLACE_TILE | 拆除树木/地板、铺设隐匿地板 | 拆除冷却 60s,每日 30 次 | 清除陷阱与布设暗道 |
| 公主 | PLACE_STRUCTURE, PLACE_TILE | 房屋基建、主干道路 | 禁止拆除地基 | 统筹公共设施建设 |

> 若需调整权限,可在 `.env` 中通过 `ROLE_PERMISSIONS_JSON` 指定 JSON 字符串覆盖默认设置。

## 任务系统
- **模型**: `Quest` 包含 `id/title/desc/giver/assignee/status/requirements/rewards/created_at/updated_at`。`ActionRequirement` 描述目标动作、瓦片、区块范围、目标次数与当前进度,支持监控 `base` 或 `deco` 层。
- **持久化**: 任务写入 `data/world/quests.json`,`QuestProgressor` 负责读取/保存,并在动作成功后调用 `on_action_success` 更新进度,完成时自动写入审计日志。
- **生成**: `QuestGenerator.ensure_seed_quests()` 根据世界状态与种子生成默认建设任务(如铺设主干道、种植护城树林、翻耕农田)。若 `quests.json` 已存在任务,则保持现状。
- **推进**: 成功的 `ActionRequest` 会返回变更列表并触发 `QuestProgressor` 增加需求进度。达成目标时任务状态由 `OPEN` → `IN_PROGRESS` → `DONE`,并记录 `payload={"quest_id":...}` 的审计条目。

## API 文档
### GET /health
- 用途: 健康检查。
- 响应: `{ "status": "ok" }`。

### GET /world/state
- 用途: 查看世界时间、地点与事件。
- 响应示例:
  ```json
  {
    "version": "v1",
    "year": 302,
    "season": "春",
    "location": "王都近郊",
    "major_events": ["圣印遗失导致王国动荡", "边境魔导炉持续紊乱"],
    "seed": 42
  }
  ```

### GET /world/chunk?cx=&cy=
- 用途: 返回指定区块 32×32 网格(包含 base/deco/height/growth_stage)。
- 响应: `Chunk` Pydantic 模型序列化结果。

### GET /world/quests
- 用途: 查看当前任务列表与进度。
- 响应: `Quest[]`,其中 `requirements[].progress` 会随动作更新。

### POST /world/action
- 请求体(`ActionRequest`):
  ```json
  {
    "actor": "勇者",
    "type": "PLACE_TILE",
    "chunk": {"cx": 20, "cy": 20},
    "pos": {"x": 0, "y": 0},
    "payload": {"tile": "ROAD"},
    "client_ts": 1000000
  }
  ```
- 执行流程: 权限校验 → 配额/冷却 → 规则验证(水面造屋限制等) → 应用事务 → 持久化 → 追加审计日志 → 更新任务进度。
- 响应(`ActionResponse`):
  ```json
  {
    "success": true,
    "message": "动作执行成功",
    "changes": [
      {
        "chunk": {"cx": 20, "cy": 20},
        "pos": {"x": 0, "y": 0},
        "before": {"base": "GRASS", "deco": null, "height": 0, "growth_stage": null},
        "after": {"base": "ROAD", "deco": null, "height": 0, "growth_stage": null}
      }
    ],
    "code": 0
  }
  ```
- 错误时返回 `ErrorResponse {"code":403/400/404, "msg":"..."}`。

### POST /world/tick
- 用途: 推进世界时间并处理树苗成长。
- 响应示例:
  ```json
  {
    "message": "世界时间推进完成",
    "changes": [
      {
        "chunk": {"cx": 0, "cy": 0},
        "pos": {"x": 3, "y": 8},
        "before": {"base": "GRASS", "deco": "TREE_SAPLING", "height": 0, "growth_stage": 2},
        "after": {"base": "GRASS", "deco": "TREE", "height": 0, "growth_stage": null}
      }
    ]
  }
  ```

### GET /personas
- 用途: 返回角色人设及权限摘要。
- 响应示例:
  ```json
  {
    "personas": [
      {
        "persona": {"name": "勇者", "archetype": "来自异世界的勇者", ...},
        "allowed_actions": ["FARM_TILL", "PLACE_TILE", "PLANT_TREE"],
        "tile_whitelist": {"PLACE_TILE": ["GRASS", "ROAD", "SOIL", "WOODFLOOR"]},
        "cooldown_seconds": {},
        "daily_quota": {"PLANT_TREE": 20}
      }
    ]
  }
  ```

### POST /chat/simulate
- 用途: 根据世界概况与任务摘要生成多角色回复。
- 请求示例:
  ```json
  {"content": "请汇报道路建设", "roles": ["公主", "剑士"]}
  ```
- 响应(`ChatSimulateResponse`): `replies` 数组,每条文本包含地点、季节、任务摘要等提示,便于前端展示“群聊播报”。

## 前端协作契约
- **世界加载**: 前端按需请求 `/world/chunk?cx=&cy=` 获取 32×32 网格,可根据 `version` 实现未来的 ETag 缓存策略。
- **动作执行**: 调用 `/world/action` 后,客户端可根据 `changes` 乐观更新本地场景,如失败则回滚。
- **任务面板**: `/world/quests` 返回的 `progress` 与 `target_count` 可直接驱动进度条,任务完成时会在审计日志与群聊播报中同步提示。
- **群聊播报**: `/chat/simulate` 输出文本已包含 `地点/季节/任务摘要`,前端可直接渲染为群聊气泡或系统公告。

## 用户角色生成与操控

miniWorld 新增了“玩家角色”素材管线,用于快速替换探索者形象并在前端地图中移动。该流程完全离线,默认生成 PNG 占位图,也支持接入外部 AI 生成器。

### 目录结构

```
assets/
  sprites/
    user_character/
      description.txt    # 角色外观的自然语言描述
      front.png           # 正面视角(可手工或 AI 生成)
      side.png            # 侧面视角
      back.png            # 背面视角
      sheet.png           # 本地拼接出的三连帧 spritesheet
frontend/
  explorer.html          # 浏览器端地图+角色控制页面
  explorer.js            # 渲染逻辑、键盘交互与碰撞检测
scripts/
  gen_sprite.py          # 读取描述并生成/拼接占位图
```

### 角色素材生成流程

1. 在 `assets/sprites/user_character/description.txt` 中撰写角色外观描述,例如“细长的列车外形角色,拥有圆形的大嘴巴作为头部……”。
2. 执行 `python scripts/gen_sprite.py`,脚本会:
   - 读取描述文本并打印到终端,预留外部 AI 接口调用位置(默认不发起网络请求)。
   - 若 `front.png`/`side.png`/`back.png` 不存在,自动生成带标签的占位图,方便后续替换。
   - 校验三张图片尺寸一致,然后横向拼接为 `sheet.png`。
3. 脚本仅在本地写出 PNG 文件,不会将二进制素材提交到仓库。替换角色时,直接把新图片放入对应路径并重新执行脚本即可。

### 对接外部 AI 生成器(可选)

`scripts/gen_sprite.py` 中的 `request_ai_images` 函数预留了扩展点。可以在函数内部加入 API 调用逻辑,将生成的临时文件保存至 `front.png` 等路径。例如:

```python
def request_ai_images(description: str) -> dict[str, str]:
    """示例伪代码,展示如何对接外部服务。"""
    payload = {"prompt": description, "views": ["front", "side", "back"]}
    response = client.post("https://api.example.com/sprite", json=payload, timeout=30)
    response.raise_for_status()
    images = response.json()["images"]
    for view, base64_png in images.items():
        (ASSETS_ROOT / f"{view}.png").write_bytes(base64.b64decode(base64_png))
    return images
```

> 提示: 仍需遵守各自 API 的使用条款,并注意不要泄露密钥。仓库保持“零二进制”原则,因此生成后的 PNG 仅在本地保存。

### 地图探索器

- 打开 `frontend/explorer.html`(推荐通过 `python -m http.server` 或任何静态服务托管),页面会自动请求本地运行的 miniWorld 后端 `GET /world/chunk?cx=0&cy=0`。
- 前端以 `tileset_binding.json` 的 `tile_size` 为像素基准渲染地图,缺失图集时退化为纯色瓦片。
- 角色素材来自 `sheet.png` 的三帧,按“正面/侧面/背面”顺序绘制。按下方向键或 WASD:
  - ↑/W 使用背面帧,尝试向上移动一格。
  - ↓/S 使用正面帧,向下移动。
  - ←/A 使用侧面帧,向左移动。
  - →/D 水平翻转侧面帧,向右移动。
- 遇到 `WATER`、`HOUSE_BASE` 等阻挡瓦片时会停止移动;移动过程中简单循环方向帧,松开按键后回到静止帧。

### 常见问题

- **如何替换占位图?** 直接以同尺寸 PNG 覆盖 `front.png` 等文件,再次运行 `python scripts/gen_sprite.py` 即可生成新的 `sheet.png`。
- **没有图形编辑器怎么办?** 可以保留脚本生成的占位图,或使用任意在线像素绘制工具导出 PNG 后覆盖。
- **想换新角色?** 修改 `description.txt` 并替换图片,流程与初次生成一致,前端会自动加载最新的 spritesheet。


## 素材接入与许可
- **为什么仓库不含图片**: miniWorld 遵循“纯文本仓库”原则,任何 PNG/ZIP 等二进制素材都通过 `.gitignore` 排除。外部像素资源使用 `assets/external_catalog.json` 描述来源、许可与放置路径,并由 `scripts/fetch_assets.py` 在本地创建占位或下载,确保审计透明、仓库轻量。
- **许可合规策略**:
  - CC0 素材可在不署名情况下使用,脚本会在 `assets/licenses/ASSETS_LICENSES.md` 中写明“无需署名”。
  - CC-BY/CC-BY-SA 素材需要在发布渠道列出作者、链接与许可条款,脚本会自动生成可复制的署名段落;若选择 `--with-lpc`,还会追加 LPC 专用模板。
  - 发布包含 CC-BY-SA 素材的制品时必须以相同许可共享衍生作品,建议在游戏内“制作人员”或“资源来源”页引用 `ASSETS_LICENSES.md` 中的内容。
- **快速上手流程**:
  1. `make assets` —— 本地仅处理 CC0 源,会在 `assets/build/` 下生成占位文件或下载的 ZIP 解压结果。
  2. 如需包含 LPC 资源,使用 `make assets-cc0-lpc`;脚本会在许可证文档中自动附加署名提示。
  3. `make assets-verify` —— 运行 `scripts/verify_bindings.py`,校验 `assets/mapping/*.json` 引用的文件是否存在。
  4. 启动后端 `uvicorn miniWorld.app:app --reload`,前端可访问以下新接口:
     - `GET /assets/tilesets`
       ```json
       {
         "tile_size": 32,
         "atlas_hint": "assets/build/kenney/tilesheet.png",
         "bindings": {
           "GRASS": {"atlas": "assets/build/kenney/tilesheet.png", "id": 101}
         }
       }
       ```
     - `GET /assets/personas`
       ```json
       {
         "勇者": {"avatar": "assets/build/kenney/portraits/hero_01.png"},
         "剑士": {"avatar": "assets/build/kenney/portraits/knight_01.png"}
       }
       ```
  5. 前端按照映射加载实际 PNG;若文件缺失,可回退到占位色块或文字徽标。
- **失败与降级策略**:
  - `fetch_assets.py --dry-run` 会创建目录与 `.placeholder` 文件计划,并在许可证文档写明“当前未拉取任何素材”。
  - API 在文件缺失时返回 200 与带提示的空结构,日志会记录警告,避免前端崩溃。
  - `assets-verify` 会在素材缺失时返回非零,并输出“需要先执行 fetch 或手动放置素材”等指导语。
- **常见问题 FAQ**:
  - *网络受限怎么办?* —— 使用 `--dry-run` 获取本地目录结构,然后手动将下载好的 PNG 放入 `assets/build/<source>/`。
  - *直链失效或无哈希?* —— `external_catalog.json` 的 `notes` 字段提供手动下载说明;脚本会提示“未提供哈希校验”。
  - *如何仅使用自制素材?* —— 将自制 PNG 放入 `assets/build/custom/`,并更新 `assets/mapping/*.json` 指向新的路径,再执行 `make assets-verify`。
  - *需要在何处展示署名?* —— 游戏内设置“素材来源”页或 README 中引用 `ASSETS_LICENSES.md`,确保 CC-BY/SA 的条款可见。

## 外部 LLM 接入说明
- 默认使用 `PersonaAwareGenerator` 离线模板生成器,不会访问网络。
- 若需启用外部 LLM:
  1. 在 `.env` 中设置 `USE_EXTERNAL_LLM=true` 并提供 `OPENAI_API_KEY`、`LLM_PROVIDER`、`OPENAI_BASE_URL`(可选)。
  2. 建议在生产环境配置调用超时、重试策略、速率限制与审计日志,并对 Prompt 内容进行脱敏处理。
  3. 当前 `ExternalLLMGenerator` 为占位实现,需要根据实际供应商补全 SDK 调用代码。

## 开发规范
- **注释**: 所有 `src/**/*.py` 使用中文逐行注释与完整 docstring,确保世界观信息易于共享。
- **类型与格式**: `ruff` 负责静态检查,`black` 管理格式,`pytest` 覆盖关键逻辑;`make check` 会依次执行三者。
- **数据文件**: 禁止提交 `assets/build/` 等生成物;运行期写入的 JSON/日志保留在 `data/` 下,利于本地调试。
- **测试**: 新增用例覆盖区块持久化、动作权限、任务推进、聊天上下文与 API 冒烟。

## 路线图
- 多玩家协作: 引入身份认证与队伍分组,支持实时协同建设。
- 回放系统: 基于审计日志重建施工时间线,提供可视化时光轴。
- WebSocket 推送: 即时广播世界变更与任务完成状态。
- 权限可视化: 构建 GUI 管理界面,动态调整角色配额、禁区。
- 存档/快照: 定期生成世界快照,支持回滚与分支试验。

## Changelog
- **第四轮: 外部像素素材库接入**: 新增 `assets/external_catalog.json` 管理素材源,提供 `scripts/fetch_assets.py`/`scripts/verify_bindings.py` 本地拉取与校验流程,并开放 `/assets/tilesets`、`/assets/personas` API,确保仓库仍保持纯文本与可审计。
- **角色互动 + 世界建设 + 任务系统**: 引入区块化世界模型、角色权限矩阵、任务生成与推进机制,拓展 `/world/*` 与 `/chat/simulate` 接口以返回建设上下文。当前仍以离线本地生成器为默认实现,外部 LLM 接入保持可选开关。
