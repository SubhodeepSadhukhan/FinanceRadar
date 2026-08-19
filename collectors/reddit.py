import os
import time
from datetime import datetime, timezone
from typing import List, Dict

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
    "India stocks",
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


def _setting(name: str):
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name)
    except Exception:
        return None


def get_access_token() -> str:
    client_id = _setting("REDDIT_CLIENT_ID")
    client_secret = _setting("REDDIT_CLIENT_SECRET")
    user_agent = _setting("REDDIT_USER_AGENT") or "FinanceConversationRadar/1.0"

    if not client_id or not client_secret:
        raise RedditAPIError(
            "Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET."
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
            f"Reddit token request failed ({response.status_code}): {response.text[:300]}"
        )

    data = response.json()
    return data["access_token"]


def _request(url: str, token: str, params=None):
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
        raise RedditAPIError("Reddit rate limit reached. Try again later.")

    if response.status_code != 200:
        raise RedditAPIError(
            f"Reddit request failed ({response.status_code}): {response.text[:300]}"
        )

    return response.json()


def _normalise(post: dict, subreddit: str) -> dict:
    created = datetime.fromtimestamp(post["created_utc"], tz=timezone.utc)
    return {
        "platform": "Reddit",
        "title": post.get("title", ""),
        "text": post.get("selftext", "")[:3000],
        "url": "https://www.reddit.com" + post.get("permalink", ""),
        "published": created,
        "engagement": int(post.get("score", 0)) + 2 * int(post.get("num_comments", 0)),
        "velocity": 0,
        "upvotes": int(post.get("score", 0)),
        "comments": int(post.get("num_comments", 0)),
        "subreddit": subreddit,
        "topic_hint": "",
    }


def fetch_subreddit_posts(subreddit: str, limit: int = 50) -> List[Dict]:
    token = get_access_token()
    data = _request(
        f"https://oauth.reddit.com/r/{subreddit}/new",
        token,
        {"limit": min(limit, 100), "raw_json": 1},
    )

    rows = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        if post:
            rows.append(_normalise(post, subreddit))
    return rows


def fetch_search(term: str, limit: int = 50) -> List[Dict]:
    token = get_access_token()
    data = _request(
        "https://oauth.reddit.com/search",
        token,
        {
            "q": term,
            "sort": "new",
            "t": "week",
            "limit": min(limit, 100),
            "raw_json": 1,
        },
    )

    rows = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        if post:
            rows.append(_normalise(post, post.get("subreddit", "")))
    return rows


def fetch_reddit(max_per_subreddit: int = 40, search_limit: int = 20) -> List[Dict]:
    all_rows = []
    seen = set()

    for subreddit in SUBREDDITS:
        try:
            rows = fetch_subreddit_posts(subreddit, max_per_subreddit)
        except RedditAPIError:
            continue

        for row in rows:
            if row["url"] not in seen:
                seen.add(row["url"])
                all_rows.append(row)

    for term in SEARCH_TERMS:
        try:
            rows = fetch_search(term, search_limit)
        except RedditAPIError:
            continue

        for row in rows:
            if row["url"] not in seen:
                seen.add(row["url"])
                all_rows.append(row)

    return all_rows
