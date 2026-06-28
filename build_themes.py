"""네이버 '테마'별 종목 그룹을 수집해 기존 market_data.js에 themes로 합친다.
가격/등락률은 market_data.js 전 종목 데이터에서 코드로 조회하므로 여기선
테마명·평균등락률·멤버(코드/이름)만 모은다."""
import json
import re
import time
import urllib.request

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

THEME_RE = re.compile(
    r'sise_group_detail\.naver\?type=theme&no=(\d+)">([^<]+)</a>'
    r'.*?col_type2">\s*<span class="tah p11 [^"]*"[^>]*>\s*([+\-]?[\d.]+)%',
    re.S,
)
MEMBER_RE = re.compile(r'name_area"><a href="/item/main\.naver\?code=(\d+)">([^<]+)</a>')


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("euc-kr", "replace")


def collect_theme_list():
    themes = []
    seen = set()
    for page in range(1, 13):
        html = fetch(f"https://finance.naver.com/sise/theme.naver?page={page}")
        rows = THEME_RE.findall(html)
        if not rows:
            break
        new = 0
        for no, nm, rate in rows:
            if no in seen:
                continue
            seen.add(no)
            themes.append({"no": no, "nm": nm.strip(), "rate": rate + "%"})
            new += 1
        print(f"  theme list page {page} -> +{new} (total {len(themes)})")
        if new == 0:
            break
    return themes


def collect_members(no):
    html = fetch(f"https://finance.naver.com/sise/sise_group_detail.naver?type=theme&no={no}")
    out, seen = [], set()
    for code, nm in MEMBER_RE.findall(html):
        if code in seen:
            continue
        seen.add(code)
        out.append({"c": code, "nm": nm.strip()})
    return out


def main():
    with open("market_data.js", "r", encoding="utf-8") as f:
        s = f.read()
    data = json.loads(s[s.index("{"): s.rindex("}") + 1])

    print("테마 목록 수집...")
    themes = collect_theme_list()
    print(f"테마 {len(themes)}개. 멤버 종목 수집...")
    for i, t in enumerate(themes, 1):
        try:
            t["stocks"] = collect_members(t["no"])
        except Exception as e:
            t["stocks"] = []
            print(f"  ! {t['nm']} 실패: {e}")
        if i % 30 == 0:
            print(f"  {i}/{len(themes)} ...")
        time.sleep(0.05)

    data["themes"] = themes
    payload = "window.MARKET_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n"
    with open("market_data.js", "w", encoding="utf-8") as f:
        f.write(payload)
    total_members = sum(len(t["stocks"]) for t in themes)
    print(f"\n[완료] 테마 {len(themes)}개, 멤버 매핑 {total_members}건")
    print(f"[저장] market_data.js ({len(payload):,} bytes)")


if __name__ == "__main__":
    main()
