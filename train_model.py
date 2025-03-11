import os
os.makedirs('models', exist_ok=True)

from analytics.predictive_analytics import PredictiveAnalytics

def train_model():
    analytics = PredictiveAnalytics(model_path='models/prediction_model.h5')
    feature_columns = ['cpu_percent', 'memory_percent', 'disk_usage']
    success = analytics.train('data/metrics.csv', feature_columns=feature_columns, look_back=6)
    
    if success:
        print('模型训练成功并已保存')
    else:
        print('模型训练失败')

if __name__ == '__main__':
    train_model()