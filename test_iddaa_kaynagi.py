
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
    "User-Agent": "Mozilla/5.0 YaPaYCiN-SourceCheck/1.1",
    "Accept": "application/json, text/plain, */*"
}

def inspect_events(events):
    result = {"events_count": len(events)}

    if not events:
        result["events_sample"] = "Liste boş"
        return result

    event = events[0]

    if isinstance(event, dict):
        result["first_event_keys"] = list(event.keys())

        result["first_event_sample"] = {
            key: event.get(key)
            for key in ("i", "hn", "an", "d", "ci")
        }

        markets = event.get("m", [])

        result["first_event_market_count"] = (
            len(markets) if isinstance(markets, list) else 0
        )

        samples = []

        if isinstance(markets, list):
            for market in markets[:30]:
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
                        for outcome in outcomes[:10]
                        if isinstance(outcome, dict)
                    ]

                samples.append(item)

        result["market_samples"] = samples

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
        with urllib.request.urlopen(req, timeout=25) as response:
            body = response.read(2_000_001)

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
                        else:
                            result["events_type"] = type(events).__name__
                            result["events_value"] = events

                    else:
                        result["data_type"] = type(payload).__name__

                else:
                    if isinstance(payload, list):
                        result["competition_count"] = len(payload)

                        if payload and isinstance(payload[0], dict):
                            result["first_competition_keys"] = list(
                                payload[0].keys()
                            )
                            result["first_competition_sample"] = (
                                payload[0]
                            )

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
        "tool": "YaPaYCiN Iddaa Source Test v1.1",
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
