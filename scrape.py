import json, re, html, os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import feedparser
import requests

UTC=timezone.utc
NOW=datetime.now(UTC)
SINCE=NOW-timedelta(hours=24)
OUT="data.json"
FEEDS=[
 ("OpenAI","https://openai.com/news/rss.xml"),
 ("Anthropic","https://www.anthropic.com/news/rss.xml"),
 ("Google AI","https://blog.google/technology/google-labs/rss/"),
 ("Hugging Face","https://huggingface.co/blog/feed.xml"),
 ("arXiv cs.AI","https://export.arxiv.org/rss/cs.AI"),
 ("arXiv cs.CL","https://export.arxiv.org/rss/cs.CL"),
 ("arXiv cs.CV","https://export.arxiv.org/rss/cs.CV"),
 ("arXiv cs.LG","https://export.arxiv.org/rss/cs.LG"),
]
CATS=[
"1. AI 新消息","2. 热门 AI 工具","3. 热门提示词","4. 大神热门教程","5. AI 赚钱案例",
"6. 热门 AI 视频","7. AI 论文与研究","8. AI 编程与开发","9. AI 政策与法规",
"10. AI 观点与争议","11. AI 垂直领域行业"
]
RULES={
"1. AI 新消息":["launch","announces","announced","release","introducing","发布","推出","宣布","上线","新模型"],
"2. 热门 AI 工具":["tool","product","app","platform","工具","产品","应用","平台"],
"3. 热门提示词":["prompt","prompting","提示词","提示语"],
"4. 大神热门教程":["tutorial","how to","guide","course","教程","手把手","指南","课程"],
"5. AI 赚钱案例":["revenue","earning","income","business","monetiz","收入","赚钱","营收","变现","创业"],
"6. 热门 AI 视频":["video","text-to-video","video generation","视频生成","AI视频","短视频"],
"7. AI 论文与研究":["arxiv","paper","research","benchmark","研究","论文","技术报告","benchmark"],
"8. AI 编程与开发":["coding","code","developer","agent","framework","github","编程","开发","智能体","工作流","开源"],
"9. AI 政策与法规":["policy","regulation","law","copyright","safety","governance","法规","监管","版权","安全","合规"],
"10. AI 观点与争议":["opinion","debate","controversy","risk","criticism","观点","争议","风险","预测"],
"11. AI 垂直领域行业":["health","medical","education","finance","legal","robotics","healthcare","医疗","教育","金融","法律","机器人"]
}
def clean(s):
    s=html.unescape(re.sub(r"<[^>]+>"," ",s or ""))
    return re.sub(r"\s+"," ",s).strip()
def parse_date(entry):
    for key in ("published","updated","created"):
        val=entry.get(key)
        if val:
            try:
                dt=parsedate_to_datetime(val)
                if dt.tzinfo is None: dt=dt.replace(tzinfo=UTC)
                return dt.astimezone(UTC)
            except Exception: pass
    for key in ("published_parsed","updated_parsed"):
        val=entry.get(key)
        if val:
            try: return datetime(*val[:6],tzinfo=UTC)
            except Exception: pass
    return None
def choose_category(title, summary, source):
    text=(title+" "+summary+" "+source).lower()
    # Give papers a dedicated category before broad research keywords.
    if "arxiv" in source.lower(): return "7. AI 论文与研究"
    scores=[]
    for cat,words in RULES.items():
        score=sum(1 for w in words if w.lower() in text)
        scores.append((score,cat))
    best=max(scores)
    return best[1] if best[0]>0 else "1. AI 新消息"
def main():
    items=[]; errors=[]
    for source,url in FEEDS:
        try:
            response=requests.get(url,timeout=18,headers={"User-Agent":"XiaobaiAI-DailyBrief/1.0 (RSS reader)"})
            response.raise_for_status()
            feed=feedparser.parse(response.content)
            if not feed.entries: errors.append(source+": feed empty"); continue
            for e in feed.entries:
                dt=parse_date(e)
                if not dt or dt<SINCE or dt>NOW+timedelta(minutes=10): continue
                title=clean(e.get("title",""))
                link=e.get("link","")
                summary=clean(e.get("summary","") or e.get("description",""))
                if not title or not link or not link.startswith("http"): continue
                if len(summary)>500: summary=summary[:497]+"..."
                if not summary: summary="该来源在最近24小时发布了此条内容；请打开原文查看详细说明。"
                items.append({"title":title,"summary":summary,"url":link,"source":source,
                              "published_at":dt.isoformat(timespec="minutes"),"category":choose_category(title,summary,source)})
        except Exception as ex: errors.append(source+": "+str(ex)[:140])
    # Deduplicate by canonical URL and normalized title.
    unique=[]; seen=set()
    for x in sorted(items,key=lambda z:z["published_at"],reverse=True):
        key=re.sub(r"[?#].*$","",x["url"]).rstrip("/") or x["title"].lower()
        if key in seen: continue
        seen.add(key); unique.append(x)
    # RSS cannot establish virality, prompt sharing, creator earnings, or video engagement.
    # These are intentionally left empty unless real source evidence appears in a later version.
    for x in unique:
        if x["category"] in ("2. 热门 AI 工具","3. 热门提示词","4. 大神热门教程","5. AI 赚钱案例","6. 热门 AI 视频"):
            x["summary"] += "（注：RSS 发布时间可核实，但该采集方式不能证明其热度或变现数据。）"
    bycat={c:[x for x in unique if x["category"]==c] for c in CATS}
    top=unique[:5]
    if top:
        summary="最近24小时可核实的公开来源主要涉及："+ "；".join(x["title"] for x in top[:3])+"。这些条目反映本次 RSS/论文源实际抓取到的内容，不代表全网热度排名。"
    else:
        summary="最近24小时内未从配置的公开 RSS/论文源取得可确认发布时间的条目。请检查工作流日志和数据源；不会用旧闻填充当日简报。"
    now_local=NOW.astimezone(timezone(timedelta(hours=8)))
    data={"date":now_local.strftime("%Y-%m-%d"),"generated_at":NOW.isoformat(timespec="seconds"),
          "window":"最近24小时（UTC 过滤）","items":unique,"summary":summary,
          "notice":"自动采集公开 RSS 与 arXiv feed；目前不接入 X/Reddit 热度指标，也不声称能证明提示词/视频/赚钱案例爆火。各分类按真实抓取结果展示，不足时不会编造。"+(" 数据源提示："+ "；".join(errors[:4]) if errors else "")}
    with open(OUT,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    # Also create a Markdown brief with requested headings and source links.
    lines=[f"# 小白爱AI｜AI 当日简报（{data['date']}）", "", f"> 时间范围：{data['window']}；生成时间：{data['generated_at']}", ""]
    for cat in CATS:
        lines += [f"## {cat}", ""]
        group=bycat[cat][:5]
        if not group:
            lines += ["- 最近24小时没有采集到足够且可核实的内容；本栏目暂不补旧闻。",""]
        else:
            for i,x in enumerate(group,1):
                lines += [f"{i}. **{x['title']}**", f"   - 简要说明：{x['summary']}", f"   - 来源：[{x['source']}]({x['url']})", f"   - 发布时间：{x['published_at']}", ""]
    lines += ["## 当日总结","",data["summary"],""]
    with open("daily-brief.md","w",encoding="utf-8") as f: f.write("\n".join(lines))
    print(f"Saved {len(unique)} items; errors={len(errors)}")
if __name__=="__main__": main()
