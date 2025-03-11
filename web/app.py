from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
import os
import sys
import logging
from datetime import datetime, timedelta
import threading
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controller.main_controller import AIOperationsController

app = Flask(__name__)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("web_app")

# 全局控制器实例
controller = None
controller_thread = None

def start_controller():
    """在后台线程中启动控制器"""
    global controller
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json'))
    controller = AIOperationsController(config_path=config_path)
    controller.start()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    global controller
    
    if controller is None:
        return jsonify({
            "status": "stopped",
            "message": "系统未启动"
        })
    
    return jsonify({
        "status": "running" if controller.running else "stopped",
        "threads": len(controller.threads),
        "data_points": len(controller.metrics_data) if controller.metrics_data else 0,
        "last_update": datetime.now().isoformat()
    })

@app.route('/api/metrics')
def get_metrics():
    """获取最近的指标数据"""
    global controller
    
    if controller is None or not controller.metrics_data:
        return jsonify([])
    
    # 获取最近的数据点数量
    limit = request.args.get('limit', default=100, type=int)
    
    with controller.data_lock:
        recent_data = controller.metrics_data[-limit:]
    
    return jsonify(recent_data)

@app.route('/api/alerts')
def get_alerts():
    """获取最近的告警"""
    global controller
    
    if controller is None or not controller.alert_manager:
        return jsonify([])
    
    # 获取最近的告警数量
    limit = request.args.get('limit', default=50, type=int)
    
    alerts = controller.alert_manager.alert_history[-limit:]
    
    # 转换datetime对象为ISO格式字符串
    for alert in alerts:
        if isinstance(alert.get('timestamp'), datetime):
            alert['timestamp'] = alert['timestamp'].isoformat()
    
    return jsonify(alerts)

@app.route('/api/start', methods=['POST'])
def start_system():
    """启动系统"""
    global controller, controller_thread
    
    if controller is not None and controller.running:
        return jsonify({
            "success": False,
            "message": "系统已经在运行中"
        })
    
    # 在新线程中启动控制器
    controller_thread = threading.Thread(target=start_controller)
    controller_thread.daemon = True
    controller_thread.start()
    
    # 等待控制器启动
    time.sleep(2)
    
    return jsonify({
        "success": True,
        "message": "系统已启动"
    })

@app.route('/api/stop', methods=['POST'])
def stop_system():
    """停止系统"""
    global controller, controller_thread
    
    if controller is None or not controller.running:
        return jsonify({
            "success": False,
            "message": "系统未在运行"
        })
    
    try:
        # 停止控制器
        stop_success = controller.stop()
        
        if not stop_success:
            return jsonify({
                "success": False,
                "message": "系统停止失败，请稍后再试"
            })
        
        # 等待控制器线程结束
        if controller_thread and controller_thread.is_alive():
            logger.info("Waiting for controller thread to terminate...")
            controller_thread.join(timeout=15)  # 增加等待时间
            if controller_thread.is_alive():
                logger.warning("Controller thread did not terminate within timeout")
                return jsonify({
                    "success": False,
                    "message": "系统停止超时，请稍后再试"
                })
        
        # 重置控制器状态
        logger.info("System successfully stopped, resetting controller state")
        # 保留controller引用但标记为已停止，而不是设为None
        # 这样前端仍然可以获取到controller的状态
        # controller = None
        controller_thread = None
        
        return jsonify({
            "success": True,
            "message": "系统已停止"
        })
    except Exception as e:
        logger.error(f"Error stopping system: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"停止系统时发生错误: {str(e)}"
        })

@app.route('/api/forecast')
def get_forecast():
    """获取预测数据"""
    forecast_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'forecast.png'))
    
    if not os.path.exists(forecast_path):
        return jsonify({
            "success": False,
            "message": "预测数据不可用"
        })
    
    # 在实际应用中，应该返回图像文件或预测数据
    # 这里简化为返回文件路径
    return jsonify({
        "success": True,
        "forecast_path": forecast_path,
        "last_update": datetime.fromtimestamp(os.path.getmtime(forecast_path)).isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)