# 에너지신문 RSS 크롤러
# -*- coding: utf-8 -*-
import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

RSS_URL = 'https://cdn.energy-news.co.kr/rss/gns_allArticle.xml'

# 전력·원자력 관련 키워드 (S2N4 섹션 대체)
NUCLEAR_KEYWORDS = [
    '원자력', '원전', '한수원', '핵연료', '방사선', 'SMR', '핵발전',
    '우라늄', '체코 원전', '두코바니', '한전기술', '한전원자력',
    '전력거래소', '한전KDN', '한전KPS', '방사성', 'IAEA'
]

KST = timezone(timedelta(hours=9))


def crawl_energy_news_rss():
    print(f'RSS 로딩 중: {RSS_URL}')
    resp = requests.get(RSS_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    channel = root.find('channel')
    items = channel.findall('item')
    print(f'[OK] 전체 기사 {len(items)}개 수신')

    all_news = []
    for item in items:
        def txt(tag):
            el = item.find(tag)
            if el is None:
                return None
            # CDATA는 .text로 그냥 읽힘
            return (el.text or '').strip()

        title = txt('title')
        url   = txt('link') or txt('guid')
        date_raw = txt('pubDate')
        author_raw = txt('author') or ''

        # 날짜 파싱 — RFC 2822 형식
        try:
            dt = parsedate_to_datetime(date_raw).astimezone(KST)
            date_str = dt.strftime('%Y.%m.%d %H:%M')
        except Exception:
            date_str = date_raw

        # 기자명 파싱 — "email (이름)" 형식
        reporter = author_raw
        if '(' in author_raw and ')' in author_raw:
            reporter = author_raw[author_raw.index('(')+1:author_raw.index(')')]

        all_news.append({
            'title':    title,
            'url':      url,
            'date':     date_str,
            'reporter': reporter,
            'category': '전력·원자력',
            'thumbnail': None,
            'preview':  None,
            'source':   'energy_news',
        })

    # 키워드 필터링
    nuclear_news = [
        n for n in all_news
        if n['title'] and any(kw in n['title'] for kw in NUCLEAR_KEYWORDS)
    ]
    print(f'키워드 필터링: {len(all_news)}개 → {len(nuclear_news)}개')

    print('='*80)
    for i, n in enumerate(nuclear_news, 1):
        print(f'[{i}] {n["title"]}')
        print(f'    URL: {n["url"]}')
        print(f'    날짜: {n["date"]} | 기자: {n["reporter"]}')
        print('-'*80)

    output_file = 'energy_news_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'energy_news',
            'url': RSS_URL,
            'total_count': len(nuclear_news),
            'news_list': nuclear_news,
        }, f, ensure_ascii=False, indent=2)
    print(f'[OK] {len(nuclear_news)}개 저장 → {output_file}')
    return nuclear_news


if __name__ == '__main__':
    crawl_energy_news_rss()
