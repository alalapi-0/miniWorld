"""提供命令行方式启动 FastAPI 应用的入口模块。"""  # 模块级 docstring,说明用途

import logging  # 导入 logging 模块,用于输出运行信息

import uvicorn  # 导入 uvicorn,作为 ASGI 服务器

from .config import get_settings  # 导入配置函数,读取运行参数

logger = logging.getLogger(__name__)  # 创建模块级日志记录器,便于调试


def run() -> None:  # 定义运行函数,封装启动逻辑
    """根据配置启动 uvicorn 服务器供本地开发使用。"""  # 函数 docstring,说明用途

    settings = get_settings()  # 获取配置实例,用于读取 host、port 等参数
    logger.info("启动服务:%s:%d", settings.host, settings.port)  # 输出信息日志,标记启动地址
    uvicorn.run(  # 调用 uvicorn.run 启动 ASGI 应用
        "ai_groupchat.app:app",  # 指定应用路径,指向 FastAPI 实例
        host=settings.host,  # 指定监听地址
        port=settings.port,  # 指定监听端口
        reload=settings.debug,  # 根据调试模式决定是否热重载
        log_level="info",  # 设置日志级别为 info
    )  # 结束 uvicorn.run 调用


if __name__ == "__main__":  # 判断模块是否直接运行
    run()  # 直接调用 run 函数启动应用
