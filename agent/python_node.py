"""
Autopsy Labs - Data Fetcher Node
=================================
Fetches real incident data from Slack and GitHub
before passing to the AI reasoning model.

This runs as a Python Code Block inside Airia.
Credentials are injected via Airia's credential store.
"""

import urllib.request
import json


def fetch_slack_messages(slack_token: str, channel_id: str, limit: int = 50) -> list:
    """Fetch recent messages from a Slack channel."""
    req = urllib.request.Request(
        f"https://slack.com/api/conversations.history?channel={channel_id}&limit={limit}",
        headers={"Authorization": f"Bearer {slack_token}"}
    )
    messages = []
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
            if data.get("ok") and data.get("messages"):
                for msg in reversed(data["messages"]):
                    text = msg.get("text", "").strip()
                    if text:
                        messages.append(text)
            elif not data.get("ok"):
                messages.append(f"Slack API error: {data.get('error', 'unknown')}")
    except Exception as e:
        messages.append(f"Slack fetch error: {str(e)}")
    return messages


def fetch_github_commits(github_token: str, repo: str, per_page: int = 10) -> list:
    """Fetch recent commits from a GitHub repository."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/commits?per_page={per_page}",
        headers={
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AutopsyLabs"
        }
    )
    lines = []
    try:
        with urllib.request.urlopen(req) as r:
            commits = json.loads(r.read())
            for c in commits:
                sha = c["sha"][:7]
                msg = c["commit"]["message"]
                author = c["commit"]["author"]["name"]
                date = c["commit"]["author"]["date"]
                lines.append(f"[{date}] {sha} by {author}: {msg}")
    except Exception as e:
        lines.append(f"GitHub fetch error: {str(e)}")
    return lines


def build_context(slack_messages: list, commits: list, incident_report: str) -> str:
    """Combine all data sources into a single context for the AI model."""
    slack_output = "\n".join(slack_messages) if slack_messages else "No messages found"
    github_output = "\n".join(commits) if commits else "No commits found"

    return f"""=== SLACK #incidents CHANNEL (last 50 messages) ===
{slack_output}

=== GITHUB COMMITS (last 10) ===
{github_output}

=== INCIDENT REPORT ===
{incident_report}"""


# ── Airia Python Node Entry Point ──────────────────────────────────────────
# In Airia, `credentials` and `input` are injected automatically at runtime.
# Replace channel ID and repo with your own values when deploying.

SLACK_CHANNEL_ID = "C0AMS5RRLLC"          # Your Slack #incidents channel ID
GITHUB_REPO = "geeked-anshuk666/autopsy-labs-demo"  # Your GitHub repo

# Load credentials from Airia credential store
github_creds = credentials['autopsy_labs']
github_token = github_creds['data']['accesstoken']

slack_creds = credentials['autopsy_labs_demo']
slack_token = slack_creds['data']['headervalue']

# Fetch data from both sources
slack_messages = fetch_slack_messages(slack_token, SLACK_CHANNEL_ID)
commits = fetch_github_commits(github_token, GITHUB_REPO)

# Build combined context and pass to AI Model node
output = build_context(slack_messages, commits, input)
