# 원자력 뉴스봇 메인 파일
# 여러 크롤러를 통합 관리

# -*- coding: utf-8 -*-
from crawler_energy_news import crawl_energy_news
from crawler_knpnews import crawl_knpnews
from crawler_kaif import crawl_kaif
import json
from datetime import datetime

def crawl_all_news():
    """
    모든 뉴스 사이트에서 크롤링
    """
    print("="*100)
    print("원자력 뉴스 크롤링 시작")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    all_news = []
    kaif_posts = []

    # 1. 에너지신문 크롤링
    print("\n[1/3] 에너지신문 크롤링 중...")
    print("-"*100)
    energy_news_url = "https://www.energy-news.co.kr/news/articleList.html?sc_sub_section_code=S2N4&view_type=sm"
    energy_news = crawl_energy_news(energy_news_url)
    all_news.extend(energy_news)

    # 2. 한국원자력산업신문 크롤링
    print("\n[2/3] 한국원자력산업신문 크롤링 중...")
    print("-"*100)
    knpnews_url = "https://www.knpnews.com/news/articleList.html?sc_section_code=S1N1&view_type=sm"
    knp_news = crawl_knpnews(knpnews_url)
    all_news.extend(knp_news)

    # 3. 한국원자력산업회의 크롤링 (오늘 날짜만)
    print("\n[3/3] 한국원자력산업회의 크롤링 중 (오늘 날짜 게시물)...")
    print("-"*100)
    kaif_url = "https://www.kaif.or.kr/ko/ko/?c=250&s=250"
    kaif_posts = crawl_kaif(kaif_url)

    # 전체 결과 저장
    output_file = 'all_news_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(all_news),
            'kaif_posts_count': len(kaif_posts),
            'sources': {
                'energy_news': len(energy_news),
                'knpnews': len(knp_news),
                'kaif': len(kaif_posts)
            },
            'news_list': all_news,
            'kaif_posts': kaif_posts
        }, f, ensure_ascii=False, indent=2)

    print("\n" + "="*100)
    print("크롤링 완료!")
    print(f"뉴스 기사: {len(all_news)}개 (에너지신문: {len(energy_news)}, 한국원자력산업신문: {len(knp_news)})")
    print(f"KAIF 오늘 게시물: {len(kaif_posts)}개")
    print(f"결과 파일: {output_file}")
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    return all_news, kaif_posts


if __name__ == "__main__":
    import os

    # 1. 모든 뉴스 크롤링
    crawl_all_news()

    # 2. 어제의 뉴스 요약 및 Slack 전송
    print("\n")
    from slack_formatter import main_with_slack

    # Slack Webhook URL (환경 변수에서 가져옴)
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

    main_with_slack(SLACK_WEBHOOK_URL)
