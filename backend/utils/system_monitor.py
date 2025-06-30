# 系统状态监控工具
# 用于统一管理系统的健康状态、性能指标和系统信息

import psutil
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging
from backend.db import db
from sqlalchemy import text
from backend.utils import APIResponse, ValidationHelper

logger = logging.getLogger(__name__)

class SystemMonitor:
    """
    系统状态监控类
    提供系统健康状态、性能指标和资源使用情况的监控
    """
    
    def __init__(self):
        """初始化系统监控器"""
        self.start_time = datetime.now()
        self.last_check_time = None
        self.health_status = "healthy"
        self.error_count = 0
        self.warning_count = 0
        
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统基本信息
        
        Returns:
            dict: 系统信息字典
        """
        try:
            return {
                "platform": {
                    "system": os.name,
                    "platform": os.sys.platform,
                    "python_version": os.sys.version,
                    "architecture": os.sys.platform
                },
                "uptime": {
                    "start_time": self.start_time.isoformat(),
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "uptime_formatted": str(datetime.now() - self.start_time).split('.')[0]
                },
                "process": {
                    "pid": os.getpid(),
                    "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                    "cpu_percent": psutil.Process().cpu_percent()
                }
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {str(e)}")
            return {"error": str(e)}
    
    def get_system_resources(self) -> Dict[str, Any]:
        """
        获取系统资源使用情况
        
        Returns:
            dict: 系统资源信息字典
        """
        try:
            # CPU信息
            cpu_info = {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_info = {
                "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                "available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "used_gb": round(memory.used / 1024 / 1024 / 1024, 2),
                "percent": memory.percent,
                "free_gb": round(memory.free / 1024 / 1024 / 1024, 2)
            }
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_info = {
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "percent": round((disk.used / disk.total) * 100, 2)
            }
            
            # 网络信息
            network = psutil.net_io_counters()
            network_info = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            return {
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取系统资源信息失败: {str(e)}")
            return {"error": str(e)}
    
    def check_database_health(self) -> Dict[str, Any]:
        """
        检查数据库健康状态
        
        Returns:
            dict: 数据库健康状态信息
        """
        try:
            start_time = time.time()
            
            # 测试数据库连接
            result = db.session.execute(text("SELECT 1"))
            result.fetchone()
            
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 检查数据库表
            tables_result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in tables_result.fetchall()]
            
            # 检查关键表是否存在
            required_tables = [
                'employee_mappings', 'projects', 'file_records', 
                'chat_messages', 'keyword_categories', 'keywords'
            ]
            missing_tables = [table for table in required_tables if table not in tables]
            
            health_status = "healthy"
            if missing_tables:
                health_status = "warning"
            if response_time > 1000:  # 响应时间超过1秒
                health_status = "warning"
            
            return {
                "status": health_status,
                "response_time_ms": round(response_time, 2),
                "tables_count": len(tables),
                "required_tables": required_tables,
                "missing_tables": missing_tables,
                "connection": "connected",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"数据库健康检查失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "connection": "disconnected",
                "timestamp": datetime.now().isoformat()
            }
    
    def check_application_health(self) -> Dict[str, Any]:
        """
        检查应用程序健康状态
        
        Returns:
            dict: 应用程序健康状态信息
        """
        try:
            # 检查关键模块导入
            modules_status = {}
            try:
                from backend.models import EmployeeMapping, Project, FileRecord, ChatMessage
                modules_status["models"] = "ok"
            except Exception as e:
                modules_status["models"] = f"error: {str(e)}"
            
            try:
                from backend.routes import employees_bp, projects_bp, files_bp
                modules_status["routes"] = "ok"
            except Exception as e:
                modules_status["routes"] = f"error: {str(e)}"
            
            try:
                from utils import APIResponse, ValidationHelper
                modules_status["utils"] = "ok"
            except Exception as e:
                modules_status["utils"] = f"error: {str(e)}"
            
            # 检查配置文件
            try:
                from config import Config
                config_status = "ok"
            except Exception as e:
                config_status = f"error: {str(e)}"
            
            # 确定整体健康状态
            error_modules = [k for k, v in modules_status.items() if v.startswith("error")]
            if error_modules or config_status.startswith("error"):
                health_status = "error"
            elif any("warning" in v for v in modules_status.values()):
                health_status = "warning"
            else:
                health_status = "healthy"
            
            return {
                "status": health_status,
                "modules": modules_status,
                "config": config_status,
                "error_count": self.error_count,
                "warning_count": self.warning_count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"应用程序健康检查失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_comprehensive_health_status(self) -> Dict[str, Any]:
        """
        获取综合健康状态
        
        Returns:
            dict: 综合健康状态信息
        """
        try:
            # 获取各项健康状态
            system_info = self.get_system_info()
            system_resources = self.get_system_resources()
            database_health = self.check_database_health()
            application_health = self.check_application_health()
            
            # 确定整体健康状态
            statuses = [
                database_health.get("status", "unknown"),
                application_health.get("status", "unknown")
            ]
            
            if "error" in statuses:
                overall_status = "error"
            elif "warning" in statuses:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            # 检查系统资源警告
            if system_resources.get("memory", {}).get("percent", 0) > 80:
                overall_status = "warning"
            if system_resources.get("disk", {}).get("percent", 0) > 90:
                overall_status = "warning"
            
            self.health_status = overall_status
            self.last_check_time = datetime.now()
            
            return {
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "system": system_info,
                "resources": system_resources,
                "database": database_health,
                "application": application_health,
                "summary": {
                    "uptime": system_info.get("uptime", {}).get("uptime_formatted", "unknown"),
                    "memory_usage_percent": system_resources.get("memory", {}).get("percent", 0),
                    "disk_usage_percent": system_resources.get("disk", {}).get("percent", 0),
                    "database_response_time": database_health.get("response_time_ms", 0),
                    "error_count": self.error_count,
                    "warning_count": self.warning_count
                }
            }
        except Exception as e:
            logger.error(f"获取综合健康状态失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            dict: 性能指标信息
        """
        try:
            # 获取系统资源
            resources = self.get_system_resources()
            
            # 计算性能评分（0-100）
            cpu_score = max(0, 100 - resources.get("cpu", {}).get("cpu_percent", 0))
            memory_score = max(0, 100 - resources.get("memory", {}).get("percent", 0))
            disk_score = max(0, 100 - resources.get("disk", {}).get("percent", 0))
            
            # 综合评分
            overall_score = round((cpu_score + memory_score + disk_score) / 3, 2)
            
            # 性能等级
            if overall_score >= 90:
                performance_level = "excellent"
            elif overall_score >= 70:
                performance_level = "good"
            elif overall_score >= 50:
                performance_level = "fair"
            else:
                performance_level = "poor"
            
            return {
                "overall_score": overall_score,
                "performance_level": performance_level,
                "cpu_score": cpu_score,
                "memory_score": memory_score,
                "disk_score": disk_score,
                "metrics": {
                    "cpu_usage": resources.get("cpu", {}).get("cpu_percent", 0),
                    "memory_usage": resources.get("memory", {}).get("percent", 0),
                    "disk_usage": resources.get("disk", {}).get("percent", 0),
                    "available_memory_gb": resources.get("memory", {}).get("available_gb", 0),
                    "free_disk_gb": resources.get("disk", {}).get("free_gb", 0)
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取性能指标失败: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def log_health_check(self, health_data: Dict[str, Any]):
        """
        记录健康检查日志
        
        Args:
            health_data: 健康检查数据
        """
        try:
            status = health_data.get("status", "unknown")
            timestamp = health_data.get("timestamp", datetime.now().isoformat())
            
            if status == "error":
                self.error_count += 1
                logger.error(f"健康检查发现错误: {health_data}")
            elif status == "warning":
                self.warning_count += 1
                logger.warning(f"健康检查发现警告: {health_data}")
            else:
                logger.info(f"健康检查正常: {status}")
                
        except Exception as e:
            logger.error(f"记录健康检查日志失败: {str(e)}")

# 全局系统监控实例
system_monitor = SystemMonitor() 