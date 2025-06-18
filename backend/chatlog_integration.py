# chatlog_integration.py
# 这个文件负责与 chatlog 工具的 HTTP API 进行交互
# 主要功能包括：获取群聊列表、查询聊天记录、获取联系人信息等
# 严格按照 chatlog 官方接口规范实现

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import quote

# 配置日志
logger = logging.getLogger(__name__)

# chatlog HTTP 服务的基础地址
# 默认运行在本地 5030 端口，支持环境变量配置
import os
CHATLOG_API_BASE = os.getenv('CHATLOG_API_URL', "http://127.0.0.1:5030")

class ChatlogIntegration:
    """
    chatlog 工具集成类
    负责与 chatlog 的 HTTP API 进行交互，获取微信群聊数据
    严格按照官方接口规范实现
    """
    
    def __init__(self, api_base: str = CHATLOG_API_BASE):
        """
        初始化 chatlog 集成
        
        参数:
            api_base: chatlog HTTP 服务的基础地址
        """
        self.api_base = api_base.rstrip('/')  # 移除末尾斜杠
        self.session = requests.Session()
        # 设置请求超时时间（秒）
        self.session.timeout = 30
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'ChatBoom-Integration/1.0',
            'Accept': 'application/json'
        })
    
    def check_service_status(self) -> Dict[str, Any]:
        """
        检查 chatlog 服务是否正常运行
        
        返回:
            包含服务状态信息的字典
        """
        try:
            # 尝试访问群聊列表接口来检查服务状态
            response = self.session.get(f"{self.api_base}/api/v1/chatroom")
            if response.status_code == 200:
                return {
                    "status": "running",
                    "message": "chatlog 服务正常运行",
                    "timestamp": datetime.now().isoformat(),
                    "api_base": self.api_base
                }
            else:
                return {
                    "status": "error",
                    "message": f"chatlog 服务响应异常，状态码: {response.status_code}",
                    "timestamp": datetime.now().isoformat(),
                    "api_base": self.api_base
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": f"无法连接到 chatlog 服务 {self.api_base}，请确保服务已启动",
                "timestamp": datetime.now().isoformat(),
                "api_base": self.api_base
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "连接 chatlog 服务超时",
                "timestamp": datetime.now().isoformat(),
                "api_base": self.api_base
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查服务状态时发生错误: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "api_base": self.api_base
            }
    
    def get_chatrooms(self) -> List[Dict[str, Any]]:
        """
        获取所有微信群聊列表
        
        返回:
            群聊信息列表，每个群聊包含 id、name 等信息
        """
        try:
            response = self.session.get(f"{self.api_base}/api/v1/chatroom")
            if response.status_code == 200:
                chatrooms = response.json()
                logger.info(f"成功获取 {len(chatrooms)} 个群聊")
                return chatrooms
            else:
                logger.error(f"获取群聊列表失败，状态码: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取群聊列表时发生错误: {str(e)}")
            return []
    
    def get_contacts(self) -> List[Dict[str, Any]]:
        """
        获取所有联系人列表
        
        返回:
            联系人信息列表
        """
        try:
            response = self.session.get(f"{self.api_base}/api/v1/contact")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取联系人列表失败，状态码: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取联系人列表时发生错误: {str(e)}")
            return []
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """
        获取最近会话列表
        
        返回:
            会话信息列表
        """
        try:
            response = self.session.get(f"{self.api_base}/api/v1/session")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取会话列表失败，状态码: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取会话列表时发生错误: {str(e)}")
            return []
    
    def get_chatlog(self, 
                   talker: Optional[str] = None,
                   time_range: Optional[str] = None,
                   limit: int = 100,
                   offset: int = 0,
                   format_type: str = "json") -> List[Dict[str, Any]]:
        """
        获取聊天记录 - 严格按照官方接口规范
        
        参数:
            talker: 聊天对象标识（支持 wxid、群聊 ID、备注名、昵称等）
            time_range: 时间范围，格式为 YYYY-MM-DD 或 YYYY-MM-DD~YYYY-MM-DD
            limit: 返回记录数量限制
            offset: 分页偏移量
            format_type: 输出格式，支持 json、csv 或纯文本
        
        返回:
            聊天记录列表
        """
        try:
            # 构建查询参数 - 严格按照官方规范
            params = {
                "limit": limit,
                "offset": offset,
                "format": format_type
            }
            
            if talker:
                params["talker"] = talker
            
            if time_range:
                params["time"] = time_range
            
            # 构建完整的 URL
            url = f"{self.api_base}/api/v1/chatlog"
            logger.info(f"请求聊天记录: {url}，参数: {params}")
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                if format_type == "json":
                    data = response.json()
                    logger.info(f"成功获取聊天记录，数量: {len(data)}")
                    return data
                else:
                    # 对于非 JSON 格式，返回文本内容
                    return [{"content": response.text}]
            else:
                logger.error(f"获取聊天记录失败，状态码: {response.status_code}，响应: {response.text}")
                return []
        except Exception as e:
            logger.error(f"获取聊天记录时发生错误: {str(e)}")
            return []
    
    def get_chatlog_by_talker_and_time(self, 
                                     talker: str, 
                                     start_date: str, 
                                     end_date: str,
                                     format_type: str = "json") -> List[Dict[str, Any]]:
        """
        根据群聊名称和时间范围获取聊天记录
        这是最常用的接口，严格按照官方规范实现
        
        参数:
            talker: 群聊名称（如：越城天地&巨象微信工作群）
            start_date: 起始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            format_type: 输出格式，默认 json
        
        返回:
            聊天记录列表
        """
        try:
            # 构建时间范围参数，格式：YYYY-MM-DD~YYYY-MM-DD
            time_range = f"{start_date}~{end_date}"
            
            # 构建查询参数
            params = {
                "time": time_range,
                "talker": talker,
                "format": format_type
            }
            
            # 构建完整的 URL
            url = f"{self.api_base}/api/v1/chatlog"
            logger.info(f"请求聊天记录: {url}，群聊: {talker}，时间范围: {time_range}")
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                if format_type == "json":
                    data = response.json()
                    logger.info(f"成功获取群聊 {talker} 的聊天记录，数量: {len(data)}")
                    return data
                else:
                    return [{"content": response.text}]
            else:
                logger.error(f"获取群聊 {talker} 聊天记录失败，状态码: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取群聊 {talker} 聊天记录时发生错误: {str(e)}")
            return []
    
    def get_media_content(self, msgid: str) -> Optional[Dict[str, Any]]:
        """
        获取多媒体消息内容
        
        参数:
            msgid: 消息ID
        
        返回:
            多媒体内容信息
        """
        try:
            response = self.session.get(f"{self.api_base}/api/v1/media", params={"msgid": msgid})
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取多媒体内容失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"获取多媒体内容时发生错误: {str(e)}")
            return None
    
    def get_recent_chatlog(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取最近几天的聊天记录
        
        参数:
            days: 天数，默认获取最近7天的记录
        
        返回:
            聊天记录列表
        """
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        time_range = f"{start_date.strftime('%Y-%m-%d')}~{end_date.strftime('%Y-%m-%d')}"
        
        return self.get_chatlog(time_range=time_range, limit=1000)
    
    def sync_project_chatlogs(self, 
                             project_name: str,
                             chatroom_names: List[str],
                             start_date: str,
                             end_date: str) -> Dict[str, Any]:
        """
        同步指定项目的群聊聊天记录
        
        参数:
            project_name: 项目名称
            chatroom_names: 群聊名称列表
            start_date: 起始日期
            end_date: 结束日期
        
        返回:
            同步结果信息
        """
        try:
            sync_results = {
                "project_name": project_name,
                "start_date": start_date,
                "end_date": end_date,
                "total_chatrooms": len(chatroom_names),
                "success_count": 0,
                "failed_count": 0,
                "total_messages": 0,
                "details": [],
                "timestamp": datetime.now().isoformat()
            }
            
            for chatroom_name in chatroom_names:
                try:
                    # 获取该群聊的聊天记录
                    chatlog = self.get_chatlog_by_talker_and_time(
                        talker=chatroom_name,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    sync_results["success_count"] += 1
                    sync_results["total_messages"] += len(chatlog)
                    sync_results["details"].append({
                        "chatroom_name": chatroom_name,
                        "message_count": len(chatlog),
                        "status": "success",
                        "first_message_time": chatlog[0]["time"] if chatlog else None,
                        "last_message_time": chatlog[-1]["time"] if chatlog else None
                    })
                    
                    logger.info(f"成功同步群聊 {chatroom_name}，获取 {len(chatlog)} 条消息")
                    
                except Exception as e:
                    sync_results["failed_count"] += 1
                    sync_results["details"].append({
                        "chatroom_name": chatroom_name,
                        "error": str(e),
                        "status": "failed"
                    })
                    logger.error(f"同步群聊 {chatroom_name} 失败: {str(e)}")
            
            return sync_results
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"同步项目 {project_name} 聊天记录时发生错误: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def sync_all_chatrooms(self) -> Dict[str, Any]:
        """
        同步所有群聊的聊天记录
        
        返回:
            同步结果信息
        """
        try:
            # 获取所有群聊
            chatrooms = self.get_chatrooms()
            
            sync_results = {
                "total_chatrooms": len(chatrooms),
                "success_count": 0,
                "failed_count": 0,
                "details": []
            }
            
            for chatroom in chatrooms:
                try:
                    # 获取每个群聊的最近聊天记录
                    chatlog = self.get_chatlog(
                        talker=chatroom.get("id"),
                        time_range=f"{datetime.now().strftime('%Y-%m-%d')}~{datetime.now().strftime('%Y-%m-%d')}",
                        limit=100
                    )
                    
                    sync_results["success_count"] += 1
                    sync_results["details"].append({
                        "chatroom_id": chatroom.get("id"),
                        "chatroom_name": chatroom.get("name"),
                        "message_count": len(chatlog),
                        "status": "success"
                    })
                except Exception as e:
                    sync_results["failed_count"] += 1
                    sync_results["details"].append({
                        "chatroom_id": chatroom.get("id"),
                        "chatroom_name": chatroom.get("name"),
                        "error": str(e),
                        "status": "failed"
                    })
            
            return sync_results
        except Exception as e:
            return {
                "status": "error",
                "message": f"同步群聊数据时发生错误: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

# 创建全局实例，方便在其他模块中使用
chatlog_client = ChatlogIntegration() 