# NetworksOps

ipTIME EasyMesh 진단 스크립트 모음 (읽기 전용 위주).

## 스크립트
- `check_iptime_easymesh.py` — `/easymesh/api.cgi?key=topology` 조회, 비밀번호/쿠키/MAC 미출력
- `MACID_Searcher.py` — `arp -a`로 게이트웨이 MAC 확인
- `NetworksOps.py` / `MeshMethodSearch.py` — API 탐색용 (로그인 필요)

## 사용법
```powershell
pip install -r requirements.txt
copy .env.example .env
# .env 편집 후
$env:IPTIME_URL="http://192.168.0.1"
$env:IPTIME_ID="관리자아이디"
$env:IPTIME_PW="관리자비밀번호"
python check_iptime_easymesh.py
python check_iptime_easymesh.py --watch --interval 20
```

보안: 자격증명은 환경변수로만 전달. `.env`는 커밋하지 마세요.
