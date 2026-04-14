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

        # 디버그: HTML을 파일로 저장해서 구조 확인
        with open('kaif_newsletter_debug.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print('[KAIF Newsletter] HTML 저장됨: kaif_newsletter_debug.html')

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

    def _find_section_header(self, soup, keyword):
        """섹션 헤더 태그 찾기 (div/td 중 키워드 포함 + 짧은 텍스트)"""
        for tag in soup.find_all(['div', 'td', 'tr']):
            text = tag.get_text(strip=False).replace('\xa0', ' ').strip()
            if keyword in text and len(text) < 30:
                return tag
        return None

    def _parse_sections(self, html, date):
        """HTML에서 원자력계 소식/이벤트 섹션의 링크만 추출"""
        # html.parser: lxml보다 malformed HTML에서 tag 순서를 더 잘 보존
        soup = BeautifulSoup(html, 'html.parser')
        date_str = date.strftime('%Y.%m.%d')
        items = []
        seen_urls = set()

        # 다음 섹션 경계 키워드 (소식/이벤트 처리 중 멈춰야 할 지점)
        all_boundaries = set(self.TARGET_SECTIONS.keys()) | self.SKIP_SECTIONS

        for target_keyword, category in self.TARGET_SECTIONS.items():
            header = self._find_section_header(soup, target_keyword)
            if not header:
                print(f'[KAIF Newsletter] 섹션 미발견: {target_keyword}')
                continue

            # 헤더 이후 모든 <a> 태그를 순서대로 순회
            for a in header.find_all_next('a'):
                href = a.get('href', '')
                title = a.get_text(strip=False).replace('\xa0', ' ').strip()

                # 다른 섹션 경계에 도달하면 수집 중단
                hit_boundary = False
                for boundary in all_boundaries:
                    if boundary == target_keyword:
                        continue
                    # 이 <a>의 가장 가까운 div/td 조상이 경계 헤더인지 확인
                    for ancestor in a.parents:
                        if ancestor.name in ('div', 'td', 'tr'):
                            anc_text = ancestor.get_text(strip=True).replace('\xa0', ' ').strip()
                            if boundary in anc_text and len(anc_text) < 30:
                                hit_boundary = True
                                break
                    if hit_boundary:
                        break
                if hit_boundary:
                    break

                if href.startswith('http') and title and len(title) > 3 and href not in seen_urls:
                    seen_urls.add(href)
                    items.append({
                        'title': title,
                        'url': href,
                        'source': 'kaif_newsletter',
                        'date': date_str,
                        'category': category,
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
