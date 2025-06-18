#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版同步功能
验证文件解析、去重、人员匹配等功能
"""

import requests
import json
from datetime import datetime, timedelta

def test_enhanced_sync():
    """测试增强版同步功能"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("=== 测试增强版同步功能 ===")
    
    # 1. 检查服务状态
    print("\n1. 检查 chatlog 服务状态")
    try:
        response = requests.get(f"{base_url}/api/v1/sync/status")
        if response.status_code == 200:
            data = response.json()
            print(f"服务状态: {data['data']['status']}")
            print(f"状态信息: {data['data']['message']}")
        else:
            print(f"检查状态失败: {response.status_code}")
    except Exception as e:
        print(f"检查状态异常: {str(e)}")
    
    # 2. 获取群聊列表
    print("\n2. 获取群聊列表")
    try:
        response = requests.get(f"{base_url}/api/v1/sync/chatrooms")
        if response.status_code == 200:
            data = response.json()
            chatrooms = data['data']
            print(f"群聊数量: {len(chatrooms)}")
            if chatrooms:
                print(f"第一个群聊: {chatrooms[0].get('nickName', 'N/A')}")
        else:
            print(f"获取群聊列表失败: {response.status_code}")
    except Exception as e:
        print(f"获取群聊列表异常: {str(e)}")
    
    # 3. 测试项目同步（增强版）
    print("\n3. 测试项目同步（增强版）")
    try:
        # 计算时间范围（最近7天）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        sync_data = {
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "sync_type": "all",
            "force_resync": False  # 不强制重新同步，测试去重功能
        }
        
        print(f"同步参数: {json.dumps(sync_data, indent=2, ensure_ascii=False)}")
        
        # 假设项目ID为1，实际使用时需要根据数据库中的项目ID调整
        response = requests.post(f"{base_url}/api/v1/sync/project/1", json=sync_data)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                results = data['data']['results']
                log = data['data']['log']
                
                print("\n同步结果:")
                print(f"项目名称: {results['project_name']}")
                print(f"时间范围: {results['start_date']} ~ {results['end_date']}")
                print(f"群聊数量: {results['total_chatrooms']}")
                print(f"成功群聊: {results['success_count']}")
                print(f"失败群聊: {results['failed_count']}")
                print(f"总消息数: {results['total_messages']}")
                print(f"处理消息数: {results['processed_messages']}")
                print(f"去重消息数: {results['duplicate_messages']}")
                print(f"文件消息数: {results['file_messages']}")
                print(f"文本消息数: {results['text_messages']}")
                print(f"人员匹配成功: {results['matched_employees']}")
                print(f"人员未匹配: {results['unmatched_employees']}")
                print(f"文件记录数: {results['total_files']}")
                
                print("\n员工统计:")
                employee_stats = results.get('employee_stats', {})
                for emp_id, stats in employee_stats.items():
                    emp = stats['employee']
                    print(f"  {emp['real_name']} ({emp['wechat_nickname']}): "
                          f"消息 {stats['message_count']} 条，文件 {stats['file_count']} 个")
                
                print("\n同步日志:")
                for log_entry in log:
                    print(f"  {log_entry}")
                
                print("\n群聊详情:")
                for detail in results.get('details', []):
                    print(f"  {detail['chatroom_name']}: "
                          f"消息 {detail.get('message_count', 0)} 条，"
                          f"文件 {detail.get('file_count', 0)} 个，"
                          f"去重 {detail.get('duplicate_count', 0)} 条，"
                          f"状态 {detail['status']}")
            else:
                print(f"同步失败: {data.get('error', '未知错误')}")
        else:
            print(f"同步请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"测试同步异常: {str(e)}")
    
    # 4. 测试强制重新同步
    print("\n4. 测试强制重新同步")
    try:
        sync_data = {
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "sync_type": "all",
            "force_resync": True  # 强制重新同步
        }
        
        response = requests.post(f"{base_url}/api/v1/sync/project/1", json=sync_data)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                results = data['data']['results']
                print(f"强制重新同步完成:")
                print(f"处理消息数: {results['processed_messages']}")
                print(f"去重消息数: {results['duplicate_messages']}")
                print(f"文件消息数: {results['file_messages']}")
            else:
                print(f"强制重新同步失败: {data.get('error', '未知错误')}")
        else:
            print(f"强制重新同步请求失败: {response.status_code}")
    except Exception as e:
        print(f"测试强制重新同步异常: {str(e)}")

def test_chat_parser():
    """测试聊天记录解析器"""
    print("\n=== 测试聊天记录解析器 ===")
    
    try:
        from chat_parser import ChatMessageParser, EmployeeMatcher, ChatlogProcessor
        
        # 测试消息解析器
        parser = ChatMessageParser()
        
        # 模拟文件消息
        file_message = {
            'seq': 1746528363000,
            'time': '2025-05-06T18:46:03+08:00',
            'talker': '17720451683@chatroom',
            'talkerName': '越城天地&巨象微信工作群',
            'sender': 'wxid_v1rk05t1abl232',
            'senderName': 'nothing继康',
            'type': 49,
            'subType': 6,
            'content': '<?xml version="1.0"?>\n<msg>\n\t<appmsg appid="" sdkver="0">\n\t\t<title>2025.5.6越城天地视频脚本一V.docx</title>\n\t\t<des />\n\t\t<action />\n\t\t<type>6</type>\n\t\t<showtype>0</showtype>\n\t\t<soundtype>0</soundtype>\n\t\t<mediatagname />\n\t\t<messageext />\n\t\t<messageaction />\n\t\t<content />\n\t\t<contentattr>0</contentattr>\n\t\t<url />\n\t\t<lowurl />\n\t\t<dataurl />\n\t\t<lowdataurl />\n\t\t<appattach>\n\t\t\t<totallen>982829</totallen>\n\t\t\t<attachid>test_attach_id</attachid>\n\t\t\t<emoticonmd5 />\n\t\t\t<fileext>docx</fileext>\n\t\t\t<cdnattachurl>test_cdn_url</cdnattachurl>\n\t\t\t<aeskey>test_aes_key</aeskey>\n\t\t\t<encryver>0</encryver>\n\t\t\t<overwrite_newmsgid>3698272762598796406</overwrite_newmsgid>\n\t\t\t<fileuploadtoken>test_token</fileuploadtoken>\n\t\t</appattach>\n\t\t<extinfo />\n\t\t<sourceusername />\n\t\t<sourcedisplayname />\n\t\t<thumburl />\n\t\t<md5>1d689464d9c7d16d3ac3d60d292bc9c7</md5>\n\t\t<statextstr />\n\t</appmsg>\n\t<fromusername>wxid_v1rk05t1abl232</fromusername>\n\t<scene>0</scene>\n\t<appinfo>\n\t\t<version>1</version>\n\t\t<appname></appname>\n\t</appinfo>\n\t<commenturl></commenturl>\n</msg>\n\x00',
            'contents': {'md5': '1d689464d9c7d16d3ac3d60d292bc9c7', 'title': '2025.5.6越城天地视频脚本一V.docx'}
        }
        
        parsed = parser.parse_message(file_message)
        print(f"解析文件消息:")
        print(f"  消息类型: {parsed['message_type_name']}")
        print(f"  发送者: {parsed['senderName']}")
        if parsed['file_info']:
            print(f"  文件名: {parsed['file_info']['title']}")
            print(f"  文件扩展名: {parsed['file_info']['fileext']}")
            print(f"  文件大小: {parsed['file_info']['totallen']} 字节")
        
        # 测试员工匹配器
        matcher = EmployeeMatcher()
        
        # 模拟员工数据
        employees = [
            {
                'id': 1,
                'real_name': '张三',
                'wechat_nickname': 'nothing继康',
                'name_abbreviation': 'ZS',
                'position': '设计师'
            },
            {
                'id': 2,
                'real_name': '李四',
                'wechat_nickname': '李四',
                'name_abbreviation': 'LS',
                'position': '项目经理'
            }
        ]
        
        matched_employee = matcher.match_employee('nothing继康', employees)
        if matched_employee:
            print(f"\n员工匹配成功:")
            print(f"  微信昵称: nothing继康")
            print(f"  真实姓名: {matched_employee['real_name']}")
            print(f"  职位: {matched_employee['position']}")
        else:
            print(f"\n员工匹配失败: nothing继康")
        
        # 测试聊天记录处理器
        processor = ChatlogProcessor()
        
        # 模拟聊天记录
        chatlog = [file_message]
        
        result = processor.process_chatlog(chatlog, employees)
        print(f"\n聊天记录处理结果:")
        print(f"  总消息数: {result['total_messages']}")
        print(f"  处理消息数: {result['processed_messages']}")
        print(f"  文件消息数: {result['file_messages']}")
        print(f"  匹配员工数: {result['matched_employees']}")
        print(f"  文件记录数: {len(result['file_records'])}")
        
        if result['file_records']:
            file_record = result['file_records'][0]
            print(f"  文件记录:")
            print(f"    原始名称: {file_record['original_name']}")
            print(f"    项目名称: {file_record['project_name']}")
            print(f"    版本号: {file_record['version']}")
            print(f"    上传者: {file_record['uploader']}")
        
    except Exception as e:
        print(f"测试聊天记录解析器异常: {str(e)}")

if __name__ == '__main__':
    test_enhanced_sync()
    test_chat_parser() 