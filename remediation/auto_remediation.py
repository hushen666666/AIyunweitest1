import subprocess
import logging
import os
import time

class RemediationEngine:
    def __init__(self):
        self.logger = self._setup_logger()
        self.remediation_actions = {
            "high_cpu": self.handle_high_cpu,
            "memory_leak": self.handle_memory_leak,
            "disk_full": self.handle_disk_full,
            "service_down": self.handle_service_down
        }
        
    def _setup_logger(self):
        logger = logging.getLogger("remediation_engine")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("remediation.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def execute_command(self, command):
        """执行系统命令"""
        try:
            self.logger.info(f"Executing command: {command}")
            result = subprocess.run(command, shell=True, check=True, 
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True)
            self.logger.info(f"Command output: {result.stdout}")
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e.stderr}")
            return False, e.stderr
    
    def handle_high_cpu(self, process_name=None):
        """处理CPU使用率过高的问题"""
        self.logger.info("Handling high CPU usage")
        
        if process_name:
            # 尝试终止特定进程
            success, output = self.execute_command(f"taskkill /F /IM {process_name}")
            if success:
                self.logger.info(f"Successfully terminated process: {process_name}")
            else:
                self.logger.error(f"Failed to terminate process: {process_name}")
        else:
            # 查找CPU使用率最高的进程
            success, output = self.execute_command("powershell \"Get-Process | Sort-Object CPU -Descending | Select-Object -First 5\"")
            self.logger.info(f"Top CPU consuming processes: {output}")
        
        return success
    
    def handle_memory_leak(self, process_name=None):
        """处理内存泄漏问题"""
        self.logger.info("Handling memory leak")
        
        if process_name:
            # 尝试重启特定进程
            success, output = self.execute_command(f"taskkill /F /IM {process_name} && start {process_name}")
            if success:
                self.logger.info(f"Successfully restarted process: {process_name}")
            else:
                self.logger.error(f"Failed to restart process: {process_name}")
        else:
            # 查找内存使用率最高的进程
            success, output = self.execute_command("powershell \"Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 5\"")
            self.logger.info(f"Top memory consuming processes: {output}")
        
        return success
    
    def handle_disk_full(self, path="C:\\"):
        """处理磁盘空间不足问题"""
        self.logger.info(f"Handling disk full issue for path: {path}")
        
        # 清理临时文件
        temp_paths = [
            os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp')),
            "C:\\Windows\\Temp"
        ]
        
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                self.logger.info(f"Cleaning temporary files in {temp_path}")
                success, output = self.execute_command(f"del /q /s /f \"{temp_path}\\*.*\"")
                if success:
                    self.logger.info(f"Successfully cleaned temp files in {temp_path}")
                else:
                    self.logger.warning(f"Failed to clean some temp files in {temp_path}")
        
        # 运行磁盘清理
        success, output = self.execute_command("cleanmgr /sagerun:1")
        
        return success
    
    def handle_service_down(self, service_name):
        """处理服务宕机问题"""
        self.logger.info(f"Handling service down issue for service: {service_name}")
        
        # 检查服务状态
        success, output = self.execute_command(f"sc query {service_name}")
        
        if "RUNNING" not in output:
            # 尝试启动服务
            self.logger.info(f"Service {service_name} is not running, attempting to start")
            success, output = self.execute_command(f"sc start {service_name}")
            if success:
                self.logger.info(f"Successfully started service: {service_name}")
            else:
                self.logger.error(f"Failed to start service: {service_name}")
        else:
            self.logger.info(f"Service {service_name} is already running")
            success = True
        
        return success
    
    def remediate(self, issue_type, **kwargs):
        """执行修复操作"""
        if issue_type in self.remediation_actions:
            self.logger.info(f"Initiating remediation for issue: {issue_type}")
            return self.remediation_actions[issue_type](**kwargs)
        else:
            self.logger.error(f"Unknown issue type: {issue_type}")
            return False