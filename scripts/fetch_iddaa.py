#!/usr/bin/env python3
"""Fetch the public Iddaa sportsbook bulletin for the YaPaYCiN static site."""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

BASE = "https://sportsbookv2.iddaa.com/sportsbook"
URLS = {
    "events": BASE + "/events?st=1&type=0&version=0",
    "competitions": BASE + "/competitions?st=1",
}
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
    "Referer": "https://www.iddaa.com/",
    "Origin": "https://www.iddaa.com",
}

def get_json(url):
    last_error = None
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=35) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                raw = response.read()
            data = json.loads(raw.decode("utf-8-sig"))
            if not isinstance(data, dict):
                raise RuntimeError("Beklenmeyen JSON biçimi")
            return data
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Kaynak okunamadı: {url}: {last_error}")

def extract(payload, keys):
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []

def main():
    events_payload = get_json(URLS["events"])
    comps_payload = get_json(URLS["competitions"])
    events = extract(events_payload, ("events",))
    competitions = extract(comps_payload, ("competitions",))
    if not events:
        raise RuntimeError("İddaa etkinlik listesi boş; mevcut dosya korunacak.")
    # Sanity check: the feed should contain at least some recognizable event records.
    recognizable = sum(1 for event in events if isinstance(event, dict) and event.get("hn") and event.get("an"))
    if recognizable == 0:
        raise RuntimeError("Bültende takım adı olan etkinlik bulunamadı; mevcut dosya korunacak.")
    result = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "sportsbookv2.iddaa.com",
        "events": events,
        "competitions": competitions,
        "event_count": len(events),
    }
    temp = "iddaa.json.tmp"
    with open(temp, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, separators=(",", ":"))
    os.replace(temp, "iddaa.json")
    print(f"İddaa bülteni alındı: {len(events)} etkinlik, {len(competitions)} lig/kupa kaydı.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
