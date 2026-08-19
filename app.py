import streamlit as st
import pandas as pd
import os
from data import get_items
from scoring import score_conversations

st.set_page_config(
    page_title="Finance Conversation Radar",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Finance Conversation Radar")
st.caption("The 10 finance conversations worth paying attention to this week")

mode = st.sidebar.selectbox("Data mode", ["demo", "live"], index=0)
if mode == "live":
    os.environ["RADAR_MODE"] = "live"
else:
    os.environ["RADAR_MODE"] = "demo"

try:
    items = get_items()
    results = score_conversations(items)
    data_error = None
except Exception as exc:
    items, results = get_items() if mode == "demo" else [], []
    data_error = str(exc)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Conversations detected", len(results))
c2.metric("Source items", len(items))
c3.metric("Platforms", len(set(i["platform"] for i in items)))
c4.metric("Mode", mode.upper())

if data_error:
    st.error(f"Live data could not be loaded: {data_error}")
    st.info("Switch back to DEMO mode while checking your Reddit credentials.")

st.divider()

st.subheader("Top conversations")

for rank, r in enumerate(results[:10], 1):
    with st.container(border=True):
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            st.markdown(f"### #{rank} — {r['topic']}")
            st.write(
                f"**Platforms:** {r['platforms']}  •  "
                f"**Items:** {r['items']}  •  "
                f"**Engagement:** {r['engagement']:,}"
            )
        with col2:
            st.metric("Radar score", r["score"])
        with col3:
            st.metric("Content opp.", f"{r['content_opportunity']}/100")

        st.progress(min(100, int(r["score"])) / 100)

        if rank <= 3:
            st.markdown("**Why this matters:** This conversation has strong momentum and/or cross-platform evidence and is worth investigating for a content angle.")

        with st.expander("View source signals"):
            df = pd.DataFrame([
                {
                    "Platform": s["platform"],
                    "Title": s["title"],
                    "Engagement": s["engagement"],
                    "Velocity": s["velocity"],
                    "Published": s["published"].strftime("%Y-%m-%d %H:%M UTC"),
                    "Source": s["url"],
                }
                for s in r["sources"]
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Content opportunities")

for r in results[:3]:
    st.markdown(
        f"**{r['topic']}** — investigate the underlying investor question, "
        f"the strongest opposing view, and whether there is a differentiated educational angle."
    )

st.info(
    "V1 is running in DEMO mode. The architecture keeps Reddit/X credentials server-side. "
    "Connect live APIs through environment variables when ready."
)
