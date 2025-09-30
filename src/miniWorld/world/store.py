"""实现基于 JSON 文件的世界状态与区块存储。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

import json  # 导入 json 模块,用于读写数据
from collections.abc import Iterable  # 导入 Iterable,用于返回区块迭代器
from pathlib import Path  # 导入 Path,处理文件路径
from threading import Lock  # 导入 Lock,实现简单文件锁

from .chunk import Chunk  # 导入区块模型
from .world_state import WorldState  # 导入世界状态模型


class UsageLimitError(Exception):  # 定义用量限制异常
    """在配额或冷却校验失败时抛出的异常。"""  # 类 docstring,说明用途

    def __init__(self, message: str, code: int = 429) -> None:  # 定义构造函数
        """保存错误信息与错误码。"""  # 方法 docstring,说明用途

        super().__init__(message)  # 调用父类构造
        self.code = code  # 保存错误码
        self.message = message  # 保存错误消息


class WorldStore:  # 定义世界存储类
    """负责持久化区块、世界状态、任务与使用记录。"""  # 类 docstring,说明用途

    def __init__(  # 定义构造函数
        self,  # 传入实例自身
        root: Path,  # 数据根目录
        chunk_size: int,  # 区块边长
        default_world_state: WorldState,  # 默认世界状态
        tick_tree_grow_steps: int,  # 树苗成长所需步数
    ) -> None:  # 构造函数返回 None
        """初始化目录结构并创建缓存容器。"""  # 方法 docstring,说明用途

        self._root = root  # 保存根目录
        self._chunk_size = chunk_size  # 保存区块尺寸
        self._default_world_state = default_world_state  # 保存默认世界状态
        self._tick_tree_grow_steps = tick_tree_grow_steps  # 保存成长步数
        self._chunk_dir = self._root / "world" / "chunks"  # 构建区块目录路径
        self._world_state_path = self._root / "world" / "world_state.json"  # 世界状态文件
        self._quests_path = self._root / "world" / "quests.json"  # 任务文件
        self._usage_path = self._root / "world" / "actor_usage.json"  # 用量记录文件
        self._log_path = self._root / "logs" / "actions.log"  # 审计日志文件
        self._chunk_dir.mkdir(parents=True, exist_ok=True)  # 确保区块目录存在
        self._log_path.parent.mkdir(parents=True, exist_ok=True)  # 确保日志目录存在
        self._world_cache: dict[tuple[int, int], Chunk] = {}  # 初始化区块缓存
        self._world_state_cache: WorldState | None = None  # 初始化世界状态缓存
        self._quests_cache: list[dict] | None = None  # 初始化任务缓存(字典形式)
        self._usage_cache: dict | None = None  # 初始化用量缓存
        self._lock = Lock()  # 创建互斥锁

    @property
    def chunk_size(self) -> int:  # 定义区块尺寸属性
        """返回区块边长。"""  # 属性 docstring,说明用途

        return self._chunk_size  # 返回区块尺寸

    @property
    def tick_tree_grow_steps(self) -> int:  # 定义树成长步数属性
        """返回树苗成长所需的 tick 数。"""  # 属性 docstring,说明用途

        return self._tick_tree_grow_steps  # 返回成长步数

    def load_world_state(self) -> WorldState:  # 定义加载世界状态方法
        """读取 world_state.json,若不存在则写入默认值。"""  # 方法 docstring,说明用途

        if self._world_state_cache is not None:  # 若缓存存在
            return self._world_state_cache  # 直接返回缓存
        if not self._world_state_path.exists():  # 若文件不存在
            self.save_world_state(self._default_world_state)  # 写入默认世界状态
            self._world_state_cache = self._default_world_state  # 缓存默认值
            return self._default_world_state  # 返回默认值
        with self._world_state_path.open("r", encoding="utf-8") as handle:  # 打开文件
            data = json.load(handle)  # 读取 JSON 数据
        self._world_state_cache = WorldState.model_validate(data)  # 验证并缓存
        return self._world_state_cache  # 返回缓存

    def save_world_state(self, world_state: WorldState) -> None:  # 定义保存世界状态方法
        """将世界状态写入磁盘并更新缓存。"""  # 方法 docstring,说明用途

        self._world_state_path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        with self._world_state_path.open("w", encoding="utf-8") as handle:  # 打开文件以写入
            json.dump(world_state.model_dump(), handle, ensure_ascii=False, indent=2)  # 写入 JSON
        self._world_state_cache = world_state  # 更新缓存

    def load_chunk(self, cx: int, cy: int) -> Chunk:  # 定义加载区块方法
        """读取指定区块,若不存在则创建默认区块。"""  # 方法 docstring,说明用途

        key = (cx, cy)  # 构建缓存键
        if key in self._world_cache:  # 如果缓存中存在
            return self._world_cache[key]  # 返回缓存
        path = self._chunk_dir / f"{cx}_{cy}.json"  # 构建文件路径
        if not path.exists():  # 若文件不存在
            chunk = Chunk.create_default(cx=cx, cy=cy, size=self._chunk_size)  # 创建默认区块
            self._world_cache[key] = chunk  # 缓存默认区块
            return chunk  # 返回默认区块
        with path.open("r", encoding="utf-8") as handle:  # 打开文件读取
            data = json.load(handle)  # 解析 JSON
        chunk = Chunk.model_validate(data)  # 验证并构建区块
        self._world_cache[key] = chunk  # 缓存区块
        return chunk  # 返回区块

    def save_chunk(self, chunk: Chunk) -> None:  # 定义保存区块方法
        """将区块数据写回磁盘。"""  # 方法 docstring,说明用途

        path = self._chunk_dir / f"{chunk.cx}_{chunk.cy}.json"  # 构建文件路径
        with path.open("w", encoding="utf-8") as handle:  # 打开文件写入
            json.dump(  # 写入 JSON
                chunk.model_dump(mode="json"),  # 序列化区块
                handle,  # 目标文件句柄
                ensure_ascii=False,  # 保留中文
                indent=2,  # 设置缩进
            )  # 结束 json.dump
        self._world_cache[(chunk.cx, chunk.cy)] = chunk  # 更新缓存

    def iter_chunks(self) -> Iterable[Chunk]:  # 定义遍历区块方法
        """遍历所有已存在的区块。"""  # 方法 docstring,说明用途

        for path in sorted(self._chunk_dir.glob("*.json")):  # 遍历所有区块文件
            cx, cy = map(int, path.stem.split("_", maxsplit=1))  # 解析坐标
            yield self.load_chunk(cx, cy)  # 逐个返回区块

    def load_quests_raw(self) -> list[dict]:  # 定义加载任务原始数据的方法
        """以字典形式读取任务列表,供 Quest 模型解析。"""  # 方法 docstring,说明用途

        if self._quests_cache is not None:  # 如果缓存存在
            return self._quests_cache  # 返回缓存
        if not self._quests_path.exists():  # 若任务文件不存在
            self.save_quests_raw([])  # 写入空列表
            self._quests_cache = []  # 缓存空列表
            return []  # 返回空列表
        with self._quests_path.open("r", encoding="utf-8") as handle:  # 打开文件读取
            data = json.load(handle)  # 解析 JSON
        if not isinstance(data, list):  # 校验数据类型
            raise ValueError("quests.json 必须是列表")  # 抛出错误
        self._quests_cache = data  # 缓存数据
        return data  # 返回数据

    def save_quests_raw(self, quests: list[dict]) -> None:  # 定义保存任务原始数据的方法
        """将任务列表写入磁盘。"""  # 方法 docstring,说明用途

        self._quests_path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        with self._quests_path.open("w", encoding="utf-8") as handle:  # 打开文件写入
            json.dump(quests, handle, ensure_ascii=False, indent=2)  # 写入 JSON
        self._quests_cache = quests  # 更新缓存

    def ensure_usage(  # 定义用量与冷却校验方法
        self,
        actor: str,  # 执行者
        action_type: str,  # 动作类型
        client_ts: int,  # 时间戳(毫秒)
        quota: int | None,  # 每日配额
        cooldown: int | None,  # 冷却秒数
    ) -> None:  # 方法返回 None
        """校验并记录角色动作的配额与冷却状态。"""  # 方法 docstring,说明用途

        usage = self._load_usage()  # 加载用量数据
        actor_usage = usage.setdefault(actor, {})  # 获取或创建角色记录
        record = actor_usage.setdefault(  # 获取或创建动作记录
            action_type,  # 动作类型
            {"count": 0, "day": None, "last_ts": None},  # 默认数据结构
        )  # 结束默认值
        current_day = client_ts // 86_400_000  # 计算当前日期编号
        if record["day"] != current_day:  # 若跨天
            record["day"] = current_day  # 重置日期
            record["count"] = 0  # 重置计数
        if quota is not None and record["count"] >= quota:  # 检查配额
            raise UsageLimitError("已达到今日配额", code=429)  # 抛出异常
        if cooldown is not None and record["last_ts"] is not None:  # 检查冷却
            elapsed = (client_ts - record["last_ts"]) / 1000  # 计算已过秒数
            if elapsed < cooldown:  # 若未达到冷却时间
                raise UsageLimitError("动作处于冷却中", code=429)  # 抛出异常
        record["count"] += 1  # 增加计数
        record["last_ts"] = client_ts  # 更新最后执行时间
        self._save_usage(usage)  # 保存用量数据

    def _load_usage(self) -> dict:  # 定义加载用量数据的内部方法
        """从磁盘读取 actor_usage.json。"""  # 方法 docstring,说明用途

        if self._usage_cache is not None:  # 若缓存存在
            return self._usage_cache  # 返回缓存
        if not self._usage_path.exists():  # 若文件不存在
            self._usage_cache = {}  # 初始化空字典
            return self._usage_cache  # 返回空字典
        with self._usage_path.open("r", encoding="utf-8") as handle:  # 打开文件
            data = json.load(handle)  # 解析 JSON
        if not isinstance(data, dict):  # 校验类型
            raise ValueError("actor_usage.json 必须是字典")  # 抛出错误
        self._usage_cache = data  # 缓存数据
        return data  # 返回数据

    def _save_usage(self, usage: dict) -> None:  # 定义保存用量数据的内部方法
        """将用量数据写入磁盘并更新缓存。"""  # 方法 docstring,说明用途

        self._usage_path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        with self._usage_path.open("w", encoding="utf-8") as handle:  # 打开文件写入
            json.dump(usage, handle, ensure_ascii=False, indent=2)  # 写入 JSON
        self._usage_cache = usage  # 更新缓存

    def append_action_log(  # 定义追加审计日志的方法
        self,
        actor: str,  # 执行者
        action_type: str,  # 动作类型
        chunk: dict,  # 区块信息
        pos: dict,  # 坐标信息
        payload: dict,  # 附加参数
    ) -> None:  # 方法返回 None
        """向 actions.log 追加一行文本记录。"""  # 方法 docstring,说明用途

        line = json.dumps(  # 构建日志行
            {
                "actor": actor,  # 记录执行者
                "action": action_type,  # 记录动作类型
                "chunk": chunk,  # 记录区块
                "pos": pos,  # 记录坐标
                "payload": payload,  # 记录附加参数
            },
            ensure_ascii=False,  # 保留中文
        )  # 结束 json.dumps
        with (
            self._lock,
            self._log_path.open(  # 使用互斥锁并打开文件
                "a",
                encoding="utf-8",
            ) as handle,
        ):
            handle.write(line + "\n")  # 写入日志行

    def reset_usage(self) -> None:  # 定义测试辅助方法,重置用量
        """清空配额记录,主要用于单元测试。"""  # 方法 docstring,说明用途

        self._usage_cache = {}  # 清空缓存
        if self._usage_path.exists():  # 如果文件存在
            self._usage_path.unlink()  # 删除文件
