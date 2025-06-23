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
from chatlog_processor import ChatLogProcessor

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
        """
        self.api_base = api_base.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        self.session.headers.update({
            'User-Agent': 'ChatBoom-Integration/1.0',
            'Accept': 'application/json'
        })
        # 群聊名/ID映射缓存
        self.chatroom_name2id = {}
        self.chatroom_id2name = {}
        self._refresh_chatroom_mapping()

    def _refresh_chatroom_mapping(self):
        """拉取所有群聊，建立 name<->id 映射表，兼容字符串或字典格式"""
        try:
            chatrooms = self.get_chatrooms()
            for room in chatrooms:
                if isinstance(room, dict):
                    name = room.get('name')
                    cid = room.get('id')
                    if name and cid:
                        self.chatroom_name2id[name] = cid
                        self.chatroom_id2name[cid] = name
                elif isinstance(room, str):
                    # 兼容字符串格式（如只返回群聊名）
                    self.chatroom_name2id[room] = room
                    self.chatroom_id2name[room] = room
                else:
                    logger.warning(f"未知群聊数据格式: {room}")
        except Exception as e:
            logger.warning(f"初始化群聊映射失败: {e}")

    def resolve_talker_id(self, talker: str) -> str:
        """
        优先用群聊ID，查不到降级用群聊名，支持多群聊合并（用&分隔）
        """
        if not talker:
            return ''
        talkers = [t.strip() for t in talker.split('&') if t.strip()]
        resolved = []
        for t in talkers:
            # 优先用ID
            if t in self.chatroom_name2id:
                resolved.append(self.chatroom_name2id[t])
            elif t in self.chatroom_id2name:
                resolved.append(t)
            else:
                resolved.append(t)  # 兜底用原始名
        return '&'.join(resolved)

    def get_chatlog_by_talker_and_time(self, 
                                     talker: str, 
                                     start_date: str, 
                                     end_date: str,
                                     format_type: str = "json",
                                     page_limit: int = 1000) -> List[Dict[str, Any]]:
        """
        根据群聊名称和时间范围获取聊天记录，自动分页、ID适配、异常处理、去重
        """
        try:
            # 自动适配群聊ID
            resolved_talker = self.resolve_talker_id(talker)
            time_range = f"{start_date}~{end_date}"
            offset = 0
            all_msgs = []
            seen_ids = set()
            while True:
                params = {
                    "time": time_range,
                    "talker": resolved_talker,
                    "format": format_type,
                    "limit": page_limit,
                    "offset": offset
                }
                url = f"{self.api_base}/api/v1/chatlog"
                try:
                    resp = self.session.get(url, params=params, timeout=30)
                    if resp.status_code != 200:
                        logger.error(f"chatlog接口失败: {resp.status_code}, {resp.text[:200]}")
                        break
                    data = resp.json()
                    if not data:
                        break
                    # 去重（优先用msgid，其次seq）
                    for msg in data:
                        msgid = msg.get('msgid') or msg.get('seq')
                        if msgid and msgid not in seen_ids:
                            all_msgs.append(msg)
                            seen_ids.add(msgid)
                    if len(data) < page_limit:
                        break
                    offset += page_limit
                except Exception as e:
                    logger.error(f"分页拉取chatlog失败: {e}")
                    break
            logger.info(f"最终获取群聊 {talker} 聊天记录 {len(all_msgs)} 条（去重后）")
            return all_msgs
        except Exception as e:
            logger.error(f"获取群聊 {talker} 聊天记录时发生严重错误: {e}")
            return []
    
    def check_service_status(self) -> Dict[str, Any]:
        """
        检查 chatlog 服务是否正常运行，只允许JSON格式
        返回:
            包含服务状态信息的字典
        """
        try:
            # 添加 format=json 参数确保返回 JSON 格式
            params = {"format": "json"}
            response = self.session.get(f"{self.api_base}/api/v1/chatroom", params=params)
            logger.info(f"检查服务状态: {self.api_base}/api/v1/chatroom，参数: {params}，状态码: {response.status_code}")
            if response.status_code == 200:
                if not response.text.strip():
                    return {
                        "status": "warning",
                        "message": "chatlog 服务响应为空，可能服务未完全启动",
                        "timestamp": datetime.now().isoformat(),
                        "api_base": self.api_base
                    }
                content_type = response.headers.get('Content-Type', '')
                logger.info(f"响应Content-Type: {content_type}")
                if 'application/json' not in content_type:
                    return {
                        "status": "error",
                        "message": f"chatlog 服务返回的不是JSON格式，Content-Type: {content_type}",
                        "timestamp": datetime.now().isoformat(),
                        "api_base": self.api_base
                    }
                try:
                    response.json()
                    return {
                        "status": "running",
                        "message": "chatlog 服务正常运行（JSON格式）",
                        "timestamp": datetime.now().isoformat(),
                        "api_base": self.api_base
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"chatlog 服务JSON解析失败: {str(e)}，内容预览: {response.text[:200]}",
                        "timestamp": datetime.now().isoformat(),
                        "api_base": self.api_base
                    }
            else:
                return {
                    "status": "error",
                    "message": f"chatlog 服务响应异常，状态码: {response.status_code}，响应: {response.text[:100]}...",
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
        只允许JSON格式，非JSON直接报错
        返回:
            群聊信息列表，每个群聊包含 id、name 等信息
        """
        try:
            # 添加 format=json 参数确保返回 JSON 格式
            params = {"format": "json"}
            response = self.session.get(f"{self.api_base}/api/v1/chatroom", params=params)
            logger.info(f"请求群聊列表: {self.api_base}/api/v1/chatroom，参数: {params}，状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 检查响应内容
                if not response.text.strip():
                    logger.error("群聊列表响应为空")
                    return []
                
                content_type = response.headers.get('Content-Type', '')
                logger.info(f"响应Content-Type: {content_type}")
                if 'application/json' not in content_type:
                    logger.error(f"chatlog 群聊列表接口返回的不是JSON格式，Content-Type: {content_type}")
                    raise ValueError(f"chatlog 群聊列表接口返回的不是JSON格式，Content-Type: {content_type}")
                try:
                    chatrooms = response.json()
                    logger.info(f"成功获取 {len(chatrooms)} 个群聊（JSON格式）")
                    return chatrooms
                except Exception as e:
                    logger.error(f"chatlog 群聊列表接口JSON解析失败: {str(e)}，内容预览: {response.text[:200]}")
                    raise
            else:
                logger.error(f"获取群聊列表失败，状态码: {response.status_code}，响应: {response.text[:200]}...")
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
                             project_id: int,
                             force_resync: bool = False) -> Dict[str, Any]:
        """
        为指定项目同步聊天记录 - 已重构为使用新的ChatLogProcessor
        它现在是ChatLogProcessor的前端代理
        """
        logger.info(f"开始为项目ID {project_id} 同步聊天记录...")
        
        # 定义一个简单的日志记录器，用于捕获来自处理器的日志
        sync_logs = []
        def capture_log(message: str):
            sync_logs.append(message)
            logger.info(f"[Sync Log - P{project_id}]: {message}")
            
        try:
            # 动态创建与项目绑定的处理器实例
            processor = ChatLogProcessor(project_id=project_id, yield_log=capture_log)
            
            # 执行核心处理逻辑
            result = processor.process_chatlogs()
            
            # 在返回结果中附加详细日志
            result['logs'] = sync_logs
            
            if result.get('success'):
                logger.info(f"项目ID {project_id} 同步成功。")
            else:
                logger.warning(f"项目ID {project_id} 同步过程有警告或失败: {result.get('message', '无详细信息')}")

            return result

        except Exception as e:
            error_message = f"为项目ID {project_id} 同步聊天记录时发生严重错误: {e}"
            logger.error(error_message, exc_info=True)
            return {
                'success': False,
                'message': error_message,
                'logs': sync_logs
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