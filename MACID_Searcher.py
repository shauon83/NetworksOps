import subprocess
import re

def get_gateway_mac():
    try:
        # 1. arp -a 명령어로 네트워크 캐시를 읽어옵니다.
        result = subprocess.check_output("arp -a", shell=True, text=True)
        
        # 2. 192.168.0.1 (기본 게이트웨이)에 해당하는 MAC 주소를 찾습니다.
        # 정규식 패턴: 192.168.0.1 뒤에 공백 후 xx-xx-xx-xx-xx-xx 형태를 찾음
        match = re.search(r'192\.168\.0\.1\s+([0-9a-fA-F-]+)', result)
        
        if match:
            mac_address = match.group(1).upper()
            print("==================================================")
            print(f"📡 현재 PC가 직접 통신하고 있는 공유기 MAC 주소: {mac_address}")
            print("==================================================")
            print("\n[진단 방법]")
            print("이 MAC 주소가 공유기 뒷면 라벨에 적힌 MAC 주소와 같은지 확인하세요.")
            print("- 메인 공유기 라벨과 같다면 -> 메인 공유기에 직접 연결됨")
            print("- 증폭기(에이전트) 라벨과 같다면 -> 에이전트에 연결됨")
            return mac_address
        else:
            print("공유기(192.168.0.1)의 MAC 주소를 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        print(f"오류 발생: {e}")
        return None

if __name__ == "__main__":
    get_gateway_mac()