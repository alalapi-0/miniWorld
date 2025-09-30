"""定义区块与格子的数据结构,用于描述世界瓦片状态。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用类型

from pydantic import BaseModel, Field, model_validator  # 导入 BaseModel 等工具,用于数据验证

from .tiles import TileType  # 导入 TileType 枚举,描述瓦片类型


class TileCell(BaseModel):  # 定义单个格子的模型
    """表示 32x32 区块中的单个格子数据。"""  # 类 docstring,说明用途

    base: TileType = Field(default=TileType.GRASS, description="地表基础瓦片类型")  # 地表瓦片
    deco: TileType | None = Field(default=None, description="装饰槽瓦片类型")  # 装饰瓦片
    height: int = Field(default=0, ge=-16, le=16, description="格子高度差")  # 高度值
    growth_stage: int | None = Field(  # 定义成长阶段字段
        default=None,  # 默认无成长数据
        description="用于树苗成长的阶段计数",  # 字段描述
        ge=0,  # 最小为 0
        le=10,  # 最大允许 10
    )  # 结束 Field 定义

    class Config:  # 定义内部配置
        """配置项用于序列化时保留枚举值。"""  # Config docstring

        use_enum_values = True  # 序列化时输出枚举值字符串


class Chunk(BaseModel):  # 定义区块模型
    """表示一个固定尺寸的区块,包含 32x32 的瓦片信息。"""  # 类 docstring,说明用途

    cx: int = Field(..., description="区块 X 坐标")  # 区块横向坐标
    cy: int = Field(..., description="区块 Y 坐标")  # 区块纵向坐标
    size: int = Field(default=32, description="区块边长,默认 32")  # 区块边长
    version: str = Field(default="v1", description="区块数据版本号")  # 数据版本
    grid: list[list[TileCell]] = Field(  # 定义网格字段
        default_factory=list,  # 默认提供空列表,稍后填充
        description="区块内的格子二维数组",  # 字段描述
    )  # 结束 Field 定义

    class Config:  # 定义内部配置
        """配置项用于序列化时保留枚举值。"""  # Config docstring

        use_enum_values = True  # 序列化时输出枚举值字符串

    @model_validator(mode="after")  # 使用模型验证器在实例化后检查数据
    def _ensure_grid(self) -> Chunk:  # 定义验证方法
        """确保区块网格尺寸正确,不足时自动填充。"""  # 方法 docstring,说明用途

        if not self.grid:  # 如果尚未提供网格
            self.grid = [  # 创建二维数组
                [TileCell() for _ in range(self.size)]  # 为每一行填充默认格子
                for _ in range(self.size)  # 总共 size 行
            ]  # 结束数组生成
        else:  # 如果已有网格
            if len(self.grid) != self.size:  # 检查行数是否匹配
                raise ValueError("区块行数与尺寸不符")  # 抛出错误
            for row in self.grid:  # 遍历每一行
                if len(row) != self.size:  # 检查列数
                    raise ValueError("区块列数与尺寸不符")  # 抛出错误
        return self  # 返回经过验证的实例

    def cell_at(self, x: int, y: int) -> TileCell:  # 定义获取格子的方法
        """返回指定坐标的格子,坐标从 0 开始。"""  # 方法 docstring,说明用途

        self._validate_coord(x, y)  # 调用内部校验坐标
        return self.grid[y][x]  # 返回对应的 TileCell

    def apply_cell(self, x: int, y: int, cell: TileCell) -> None:  # 定义设置格子的方法
        """将指定坐标更新为新的格子对象。"""  # 方法 docstring,说明用途

        self._validate_coord(x, y)  # 校验坐标
        self.grid[y][x] = cell  # 替换对应格子

    def _validate_coord(self, x: int, y: int) -> None:  # 定义内部坐标校验方法
        """验证坐标是否位于区块范围内。"""  # 方法 docstring,说明用途

        if not 0 <= x < self.size or not 0 <= y < self.size:  # 判断坐标范围
            raise ValueError(f"坐标越界: ({x}, {y}) not in [0,{self.size})")  # 抛出错误

    def to_summary(self) -> dict[str, int]:  # 定义区块统计方法
        """返回区块内基础瓦片的统计信息,用于调试。"""  # 方法 docstring,说明用途

        counts: dict[str, int] = {}  # 初始化计数字典
        for row in self.grid:  # 遍历每一行
            for cell in row:  # 遍历每个格子
                counts[cell.base] = counts.get(cell.base, 0) + 1  # 累加基础瓦片数量
        return counts  # 返回统计结果

    @classmethod
    def create_default(cls, cx: int, cy: int, size: int = 32) -> Chunk:  # 定义默认工厂
        """创建填充草地的默认区块。"""  # 方法 docstring,说明用途

        grid = [  # 构建网格列表
            [TileCell(base=TileType.GRASS, height=0) for _ in range(size)]  # 填充草地
            for _ in range(size)  # 生成 size 行
        ]  # 结束网格构造
        return cls(cx=cx, cy=cy, size=size, grid=grid)  # 返回 Chunk 实例
