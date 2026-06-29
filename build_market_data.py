"""대한민국 전 종목(코스피+코스닥) 시가총액 데이터를 네이버에서 받아 market_data.js로 저장."""
import json
import re
import datetime
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
NAME_RE = re.compile(r'class="tltle"[^>]*>([^<]+)</a>')
CODE_RE = re.compile(r'/item/main\.naver\?code=(\d+)')
RANK_RE = re.compile(r'class="no"[^>]*>\s*(\d+)\s*</td>')
PRICE_RE = re.compile(r'<td class="number">\s*([\d,]+)\s*</td>')
RATE_RE = re.compile(r'<span class="tah p11 ([^"]*)"[^>]*>\s*([+\-]?[\d,]+\.\d+)%')

IDX_CODES = [("코스피", "KOSPI"), ("코스닥", "KOSDAQ"), ("코스피200", "KPI200")]


def collect_indices():
    """네이버 모바일 지수 API(JSON)에서 코스피/코스닥/코스피200 시세를 받아온다."""
    out = []
    for nm, code in IDX_CODES:
        try:
            url = f"https://m.stock.naver.com/api/index/{code}/basic"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read().decode("utf-8", "replace"))
            val = d.get("closePrice", "-")
            direction = (d.get("compareToPreviousPrice") or {}).get("name", "")
            sign = "+" if direction == "RISING" else ("-" if direction == "FALLING" else "")
            amount = str(d.get("compareToPreviousClosePrice", "0")).lstrip("+-")
            rate = str(d.get("fluctuationsRatio", "0")).lstrip("+-")
            chg_str = f"{sign}{amount} ({sign}{rate}%)"
            out.append({"name": nm, "val": val, "chg": chg_str})
            print(f"  지수 {nm}: {val} {chg_str}")
        except Exception as e:
            out.append({"name": nm, "val": "-", "chg": "0.00 (0.00%)"})
            print(f"  ! {nm} 지수 실패: {e}")
    return out


def fetch(sosok, page):
    url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={page}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("euc-kr", "replace")


def parse(html):
    out = []
    for chunk in ROW_RE.findall(html):
        if 'class="tltle"' not in chunk:
            continue
        name = NAME_RE.search(chunk)
        if not name:
            continue
        rank = RANK_RE.search(chunk)
        code = CODE_RE.search(chunk)
        price = PRICE_RE.search(chunk)
        rate_m = RATE_RE.search(chunk)
        if rate_m:
            cls, num = rate_m.group(1), rate_m.group(2)
            if num.startswith("+") or num.startswith("-"):
                rate = num + "%"
            elif "0.00" == num:
                rate = "0.00%"
            elif "red" in cls or "up" in cls:
                rate = "+" + num + "%"
            elif "nv" in cls or "blue" in cls or "down" in cls:
                rate = "-" + num + "%"
            else:
                rate = num + "%"
        else:
            rate = "0.00%"
        out.append({
            "r": int(rank.group(1)) if rank else None,
            "c": code.group(1) if code else "",
            "nm": name.group(1).strip(),
            "price": price.group(1) if price else "",
            "rate": rate,
        })
    return out


def collect(sosok, last):
    rows = []
    for p in range(1, last + 1):
        rows.extend(parse(fetch(sosok, p)))
        print(f"  sosok={sosok} page {p}/{last} -> total {len(rows)}")
    return rows


def main():
    print("지수 수집...")
    indices = collect_indices()
    print("KOSPI 수집...")
    kospi = collect(0, 50)
    print("KOSDAQ 수집...")
    kosdaq = collect(1, 37)
    data = {
        "generatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "indices": indices,
        "kospi": kospi,
        "kosdaq": kosdaq,
    }
    payload = "window.MARKET_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
    with open("market_data.js", "w", encoding="utf-8") as f:
        f.write(payload)
    print(f"\n[완료] 코스피 {len(kospi)}종목 + 코스닥 {len(kosdaq)}종목 = {len(kospi)+len(kosdaq)}개")
    print(f"[저장] market_data.js ({len(payload):,} bytes)")


if __name__ == "__main__":
    main()
