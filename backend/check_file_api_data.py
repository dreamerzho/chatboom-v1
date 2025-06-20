# 自动采集后端文件API数据
# 用于排查文件视图无数据问题

import requests
import json

API_URL = 'http://localhost:5000/api/v1/files/'

def main():
    try:
        resp = requests.get(API_URL)
        print(f'HTTP状态码: {resp.status_code}')
        data = resp.json()
        print('接口返回内容:')
        print(json.dumps(data, ensure_ascii=False, indent=2))
        if data.get('success') and data.get('data'):
            items = data['data'].get('items')
            if items is not None:
                print(f'文件条数: {len(items)}')
                if len(items) > 0:
                    print('示例文件记录:')
                    print(json.dumps(items[0], ensure_ascii=False, indent=2))
                else:
                    print('items数组为空，数据库可能无文件数据。')
            else:
                print('data.items字段不存在，后端API结构异常。')
        else:
            print('API未返回success或data字段，或接口报错。')
    except Exception as e:
        print(f'采集API数据失败: {e}')

if __name__ == '__main__':
    main() 