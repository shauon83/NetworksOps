import requests
import json
import time
import os

# ==========================================
# 1. 사용자 설정 (환경변수 사용 - 하드코딩 금지)
# ==========================================
IPTIME_URL = os.environ.get("IPTIME_URL", "http://YOUR_ROUTER_IP")
USERNAME = os.environ.get("IPTIME_ID", "")                 # 관리자 아이디
PASSWORD = os.environ.get("IPTIME_PW", "")          # 관리자 비밀번호

def iptime_api_login_perfect(url, username, password):
    # 세션 객체 생성 (쿠키 및 헤더를 자동으로 유지해줌)
    session = requests.Session()
    
    # 1. 헤더 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Origin': url,
        'Referer': f"{url}/"
    }
    
    # 2. 정확한 로그인 페이로드 구성 (F12에서 확인하신 구조)
    login_payload = {
        "method": "session/login",
        "params": {
            "id": username,
            "pw": password
        }
    }
    
    try:
        print("▶ [1단계] 공유기 API로 로그인 데이터 전송 중...")
        
        # 3. 로그인 요청 (service.cgi)
        response = session.post(
            f"{url}/cgi/service.cgi",
            data=json.dumps(login_payload),
            headers=headers,
            timeout=10 # 타임아웃 10초 설정
        )
        
        # 4. 응답 확인
        res_data = response.json()
        
        # ipTIME API는 보통 {"success": true} 또는 토큰을 반환합니다.
        if "pw" not in response.text.lower(): # 단순 에러 메시지가 아니라면
            print("✅ API 로그인 성공!")
            
            # 응답 데이터 안에 발급된 토큰이나 세션 ID가 있는지 확인
            # (펌웨어에 따라 쿠키로만 구워주고 응답 본문에는 없을 수도 있습니다.)
            token = res_data.get('token') or res_data.get('session_id')
            if token:
                print(f"🔑 발급된 Token: {token}")
                # 이후 요청을 위해 헤더 업데이트
                headers['Authorization'] = f"Bearer {token}"
            
            # 현재 세션(쿠키 포함)과 헤더를 반환하여 계속 사용할 수 있게 함
            session.headers.update(headers)
            return session
            
        else:
            print("❌ 로그인 실패 (응답 거부). 아이디/비밀번호를 확인하세요.")
            print("응답:", res_data)
            return None
            
    except requests.exceptions.Timeout:
        print("❌ 요청 시간 초과 (Timeout). 공유기가 응답을 멈췄습니다.")
        print("   - 공유기가 너무 많은 비정상 접근을 감지해 차단했을 수 있습니다. 공유기를 재부팅하거나 10분 후 다시 시도해보세요.")
        return None
    except json.JSONDecodeError:
        print("❌ JSON 파싱 실패. 공유기가 예상치 못한 형식으로 응답했습니다.")
        print("응답 원본:", response.text[:200])
        return None
    except Exception as e:
        print(f"❌ 네트워크 오류: {e}")
        return None

# ... (위쪽 iptime_api_login_perfect 함수는 그대로 유지) ...

# ... (위쪽 로그인 코드는 유지) ...

if __name__ == "__main__":
    active_session = iptime_api_login_perfect(IPTIME_URL, USERNAME, PASSWORD)
    
    if active_session:
        print("\n▶ [2단계] 메쉬 노드 상세 정보 발굴 중...\n")
        
        # easymesh/status 메서드에 들어갈 수 있는 다양한 key 후보군
        test_keys = [
            "topology",
            "node_list",
            "nodes",
            "devices",
            "info",
            "status",
            "tree",
            "mac_list"
        ]
        
        found_data = False
        
        for key in test_keys:
            print(f"🔍 파라미터 테스트 중: {{'key': '{key}'}}")
            payload = {
                "method": "easymesh/status",
                "params": {"key": key}
            }
            
            try:
                time.sleep(0.5) # 과부하 방지
                res = active_session.post(
                    f"{IPTIME_URL}/cgi/service.cgi",
                    data=json.dumps(payload),
                    timeout=5
                )
                data = res.json()
                
                # 에러가 아니고, 결과가 존재하며, 단순히 "configured" 같은 문자열 하나가 아닐 때
                if "error" not in data and "result" in data:
                    result_data = data["result"]
                    
                    if isinstance(result_data, (dict, list)):
                        print(f"🎉 빙고! 노드 데이터 발견! (Key: {key})")
                        print("\n--- 🌐 메쉬 상세 데이터 ---")
                        # 들여쓰기를 적용하여 보기 좋게 출력
                        print(json.dumps(result_data, indent=2, ensure_ascii=False)[:2000]) # 앞 2000자 출력
                        print("----------------------------\n")
                        found_data = True
                        break # 데이터를 찾았으므로 반복문 탈출
                    elif isinstance(result_data, str) and result_data != "configured":
                        print(f"⚠️ {key} 의 결과가 문자열입니다: {result_data}")
                    
            except Exception as e:
                print(f"❌ 요청 실패: {e}")
                
        if not found_data:
            print("\n❌ 모든 키를 시도했으나 노드 리스트를 찾지 못했습니다.")
            print("💡 진단 결과: 공유기(컨트롤러) 내부의 메쉬 프로세스가 완전히 뻗어있는 상태(Hang)일 확률이 매우 높습니다.")
            print("👉 메인 공유기와 에이전트 공유기들의 전원을 모두 뽑았다가 1분 뒤 켜서 재부팅한 후 스크립트를 다시 실행해보세요.")