# 한국원자력산업신문 크롤링 파일

# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import tempfile
import shutil

def crawl_knpnews(url):
    """
    한국원자력산업신문 크롤링
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

        # 페이지 소스 저장 (디버깅용)
        with open('knpnews_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("[DEBUG] 페이지 소스가 'knpnews_page_source.html'에 저장되었습니다.")

        # 여러 가능한 선택자 시도
        possible_selectors = [
            "#section-list ul li",
            "#section-list .type2 li",
            "section.section-list ul li",
            "div.article-list li",
            "ul.article-list li",
            ".news-list li",
        ]

        news_items = []
        used_selector = None

        for selector in possible_selectors:
            try:
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                if items and len(items) > 5:  # 최소 5개 이상의 아이템이 있어야 유효
                    print(f"[OK] 발견된 선택자: {selector} ({len(items)}개 항목)")
                    news_items = items
                    used_selector = selector
                    break
            except:
                continue

        if not news_items:
            print("뉴스 항목을 찾을 수 없습니다. 수동으로 HTML을 확인해주세요.")
            return []

        print(f"\n총 {len(news_items)}개의 뉴스 발견\n")
        print("="*100)

        all_news = []

        for idx, item in enumerate(news_items, 1):
            news_data = {}

            try:
                # 썸네일 이미지
                try:
                    img = item.find_element(By.CSS_SELECTOR, 'img')
                    news_data['thumbnail'] = img.get_attribute('src')
                except:
                    news_data['thumbnail'] = None

                # 제목 및 링크
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, 'h2 a, h3 a, .titles a, strong a')
                    news_data['title'] = title_elem.text.strip()
                    news_data['url'] = title_elem.get_attribute('href')
                except:
                    try:
                        link_elem = item.find_element(By.CSS_SELECTOR, 'a')
                        news_data['title'] = link_elem.text.strip()
                        news_data['url'] = link_elem.get_attribute('href')
                    except:
                        news_data['title'] = None
                        news_data['url'] = None

                # 본문 미리보기
                try:
                    lead_elem = item.find_element(By.CSS_SELECTOR, 'p.lead, .description, .summary')
                    news_data['preview'] = lead_elem.text.strip()
                except:
                    news_data['preview'] = None

                # 메타 정보 (카테고리, 기자, 날짜)
                try:
                    byline = item.find_element(By.CSS_SELECTOR, 'span.byline, .info, .meta')
                    em_elements = byline.find_elements(By.TAG_NAME, 'em')

                    if len(em_elements) >= 3:
                        news_data['category'] = em_elements[0].text.strip()
                        news_data['reporter'] = em_elements[1].text.strip()
                        news_data['date'] = em_elements[2].text.strip()
                    elif len(em_elements) >= 2:
                        news_data['category'] = None
                        news_data['reporter'] = em_elements[0].text.strip()
                        news_data['date'] = em_elements[1].text.strip()
                    elif len(em_elements) >= 1:
                        news_data['category'] = None
                        news_data['reporter'] = None
                        news_data['date'] = em_elements[0].text.strip()
                    else:
                        news_data['category'] = None
                        news_data['reporter'] = None
                        news_data['date'] = None
                except:
                    news_data['category'] = None
                    news_data['reporter'] = None
                    news_data['date'] = None

                # 유효한 데이터가 있는 경우만 추가
                if news_data['title'] and news_data['url']:
                    all_news.append(news_data)

                    # 출력 (처음 5개만)
                    if idx <= 5:
                        print(f"[{idx}] {news_data['title']}")
                        print(f"    URL: {news_data['url']}")
                        print(f"    카테고리: {news_data['category']}")
                        print(f"    기자: {news_data['reporter']}")
                        print(f"    날짜: {news_data['date']}")
                        print(f"    썸네일: {news_data['thumbnail']}")
                        print(f"    미리보기: {news_data['preview'][:100]}..." if news_data['preview'] else "    미리보기: None")
                        print("-"*100)

            except Exception as e:
                print(f"항목 {idx} 파싱 오류: {e}")

        # JSON 파일로 저장
        output_file = 'knpnews_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source': 'knpnews',
                'url': url,
                'total_count': len(all_news),
                'news_list': all_news
            }, f, ensure_ascii=False, indent=2)

        print("\n" + "="*100)
        print(f"[OK] {len(all_news)}개의 뉴스 데이터가 '{output_file}' 파일에 저장되었습니다.")

        return all_news

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
    url = "https://www.knpnews.com/news/articleList.html?sc_section_code=S1N1&view_type=sm"
    crawl_knpnews(url)
