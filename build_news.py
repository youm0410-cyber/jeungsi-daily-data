"""구글 뉴스 RSS(한국어)에서 증시 관련 뉴스를 모아 news_data.js로 저장.
앱은 실행 시 런타임으로도 갱신하지만, 이 파일은 기본(번들)·웹용 폴백 + 요약을 제공한다."""
import json
import re
import datetime
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
QUERIES = ["코스피", "코스닥", "증시 전망", "삼성전자 주가"]
TAG_RE = re.compile(r"<[^>]+>")


def rss_url(q):
    return ("https://news.google.com/rss/search?q="
            + urllib.parse.quote(q)
            + "&hl=ko&gl=KR&ceid=KR:ko")


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def fmt_time(pub):
    try:
        dt = datetime.datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.strftime("%m-%d %H:%M")
    except Exception:
        return ""


def parse(xml_bytes):
    items = []
    root = ET.fromstring(xml_bytes)
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "").strip()
        src_el = it.find("source")
        src = (src_el.text.strip() if src_el is not None and src_el.text else "")
        t, s = title, src
        if " - " in title and not src:
            t, s = title.rsplit(" - ", 1)
        elif " - " in title and src and title.endswith(" - " + src):
            t = title[: -(len(src) + 3)]
        items.append({"t": t.strip(), "src": s or "뉴스", "h": link, "time": fmt_time(pub)})
    return items


def main():
    seen, items = set(), []
    for q in QUERIES:
        try:
            for it in parse(fetch(rss_url(q))):
                key = it["t"][:40]
                if key in seen or not it["t"]:
                    continue
                seen.add(key)
                items.append(it)
        except Exception as e:
            print(f"  ! {q} 실패: {e}")
    items = items[:20]

    summary = [it["t"] for it in items[:6]]
    data = {
        "generatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": items,
        "summary": summary,
    }
    payload = "window.NEWS_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
    with open("news_data.js", "w", encoding="utf-8") as f:
        f.write(payload)
    print(f"[완료] 뉴스 {len(items)}건, 요약 {len(summary)}건")
    print(f"[저장] news_data.js ({len(payload):,} bytes)")


if __name__ == "__main__":
    main()
