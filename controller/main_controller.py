import os
import sys
import time
import logging
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import threading

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.data_collector import SystemDataCollector
from models.anomaly_detection import AnomalyDetector
from remediation.auto_remediation import RemediationEngine
from analytics.predictive_analytics import PredictiveAnalytics
from alerting.alert_manager import AlertManager

class AIOperationsController:
    def __init__(self, config_path=None):
        self.logger = self._setup_logger()
        self.config = self._load_config(config_path)
        
        # 初始化组件
        self.data_collector = SystemDataCollector(
            collection_interval=self.config.get("collection_interval", 60)
        )
        
        self.anomaly_detector = AnomalyDetector(
            model_path=self.config.get("anomaly_model_path", "models/anomaly_model.pkl")
        )
        
        self.remediation_engine = RemediationEngine()
        
        self.predictive_analytics = PredictiveAnalytics(
            model_path=self.config.get("prediction_model_path", "models/prediction_model.h5")
        )
        
        self.alert_manager = AlertManager(
            config_path=self.config.get("alert_config_path", "config/alerts.json")
        )
        
        # 数据存储
        self.metrics_data = []
        self.metrics_df = None
        self.data_lock = threading.Lock()
        
        # 运行状态
        self.running = False
        self.threads = []
    
    def _setup_logger(self):
        logger = logging.getLogger("ai_ops_controller")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("controller.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def _load_config(self, config_path):
        """加载配置"""
        default_config = {
            "collection_interval": 60,
            "anomaly_detection_interval": 300,
            "prediction_interval": 3600,
            "data_retention_days": 30,
            "anomaly_model_path": "models/anomaly_model.pkl",
            "prediction_model_path": "models/prediction_model.h5",
            "alert_config_path": "config/alerts.json",
            "data_path": "data/metrics.csv",
            "auto_remediation": True,
            "thresholds": {
                "cpu_percent": 90,
                "memory_percent": 85,
                "disk_usage": 90
            }
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # 合并配置
                    for key, value in loaded_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
                    self.logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                self.logger.error(f"Error loading configuration: {str(e)}")
        
        return default_config
    
    def _save_metrics_to_csv(self):
        """保存指标数据到CSV文件"""
        if not self.metrics_data:
            return
        
        data_path = self.config.get("data_path", "data/metrics.csv")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        with self.data_lock:
            df = pd.DataFrame(self.metrics_data)
            df.to_csv(data_path, index=False)
            self.logger.info(f"Metrics data saved to {data_path}")
    
    def _clean_old_data(self):
        """清理旧数据"""
        retention_days = self.config.get("data_retention_days", 30)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with self.data_lock:
            if self.metrics_df is not None and 'timestamp' in self.metrics_df.columns:
                self.metrics_df['timestamp'] = pd.to_datetime(self.metrics_df['timestamp'])
                self.metrics_df = self.metrics_df[self.metrics_df['timestamp'] >= cutoff_date]
                self.logger.info(f"Cleaned data older than {cutoff_date}")
    
    def _check_thresholds(self, metrics):
        """检查指标是否超过阈值"""
        thresholds = self.config.get("thresholds", {})
        alerts = []
        
        for metric, value in metrics.items():
            if metric in thresholds and isinstance(value, (int, float)):
                threshold = thresholds[metric]
                if value >= threshold:
                    alerts.append({
                        "metric": metric,
                        "value": value,
                        "threshold": threshold
                    })
        
        return alerts
    
    def data_collection_thread(self):
        """数据收集线程"""
        self.logger.info("Starting data collection thread")
        
        while self.running:
            try:
                # 收集系统指标
                metrics = self.data_collector.collect_system_metrics()
                
                # 检查阈值
                threshold_alerts = self._check_thresholds(metrics)
                for alert in threshold_alerts:
                    self.alert_manager.trigger_alert(
                        alert_type="threshold_exceeded",
                        resource_id=alert["metric"],
                        severity="warning",
                        message=f"{alert['metric']} 超过阈值: {alert['value']} >= {alert['threshold']}",
                        details=alert
                    )
                
                # 存储指标
                with self.data_lock:
                    self.metrics_data.append(metrics)
                    
                    # 每100条数据保存一次
                    if len(self.metrics_data) % 100 == 0:
                        self._save_metrics_to_csv()
                
                # 休眠
                time.sleep(self.config.get("collection_interval", 60))
            except Exception as e:
                self.logger.error(f"Error in data collection thread: {str(e)}")
                time.sleep(10)  # 出错后短暂休眠
    
    def anomaly_detection_thread(self):
        """异常检测线程"""
        self.logger.info("Starting anomaly detection thread")
        
        # 等待收集足够的数据
        time.sleep(self.config.get("collection_interval", 60) * 5)
        
        while self.running:
            try:
                # 加载或训练模型
                if not self.anomaly_detector.load_model():
                    with self.data_lock:
                        if len(self.metrics_data) > 60:  # 确保有至少1小时的数据（假设每分钟采集一次）
                            # 创建临时CSV用于训练
                            temp_df = pd.DataFrame(self.metrics_data)
                            temp_path = "temp_training_data.csv"
                            temp_df.to_csv(temp_path, index=False)
                            
                            # 训练模型
                            self.anomaly_detector.train(temp_path, save_model=True)
                            
                            # 清理临时文件
                            os.remove(temp_path)
                
                # 检测异常
                with self.data_lock:
                    if len(self.metrics_data) > 10:  # 确保有足够的最近数据
                        recent_data = pd.DataFrame(self.metrics_data[-10:])
                        features = ['cpu_percent', 'memory_percent', 'disk_usage']
                        
                        if all(f in recent_data.columns for f in features):
                            X = recent_data[features].values
                            anomalies = self.anomaly_detector.detect_anomalies(X)
                            
                            if anomalies is not None and len(anomalies) > 0:
                                for idx in anomalies:
                                    anomaly_data = recent_data.iloc[idx].to_dict()
                                    self.logger.warning(f"Anomaly detected: {anomaly_data}")
                                    
                                    # 触发告警
                                    self.alert_manager.trigger_alert(
                                        alert_type="anomaly_detected",
                                        resource_id="system",
                                        severity="critical",
                                        message="系统异常行为检测",
                                        details=anomaly_data
                                    )
                                    
                                    # 自动修复
                                    if self.config.get("auto_remediation", True):
                                        # 根据异常类型执行不同的修复操作
                                        if anomaly_data.get('cpu_percent', 0) > 90:
                                            self.remediation_engine.remediate("high_cpu")
                                        
                                        if anomaly_data.get('memory_percent', 0) > 90:
                                            self.remediation_engine.remediate("memory_leak")
                                        
                                        if anomaly_data.get('disk_usage', 0) > 90:
                                            self.remediation_engine.remediate("disk_full")
                
                # 休眠
                time.sleep(self.config.get("anomaly_detection_interval", 300))
            except Exception as e:
                self.logger.error(f"Error in anomaly detection thread: {str(e)}")
                time.sleep(30)  # 出错后短暂休眠
    
    def prediction_thread(self):
        """预测分析线程"""
        self.logger.info("Starting prediction thread")
        
        # 等待收集足够的数据（1小时）
        time.sleep(self.config.get("collection_interval", 60))
        
        while self.running:
            try:
                # 加载或训练模型
                if not self.predictive_analytics.load_model():
                    with self.data_lock:
                        if len(self.metrics_data) > 60:  # 确保有至少1小时的数据（假设每分钟采集一次）
                            # 创建临时CSV用于训练
                            temp_df = pd.DataFrame(self.metrics_data)
                            temp_path = "temp_prediction_data.csv"
                            temp_df.to_csv(temp_path, index=False)
                            
                            # 训练模型
                            feature_columns = ['cpu_percent', 'memory_percent', 'disk_usage']
                            self.predictive_analytics.train(
                                temp_path, 
                                feature_columns=feature_columns,
                                look_back=24
                            )
                            
                            # 清理临时文件
                            os.remove(temp_path)
                
                # 进行预测
                with self.data_lock:
                    if len(self.metrics_data) > 30:  # 确保有足够的历史数据（至少30分钟）
                        df = pd.DataFrame(self.metrics_data)
                        features = ['cpu_percent', 'memory_percent', 'disk_usage']
                        
                        if all(f in df.columns for f in features):
                            # 获取最近的数据
                            recent_data = df[features].values
                            
                            # 预测未来1小时
                            forecast = self.predictive_analytics.forecast_next_days(
                                recent_data, days=1, look_back=6  # 使用最近6个数据点进行预测
                            )
                            
                            if forecast is not None:
                                # 检查预测结果是否有潜在问题
                                for day, day_forecast in enumerate(forecast):
                                    for i, feature in enumerate(features):
                                        threshold = self.config.get("thresholds", {}).get(feature, 90)
                                        if day_forecast[i] > threshold * 0.9:  # 接近阈值的90%
                                            self.logger.warning(f"Prediction warning: {feature} may reach {day_forecast[i]} in {day+1} days")
                                            
                                            # 触发预测告警
                                            self.alert_manager.trigger_alert(
                                                alert_type="prediction_warning",
                                                resource_id=feature,
                                                severity="warning",
                                                message=f"预测 {day+1} 天后 {feature} 可能达到 {day_forecast[i]:.2f}%",
                                                details={
                                                    "feature": feature,
                                                    "current_value": recent_data[-1][i],
                                                    "predicted_value": float(day_forecast[i]),
                                                    "days_ahead": day + 1,
                                                    "threshold": threshold
                                                }
                                            )
                                
                                # 绘制预测图表
                                self.predictive_analytics.plot_forecast(
                                    recent_data[-30:],  # 最近30天的历史数据
                                    forecast,
                                    feature_index=0,  # CPU使用率
                                    feature_name="CPU Usage (%)"
                                )
                
                # 休眠
                time.sleep(self.config.get("prediction_interval", 3600))
            except Exception as e:
                self.logger.error(f"Error in prediction thread: {str(e)}")
                time.sleep(60)  # 出错后短暂休眠
    
    def start(self):
        """启动AI运维系统"""
        if self.running:
            self.logger.warning("System is already running")
            return
        
        self.running = True
        self.logger.info("Starting AI Operations System")
        
        # 创建并启动线程
        threads = [
            threading.Thread(target=self.data_collection_thread),
            threading.Thread(target=self.anomaly_detection_thread),
            threading.Thread(target=self.prediction_thread)
        ]
        
        for thread in threads:
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
        
        self.logger.info("All threads started")
    
    def stop(self):
        """停止AI运维系统"""
        if not self.running:
            self.logger.warning("System is not running")
            return False
        
        self.logger.info("Stopping AI Operations System")
        self.running = False
        
        # 等待所有线程结束，增加等待时间
        for i, thread in enumerate(self.threads):
            self.logger.info(f"Waiting for thread {i} to terminate...")
            thread.join(timeout=10)  # 增加超时时间
            if thread.is_alive():
                self.logger.warning(f"Thread {i} did not terminate within timeout")
        
        # 清空线程列表
        self.threads = []
        
        # 保存数据
        self._save_metrics_to_csv()
        
        self.logger.info("System stopped")
        return True