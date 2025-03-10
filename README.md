# AI智能运维系统

## 项目概述
本项目是一个基于AI技术的智能运维系统，通过实时监控、异常检测、预测分析和自动修复等功能，帮助运维人员更高效地管理和维护系统。

## 系统架构
系统由以下主要模块组成：

### 1. 数据采集模块 (infrastructure/data_collector.py)
- 负责实时收集系统指标数据，包括CPU使用率、内存使用率、磁盘使用情况和网络IO等
- 数据采集间隔可通过配置文件调整

### 2. 异常检测模块 (models/anomaly_detection.py)
- 使用机器学习模型检测系统异常行为
- 支持模型的自动训练和更新
- 异常检测结果会触发告警和自动修复

### 3. 预测分析模块 (analytics/predictive_analytics.py)
- 基于历史数据预测系统未来的资源使用趋势
- 支持多天的资源使用预测
- 可视化预测结果

### 4. 自动修复模块 (remediation/auto_remediation.py)
- 根据检测到的异常自动执行修复操作
- 支持CPU、内存、磁盘等多种异常的修复策略

### 5. 告警管理模块 (alerting/alert_manager.py)
- 支持多种告警方式：邮件、Webhook、短信等
- 告警规则可配置
- 支持告警抑制机制

### 6. Web界面 (web/)
- 提供友好的可视化界面
- 实时展示系统状态和监控指标
- 支持系统的启动、停止等操作

## 配置说明

### 主配置文件 (config/config.json)
```json
{
    "collection_interval": 60,        // 数据采集间隔（秒）
    "anomaly_detection_interval": 300, // 异常检测间隔（秒）
    "prediction_interval": 3600,       // 预测分析间隔（秒）
    "data_retention_days": 30,        // 数据保留天数
    "auto_remediation": true,         // 是否启用自动修复
    "thresholds": {                   // 指标阈值设置
        "cpu_percent": 90,
        "memory_percent": 85,
        "disk_usage": 90
    }
}
```

### 告警配置文件 (config/alerts.json)
- 配置告警通知方式
- 设置告警规则和阈值
- 配置告警抑制时间

## 使用指南

### 1. 启动系统
```bash
# 使用默认配置启动
python main.py

# 指定配置文件启动
python main.py --config /path/to/config.json

# 以守护进程模式运行
python main.py --daemon
```

### 2. Web界面访问
- 访问 http://localhost:5000 打开管理界面
- 可查看实时监控数据和系统状态
- 支持系统的启动/停止操作

### 3. 日志文件
系统会生成以下日志文件：
- web_app.log: Web应用日志
- controller.log: 控制器日志
- anomaly_detection.log: 异常检测日志
- predictions.log: 预测分析日志
- alerts.log: 告警日志
- system_metrics.log: 系统指标日志

## 主要功能

1. 实时监控
   - 系统资源使用情况实时监控
   - 自定义监控指标阈值
   - 图表化展示监控数据

2. 异常检测
   - 基于机器学习的异常行为检测
   - 自动学习正常行为模式
   - 及时发现系统异常

3. 预测分析
   - 资源使用趋势预测
   - 提前预警潜在问题
   - 可视化预测结果

4. 自动修复
   - 自动响应系统异常
   - 可配置的修复策略
   - 修复操作日志记录

5. 告警通知
   - 多渠道告警通知
   - 可配置的告警规则
   - 告警抑制机制

## 注意事项
1. 首次启动时，系统需要一定时间收集数据并训练模型
2. 建议根据实际情况调整配置文件中的参数
3. 请确保所有依赖模块已正确安装
4. 建议定期检查日志文件了解系统运行状况

## 系统要求
- Python 3.6+
- 足够的系统资源用于数据收集和分析
- 建议在生产环境使用专门的WSGI服务器