# chatlog_integration.py
# 这个文件负责与 chatlog 工具的 HTTP API 进行交互
# 主要功能包括：获取群聊列表、查询聊天记录、获取联系人信息等

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# 配置日志
logger = logging.getLogger(__name__)

# chatlog HTTP 服务的基础地址
# 默认运行在本地 5030 端口
CHATLOG_API_BASE = "http://127.0.0.1:5030"

class ChatlogIntegration:
    """
    chatlog 工具集成类
    负责与 chatlog 的 HTTP API 进行交互，获取微信群聊数据
    """
    
    def __init__(self, api_base: str = CHATLOG_API_BASE):
        """
        初始化 chatlog 集成
        
        参数:
            api_base: chatlog HTTP 服务的基础地址
        """
        self.api_base = api_base
        self.session = requests.Session()
        # 设置请求超时时间（秒）
        self.session.timeout = 10
    
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
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"chatlog 服务响应异常，状态码: {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "无法连接到 chatlog 服务，请确保服务已启动",
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "连接 chatlog 服务超时",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"检查服务状态时发生错误: {str(e)}",
                "timestamp": datetime.now().isoformat()
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
                return response.json()
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
        获取聊天记录
        
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
            # 构建查询参数
            params = {
                "limit": limit,
                "offset": offset,
                "format": format_type
            }
            
            if talker:
                params["talker"] = talker
            
            if time_range:
                params["time"] = time_range
            
            response = self.session.get(f"{self.api_base}/api/v1/chatlog", params=params)
            
            if response.status_code == 200:
                if format_type == "json":
                    return response.json()
                else:
                    # 对于非 JSON 格式，返回文本内容
                    return [{"content": response.text}]
            else:
                logger.error(f"获取聊天记录失败，状态码: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"获取聊天记录时发生错误: {str(e)}")
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