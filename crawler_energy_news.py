# 에너지신문 크롤링 파일

# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import time
import tempfile
import shutil

def crawl_energy_news(url):
    """
    에너지데일리 뉴스 크롤링
    """
    # 임시 디렉토리 생성
    temp_dir = tempfile.mkdtemp(prefix='selenium_')

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(f'--user-data-dir={temp_dir}')  # 임시 디렉토리 지정
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Selenium 4.6+ 자동 드라이버 관리 사용
    driver = webdriver.Chrome(options=chrome_options)

    try:
        print(f"페이지 로딩 중: {url}")
        driver.get(url)
        time.sleep(5)

        # 디버그: 페이지 소스 저장
        with open('energy_news_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

        # 뉴스 리스트 찾기 (fallback 선택자 포함)
        news_list = None
        possible_selectors = [
            '#section-list ul.type2',
            '#section-list ul',
            '.type2',
            'ul.type2',
            '#article-list ul',
            '.article-list ul',
        ]
        for selector in possible_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                items = elem.find_elements(By.TAG_NAME, 'li')
                if len(items) >= 3:
                    news_list = elem
                    print(f"[OK] 선택자 적용: {selector} ({len(items)}개)")
                    break
            except:
                continue

        if not news_list:
            raise Exception("뉴스 리스트를 찾을 수 없습니다. energy_news_page_source.html 확인 필요")

        news_items = news_list.find_elements(By.TAG_NAME, 'li')

        print(f"\n총 {len(news_items)}개의 뉴스 발견\n")
        print("="*100)

        all_news = []

        for idx, item in enumerate(news_items, 1):
            news_data = {}

            try:
                # 썸네일 이미지
                try:
                    img = item.find_element(By.CSS_SELECTOR, 'a.thumb img')
                    news_data['thumbnail'] = img.get_attribute('src')
                except:
                    news_data['thumbnail'] = None

                # 제목 및 URL
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, 'h2.titles a')
                    news_data['title'] = title_elem.text.strip()
                    news_data['url'] = title_elem.get_attribute('href')
                except:
                    news_data['title'] = None
                    news_data['url'] = None

                # 본문 미리보기
                try:
                    news_data['preview'] = item.find_element(By.CSS_SELECTOR, 'p.lead a').text.strip()
                except:
                    news_data['preview'] = None

                # 메타 정보 — type2: span.byline > em [카테고리, 기자, 날짜]
                #             type1: em.info.category / em.info.name / em.info.dated
                try:
                    byline = item.find_element(By.CSS_SELECTOR, 'span.byline')
                    ems = byline.find_elements(By.TAG_NAME, 'em')
                    news_data['category'] = ems[0].text.strip() if len(ems) >= 1 else None
                    news_data['reporter'] = ems[1].text.strip() if len(ems) >= 2 else None
                    news_data['date']     = ems[2].text.strip() if len(ems) >= 3 else None
                except:
                    # type1 fallback
                    try:
                        news_data['category'] = item.find_element(By.CSS_SELECTOR, 'em.info.category').text.strip()
                    except:
                        news_data['category'] = None
                    try:
                        news_data['reporter'] = item.find_element(By.CSS_SELECTOR, 'em.info.name').text.strip()
                    except:
                        news_data['reporter'] = None
                    try:
                        news_data['date'] = item.find_element(By.CSS_SELECTOR, 'em.info.dated').text.strip()
                    except:
                        news_data['date'] = None

                all_news.append(news_data)

                # 출력
                try:
                    print(f"[{idx}] {news_data['title']}")
                    print(f"    URL: {news_data['url']}")
                    print(f"    카테고리: {news_data['category']}")
                    print(f"    기자: {news_data['reporter']}")
                    print(f"    날짜: {news_data['date']}")
                    print(f"    썸네일: {news_data['thumbnail']}")
                    print(f"    미리보기: {news_data['preview'][:100]}..." if news_data['preview'] else "    미리보기: None")
                    print("-"*100)
                except UnicodeEncodeError:
                    title_safe = news_data['title'].encode('cp949', errors='replace').decode('cp949')
                    print(f"[{idx}] {title_safe} (일부 문자 대체)")
                    print("-"*100)

            except Exception as e:
                print(f"항목 {idx} 파싱 오류: {e}")

        # 전력·원자력 카테고리만 필터링
        # (페이지가 JS 클라이언트 필터링 구조라 전체 기사가 로딩됨)
        nuclear_news = [
            n for n in all_news
            if n.get('category') and '원자력' in n['category']
        ]
        print(f"\n전력·원자력 필터링: {len(all_news)}개 → {len(nuclear_news)}개")

        # JSON 파일로 저장
        output_file = 'energy_news_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source': 'energy_news',
                'url': url,
                'total_count': len(nuclear_news),
                'news_list': nuclear_news
            }, f, ensure_ascii=False, indent=2)

        print("="*100)
        print(f"[OK] {len(nuclear_news)}개의 뉴스 데이터가 '{output_file}' 파일에 저장되었습니다.")

        return nuclear_news

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
    url = "https://www.energy-news.co.kr/news/articleList.html?sc_sub_section_code=S2N4&view_type=sm"
    crawl_energy_news(url)
