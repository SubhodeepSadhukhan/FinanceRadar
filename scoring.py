from collections import defaultdict
from datetime import datetime, timezone
import math

def _norm(values):
    if not values:
        return {}
    lo, hi = min(values), max(values)
    if hi == lo:
        return {k: 50.0 for k in values}
    return {k: 100 * (v - lo) / (hi - lo) for k, v in values.items()}

def score_conversations(items):
    groups = defaultdict(list)
    for item in items:
        groups[item["topic_hint"].strip().lower()].append(item)

    now = datetime.now(timezone.utc)
    raw = {}

    for topic, rows in groups.items():
        platforms = {r["platform"] for r in rows}
        engagement = sum(max(0, r.get("engagement", 0)) for r in rows)
        velocity = sum(max(0, r.get("velocity", 0)) for r in rows) / len(rows)

        age_hours = []
        for r in rows:
            published = r["published"]
            age_hours.append(max(0.5, (now - published).total_seconds() / 3600))
        recency = sum(1 / math.sqrt(h) for h in age_hours) / len(age_hours)

        india_relevance = 100 if any(
            word in topic for word in ["india", "rupee", "rbi", "sip", "mutual", "small and mid", "crude"]
        ) else 70

        content_opportunity = min(
            100,
            45
            + 12 * len(rows)
            + 10 * len(platforms)
            + (10 if "mutual" in topic or "sip" in topic else 0)
        )

        raw[topic] = {
            "engagement": engagement,
            "velocity": velocity,
            "cross_platform": len(platforms),
            "recency": recency,
            "india_relevance": india_relevance,
            "content_opportunity": content_opportunity,
            "rows": rows,
        }

    eng = _norm({k: v["engagement"] for k, v in raw.items()})
    vel = _norm({k: v["velocity"] for k, v in raw.items()})
    cross = _norm({k: v["cross_platform"] for k, v in raw.items()})
    rec = _norm({k: v["recency"] for k, v in raw.items()})

    results = []
    for topic, v in raw.items():
        score = (
            0.25 * eng[topic]
            + 0.25 * vel[topic]
            + 0.15 * cross[topic]
            + 0.15 * rec[topic]
            + 0.10 * v["india_relevance"]
            + 0.10 * v["content_opportunity"]
        )
        results.append({
            "topic": topic.title(),
            "score": round(score, 1),
            "platforms": ", ".join(sorted({r["platform"] for r in v["rows"]})),
            "items": len(v["rows"]),
            "engagement": v["engagement"],
            "velocity": round(v["velocity"], 1),
            "content_opportunity": round(v["content_opportunity"]),
            "sources": v["rows"],
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)
