import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import logging

class AnomalyDetector:
    def __init__(self, model_path=None):
        self.model = None
        self.model_path = model_path
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger("anomaly_detector")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("anomaly_detection.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def train(self, data_path, save_model=True):
        """训练异常检测模型"""
        try:
            # 加载数据
            df = pd.read_csv(data_path)
            
            # 选择特征
            features = ['cpu_percent', 'memory_percent', 'disk_usage']
            X = df[features].values
            
            # 训练模型
            self.logger.info("Training anomaly detection model...")
            self.model = IsolationForest(contamination=0.05, random_state=42)
            self.model.fit(X)
            
            if save_model and self.model_path:
                joblib.dump(self.model, self.model_path)
                self.logger.info(f"Model saved to {self.model_path}")
                
            return True
        except Exception as e:
            self.logger.error(f"Error training model: {str(e)}")
            return False
    
    def load_model(self):
        """加载已训练的模型"""
        if self.model_path:
            try:
                # 确保模型目录存在
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                
                if os.path.exists(self.model_path):
                    self.model = joblib.load(self.model_path)
                    self.logger.info(f"Model loaded from {self.model_path}")
                    return True
                else:
                    self.logger.info(f"Model file not found at {self.model_path}, will train a new model")
                    return False
            except Exception as e:
                self.logger.error(f"Error loading model: {str(e)}")
                return False
        return False
    
    def detect_anomalies(self, data):
        """检测异常"""
        if self.model is None:
            self.logger.error("Model not trained or loaded")
            return None
        
        try:
            # 预测
            predictions = self.model.predict(data)
            # -1表示异常，1表示正常
            anomalies = np.where(predictions == -1)[0]
            
            return anomalies
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}")
            return None