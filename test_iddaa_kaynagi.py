
#!/usr/bin/env python3
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE = "https://sportsbookv2.iddaa.com"

CHECKS = [
    {
        "name": "events",
        "path": "/sportsbook/events?st=1&type=0&version=0"
    },
    {
        "name": "competitions",
        "path": "/sportsbook/competitions?st=1"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 YaPaYCiN-SourceCheck/1.2",
    "Accept": "application/json, text/plain, */*"
}


def inspect_events(events):
    result = {
        "events_count": len(events),
        "events_sample": []
    }

    for event in events[:5]:
        if not isinstance(event, dict):
            continue

        sample = {
            key: event.get(key)
            for key in ("i", "hn", "an", "d", "ci")
        }

        markets = event.get("m", [])
        sample["market_count"] = (
            len(markets) if isinstance(markets, list) else 0
        )

        market_samples = []

        if isinstance(markets, list):
            for market in markets[:20]:
                if not isinstance(market, dict):
                    continue

                item = {
                    key: market.get(key)
                    for key in ("t", "st", "sov")
                }

                outcomes = market.get("o", [])

                if isinstance(outcomes, list):
                    item["outcomes"] = [
                        {
                            key: outcome.get(key)
                            for key in ("no", "odd", "n")
                        }
                        for outcome in outcomes[:8]
                        if isinstance(outcome, dict)
                    ]

                market_samples.append(item)

        sample["markets"] = market_samples
        result["events_sample"].append(sample)

    return result


def inspect_event_details(events):
    result = {"detail_samples": []}
    for event in events[:3]:
        if not isinstance(event, dict) or not event.get("i"):
            continue
        url = f"{BASE}/sportsbook/event/{event['i']}"
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        sample = {"event_id": event.get("i"), "home": event.get("hn"), "away": event.get("an")}
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                data = json.loads(response.read().decode("utf-8-sig"))
            payload = data.get("data") if isinstance(data, dict) else None
            markets = payload.get("m", []) if isinstance(payload, dict) else []
            sample["market_count"] = len(markets) if isinstance(markets, list) else 0
            sample["markets"] = [
                {
                    "fields": list(market.keys()),
                    "t": market.get("t"),
                    "st": market.get("st"),
                    "sov": market.get("sov"),
                    "name_fields": {k: market.get(k) for k in ("n", "name", "title", "mn", "sn", "stn", "desc", "label") if market.get(k) is not None},
                    "outcomes": [o.get("n") for o in (market.get("o") or []) if isinstance(o, dict)][:8]
                }
                for market in markets if isinstance(market, dict)
            ]
        except Exception as exc:
            sample["error"] = type(exc).__name__ + ": " + str(exc)
        result["detail_samples"].append(sample)
    return result


def check(item):
    url = BASE + item["path"]

    req = urllib.request.Request(
        url,
        headers=HEADERS,
        method="GET"
    )

    started = time.time()

    result = {
        "name": item["name"],
        "url": url,
        "checked_at_utc": datetime.now(timezone.utc).isoformat()
    }

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read()

            result["http_status"] = response.status
            result["content_type"] = response.headers.get(
                "Content-Type", ""
            )
            result["bytes_read"] = len(body)
            result["elapsed_seconds"] = round(
                time.time() - started, 2
            )

            data = json.loads(body.decode("utf-8-sig"))
            result["valid_json"] = True

            if isinstance(data, dict):
                result["top_level_keys"] = list(data.keys())
                result["is_success"] = data.get("isSuccess")
                payload = data.get("data")

                if item["name"] == "events":
                    if isinstance(payload, dict):
                        result["data_keys"] = list(payload.keys())
                        result["version"] = payload.get("version")
                        result["isdiff"] = payload.get("isdiff")

                        events = payload.get("events")

                        if isinstance(events, list):
                            result.update(inspect_events(events))
                            result.update(inspect_event_details(events))
                        else:
                            result["events_type"] = type(events).__name__
                            result["events_value"] = events

                    elif isinstance(payload, list):
                        result.update(inspect_events(payload))
                        result.update(inspect_event_details(payload))
                    else:
                        result["data_type"] = type(payload).__name__
                        result["data_value"] = payload

                elif isinstance(payload, list):
                    result["competition_count"] = len(payload)

                    if payload and isinstance(payload[0], dict):
                        result["first_competition_sample"] = payload[0]

                else:
                    result["data_type"] = type(payload).__name__

            elif isinstance(data, list):
                result["record_count"] = len(data)

    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
        result["error"] = str(exc)

    except Exception as exc:
        result["error"] = (
            type(exc).__name__ + ": " + str(exc)
        )

    return result


if __name__ == "__main__":
    report = {
        "tool": "YaPaYCiN Iddaa Source Test v1.2",
        "warning": (
            "HTTP access does not establish permission "
            "to bulk collect, archive or redistribute data."
        ),
        "checks": [
            check(item) for item in CHECKS
        ]
    }

    with open(
        "iddaa-kaynak-test-raporu.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        )
    )
