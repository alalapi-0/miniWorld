"""定义 miniWorld 的瓦片类型枚举与判定工具。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

from enum import Enum  # 导入 Enum,用于定义枚举类型


class TileType(str, Enum):  # 定义 TileType 枚举,继承自 str 与 Enum 便于序列化
    """用于描述世界地表与装饰的瓦片类型枚举。"""  # 类 docstring,说明枚举用途

    GRASS = "GRASS"  # 草地,最常见的地表
    ROAD = "ROAD"  # 石路,用于通行
    WATER = "WATER"  # 水面,不可直接建造
    SOIL = "SOIL"  # 土地,可翻耕
    WOODFLOOR = "WOODFLOOR"  # 木地板,室内或桥梁基础
    HOUSE_BASE = "HOUSE_BASE"  # 房屋地基,承载建筑
    TREE_SAPLING = "TREE_SAPLING"  # 树苗装饰,等待成长
    TREE = "TREE"  # 成树装饰,提供景观
    FARM = "FARM"  # 农田,翻耕后的土地
    ROCK = "ROCK"  # 岩石障碍,需要清除
    SHRUB = "SHRUB"  # 灌木装饰,可被移除
    MAGIC_SIGIL = "MAGIC_SIGIL"  # 魔导法阵,由魔导师铺设

    @classmethod
    def is_structure(cls, tile: TileType) -> bool:  # 定义判断结构瓦片的类方法
        """判断给定瓦片是否为结构基础。"""  # 方法 docstring,说明用途

        return tile in {cls.HOUSE_BASE, cls.MAGIC_SIGIL, cls.WOODFLOOR}  # 返回布尔判断

    @classmethod
    def can_be_decor(cls, tile: TileType) -> bool:  # 定义判断瓦片能否作为装饰的类方法
        """判断给定瓦片是否可以放置在装饰槽。"""  # 方法 docstring,说明用途

        return tile in {cls.TREE_SAPLING, cls.TREE, cls.SHRUB, cls.ROCK}  # 返回布尔判断
