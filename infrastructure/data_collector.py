import time
import psutil
import logging
from datetime import datetime

class SystemDataCollector:
    def __init__(self, collection_interval=60):
        self.collection_interval = collection_interval
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger("system_collector")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("system_metrics.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def collect_system_metrics(self):
        """收集系统基础指标"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict()
        }
        return metrics
    
    def start_collection(self):
        """开始持续收集数据"""
        self.logger.info("Starting system metrics collection")
        try:
            while True:
                metrics = self.collect_system_metrics()
                self.logger.info(f"Collected metrics: {metrics}")
                time.sleep(self.collection_interval)
        except KeyboardInterrupt:
            self.logger.info("Data collection stopped by user")
        except Exception as e:
            self.logger.error(f"Error in data collection: {str(e)}")

if __name__ == "__main__":
    collector = SystemDataCollector()
    collector.start_collection()