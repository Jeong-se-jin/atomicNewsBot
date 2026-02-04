# Slack 메시지 포맷팅 및 전송

# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta, timezone
import requests

# 한국 시간대 (UTC+9)
KST = timezone(timedelta(hours=9))

def format_slack_message(all_news_data, kaif_data):
    """
    어제의 원자력 뉴스를 Slack 메시지 형식으로 포맷팅
    """
    now_kst = datetime.now(KST)
    yesterday = now_kst - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y년 %m월 %d일 (%A)')

    # Slack Block Kit 형식으로 메시지 구성
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📰 원자력 뉴스 브리핑 - {yesterday_str}",
                "emoji": True
            }
        },
        {
            "type": "divider"
        }
    ]

    # 모든 뉴스를 한곳에 모으기
    all_news_list = []

    # 일반 뉴스 (에너지신문, 한국원자력산업신문)
    for news in all_news_data:
        all_news_list.append({
            'title': news.get('title', ''),
            'url': news.get('url', '')
        })

    # KAIF 뉴스 링크 (국내기사, 세계기사만)
    if kaif_data and len(kaif_data) > 0:
        kaif_post = kaif_data[0]
        news_links = kaif_post.get('news_links', {})

        # 국내기사
        for news in news_links.get('domestic', []):
            all_news_list.append({
                'title': news.get('title', ''),
                'url': news.get('url', '')
            })

        # 세계기사
        for news in news_links.get('international', []):
            all_news_list.append({
                'title': news.get('title', ''),
                'url': news.get('url', '')
            })

    # 뉴스 목록 출력
    if all_news_list:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📌 어제의 뉴스* ({len(all_news_list)}건)"
            }
        })

        for idx, news in enumerate(all_news_list, 1):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{idx}. <{news['url']}|{news['title']}>"
                }
            })

    # 푸터
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"총 {len(all_news_list)}건의 뉴스 | 수집 시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')} (KST)"
            }
        ]
    })

    return blocks


def send_to_slack(webhook_url, blocks):
    """
    Slack Webhook으로 메시지 전송
    """
    payload = {
        "blocks": blocks
    }

    response = requests.post(
        webhook_url,
        json=payload,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        print("[OK] Slack 메시지 전송 완료!")
        return True
    else:
        print(f"[ERROR] Slack 전송 실패: {response.status_code} - {response.text}")
        return False


def create_today_summary():
    """
    오늘 날짜 뉴스 요약 JSON 생성
    """
    # 데이터 파일 읽기
    try:
        with open('energy_news_data.json', 'r', encoding='utf-8') as f:
            energy_data = json.load(f)
            energy_news = energy_data.get('news_list', [])
            # source 필드 추가
            for news in energy_news:
                news['source'] = 'energy_news'
    except:
        energy_news = []

    try:
        with open('knpnews_data.json', 'r', encoding='utf-8') as f:
            knp_data = json.load(f)
            knp_news = knp_data.get('news_list', [])
            # source 필드 추가
            for news in knp_news:
                news['source'] = 'knpnews'
    except:
        knp_news = []

    try:
        with open('kaif_data.json', 'r', encoding='utf-8') as f:
            kaif_data = json.load(f)
            kaif_posts = kaif_data.get('posts', [])
    except:
        kaif_posts = []

    # 어제 날짜 확인 (한국 시간 기준)
    now_kst = datetime.now(KST)
    yesterday = now_kst - timedelta(days=1)
    today_str = yesterday.strftime('%Y.%m.%d')  # 2026.01.12
    today_str_alt = yesterday.strftime('%Y-%m-%d')  # 2026-01-12
    today_date_only = yesterday.strftime('.%m.%d')  # .01.12

    # 모든 뉴스 합치기
    all_news = energy_news + knp_news

    # 어제 날짜 뉴스만 필터링
    today_news = []
    for news in all_news:
        date_str = news.get('date') or ''
        # 다양한 날짜 형식 체크
        # "2026.01.12 09:01" 또는 "2026-01-12" 형식
        if date_str and (today_str in date_str or
            today_str_alt in date_str or
            date_str.startswith(today_str) or
            date_str.startswith(today_str_alt)):
            today_news.append(news)
            title = news.get('title', '').encode('cp949', errors='replace').decode('cp949')
            print(f"[OK] 어제 뉴스 발견: {title} - {date_str}")

    # 요약 데이터 생성
    summary = {
        'date': today_str,
        'total_count': len(today_news),
        'kaif_posts_count': len(kaif_posts),
        'sources': {
            'energy_news': len([n for n in today_news if n.get('source') == 'energy_news']),
            'knpnews': len([n for n in today_news if n.get('source') == 'knpnews']),
            'kaif': len(kaif_posts)
        },
        'news': today_news,
        'kaif_posts': kaif_posts
    }

    # JSON 파일로 저장
    output_file = f'yesterday_news_{yesterday.strftime("%Y%m%d")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 어제의 뉴스 요약이 '{output_file}'에 저장되었습니다.")
    print(f"총 {len(today_news)}개의 뉴스 기사 + {len(kaif_posts)}개의 KAIF 게시물")
    print(f"대상 날짜: {yesterday.strftime('%Y년 %m월 %d일')}")

    return summary


def main_with_slack(webhook_url=None):
    """
    어제의 뉴스 요약 생성 및 Slack 전송
    """
    print("="*100)
    print("어제의 원자력 뉴스 요약 생성 중...")
    print("="*100)

    # 요약 생성
    summary = create_today_summary()

    # Slack 메시지 포맷팅
    print("\nSlack 메시지 포맷팅 중...")
    blocks = format_slack_message(summary['news'], summary['kaif_posts'])

    # Slack 메시지 미리보기 (JSON)
    preview_file = 'slack_message_preview.json'
    with open(preview_file, 'w', encoding='utf-8') as f:
        json.dump({"blocks": blocks}, f, ensure_ascii=False, indent=2)
    print(f"[OK] Slack 메시지 미리보기가 '{preview_file}'에 저장되었습니다.")

    # Slack 전송 (Webhook URL이 제공된 경우)
    if webhook_url:
        print("\nSlack으로 전송 중...")
        send_to_slack(webhook_url, blocks)
    else:
        print("\n[INFO] Webhook URL이 없어서 Slack 전송을 건너뜁니다.")
        print("[INFO] Slack 전송을 원하시면 main_with_slack('YOUR_WEBHOOK_URL')을 호출하세요.")

    print("\n" + "="*100)
    print("완료!")
    print("="*100)


if __name__ == "__main__":
    import os
    # Slack Webhook URL (환경 변수에서 가져옴)
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

    main_with_slack(SLACK_WEBHOOK_URL)
