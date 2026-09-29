# BTC · ETH 일봉 차트 (이평선 + RSI)

매일 한국시간 09:20에 업비트 USDT 마켓 일봉 종가를 받아 `data.json`을 갱신하고, GitHub Pages로 차트를 다시 게시해요.

파일
- `index.html` : 차트 페이지 (data.json을 읽어서 이평선과 RSI를 계산)
- `data.json` : 일봉 종가 데이터 (2021-04-09부터)
- `fetch_data.py` : 업비트에서 최신 종가를 받아 data.json에 합치는 스크립트
- `.github/workflows/update.yml` : 매일 실행 + Pages 배포 설정

설정 (한 번만)
1. 이 파일들을 저장소(Public)에 올려요.
2. Settings → Pages → Build and deployment → Source를 **GitHub Actions**로 바꿔요.
3. Actions 탭 → Update chart → Run workflow로 첫 실행을 해요.
4. 초록 체크가 뜨면 Settings → Pages 상단에 나오는 주소로 접속해요.
