# -*- coding: utf-8 -*-
"""
测试 chatlog 聊天记录获取链路是否通畅
以“【内部】越城天地项目”和“越城天地&巨象微信工作群”为群昵称，获取最近一周的聊天记录
"""
import datetime
from chatlog_integration import ChatlogIntegration

if __name__ == '__main__':
    # 群昵称样本（与项目卡片一致）
    group_names = [
        '【内部】越城天地项目',
        '越城天地&巨象微信工作群'
    ]
    # 计算最近一周的起止日期
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    chatlog_client = ChatlogIntegration()

    for group in group_names:
        print(f'\n==== 群聊：{group} 最近一周聊天记录 ===')
        msgs = chatlog_client.get_chatlog_by_talker_and_time(
            talker=group,
            start_date=start_date,
            end_date=end_date
        )
        print(f'共获取到 {len(msgs)} 条消息')
        # 打印前5条消息样本
        for i, msg in enumerate(msgs[:5]):
            print(f'  [{i+1}] {msg.get("time") or msg.get("timestamp")}: {msg.get("senderName") or msg.get("sender")} -> {msg.get("content") or msg.get("text")}')
        if not msgs:
            print('  ⚠️ 未获取到任何消息，请检查群昵称是否与chatlog一致，或该时间段内无消息。') 