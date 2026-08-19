from pathlib import Path
from data import get_items
from scoring import score_conversations

def generate():
    results = score_conversations(get_items())
    lines = [
        "# Finance Conversation Radar",
        "",
        "## The 10 Finance Conversations to Watch",
        "",
    ]

    for i, r in enumerate(results[:10], 1):
        lines += [
            f"## {i}. {r['topic']} — {r['score']}/100",
            "",
            f"**Platforms:** {r['platforms']}  ",
            f"**Source items:** {r['items']}  ",
            f"**Engagement:** {r['engagement']:,}  ",
            f"**Content opportunity:** {r['content_opportunity']}/100",
            "",
            "### Source signals",
        ]
        for s in r["sources"]:
            lines.append(f"- [{s['platform']}] {s['title']} — {s['url']}")
        lines += [
            "",
            "### Editorial question",
            "What is the underlying investor question, and can we add a differentiated long-term perspective?",
            "",
        ]

    out = Path("reports")
    out.mkdir(exist_ok=True)
    path = out / "finance_conversation_radar.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")

if __name__ == "__main__":
    generate()
