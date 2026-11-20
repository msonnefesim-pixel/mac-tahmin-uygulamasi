#!/usr/bin/env python3
"""Read-only connectivity probe for publicly reachable iddaa sportsbook endpoints.
Does not place bets, authenticate, modify data, or archive odds."""
import json, time, urllib.request, urllib.error
from datetime import datetime, timezone

BASE = "https://sportsbookv2.iddaa.com"
PATHS = [
    "/sportsbook/events",
    "/sportsbook/competitions",
]
HEADERS = {
    "User-Agent": "YaPaYCiN-SourceCheck/1.0 (+https://github.com/msonnefesim-pixel/mac-tahmin-uygulamasi)",
    "Accept": "application/json, text/plain, */*",
}

def check(path):
    url = BASE + path
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    started = time.time()
    result = {"url": url, "checked_at_utc": datetime.now(timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read(2_000_001)
            result.update({
                "http_status": response.status,
                "content_type": response.headers.get("Content-Type", ""),
                "bytes_read": len(body),
                "response_truncated_at_2mb": len(body) > 2_000_000,
                "elapsed_seconds": round(time.time() - started, 2),
            })
            try:
                data = json.loads(body.decode("utf-8-sig"))
                result["valid_json"] = True
                result["json_top_level_type"] = type(data).__name__
                if isinstance(data, dict):
                    result["top_level_keys"] = list(data.keys())[:30]
                    for key in ("data", "events", "competitions", "result"):
                        if key in data:
                            value = data[key]
                            result["sample_field"] = key
                            result["sample_field_type"] = type(value).__name__
                            if isinstance(value, list):
                                result["sample_field_count"] = len(value)
                            elif isinstance(value, dict):
                                result["sample_field_keys"] = list(value.keys())[:20]
                            break
                elif isinstance(data, list):
                    result["record_count"] = len(data)
            except Exception as exc:
                result["valid_json"] = False
                result["parse_error"] = str(exc)[:200]
                result["body_preview"] = body[:250].decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        result.update({"http_status": exc.code, "error": str(exc), "elapsed_seconds": round(time.time()-started, 2)})
        try:
            result["body_preview"] = exc.read(250).decode("utf-8", "replace")
        except Exception:
            pass
    except Exception as exc:
        result.update({"error": f"{type(exc).__name__}: {exc}", "elapsed_seconds": round(time.time()-started, 2)})
    return result

if __name__ == "__main__":
    report = {
        "tool": "YaPaYCiN read-only iddaa endpoint check",
        "warning": "A successful HTTP response does not establish permission to bulk collect or redistribute data.",
        "checks": [check(path) for path in PATHS],
    }
    with open("iddaa-kaynak-test-raporu.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
