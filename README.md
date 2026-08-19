# Finance Conversation Radar — V1

A weekly intelligence system for finding the 10 finance conversations worth paying attention to, with an initial focus on Indian investors.

## What V1 does

- Combines finance news, Reddit, X and Google Trends adapters
- Clusters items into conversation themes
- Scores conversations on engagement, momentum, cross-platform presence, India relevance and content opportunity
- Produces a weekly Markdown report
- Includes a Streamlit dashboard
- Works immediately in DEMO mode
- Keeps live API credentials server-side via environment variables

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

## Demo vs live mode

The app runs in DEMO mode unless `RADAR_MODE=live`.

For live integrations, set environment variables in a `.env` file or your hosting platform:

```text
RADAR_MODE=live

REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=FinanceConversationRadar/1.0

X_BEARER_TOKEN=

NEWS_RSS_URLS=
```

The current implementation deliberately avoids browser-to-Reddit/X calls. All external requests belong in the server-side collector.

## Generate the weekly report

```bash
python generate_report.py
```

This writes:

`reports/finance_conversation_radar.md`

## Architecture

```text
Sources
  ├── News/RSS
  ├── Reddit API
  ├── X API
  └── Google Trends
        ↓
Collectors
        ↓
Normalised items
        ↓
Topic clustering
        ↓
Conversation scoring
        ↓
Top 10
        ↓
Weekly report + dashboard
```

## Production next step

For a production deployment, schedule `generate_report.py` once per week using GitHub Actions, Cloud Run, Railway, Render, AWS Lambda/EventBridge, or another scheduler.

The key design decision is that credentials and external API calls stay server-side.


## V2 — Live Reddit

V2 adds a server-side Reddit collector. The browser never calls Reddit directly.

### Reddit setup

Create a Reddit developer application and obtain the client ID/secret. The collector uses OAuth and sends the configured user-agent. Reddit's Data API terms require using the provided access information and not masking the OAuth identity/user-agent. See:
https://redditinc.com/policies/data-api-terms

For Streamlit Cloud, add these under **Settings → Secrets**:

```toml
RADAR_MODE = "live"
REDDIT_CLIENT_ID = "..."
REDDIT_CLIENT_SECRET = "..."
REDDIT_USER_AGENT = "FinanceConversationRadar/1.0 by your_username"
```

Then reboot the app.

### What V2 collects

The collector monitors:

- r/IndiaInvestments
- r/IndianStreetBets
- r/MutualFundsIndia
- r/stocks
- r/investing
- r/personalfinance
- r/personalfinanceindia

It also runs finance keyword searches for the last week.

The app deduplicates URLs and calculates an engagement measure from score + comments. For live Reddit data, momentum is initially estimated from engagement relative to post age; a later version can calculate true velocity from stored historical snapshots.

### Important commercial-use note

Before deploying this as a production/commercial monitoring service, review Reddit's current Data API Terms and any applicable commercial-use requirements. Reddit reserves the right to charge fees for future API use and states that commercial uses may require a separate agreement. 
