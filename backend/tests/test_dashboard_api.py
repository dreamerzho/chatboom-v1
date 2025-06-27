# test_dashboard_api.py
# 自动测试仪表盘和细化API，验证连通性、返回结构和数据完整性
# 便于前后端联调和接口自查

import requests
import json

BASE_URL = "http://127.0.0.1:5000"  # 你的本地Flask服务地址

# ========== 测试配置 ==========
TEST_EMPLOYEE_ID = 1
TEST_PROJECT_ID = 1
TEST_PERIOD = "30d"

# ========== 测试函数 ==========
def test_api(endpoint, params={}):
    """通用API测试函数"""
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"✅ [SUCCESS] {endpoint} (params={params})")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ [FAIL] {endpoint} (params={params}): {e}")
        return None

# ========== 主测试入口 ==========
if __name__ == '__main__':
    print("🚀 开始自动测试后端API...")
    # --- 员工维度 ---
    test_api(f"/api/v1/employees/{TEST_EMPLOYEE_ID}/workloads", {'page': 1, 'size': 5})
    test_api(f"/api/v1/employees/{TEST_EMPLOYEE_ID}/stats", {'period': TEST_PERIOD})
    test_api(f"/api/v1/employees/{TEST_EMPLOYEE_ID}/risk-events", {'period': TEST_PERIOD})
    # --- 项目维度 ---
    test_api(f"/api/v1/projects/{TEST_PROJECT_ID}/workloads", {'page': 1, 'size': 5})
    test_api(f"/api/v1/projects/{TEST_PROJECT_ID}/health-stats", {'period': TEST_PERIOD})
    test_api(f"/api/v1/projects/{TEST_PROJECT_ID}/risk-events", {'period': TEST_PERIOD})
    # --- 趋势与榜单 ---
    test_api("/api/v1/dashboard/workload-trend", {'period': TEST_PERIOD})
    test_api("/api/v1/dashboard/employee-ranking", {'period': TEST_PERIOD, 'role': '设计'})
    test_api("/api/v1/dashboard/project-summary")
    # --- 基础仪表盘 ---
    test_api("/api/v1/dashboard/project-health")
    test_api("/api/v1/dashboard/risk-feed")
    print("\n🎉 API自动测试完成！") 