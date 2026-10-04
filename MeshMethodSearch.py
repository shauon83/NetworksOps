import requests
import json
import time
import os

IPTIME_URL = os.environ.get("IPTIME_URL", "http://192.168.0.1")
# 실제 사용하는 관리자 아이디와 비밀번호는 환경변수로 설정하세요
USERNAME = os.environ.get("IPTIME_ID", "")                 # 관리자 아이디
PASSWORD = os.environ.get("IPTIME_PW", "")          # 관리자 비밀번호

def find_mesh_method():
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json',
        'Origin': IPTIME_URL, 'Referer': f"{IPTIME_URL}/"
    }
    
    login_payload = {"method": "session/login", "params": {"id": USERNAME, "pw": PASSWORD}}
    
    try:
        res = session.post(f"{IPTIME_URL}/cgi/service.cgi", data=json.dumps(login_payload), headers=headers, timeout=10)
        res_data = res.json()
        token = res_data.get('token')
        
        if not token:
            print("❌ 로그인 실패. 아이디/비밀번호를 확인하거나 잠시 후 다시 시도하세요.")
            print("응답:", res_data)
            return
        
        headers['Authorization'] = f"Bearer {token}"
        session.headers.update(headers)
        print("✅ 로그인 성공! 메서드 탐색을 시작합니다...\n")
        
        candidate_methods = [
            "easymesh/agent_list",
            "easymesh/slave_list",
            "easymesh/node_list",
            "easymesh/node",
            "easymesh/info",
            "easymesh/mesh_status",
            "network/easymesh/status",
            "system/easymesh/info"
        ]
        
        for method in candidate_methods:
            print(f"🔍 테스트 메서드: {method}")
            payload = {"method": method}
            
            time.sleep(0.3)
            response = session.post(
                f"{IPTIME_URL}/cgi/service.cgi",
                data=json.dumps(payload),
                timeout=5
            )
            data = response.json()
            
            if "error" not in data and data.get("result") is not None:
                print(f"🎉 [성공] 찾았습니다! 유효한 메서드: {method}")
                print("\n--- 🌐 수신된 데이터 ---")
                print(json.dumps(data["result"], indent=2, ensure_ascii=False))
                print("------------------------\n")
                return
            else:
                print(f"   ㄴ 지원 안함 또는 빈 데이터")
                
    except Exception as e:
        print(f"❌ 요청 실패: {e}")

if __name__ == "__main__":
    find_mesh_method()