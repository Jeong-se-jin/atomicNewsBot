# 한국원자력산업회의 크롤링 파일

# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import json
import time
import tempfile
import shutil
from datetime import datetime

def parse_news_table(driver):
    """
    국내외 뉴스 테이블 데이터 파싱
    """
    news_data = {
        'domestic': [],
        'international': [],
        'editorial': [],
        'nuclear_news': []
    }

    try:
        # bbsContents 안의 모든 td 찾기
        content_elem = driver.find_element(By.CSS_SELECTOR, '#bbsContents')

        # 모든 링크 찾기
        all_links = content_elem.find_elements(By.TAG_NAME, 'a')

        current_section = None

        for link in all_links:
            link_text = link.text.strip()
            link_url = link.get_attribute('href')

            # 섹션 구분
            if not link_url or 'kaif.or.kr' in link_url:
                continue

            # 빈 텍스트 제외
            if not link_text:
                continue

            # 뉴스 기사인지 확인 (외부 링크)
            if link_url and ('http://' in link_url or 'https://' in link_url):
                # 텍스트에서 언론사명 분리
                parts = link_text.split(' ')
                if len(parts) >= 2:
                    # 마지막 단어가 언론사명일 가능성
                    article_title = ' '.join(parts[:-1])
                    source = parts[-1]
                else:
                    article_title = link_text
                    source = None

                news_item = {
                    'title': article_title,
                    'source': source,
                    'url': link_url
                }

                # 섹션별로 분류 (content의 앞부분 텍스트로 판단)
                # 실제로는 td의 앞쪽 텍스트를 봐야 하지만, 간단히 처리
                news_data['domestic'].append(news_item)

        # content 전체 텍스트로 섹션 구분
        full_text = content_elem.text

        # 다시 파싱 - 텍스트 기반으로 섹션 구분
        news_data = {
            'domestic': [],
            'international': [],
            'editorial': [],
            'nuclear_news': []
        }

        # 텍스트를 줄 단위로 분석
        lines = full_text.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()

            # 섹션 헤더 감지
            if '국내기사' in line or '국내 기사' in line:
                current_section = 'domestic'
                continue
            elif '세계기사' in line or '세계 기사' in line or '국제기사' in line:
                current_section = 'international'
                continue
            elif '사설' in line or '칼럼' in line or '기고' in line:
                current_section = 'editorial'
                continue
            elif '원자력계 소식' in line:
                current_section = 'nuclear_news'
                continue

            # 뉴스 아이템 파싱 (· 로 시작하는 줄)
            if line.startswith('·'):
                # · 제거
                line = line[1:].strip()

                # 링크에서 실제 데이터 찾기
                for link in all_links:
                    if link.text.strip() and link.text.strip() in line:
                        link_url = link.get_attribute('href')
                        if link_url and ('http://' in link_url or 'https://' in link_url):
                            # 제목과 언론사 분리
                            parts = line.rsplit(' ', 1)
                            if len(parts) == 2:
                                article_title = parts[0]
                                source = parts[1]
                            else:
                                article_title = line
                                source = None

                            news_item = {
                                'title': article_title,
                                'source': source,
                                'url': link_url
                            }

                            if current_section == 'domestic':
                                news_data['domestic'].append(news_item)
                            elif current_section == 'international':
                                news_data['international'].append(news_item)
                            elif current_section == 'editorial':
                                news_data['editorial'].append(news_item)
                            elif current_section == 'nuclear_news':
                                news_data['nuclear_news'].append(news_item)
                            break

        return news_data

    except Exception as e:
        print(f"뉴스 테이블 파싱 오류: {e}")
        return news_data


