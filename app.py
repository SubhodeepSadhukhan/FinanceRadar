import os
import streamlit as st
import pandas as pd

from data import get_items
from scoring import score_conversations

st.set_page_config(
    page_title="Finance Conversation Radar",
    page_icon="📡",
    layout="wide",
)

st.title("📡 Finance Conversation Radar")
st.caption("The 10 finance conversations worth paying attention to this week")

with st.sidebar:
    st.header("Data")
    mode = st.selectbox("Data mode", ["LIVE", "DEMO"], index=0)
    st.caption("LIVE connects to Reddit. DEMO uses sample data.")

os.environ["RADAR_MODE"] = mode.lower()

items, diagnostics, fatal_error = get_items()
results = score_conversations(items)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Conversations detected", len(results))
c2.metric("Source items", len(items))
c3.metric("Platforms", len(set(i.get("platform", "") for i in items)) if items else 0)
c4.metric("Mode", mode)

if fatal_error:
    st.error(f"Live data could not be loaded: {fatal_error}")

if mode == "LIVE":
    with st.expander("Reddit connection diagnostics", expanded=True):
        for line in diagnostics:
            if "FAILED" in line:
                st.error(line)
            elif "OK" in line:
                st.success(line)
            else:
                st.write(line)

st.divider()
st.subheader("Top conversations")

if not results:
    st.warning("No conversations were returned. Check the Reddit diagnostics above.")
else:
    for rank, r in enumerate(results[:10], 1):
        with st.container(border=True):
            col1, col2, col3 = st.columns([5, 1, 1])

            with col1:
                st.markdown(f"### #{rank} — {r['topic']}")
                st.write(
                    f"**Platforms:** {r['platforms']}  •  "
                    f"**Source items:** {r['items']}  •  "
                    f"**Engagement:** {r['engagement']:,}"
                )

            with col2:
                st.metric("Radar score", r["score"])

            with col3:
                st.metric("Content opp.", f"{r['content_opportunity']}/100")

            st.progress(min(100, int(r["score"])) / 100)

            with st.expander("View source signals"):
                source_rows = []
                for source in r["sources"]:
                    source_rows.append({
                        "Platform": source.get("platform", ""),
                        "Subreddit": source.get("subreddit", ""),
                        "Title": source.get("title", ""),
                        "Upvotes": source.get("upvotes", ""),
                        "Comments": source.get("comments", ""),
                        "Engagement": source.get("engagement", ""),
                        "Published": str(source.get("published", "")),
                        "URL": source.get("url", ""),
                    })

                st.dataframe(
                    pd.DataFrame(source_rows),
                    width="stretch",
                    hide_index=True,
                )

st.divider()
st.subheader("Content opportunities")

if results:
    for r in results[:3]:
        st.markdown(
            f"**{r['topic']}** — investigate the underlying investor question, "
            "the strongest opposing view, and whether there is a differentiated educational angle."
        )
else:
    st.info("No content opportunities until live data is available.")

if mode == "DEMO":
    st.info("DEMO mode is using built-in sample data.")
