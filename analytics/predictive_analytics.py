import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import logging
import os

class PredictiveAnalytics:
    def __init__(self, model_path=None):
        self.model = None
        self.model_path = model_path
        self.scaler = MinMaxScaler()
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger("predictive_analytics")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("predictions.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def prepare_data(self, data, look_back=24):
        """准备时序数据"""
        X, y = [], []
        for i in range(len(data) - look_back):
            X.append(data[i:(i + look_back), :])
            y.append(data[i + look_back, :])
        return np.array(X).reshape(len(X), -1), np.array(y)
    
    def train(self, data_path, feature_columns, target_column=None, look_back=24):
        """训练预测模型"""
        try:
            # 加载数据
            df = pd.read_csv(data_path)
            
            # 如果没有指定目标列，使用与特征相同的列进行预测
            if target_column is None:
                target_column = feature_columns[0]
                
            # 准备特征和目标
            features = df[feature_columns].values
            
            # 标准化数据
            scaled_features = self.scaler.fit_transform(features)
            
            # 准备时序数据
            X, y = self.prepare_data(scaled_features, look_back)
            
            # 构建随机森林模型
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X, y)
            
            # 保存模型和scaler
            if self.model_path:
                import joblib
                model_dir = os.path.dirname(self.model_path)
                scaler_path = os.path.join(model_dir, 'scaler.pkl')
                joblib.dump(self.model, self.model_path)
                joblib.dump(self.scaler, scaler_path)
                self.logger.info(f"Model saved to {self.model_path}")
                self.logger.info(f"Scaler saved to {scaler_path}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error training model: {str(e)}")
            return False
    
    def load_model(self):
        """加载已训练的模型和scaler"""
        if self.model_path and os.path.exists(self.model_path):
            try:
                import joblib
                model_dir = os.path.dirname(self.model_path)
                scaler_path = os.path.join(model_dir, 'scaler.pkl')
                
                if os.path.exists(scaler_path):
                    self.scaler = joblib.load(scaler_path)
                    self.logger.info(f"Scaler loaded from {scaler_path}")
                else:
                    self.logger.error("Scaler file not found. Please train the model first.")
                    return False
                
                self.model = joblib.load(self.model_path)
                self.logger.info(f"Model loaded from {self.model_path}")
                return True
            except Exception as e:
                self.logger.error(f"Error loading model: {str(e)}")
                return False
        return False
    
    def predict(self, data, look_back=24):
        """预测未来值"""
        if self.model is None:
            self.logger.error("Model not trained or loaded")
            return None
        
        try:
            # 标准化数据
            scaled_data = self.scaler.transform(data)
            
            # 准备预测数据
            X_pred = scaled_data[-look_back:].reshape(1, -1)
            
            # 预测
            prediction_scaled = self.model.predict(X_pred)
            
            # 反向转换预测结果
            prediction = self.scaler.inverse_transform(prediction_scaled.reshape(1, -1))
            
            return prediction[0]
        except Exception as e:
            self.logger.error(f"Error making prediction: {str(e)}")
            return None
    
    def forecast_next_days(self, data, days=7, look_back=24):
        """预测未来多天的值"""
        if self.model is None:
            self.logger.error("Model not trained or loaded")
            return None
        
        try:
            # 复制最后的look_back天数据用于预测
            last_sequence = data[-look_back:].copy()
            forecasts = []
            
            for _ in range(days):
                # 预测下一天
                next_day = self.predict(last_sequence, look_back)
                if next_day is None:
                    break
                forecasts.append(next_day)
                
                # 更新序列，移除最早的一天，添加预测的一天
                last_sequence = np.vstack([last_sequence[1:], next_day])
            
            return np.array(forecasts)
        except Exception as e:
            self.logger.error(f"Error forecasting: {str(e)}")
            return None
    
    def plot_forecast(self, historical_data, forecast_data, feature_index=0, feature_name="Value"):
        """绘制历史数据和预测数据"""
        try:
            plt.figure(figsize=(12, 6))
            
            # 绘制历史数据
            plt.plot(range(len(historical_data)), 
                     historical_data[:, feature_index], 
                     label='Historical Data', color='blue')
            
            # 绘制预测数据
            plt.plot(range(len(historical_data)-1, len(historical_data) + len(forecast_data)), 
                     np.vstack([historical_data[-1:, feature_index], forecast_data[:, feature_index]]), 
                     label='Forecast', color='red', linestyle='--')
            
            plt.title(f'{feature_name} Forecast')
            plt.xlabel('Time')
            plt.ylabel(feature_name)
            plt.legend()
            plt.grid(True)
            
            forecast_path = 'forecast.png'
            plt.savefig(forecast_path)
            plt.close()
            self.logger.info(f"Forecast plot saved to {forecast_path}")
            
            return forecast_path
        except Exception as e:
            self.logger.error(f"Error plotting forecast: {str(e)}")
            return None