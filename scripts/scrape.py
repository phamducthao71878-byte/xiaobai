import feedparser
import requests
import json
import re
from datetime import datetime, timezone, timedelta

# 只保留经过验证、稳定可用的 AI 信息源
FEEDS = {
    "AI HOT 精选": "https://aihot.news/feed.xml",
    "Hacker News AI": "https://hnrss.org/newest?q=AI",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Google News AI": "https://news.google.com/rss/search?q=AI+when:1d&hl=en-US&gl=US&ceid=US:en"
}

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def main():
    items = []
    now = datetime.now(timezone.utc)
    time_limit = now - timedelta(hours=24)

    for source, url in FEEDS.items():
        try:
            response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                published_at = now
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                
                if published_at < time_limit:
                    continue

                summary = ""
                if hasattr(entry, 'summary'):
                    summary = clean_html(entry.summary)
                elif hasattr(entry, 'description'):
                    summary = clean_html(entry.description)
                    
                if len(summary) > 200:
                    summary = summary[:200] + "..."

                items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": summary,
                    "source": source,
                    "published_at": published_at.isoformat(),
                    "category": "AI 新消息"
                })
        except Exception as e:
            print(f"抓取 {source} 失败: {e}")

    # 去重逻辑
    seen = set()
    unique_items = []
    for item in items:
        if item['link'] not in seen:
            seen.add(item['link'])
            unique_items.append(item)

    unique_items.sort(key=lambda x: x['published_at'], reverse=True)
    unique_items = unique_items[:50]

    output_data = {
        "generated_at": now.isoformat(),
        "items": unique_items
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"抓取完成，共获取 {len(unique_items)} 条内容。")

if __name__ == "__main__":
    main()
