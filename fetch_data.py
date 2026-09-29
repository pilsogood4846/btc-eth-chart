#!/usr/bin/env python3
"""Upbit USDT 마켓 일봉 종가를 받아 data.json 을 갱신합니다.

- 처음(data.json 이 비어 있을 때)에는 2021-04-09 부터 전체를 받고,
  이후에는 최근 200일만 받아서 합칩니다.
- UTC 기준 '오늘' 캔들은 아직 마감 전이라 저장하지 않습니다.
- Upbit 요청이 실패하면 Coinbase(USD) 일봉으로 최근 며칠만 대신 채웁니다.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

MARKETS = {"btc": "USDT-BTC", "eth": "USDT-ETH"}
COINBASE = {"btc": "BTC-USD", "eth": "ETH-USD"}
START = "2021-04-09"
OUT = "data.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (chart-updater)"}


def http_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def upbit_candles(market, need_days):
    rows, to = {}, None
    while True:
        q = {"market": market, "count": 200}
        if to:
            q["to"] = to
        batch = http_json("https://api.upbit.com/v1/candles/days?" + urllib.parse.urlencode(q))
        if not batch:
            break
        for c in batch:
            rows[c["candle_date_time_utc"][:10]] = float(c["trade_price"])
        oldest = batch[-1]["candle_date_time_utc"]
        to = oldest + "Z"
        if len(rows) >= need_days or oldest[:10] <= START:
            break
        time.sleep(0.25)
    return rows


def coinbase_candles(product, days=30):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    url = (f"https://api.exchange.coinbase.com/products/{product}/candles"
           f"?granularity=86400&start={start.strftime(fmt)}&end={end.strftime(fmt)}")
    rows = {}
    for t, _low, _high, _open, close, _vol in http_json(url):
        rows[datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")] = float(close)
    return rows


def load():
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # 깨진 파일이면 새로 시작
            print("data.json 읽기 실패, 새로 만듭니다:", e)
    return {"series": {}, "sources": {}}


def main():
    data = load()
    data.setdefault("series", {})
    data.setdefault("sources", {})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    failed = False

    for key, market in MARKETS.items():
        s = data["series"].get(key, {"d": [], "c": []})
        cur = dict(zip(s["d"], s["c"]))
        new, src, fill_only = {}, None, False
        try:
            new = upbit_candles(market, 2500 if len(cur) < 300 else 10)
            src = f"Upbit {market}"
        except Exception as e:
            print(f"[{key}] Upbit 실패: {e}")
            try:
                new = coinbase_candles(COINBASE[key])
                fill_only = True  # 기존 Upbit 값은 덮어쓰지 않고 빠진 날만 채웁니다
                print(f"[{key}] Coinbase 로 대체")
            except Exception as e2:
                print(f"[{key}] Coinbase 도 실패: {e2}")
                failed = True
                continue

        added = 0
        for d, c in new.items():
            if d >= today:
                continue
            if d not in cur:
                added += 1
                cur[d] = round(c, 2)
            elif not fill_only:
                cur[d] = round(c, 2)
        if fill_only:
            src = f"Upbit {market}" + (f" (최근 {added}일은 Coinbase {COINBASE[key]})" if added else "")
        dates = sorted(cur)
        data["series"][key] = {"d": dates, "c": [cur[d] for d in dates]}
        if src:
            data["sources"][key] = src
        # 연속성 점검(최근 30일)
        recent = dates[-30:]
        for a, b in zip(recent, recent[1:]):
            gap = (datetime.fromisoformat(b) - datetime.fromisoformat(a)).days
            if gap > 1:
                print(f"[{key}] 경고: {a} 다음이 {b} (빠진 날 {gap - 1}일)")
        print(f"[{key}] {len(dates)}일, 마지막 {dates[-1]}, 새로 추가 {added}일")

    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    if failed:
        print("일부 종목 갱신에 실패했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
