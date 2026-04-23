import sys, io, urllib.request, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# S2N3 섹션 RSS 확인
for url in ['https://www.energy-news.co.kr/rss/S2N3.xml',
            'https://www.energy-news.co.kr/rss/S2N4.xml']:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read().decode('utf-8', errors='replace')
        # channel title + 첫 번째 item
        title_m = re.search(r'<title><!\[CDATA\[(.*?)\]\]>', content)
        item_start = content.find('<item>')
        item_end = content.find('</item>') + len('</item>')
        print(f'[{url}]')
        print(f'  채널 제목: {title_m.group(1) if title_m else "?"}')
        print(f'  첫 item:')
        print(content[item_start:item_end][:600])
        print()
    except Exception as e:
        print(f'[{url}] 실패: {e}')

# gns_allArticle.xml에 category 태그 있는지 확인
req = urllib.request.Request('https://cdn.energy-news.co.kr/rss/gns_allArticle.xml',
                              headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as r:
    content = r.read().decode('utf-8', errors='replace')
item_start = content.find('<item>')
item_end = content.find('</item>') + len('</item>')
print('[gns_allArticle] 첫 item 전체:')
print(content[item_start:item_end])
