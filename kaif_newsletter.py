# KAIF 뉴스레터 파서 (Gmail API)
# news@kaif.or.kr 에서 '원자력계 소식', '원자력계 이벤트' 섹션만 추출

# -*- coding: utf-8 -*-
import base64
import json
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from gmail_auth import setup_gmail_auth

KST = timezone(timedelta(hours=9))


class KAIFNewsletterParser:
    SENDER = 'news@kaif.or.kr'
    SUBJECT_KEYWORD = '원자력 투데이뉴스'

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

        query = f'from:{self.SENDER} subject:"{self.SUBJECT_KEYWORD}" after:{after} before:{before}'
        print(f'[KAIF Newsletter] Gmail 검색 쿼리: {query}')

        result = self.service.users().messages().list(
            userId='me', q=query, maxResults=10
        ).execute()

        messages = result.get('messages', [])
        if not messages:
            print('[KAIF Newsletter] 해당 날짜 뉴스레터 없음')
            return []

        print(f'[KAIF Newsletter] {len(messages)}개 메일 발견')
        items = []
        for i, m in enumerate(messages):
            msg = self.service.users().messages().get(
                userId='me', id=m['id'], format='full'
            ).execute()

            html_content = self._extract_html(msg)
            if not html_content:
                print(f'[KAIF Newsletter] 메일 {i+1}: HTML 파트 추출 실패, 스킵')
                continue

            # 디버그: 첫 번째 메일만 저장
            if i == 0:
                with open('kaif_newsletter_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print('[KAIF Newsletter] HTML 저장됨: kaif_newsletter_debug.html')

            items.extend(self._parse_sections(html_content, yesterday))

        # 별도 JSON 파일로 저장 (날짜 필터 없이 그대로)
        with open('kaif_newsletter_data.json', 'w', encoding='utf-8') as f:
            json.dump({
                'fetched_at': datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S'),
                'newsletter_date': yesterday.strftime('%Y.%m.%d'),
                'total_count': len(items),
                'items': items
            }, f, ensure_ascii=False, indent=2)
        print(f'[KAIF Newsletter] kaif_newsletter_data.json 저장 완료 ({len(items)}개)')

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

    def _get_text(self, tag):
        """태그 텍스트 추출: \xa0 정규화 + 줄바꿈/연속공백 정리"""
        import re
        text = tag.get_text(strip=False).replace('\xa0', ' ')
        return re.sub(r'\s+', ' ', text).strip()

    def _parse_sections(self, html, date):
        """HTML에서 원자력계 소식/이벤트 섹션의 링크만 추출.

        전략: html.parser로 파싱 후 모든 태그를 document order로 순차 스캔.
        - div/td/span의 짧은 텍스트(30자 미만)로 섹션 진입/이탈 감지
        - 섹션 헤더와 링크가 다른 <table>에 있으므로 조상 기반 탐색은 불가
        - find_all(True)로 depth-first 전체 순회
        """
        soup = BeautifulSoup(html, 'html.parser')
        date_str = date.strftime('%Y.%m.%d')
        items = []
        seen_urls = set()
        current_section = None

        for tag in soup.find_all(True):
            if tag.name in ('script', 'style', 'head', 'meta', 'link'):
                continue

            # 섹션 헤더 감지: div/td/span 중 30자 미만 텍스트
            if tag.name in ('div', 'td', 'span'):
                text = self._get_text(tag)
                if 0 < len(text) < 30:
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

            # 링크 수집: 수집 대상 섹션 안의 <a> 태그만
            if tag.name == 'a' and current_section:
                href = tag.get('href', '')
                # 수신거부·내비게이션 링크 제외
                if 'neo_reject' in href:
                    continue

                if current_section == 'nuclear_events':
                    # 이벤트: <a> 안의 직계 <span> 2개 — 첫째=제목(초록), 둘째=날짜/장소
                    spans = tag.find_all('span', recursive=False)
                    if len(spans) >= 2:
                        event_title = self._get_text(spans[0])
                        date_loc = self._get_text(spans[1])
                        display_title = f"{event_title} / {date_loc}" if date_loc else event_title
                    else:
                        display_title = self._get_text(tag)
                else:
                    display_title = self._get_text(tag)

                if '수신거부' in display_title or '>' in display_title:
                    continue

                if not href.startswith('http') or len(display_title) <= 3 or href in seen_urls:
                    continue

                # 소식: 같은 <tr>의 3번째 <td>에서 단체명 추출
                if current_section == 'nuclear_news':
                    org = ''
                    tr = tag.find_parent('tr')
                    if tr:
                        tds = tr.find_all('td', recursive=False)
                        if len(tds) >= 3:
                            org = self._get_text(tds[-1])
                    if org:
                        display_title = f"{display_title} - {org}"

                seen_urls.add(href)
                items.append({
                    'title': display_title,
                    'url': href,
                    'source': 'kaif_newsletter',
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