def crawl_kaif(url):
    """
    한국원자력산업회의 크롤링
    어제 날짜의 게시물만 상세 내용까지 수집
    """
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp(prefix='selenium_')

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(f'--user-data-dir={temp_dir}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"페이지 로딩 중: {url}")
        driver.get(url)
        time.sleep(5)

        # 어제 날짜 확인
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        today_str = yesterday.strftime('%Y-%m-%d')  # 2026-01-12
        today_str_alt = yesterday.strftime('%Y.%m.%d')  # 2026.01.12
        today_str_alt2 = yesterday.strftime('%m.%d')  # 01.12

        print(f"\n어제 날짜: {today_str}")
        print("어제 날짜의 게시물만 수집합니다.\n")

        # 여러 가능한 선택자 시도
        possible_selectors = [
            "table tbody tr",
            "div.board-list table tr",
            "table.board-list tr",
            ".list-item",
            "div.list tbody tr",
        ]

        board_items = []
        used_selector = None

        for selector in possible_selectors:
            try:
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                if items and len(items) > 3:
                    print(f"[OK] 발견된 선택자: {selector} ({len(items)}개 항목)")
                    board_items = items
                    used_selector = selector
                    break
            except:
                continue

        if not board_items:
            print("게시물 항목을 찾을 수 없습니다. 수동으로 HTML을 확인해주세요.")
            return []

        print(f"\n총 {len(board_items)}개의 게시물 발견")
        print("="*100)

        today_posts = []

        for idx, item in enumerate(board_items, 1):
            try:
                # 날짜 확인
                date_text = None
                try:
                    date_elem = item.find_element(By.CSS_SELECTOR, 'td.col-date, td.date, .date, td:last-child')
                    date_text = date_elem.text.strip()
                except:
                    continue

                # 오늘 날짜인지 확인
                is_today = False
                if date_text:
                    # 다양한 날짜 형식 체크
                    if today_str in date_text or today_str_alt in date_text or today_str_alt2 in date_text:
                        is_today = True
                    # "오늘" 텍스트 체크
                    elif "오늘" in date_text or "today" in date_text.lower():
                        is_today = True

                if not is_today:
                    continue

                print(f"\n[어제 게시물 발견] 날짜: {date_text}")

                # 제목 및 링크
                post_data = {}
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, 'td.subject a, .title a, td a')
                    post_data['title'] = title_elem.text.strip()
                    post_url = title_elem.get_attribute('href')
                    post_data['list_url'] = post_url
                    post_data['date'] = date_text
                except:
                    continue

                # 상세 페이지로 이동
                print(f"상세 페이지 접근 중: {post_data['title']}")
                driver.get(post_url)
                time.sleep(3)

                # 상세 내용 파싱
                try:
                    # 제목
                    try:
                        detail_title = driver.find_element(By.CSS_SELECTOR, 'h3.bbs-view-tit, h1, .view-title, .subject')
                        post_data['detail_title'] = detail_title.text.strip()
                    except:
                        post_data['detail_title'] = post_data['title']

                    # 본문 내용
                    try:
                        content_elem = driver.find_element(By.CSS_SELECTOR, '#bbsContents, .bbs-view-content, .view-content, .content')
                        post_data['content'] = content_elem.text.strip()
                    except:
                        post_data['content'] = None

                    # 국내외 뉴스 테이블 파싱
                    post_data['news_links'] = parse_news_table(driver)

                except Exception as e:
                    print(f"상세 내용 파싱 오류: {e}")

                    # 첨부파일
                    try:
                        attachments = []
                        attach_elems = driver.find_elements(By.CSS_SELECTOR, '.attach a, .file a, .attachment a')
                        for attach in attach_elems:
                            attachments.append({
                                'filename': attach.text.strip(),
                                'url': attach.get_attribute('href')
                            })
                        post_data['attachments'] = attachments
                    except:
                        post_data['attachments'] = []

                    # 작성자
                    try:
                        author_elem = driver.find_element(By.CSS_SELECTOR, '.author, .writer, .name')
                        post_data['author'] = author_elem.text.strip()
                    except:
                        post_data['author'] = None

                    # 조회수
                    try:
                        views_elem = driver.find_element(By.CSS_SELECTOR, '.views, .hit, .count')
                        post_data['views'] = views_elem.text.strip()
                    except:
                        post_data['views'] = None

                except Exception as e:
                    print(f"상세 내용 파싱 오류: {e}")

                today_posts.append(post_data)

                print(f"[OK] 수집 완료: {post_data['title']}")
                print(f"     내용 길이: {len(post_data.get('content', '')) if post_data.get('content') else 0}자")
                print(f"     첨부파일: {len(post_data.get('attachments', []))}개")

                # 뉴스 링크 통계
                news_links = post_data.get('news_links', {})
                print(f"     국내기사: {len(news_links.get('domestic', []))}개")
                print(f"     세계기사: {len(news_links.get('international', []))}개")
                print(f"     사설/칼럼: {len(news_links.get('editorial', []))}개")
                print(f"     원자력계 소식: {len(news_links.get('nuclear_news', []))}개")
                print("-"*100)

                # 다시 목록 페이지로 돌아가기
                driver.back()
                time.sleep(2)

            except Exception as e:
                print(f"게시물 처리 오류: {e}")
                continue

        # JSON 파일로 저장
        output_file = 'kaif_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source': 'kaif',
                'url': url,
                'crawled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'target_date': today_str,
                'total_count': len(today_posts),
                'posts': today_posts
            }, f, ensure_ascii=False, indent=2)

        print("\n" + "="*100)
        print(f"[OK] 어제 날짜 게시물 {len(today_posts)}개가 '{output_file}' 파일에 저장되었습니다.")

        return today_posts

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        driver.quit()
        # 임시 디렉토리 정리
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


if __name__ == "__main__":
    url = "https://www.kaif.or.kr/ko/ko/?c=250&s=250"
    crawl_kaif(url)
