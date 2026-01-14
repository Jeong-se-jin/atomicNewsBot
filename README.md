# 원자력 뉴스봇 🤖⚛️

원자력 관련 뉴스를 자동으로 수집하고 Slack으로 전송하는 크롤러

## 📋 기능

### 크롤링 대상
1. **에너지신문** - 전력·원자력 섹션
2. **한국원자력산업신문** - 최신 뉴스
3. **한국원자력산업회의(KAIF)** - 오늘 날짜 게시물 + 국내외 뉴스 링크

### 수집 데이터
- 뉴스 제목, 링크, 날짜, 기자, 카테고리
- 썸네일 이미지
- 본문 미리보기
- KAIF: 국내기사, 세계기사, 사설/칼럼, 원자력계 소식 링크

## 🚀 사용 방법

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 개별 크롤러 실행
```bash
# 에너지신문만
python crawler_energy_news.py

# 한국원자력산업신문만
python crawler_knpnews.py

# KAIF만 (오늘 날짜)
python crawler_kaif.py
```

### 3. 전체 실행 (추천)
```bash
python main.py
```

이 명령어는:
- 3개 사이트 모두 크롤링
- 오늘의 뉴스 요약 JSON 생성
- Slack 메시지 포맷 생성

### 4. Slack으로 전송
```bash
python slack_formatter.py
```

또는 코드에서 직접:
```python
from slack_formatter import main_with_slack

# Webhook URL 설정
webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
main_with_slack(webhook_url)
```

## 📁 출력 파일

### JSON 데이터
- `energy_news_data.json` - 에너지신문 데이터
- `knpnews_data.json` - 한국원자력산업신문 데이터
- `kaif_data.json` - KAIF 데이터
- `all_news_data.json` - 전체 통합 데이터
- `today_news_YYYYMMDD.json` - 오늘의 뉴스 요약

### Slack 메시지
- `slack_message_preview.json` - Slack Block Kit 형식 메시지

## 🔧 프로젝트 구조

```
원자력뉴스봇/
├── crawler_energy_news.py      # 에너지신문 크롤러
├── crawler_knpnews.py          # 한국원자력산업신문 크롤러
├── crawler_kaif.py             # KAIF 크롤러
├── slack_formatter.py          # Slack 포맷터
├── main.py                     # 메인 실행 파일
├── requirements.txt            # 필요 패키지
├── .gitignore                  # Git 제외 파일
└── README.md                   # 이 파일
```

## 📊 Slack 메시지 형식

```
📰 원자력 뉴스 브리핑 - 2026년 01월 13일
───────────────────────────────

⚡ 에너지신문 (20건)
1. [뉴스 제목] - 기자명 | 날짜
...

⚛️ 한국원자력산업신문 (20건)
1. [뉴스 제목] - 기자명 | 날짜
...

🏛️ 한국원자력산업회의 (KAIF)
📌 국내기사
• [기사 제목] - 언론사
...

🌍 세계기사
• [기사 제목] - 언론사
...

✍️ 사설/칼럼
• [기사 제목] - 언론사
...

📢 원자력계 소식
• [소식 제목] - 출처
...
```

## 🔐 Slack Webhook 설정

1. Slack 앱에서 Incoming Webhook 활성화
2. Webhook URL 복사
3. `slack_formatter.py`에서 `SLACK_WEBHOOK_URL` 설정

## ⚙️ 자동화 설정

### Cron (Linux/Mac)
```bash
# 매일 오전 9시 실행
0 9 * * * cd /path/to/원자력뉴스봇 && python main.py
```

### Task Scheduler (Windows)
1. 작업 스케줄러 열기
2. 새 작업 만들기
3. 트리거: 매일 오전 9시
4. 동작: `python main.py`

## 📝 라이선스

MIT License

## 🤝 기여

이슈와 PR은 언제나 환영합니다!
