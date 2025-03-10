import logging
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class AlertManager:
    def __init__(self, config_path=None):
        self.logger = self._setup_logger()
        self.config = self._load_config(config_path)
        self.alert_history = []
        
    def _setup_logger(self):
        logger = logging.getLogger("alert_manager")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("alerts.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def _load_config(self, config_path):
        """加载告警配置"""
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "username": "alerts@example.com",
                "password": "password",
                "from_address": "alerts@example.com",
                "recipients": ["admin@example.com"]
            },
            "webhook": {
                "enabled": False,
                "url": "https://hooks.slack.com/services/xxx/yyy/zzz",
                "headers": {"Content-Type": "application/json"}
            },
            "sms": {
                "enabled": False,
                "api_key": "your_api_key",
                "api_url": "https://api.sms-service.com/send",
                "from_number": "+1234567890",
                "to_numbers": ["+0987654321"]
            },
            "thresholds": {
                "cpu_percent": 90,
                "memory_percent": 85,
                "disk_usage": 90
            },
            "alert_cooldown_minutes": 15
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
    
    def _should_send_alert(self, alert_type, resource_id):
        """检查是否应该发送告警（避免告警风暴）"""
        now = datetime.now()
        cooldown_minutes = self.config.get("alert_cooldown_minutes", 15)
        
        # 检查历史告警
        for alert in self.alert_history:
            if (alert["type"] == alert_type and 
                alert["resource_id"] == resource_id and 
                (now - alert["timestamp"]).total_seconds() < cooldown_minutes * 60):
                return False
        
        return True
    
    def send_email_alert(self, subject, message):
        """发送邮件告警"""
        if not self.config["email"]["enabled"]:
            self.logger.info("Email alerts are disabled")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config["email"]["from_address"]
            msg['To'] = ", ".join(self.config["email"]["recipients"])
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.config["email"]["smtp_server"], self.config["email"]["smtp_port"])
            server.starttls()
            server.login(self.config["email"]["username"], self.config["email"]["password"])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent: {subject}")
            return True
        except Exception as e:
            self.logger.error(f"Error sending email alert: {str(e)}")
            return False
    
    def send_webhook_alert(self, payload):
        """发送Webhook告警"""
        if not self.config["webhook"]["enabled"]:
            self.logger.info("Webhook alerts are disabled")
            return False
        
        try:
            response = requests.post(
                self.config["webhook"]["url"],
                headers=self.config["webhook"]["headers"],
                data=json.dumps(payload)
            )
            
            if response.status_code < 300:
                self.logger.info(f"Webhook alert sent, status code: {response.status_code}")
                return True
            else:
                self.logger.error(f"Webhook alert failed, status code: {response.status_code}, response: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {str(e)}")
            return False
    
    def send_sms_alert(self, message):
        """发送短信告警"""
        if not self.config["sms"]["enabled"]:
            self.logger.info("SMS alerts are disabled")
            return False
        
        try:
            for to_number in self.config["sms"]["to_numbers"]:
                payload = {
                    "api_key": self.config["sms"]["api_key"],
                    "from": self.config["sms"]["from_number"],
                    "to": to_number,
                    "message": message
                }
                
                response = requests.post(
                    self.config["sms"]["api_url"],
                    json=payload
                )
                
                if response.status_code < 300:
                    self.logger.info(f"SMS alert sent to {to_number}")
                else:
                    self.logger.error(f"SMS alert to {to_number} failed, status: {response.status_code}, response: {response.text}")
            
            return True
        except Exception as e:
            self.logger.error(f"Error sending SMS alert: {str(e)}")
            return False
    
    def trigger_alert(self, alert_type, resource_id, severity, message, details=None):
        """触发告警"""
        if not self._should_send_alert(alert_type, resource_id):
            self.logger.info(f"Alert for {alert_type} on {resource_id} suppressed (cooldown period)")
            return False
        
        now = datetime.now()
        alert_record = {
            "type": alert_type,
            "resource_id": resource_id,
            "severity": severity,
            "message": message,
            "details": details,
            "timestamp": now
        }
        
        # 记录告警
        self.alert_history.append(alert_record)
        
        # 根据严重性构建告警标题
        severity_prefix = {
            "critical": "[严重]",
            "warning": "[警告]",
            "info": "[信息]"
        }.get(severity.lower(), "[通知]")
        
        subject = f"{severity_prefix} {message}"
        
        # 构建详细信息
        detail_text = ""
        if details:
            detail_text = "\n\n详细信息:\n" + json.dumps(details, indent=2, ensure_ascii=False)
        
        full_message = f"""
告警类型: {alert_type}
资源ID: {resource_id}
严重性: {severity}
时间: {now.strftime('%Y-%m-%d %H:%M:%S')}
消息: {message}{detail_text}
        """
        
        # 发送各种告警
        email_sent = self.send_email_alert(subject, full_message)
        
        webhook_payload = {
            "text": subject,
            "attachments": [
                {
                    "title": f"告警详情 - {alert_type}",
                    "text": full_message,
                    "color": {"critical": "danger", "warning": "warning", "info": "good"}.get(severity.lower(), "#439FE0")
                }
            ]
        }
        webhook_sent = self.send_webhook_alert(webhook_payload)
        
        # 短信只发送简短信息
        sms_message = f"{severity_prefix} {message} - {resource_id}"
        sms_sent = self.send_sms_alert(sms_message)
        
        self.logger.info(f"Alert triggered: {subject} (Email: {email_sent}, Webhook: {webhook_sent}, SMS: {sms_sent})")
        
        return True