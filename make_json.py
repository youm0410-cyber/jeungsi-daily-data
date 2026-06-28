"""market_data.js / news_data.js 의 window.* 래퍼를 벗겨 순수 JSON으로 저장.
원격 호스팅(앱이 fetch)용 market_data.json, news_data.json 생성."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

PAIRS = [
    ("market_data.js", "market_data.json"),
    ("news_data.js", "news_data.json"),
]


def strip(js_text):
    # window.XXX = {....};  →  {....}
    m = re.match(r"\s*window\.[A-Z_]+\s*=\s*(.*?);?\s*$", js_text, re.S)
    body = m.group(1) if m else js_text
    return json.loads(body)


def main():
    for src, dst in PAIRS:
        sp = os.path.join(HERE, src)
        if not os.path.exists(sp):
            print("skip (missing):", src)
            continue
        with open(sp, encoding="utf-8") as f:
            data = strip(f.read())
        with open(os.path.join(HERE, dst), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        print("wrote", dst)


if __name__ == "__main__":
    main()
