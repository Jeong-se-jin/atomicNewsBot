# 한국원자력산업신문 RSS 크롤러
# -*- coding: utf-8 -*-
import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

RSS_URL = 'https://www.knpnews.com/rss/gns_allArticle.xml'

KST = timezone(timedelta(hours=9))


def crawl_knpnews_rss():
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
            return (el.text or '').strip()

        title    = txt('title')
        url      = txt('link') or txt('guid')
        date_raw = txt('pubDate')
        author_raw = txt('author') or ''

        try:
            dt = parsedate_to_datetime(date_raw).astimezone(KST)
            date_str = dt.strftime('%Y.%m.%d %H:%M')
        except Exception:
            date_str = date_raw

        reporter = author_raw
        if '(' in author_raw and ')' in author_raw:
            reporter = author_raw[author_raw.index('(')+1:author_raw.index(')')]

        all_news.append({
            'title':    title,
            'url':      url,
            'date':     date_str,
            'reporter': reporter,
            'category': '뉴스',
            'thumbnail': None,
            'preview':  None,
            'source':   'knpnews',
        })

    print('='*80)
    for i, n in enumerate(all_news[:5], 1):
        print(f'[{i}] {n["title"]}')
        print(f'    URL: {n["url"]}')
        print(f'    날짜: {n["date"]} | 기자: {n["reporter"]}')
        print('-'*80)
    if len(all_news) > 5:
        print(f'... 외 {len(all_news)-5}개')

    output_file = 'knpnews_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'source': 'knpnews',
            'url': RSS_URL,
            'total_count': len(all_news),
            'news_list': all_news,
        }, f, ensure_ascii=False, indent=2)
    print(f'[OK] {len(all_news)}개 저장 → {output_file}')
    return all_news


if __name__ == '__main__':
    crawl_knpnews_rss()
