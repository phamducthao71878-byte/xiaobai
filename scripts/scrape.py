import feedparser
import requests
import json
import re
from datetime import datetime, timezone, timedelta

# 这是包含了你要求的 AI HOT 最新域名的信息源
FEEDS = {
    "AI HOT 精选": "https://aihot.news/feed.xml",
    "AI HOT 全部": "https://aihot.news/feed/all.xml",
    "Hacker News AI": "https://hnrss.org/newest?q=AI",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Google News AI": "https://news.google.com/rss/search?q=AI+when:1d&hl=en-US&gl=US&ceid=US:en"
}

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def categorize(title, summary):
    text = (title + " " + summary).lower()
    if any(k in text for k in ['tool', 'app', 'plugin', '工具', '插件', '应用', '软件']):
        return "2. 热门 AI 工具"
    if any(k in text for k in ['prompt', '提示词']):
        return "3. 热门提示词"
    if any(k in text for k in ['tutorial', 'course', 'guide', '教程', '指南', '入门']):
        return "4. 大神热门教程"
    if any(k in text for k in ['money', 'revenue', 'profit', '赚钱', '盈利', '商业化', '投资', '融资']):
        return "5. AI 赚钱案例"
    if any(k in text for k in ['video', 'youtube', 'bilibili', '视频']):
        return "6. 热门 AI 视频"
    if any(k in text for k in ['paper', 'research', 'arxiv', '论文', '研究']):
        return "7. AI 论文与研究"
    if any(k in text for k in ['code', 'developer', 'programming', 'api', '编程', '开发', 'python', '代码']):
        return "8. AI 编程与开发"
    if any(k in text for k in ['regulation', 'law', 'policy', '政策', '法规', '监管']):
        return "9. AI 政策与法规"
    if any(k in text for k in ['opinion', 'debate', '观点', '争议', '讨论']):
        return "10. AI 观点与争议"
    if any(k in text for k in ['healthcare', 'finance', 'education', '医疗', '金融', '教育', '制造']):
        return "11. AI 垂直领域行业"
    return "1. AI 新消息"

def main():
    items = []
    now = datetime.now(timezone.utc)
    time_limit = now - timedelta(hours=24)

    for source, url in FEEDS.items():
        try:
            # 增加了伪装，防止 AI HOT 网站拦截我们
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml, */*"
            }
            response = requests.get(url, timeout=15, headers=headers)
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

                category = categorize(entry.title, summary)

                items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": summary,
                    "source": source,
                    "published_at": published_at.isoformat(),
                    "category": category
                })
        except Exception as e:
            print(f"抓取 {source} 失败: {e}")

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
