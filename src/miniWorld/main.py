"""提供便捷的命令行入口以运行 FastAPI 应用。"""  # 模块 docstring,说明用途

from __future__ import annotations  # 导入未来注解特性,支持前向引用

import uvicorn  # 导入 uvicorn,用于启动 ASGI 服务

from .config import get_settings  # 导入配置获取函数


def run() -> None:  # 定义运行函数
    """使用配置文件中的 HOST 与 PORT 启动应用。"""  # 函数 docstring,说明用途

    settings = get_settings()  # 加载配置
    uvicorn.run(  # 调用 uvicorn 启动服务
        "miniWorld.app:app",  # 指定应用路径
        host=settings.host,  # 使用配置中的主机地址
        port=settings.port,  # 使用配置中的端口
        reload=settings.debug,  # 在调试模式下启用自动重载
    )  # 结束 uvicorn.run 调用


if __name__ == "__main__":  # 检查是否直接运行模块
    run()  # 启动应用
