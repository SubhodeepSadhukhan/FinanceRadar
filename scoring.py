from collections import defaultdict
from datetime import datetime, timezone
import math


def _norm(values):
    if not values:
        return {}

    numbers = list(values.values())
    lo = min(numbers)
    hi = max(numbers)

    if hi == lo:
        return {key: 50.0 for key in values}

    return {
        key: 100 * (value - lo) / (hi - lo)
        for key, value in values.items()
    }


def score_conversations(items):
    groups = defaultdict(list)

    for item in items:
        topic = str(item.get("topic_hint") or "Other finance discussion")
        groups[topic].append(item)

    if not groups:
        return []

    now = datetime.now(timezone.utc)
    raw = {}

    for topic, rows in groups.items():
        platforms = {
            row.get("platform", "")
            for row in rows
            if row.get("platform")
        }

        engagement = sum(
            max(0, float(row.get("engagement", 0) or 0))
            for row in rows
        )

        velocity_values = []

        for row in rows:
            published = row.get("published", now)

            if not isinstance(published, datetime):
                published = now

            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)

            age_hours = max(
                0.5,
                (now - published).total_seconds() / 3600,
            )

            supplied = float(row.get("velocity", 0) or 0)

            velocity_values.append(
                supplied
                if supplied
                else float(row.get("engagement", 0) or 0) / age_hours
            )

        velocity = (
            sum(velocity_values) / len(velocity_values)
            if velocity_values
            else 0
        )

        recency_values = []

        for row in rows:
            published = row.get("published", now)

            if not isinstance(published, datetime):
                published = now

            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)

            age_hours = max(
                0.5,
                (now - published).total_seconds() / 3600,
            )

            recency_values.append(1 / math.sqrt(age_hours))

        recency = sum(recency_values) / len(recency_values)

        lower_topic = topic.lower()

        india_relevance = (
            100
            if any(
                word in lower_topic
                for word in [
                    "india",
                    "rupee",
                    "rbi",
                    "sip",
                    "mutual",
                    "small",
                    "crude",
                ]
            )
            else 70
        )

        content_opportunity = min(
            100,
            45
            + 12 * len(rows)
            + 10 * len(platforms)
            + (
                10
                if "mutual" in lower_topic or "sip" in lower_topic
                else 0
            ),
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

    eng = _norm({key: value["engagement"] for key, value in raw.items()})
    vel = _norm({key: value["velocity"] for key, value in raw.items()})
    cross = _norm({key: value["cross_platform"] for key, value in raw.items()})
    rec = _norm({key: value["recency"] for key, value in raw.items()})

    results = []

    for topic, value in raw.items():
        score = (
            0.25 * eng[topic]
            + 0.25 * vel[topic]
            + 0.15 * cross[topic]
            + 0.15 * rec[topic]
            + 0.10 * value["india_relevance"]
            + 0.10 * value["content_opportunity"]
        )

        results.append({
            "topic": topic.title(),
            "score": round(score, 1),
            "platforms": ", ".join(sorted(
                {row.get("platform", "") for row in value["rows"]}
            )),
            "items": len(value["rows"]),
            "engagement": int(value["engagement"]),
            "velocity": round(value["velocity"], 1),
            "content_opportunity": round(value["content_opportunity"]),
            "sources": value["rows"],
        })

    return sorted(
        results,
        key=lambda result: result["score"],
        reverse=True,
    )
