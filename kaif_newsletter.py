# KAIF 뉴스레터 파서 (Gmail API)
# news@kaif.or.kr 에서 '원자력계 소식', '원자력계 이벤트' 섹션만 추출

# -*- coding: utf-8 -*-
import base64
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from gmail_auth import setup_gmail_auth

KST = timezone(timedelta(hours=9))


class KAIFNewsletterParser:
    SENDER = 'news@kaif.or.kr'

    # 수집할 섹션 키워드 → category 이름
    TARGET_SECTIONS = {
        '원자력계 소식': 'nuclear_news',
        '원자력계 이벤트': 'nuclear_events',
    }

    # 건너뛸 섹션 (crawler_kaif.py 웹 크롤러가 이미 수집 중)
    SKIP_SECTIONS = {'국내기사', '세계기사', '사설', '칼럼', '기고'}

    def __init__(self):
        creds = setup_gmail_auth()
        self.service = build('gmail', 'v1', credentials=creds)

    def fetch_latest_newsletter(self):
        """어제 날짜 KAIF 뉴스레터에서 원자력계 소식/이벤트 추출 (날짜 기반)"""
        now = datetime.now(KST)
        yesterday = now - timedelta(days=1)
        after = yesterday.strftime('%Y/%m/%d')
        before = now.strftime('%Y/%m/%d')

        query = f'from:{self.SENDER} after:{after} before:{before}'
        print(f'[KAIF Newsletter] Gmail 검색 쿼리: {query}')

        result = self.service.users().messages().list(
            userId='me', q=query, maxResults=1
        ).execute()

        messages = result.get('messages', [])
        if not messages:
            print('[KAIF Newsletter] 해당 날짜 뉴스레터 없음')
            return []

        msg = self.service.users().messages().get(
            userId='me', id=messages[0]['id'], format='full'
        ).execute()

        html_content = self._extract_html(msg)
        if not html_content:
            print('[KAIF Newsletter] HTML 파트 추출 실패')
            return []

        items = self._parse_sections(html_content, yesterday)
        return items

    def _extract_html(self, msg):
        """메일 payload에서 text/html 파트를 재귀 탐색 후 base64url 디코딩"""
        def find_html(payload):
            if payload.get('mimeType') == 'text/html':
                data = payload.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='replace')
            for part in payload.get('parts', []):
                result = find_html(part)
                if result:
                    return result
            return None

        return find_html(msg['payload'])

    def _parse_sections(self, html, date):
        """HTML에서 원자력계 소식/이벤트 섹션의 링크만 추출"""
        soup = BeautifulSoup(html, 'lxml')
        date_str = date.strftime('%Y.%m.%d')
        items = []
        current_section = None

        for tag in soup.find_all(['td', 'tr', 'p', 'div', 'span', 'a']):
            text = tag.get_text(strip=True)

            # 섹션 헤더 감지 (짧은 텍스트만 헤더로 간주)
            if len(text) < 30:
                matched = False
                for keyword, category in self.TARGET_SECTIONS.items():
                    if keyword in text:
                        current_section = category
                        matched = True
                        break
                if not matched:
                    for skip in self.SKIP_SECTIONS:
                        if skip in text:
                            current_section = None
                            break

            # 링크 추출 (수집 대상 섹션 내 <a> 태그만)
            if current_section and tag.name == 'a':
                href = tag.get('href', '')
                title = tag.get_text(strip=True)
                if href and title and href.startswith('http'):
                    items.append({
                        'title': title,
                        'url': href,
                        'source': f'kaif_newsletter',
                        'date': date_str,
                        'category': current_section,
                    })

        nuclear_news_count = sum(1 for i in items if i['category'] == 'nuclear_news')
        nuclear_events_count = sum(1 for i in items if i['category'] == 'nuclear_events')
        print(f'[KAIF Newsletter] 원자력계 소식: {nuclear_news_count}개')
        print(f'[KAIF Newsletter] 원자력계 이벤트: {nuclear_events_count}개')
        return items


if __name__ == '__main__':
    parser = KAIFNewsletterParser()
    items = parser.fetch_latest_newsletter()
    for item in items:
        print(f"[{item['category']}] {item['title']} → {item['url']}")
