import argparse
import os
import re
import subprocess


def detect_gateway_ip() -> str | None:
    try:
        result = subprocess.check_output("ipconfig", shell=True, text=True)
        gateways = re.findall(r"Default Gateway[^\d]*(\d+\.\d+\.\d+\.\d+)", result)
        gateways = [g for g in gateways if g and not g.startswith("fe80")]
        return gateways[0] if gateways else None
    except Exception:
        return None


def get_gateway_mac(gateway_ip: str | None):
    gateway_ip = gateway_ip or os.environ.get("GATEWAY_IP") or detect_gateway_ip()
    if not gateway_ip:
        print("게이트웨이 IP를 찾지 못했습니다. --gateway 또는 GATEWAY_IP 환경변수를 지정하세요.")
        return None
    try:
        # 1. arp -a 명령어로 네트워크 캐시를 읽어옵니다.
        result = subprocess.check_output("arp -a", shell=True, text=True)

        # 2. 게이트웨이 IP에 해당하는 MAC 주소를 찾습니다.
        match = re.search(re.escape(gateway_ip) + r"\s+([0-9a-fA-F-]+)", result)

        if match:
            mac_address = match.group(1).upper()
            print("==================================================")
            print(f"현재 PC가 직접 통신하고 있는 공유기 MAC 주소: {mac_address}")
            print(f"게이트웨이: {gateway_ip}")
            print("==================================================")
            print("\n[진단 방법]")
            print("이 MAC 주소가 공유기 뒷면 라벨에 적힌 MAC 주소와 같은지 확인하세요.")
            print("- 메인 공유기 라벨과 같다면 -> 메인 공유기에 직접 연결됨")
            print("- 증폭기(에이전트) 라벨과 같다면 -> 에이전트에 연결됨")
            return mac_address
        else:
            print(f"공유기({gateway_ip})의 MAC 주소를 찾을 수 없습니다.")
            return None

    except Exception as e:
        print(f"오류 발생: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="게이트웨이 MAC 확인")
    parser.add_argument("--gateway", default=os.environ.get("GATEWAY_IP"),
                        help="게이트웨이 IP (미지정시 자동 감지)")
    args = parser.parse_args()
    get_gateway_mac(args.gateway)
