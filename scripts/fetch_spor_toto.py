#!/usr/bin/env python3
"""Fetch the upcoming Spor Toto fixture list from the published weekly program."""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

URL = "https://totopusula.com/yeni-hafta"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; YaPaYCiNAnaliz/1.0)",
    "Accept": "text/html,application/xhtml+xml",
}

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            value = " ".join(" ".join(self.cell).split())
            self.row.append(value)
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None

def fetch():
    error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status != 200:
                    raise RuntimeError("HTTP " + str(response.status))
                return response.read().decode("utf-8", "replace")
        except Exception as exc:
            error = exc
            if attempt < 3:
                time.sleep(2 ** attempt)
    raise RuntimeError("Spor Toto kaynağı okunamadı: " + str(error))

def main():
    html = fetch()
    parser = TableParser()
    parser.feed(html)
    matches = []
    for row in parser.rows:
        if len(row) < 3 or not row[0].strip().isdigit():
            continue
        number = int(row[0].strip())
        if not 1 <= number <= 15:
            continue
        teams = row[1].replace("–", "-").replace("—", "-")
        parts = re.split(r"\s+-\s+", teams, maxsplit=1)
        if len(parts) != 2:
            continue
        schedule = " ".join(row[2:])
        date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", schedule)
        time_match = re.search(r"\b([01]?\d|2[0-3]):[0-5]\d\b", schedule)
        if not date_match or not time_match:
            continue
        day, month, year = date_match.group(1).split(".")
        matches.append({
            "number": number,
            "home": parts[0].strip(),
            "away": parts[1].strip(),
            "date": f"{year}-{month}-{day}",
            "time": time_match.group(0),
        })
    matches.sort(key=lambda item: item["number"])
    if len(matches) != 15 or [m["number"] for m in matches] != list(range(1, 16)):
        raise RuntimeError(f"Kaynakta 15 maçın tamamı doğrulanamadı ({len(matches)}/15); mevcut dosya korunuyor.")
    title_match = re.search(r"(\d+)\.\s*Hafta", re.sub(r"<[^>]+>", " ", html), re.I)
    week = int(title_match.group(1)) if title_match else None
    result = {
        "season": "2026/2027",
        "week": week,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": URL,
        "matches": matches,
    }
    temp = "spor-toto.json.tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(temp, "spor-toto.json")
    print(f"Spor Toto {week or '?'}: {len(matches)} maç güncellendi.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)
