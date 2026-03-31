# Autopsy Labs — Architecture

> Autonomous incident post-mortem investigator built on Airia

---

## Agent Flow

```
Input (incident description)
        │
        ▼
┌─────────────────────────────┐
│      Python Code Node       │
│                             │
│  • Calls Slack API          │
│    → fetches #incidents     │
│      channel history        │
│                             │
│  • Calls GitHub REST API    │
│    → fetches recent commits │
│                             │
│  • Combines both into       │
│    structured context       │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   AI Model 1 — GPT-4o mini  │
│   "The Slack Reader & Core" │
│                             │
│  • Receives Slack + GitHub  │
│    data in context          │
│                             │
│  • Uses Sequential Thinking │
│    MCP for step-by-step     │
│    evidence reasoning       │
│                             │
│  • Drafts complete          │
│    6-section post-mortem    │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│    Human Approval Node      │
│         (HITL)              │
│                             │
│  • Engineer reviews draft   │
│  • Approves or rejects      │
│  • Nothing published        │
│    without approval         │
└──────┬──────────────┬───────┘
       │ Approved     │ Denied
       ▼              ▼
┌──────────────┐  ┌──────────┐
│  AI Model 2  │  │  Output  │
│  GPT-5 Nano  │  │(rejected)│
│  "Notion     │  └──────────┘
│  Publisher"  │
│              │
│ • Creates    │
│   Notion page│
│ • Appends    │
│   content    │
│   blocks     │
└──────┬───────┘
       │
       ▼
    Output
(post-mortem live
   in Notion)
```

---

## Data Sources

| Source | Method | What It Provides |
|--------|--------|-----------------|
| Slack #incidents | Python + Slack API (`conversations.history`) | Real timestamps, messages, resolution notes from the incident thread |
| GitHub repo | Python + GitHub REST API (`/commits`) | Commits correlated to the incident window, with SHAs and authors |
| Notion | Notion MCP | Publishing destination for the approved post-mortem |

---

## Models

| Node | Model | Role |
|------|-------|------|
| AI Model 1 | GPT-4o mini | Investigation + post-mortem drafting |
| AI Model 2 | GPT-5 Nano | Notion page formatting + publishing |

---

## MCPs Used

| MCP | Provider | Purpose |
|-----|----------|---------|
| Sequential Thinking | Anthropic | Step-by-step evidence reasoning before drafting |
| Notion MCP | Notion | Automated page creation and block publishing |
| Slack MCP | Slack | Supplemental search (primary fetch done via Python) |

---

## Why Python for Data Fetching?

Airia's MCP tool calling is model-dependent — smaller models tend to skip
tool calls when they believe they can answer from training data.

By fetching Slack and GitHub data in a **Python Code Block** before the AI
model runs, we guarantee real data is always injected into the context —
regardless of model size or tool calling behavior.

This also means the AI Model receives structured, pre-formatted context
rather than having to orchestrate multiple tool calls itself — making
the reasoning step faster, cheaper, and more reliable.

---

## Credential Structure in Airia

```python
# GitHub token
github_creds = credentials['autopsy_labs']
github_token = github_creds['data']['accesstoken']

# Slack Bot token (stored as Authorization header value)
slack_creds = credentials['autopsy_labs_demo']
slack_token = slack_creds['data']['headervalue']
```

---

## Environment Setup

To deploy your own instance of Autopsy Labs:

1. Create an Airia account at [airia.com](https://airia.com)
2. Create a new Project
3. Add your LLM models (GPT-4o mini + GPT-5 Nano)
4. Add credentials:
   - GitHub Personal Access Token (classic, `repo` scope)
   - Slack Bot Token (`xoxb-`, scopes: `channels:history`, `channels:read`, `chat:write`)
   - Notion Integration Secret (`secret_`)
5. Add MCP tools: Sequential Thinking, Notion MCP, Slack MCP
6. Build the agent flow as described above
7. Update `SLACK_CHANNEL_ID` and `GITHUB_REPO` in the Python node
8. Update the Notion page ID in the publisher system prompt
9. Publish to Airia Community

---

## Built For

[Airia AI Agents Hackathon](https://airia-hackathon.devpost.com) — Track 2: Active Agents
