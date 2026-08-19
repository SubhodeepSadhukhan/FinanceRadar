import os
from datetime import datetime, timedelta, timezone

NOW = datetime.now(timezone.utc)

DEMO_ITEMS = [
    {
        "platform": "News",
        "title": "Indian shares face pressure as higher crude and Treasury yields weigh",
        "text": "Indian equities are under pressure as crude oil rises and global yields remain elevated.",
        "url": "https://www.reuters.com/",
        "published": NOW - timedelta(hours=2),
        "engagement": 920, "velocity": 88, "topic_hint": "crude oil and Indian equities",
    },
    {
        "platform": "News",
        "title": "RBI intervention keeps the rupee steadier amid oil pressure",
        "text": "Traders are watching RBI intervention as oil prices and global yields pressure the rupee.",
        "url": "https://www.reuters.com/",
        "published": NOW - timedelta(hours=5),
        "engagement": 760, "velocity": 81, "topic_hint": "rupee and RBI intervention",
    },
    {
        "platform": "News",
        "title": "Mutual fund investors debate allocation amid market volatility",
        "text": "Retail investors are weighing SIP discipline and asset allocation during volatility.",
        "url": "https://www.reuters.com/",
        "published": NOW - timedelta(hours=10),
        "engagement": 680, "velocity": 69, "topic_hint": "mutual fund allocation",
    },
    {
        "platform": "Reddit",
        "title": "Should investors change SIP behaviour during a drawdown?",
        "text": "Investors discuss whether to stop, reduce or continue SIPs.",
        "url": "https://www.reddit.com/",
        "published": NOW - timedelta(days=2),
        "engagement": 510, "velocity": 77, "topic_hint": "SIP behaviour during volatility",
    },
    {
        "platform": "X",
        "title": "Finance creators debate whether crude changes India's market outlook",
        "text": "Posts connect oil prices with inflation, the rupee, margins and equity valuations.",
        "url": "https://x.com/",
        "published": NOW - timedelta(hours=8),
        "engagement": 1380, "velocity": 94, "topic_hint": "crude oil and Indian equities",
    },
]

def get_items():
    mode = os.getenv("RADAR_MODE", "demo").lower()
    if mode != "live":
        return DEMO_ITEMS

    from collectors.reddit import fetch_reddit
    rows = fetch_reddit()

    # Give the scoring layer a topic hint based on the post title/text.
    keywords = {
        "crude oil": ["crude", "oil", "brent"],
        "rupee and RBI intervention": ["rupee", "rbi", "inr"],
        "mutual fund allocation": ["mutual fund", "sip", "allocation"],
        "small and mid-cap valuations": ["small cap", "mid cap", "valuation"],
        "gold and silver allocation": ["gold", "silver"],
        "global diversification": ["global", "international", "us stocks", "foreign"],
    }

    for row in rows:
        blob = (row["title"] + " " + row["text"]).lower()
        row["topic_hint"] = next(
            (topic for topic, words in keywords.items() if any(w in blob for w in words)),
            "other finance discussion",
        )

    return rows
