import os
from datetime import datetime, timedelta, timezone

NOW = datetime.now(timezone.utc)

DEMO_ITEMS = [
    {
        "platform": "Reddit",
        "title": "Should investors change SIP behaviour during a drawdown?",
        "text": "Investors discuss whether to stop, reduce or continue SIPs.",
        "url": "https://www.reddit.com/",
        "published": NOW - timedelta(days=2),
        "engagement": 510,
        "velocity": 77,
        "topic_hint": "SIP behaviour during volatility",
    },
    {
        "platform": "Reddit",
        "title": "Are small caps becoming too expensive?",
        "text": "Investors debate small-cap valuations and allocation.",
        "url": "https://www.reddit.com/",
        "published": NOW - timedelta(days=1),
        "engagement": 700,
        "velocity": 82,
        "topic_hint": "small and mid-cap valuations",
    },
    {
        "platform": "Reddit",
        "title": "How should investors think about a weaker rupee?",
        "text": "Discussion about the rupee, global diversification and Indian assets.",
        "url": "https://www.reddit.com/",
        "published": NOW - timedelta(hours=12),
        "engagement": 620,
        "velocity": 88,
        "topic_hint": "rupee and RBI intervention",
    },
]

def get_items():
    mode = os.getenv("RADAR_MODE", "demo").lower()

    if mode != "live":
        return DEMO_ITEMS, ["Demo mode: using built-in sample data."], None

    try:
        rows, diagnostics = fetch_reddit()
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        return [], [f"Collector crashed — {message}"], message

    keywords = {
        "crude oil and Indian equities": ["crude", "oil", "brent"],
        "rupee and RBI intervention": ["rupee", "rbi", "inr"],
        "mutual fund allocation": ["mutual fund", "sip", "allocation"],
        "small and mid-cap valuations": ["small cap", "mid cap", "valuation"],
        "gold and silver allocation": ["gold", "silver"],
        "global diversification": ["global", "international", "us stocks", "foreign"],
    }

    for row in rows:
        blob = f"{row.get('title', '')} {row.get('text', '')}".lower()

        row["topic_hint"] = next(
            (
                topic
                for topic, words in keywords.items()
                if any(word in blob for word in words)
            ),
            "other finance discussion",
        )

    return rows, diagnostics, None
