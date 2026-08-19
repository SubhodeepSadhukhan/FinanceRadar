import os
from datetime import datetime, timezone
import requests

SUBREDDITS = [
    "IndiaInvestments",
    "IndianStreetBets",
    "MutualFundsIndia",
    "stocks",
    "investing",
    "personalfinance",
    "personalfinanceindia",
]

SEARCH_TERMS = [
    "Indian stock market",
    "Nifty",
    "Sensex",
    "mutual funds",
    "SIP",
    "small cap",
    "mid cap",
    "rupee",
    "RBI",
    "gold",
    "US stocks",
    "global investing",
    "asset allocation",
    "retirement",
]


class RedditAPIError(RuntimeError):
    pass


def _setting(name):
    value = os.getenv(name)

    if value:
        return value

    try:
        import streamlit as st
        return st.secrets.get(name)
    except Exception:
        return None


def get_access_token():
    client_id = _setting("REDDIT_CLIENT_ID")
    client_secret = _setting("REDDIT_CLIENT_SECRET")
    user_agent = _setting("REDDIT_USER_AGENT") or "FinanceConversationRadar/1.0"

    if not client_id or not client_secret:
        raise RedditAPIError(
            "Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET in Streamlit Secrets."
        )

    response = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": user_agent},
        timeout=20,
    )

    if response.status_code != 200:
        raise RedditAPIError(
            f"OAuth request returned HTTP {response.status_code}. "
            f"Reddit response: {response.text[:250]}"
        )

    data = response.json()
    token = data.get("access_token")

    if not token:
        raise RedditAPIError(
            "Reddit OAuth response did not contain an access_token."
        )

    return token


def _request(url, token, params=None):
    user_agent = _setting("REDDIT_USER_AGENT") or "FinanceConversationRadar/1.0"

    response = requests.get(
        url,
        params=params or {},
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": user_agent,
        },
        timeout=20,
    )

    if response.status_code == 429:
        raise RedditAPIError("Reddit rate limit reached.")

    if response.status_code != 200:
        raise RedditAPIError(
            f"Reddit request returned HTTP {response.status_code}: "
            f"{response.text[:250]}"
        )

    return response.json()


def _normalise(post, subreddit):
    created = datetime.fromtimestamp(
        float(post.get("created_utc", 0)),
        tz=timezone.utc,
    )

    score = int(post.get("score", 0) or 0)
    comments = int(post.get("num_comments", 0) or 0)

    permalink = post.get("permalink", "")

    if permalink.startswith("http"):
        url = permalink
    else:
        url = "https://www.reddit.com" + permalink

    return {
        "platform": "Reddit",
        "title": post.get("title", ""),
        "text": post.get("selftext", "")[:3000],
        "url": url,
        "published": created,
        "engagement": score + (2 * comments),
        "velocity": 0,
        "upvotes": score,
        "comments": comments,
        "subreddit": subreddit,
        "topic_hint": "",
    }


def fetch_reddit(max_per_subreddit=30, search_limit=15):
    diagnostics = []
    rows = []
    seen = set()

    try:
        token = get_access_token()
        diagnostics.append("OAuth token: OK")
    except Exception as exc:
        diagnostics.append(
            f"OAuth token: FAILED — {type(exc).__name__}: {exc}"
        )
        return [], diagnostics

    for subreddit in SUBREDDITS:
        try:
            data = _request(
                f"https://oauth.reddit.com/r/{subreddit}/new",
                token,
                {
                    "limit": min(max_per_subreddit, 100),
                    "raw_json": 1,
                },
            )

            children = data.get("data", {}).get("children", [])
            diagnostics.append(f"r/{subreddit}: {len(children)} posts")

            for child in children:
                if not isinstance(child, dict):
                    continue

                post = child.get("data", {})

                if not isinstance(post, dict):
                    continue

                row = _normalise(post, subreddit)

                if row["url"] not in seen:
                    seen.add(row["url"])
                    rows.append(row)

        except Exception as exc:
            diagnostics.append(
                f"r/{subreddit}: FAILED — {type(exc).__name__}: {exc}"
            )

    for term in SEARCH_TERMS:
        try:
            data = _request(
                "https://oauth.reddit.com/search",
                token,
                {
                    "q": term,
                    "sort": "new",
                    "t": "week",
                    "limit": min(search_limit, 100),
                    "raw_json": 1,
                },
            )

            children = data.get("data", {}).get("children", [])
            diagnostics.append(f'Search "{term}": {len(children)} posts')

            for child in children:
                if not isinstance(child, dict):
                    continue

                post = child.get("data", {})

                if not isinstance(post, dict):
                    continue

                row = _normalise(post, post.get("subreddit", ""))

                if row["url"] not in seen:
                    seen.add(row["url"])
                    rows.append(row)

        except Exception as exc:
            diagnostics.append(
                f'Search "{term}": FAILED — {type(exc).__name__}: {exc}'
            )

    diagnostics.append(f"Total unique Reddit items: {len(rows)}")

    return rows, diagnostics
