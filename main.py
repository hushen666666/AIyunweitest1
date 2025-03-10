import os
import sys
import argparse
import json
import logging
import signal
import time

from controller.main_controller import AIOperationsController

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("ai_ops.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("main")

def signal_handler(sig, frame):
    """处理信号"""
    logger.info("Received shutdown signal")
    if controller:
        controller.stop()
    sys.exit(0)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AI智能运维系统')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--daemon', action='store_true', help='作为守护进程运行')
    return parser.parse_args()

if __name__ == "__main__":
    # 设置日志
    logger = setup_logging()
    logger.info("Starting AI Operations System")
    
    # 解析参数
    args = parse_arguments()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建控制器
    controller = AIOperationsController(config_path=args.config)
    
    try:
        # 启动系统
        controller.start()
        
        # 如果不是守护进程模式，则保持主线程运行
        if not args.daemon:
            logger.info("Press Ctrl+C to stop")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        # 停止系统
        controller.stop()
        logger.info("System shutdown complete")