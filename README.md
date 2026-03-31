# Autopsy Labs 🔬

**Autonomous incident post-mortem investigator powered by multi-agent AI.**

Autopsy Labs connects to your Slack and GitHub, fetches real incident data, reasons through the evidence, and generates a complete post-mortem - routed through human approval before publishing to Notion.

[![Hackathon](https://img.shields.io/badge/Airia%20Hackathon-Track%202%3A%20Active%20Agents-blueviolet)](https://airia-hackathon.devpost.com)
[![Platform](https://img.shields.io/badge/Platform-Airia-blue)](https://airia.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Flow](#agent-flow)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Limitations](#limitations)
- [Roadmap](#roadmap)

---

## Overview

Post-mortems are one of the most important engineering practices - and one of the most consistently skipped. Engineers write them from memory at 2am after an incident, already exhausted, context already fading.

Autopsy Labs automates the investigation phase entirely. Given an incident ID, it:

1. Fetches the real Slack incident thread from `#incidents`
2. Pulls GitHub commits made during the incident window
3. Reasons through all evidence using Anthropic's Sequential Thinking
4. Drafts a complete, publication-ready post-mortem
5. Routes the draft through a human engineer for review and approval
6. Publishes the approved report to Notion automatically

The result is a grounded, evidence-backed post-mortem in under 2 minutes - with a human in the loop before anything is published.

---

## Architecture

### System Overview

```mermaid
graph TD
    A([Engineer]) -->|Incident ID| B[Autopsy Labs Agent]

    B --> C{Python Data Fetcher}

    C -->|conversations.history| D[(Slack API)]
    C -->|GET /commits| E[(GitHub REST API)]

    D -->|Raw messages + timestamps| F[Context Builder]
    E -->|Commit SHAs + messages| F

    F -->|Structured context| G[AI Model 1\nGPT-4o mini]

    G <-->|Step-by-step reasoning| H[Sequential Thinking MCP\nAnthropic]
    G <-->|Supplemental search| I[Slack MCP]

    G -->|Draft post-mortem| J{Human Approval\nHITL Node}

    J -->|Approved| K[AI Model 2\nGPT-5 Nano]
    J -->|Denied| L([Rejected\nBack to engineer])

    K <-->|Create page + append blocks| M[(Notion MCP)]

    M -->|Published| N([Post-Mortem Live\nin Notion])
```

### Data Flow

```mermaid
sequenceDiagram
    participant E as Engineer
    participant PY as Python Node
    participant SL as Slack API
    participant GH as GitHub API
    participant AI1 as AI Model 1
    participant ST as Sequential Thinking
    participant HITL as Approval Node
    participant AI2 as AI Model 2
    participant NO as Notion

    E->>PY: Incident INC-2026-001
    PY->>SL: GET conversations.history
    SL-->>PY: Messages with timestamps
    PY->>GH: GET /repos/commits
    GH-->>PY: Commit SHAs + messages
    PY->>AI1: Structured context (Slack + GitHub + incident)

    AI1->>ST: Reason through evidence
    ST-->>AI1: Structured reasoning chain
    AI1-->>HITL: Draft post-mortem (6 sections)

    HITL->>E: Review request
    E-->>HITL: Approve

    HITL->>AI2: Approved post-mortem
    AI2->>NO: POST /pages (create blank page)
    NO-->>AI2: New page ID
    AI2->>NO: POST /blocks/append
    NO-->>E: Post-mortem published
```

### Agent Canvas (Airia)

```mermaid
flowchart LR
    IN([Input]) --> PY[Python Code\nNode]
    PY --> AI1[AI Model 1\nGPT-4o mini]
    AI1 --> AP{Approval\nRequest}
    AP -->|Approved| AI2[AI Model 2\nGPT-5 Nano]
    AP -->|Denied| OUT2([Output\nRejected])
    AI2 --> OUT1([Output\nPublished])

    style IN fill:#e8f4f8
    style OUT1 fill:#d4edda
    style OUT2 fill:#f8d7da
    style AP fill:#fff3cd
```

---

## Agent Flow

### Node 1 - Python Data Fetcher

Runs before any AI model. Guarantees real data is always in the LLM context regardless of model tool-calling reliability.

```
Inputs:  Incident description (from user input)
         credentials dict (Slack Bot Token, GitHub PAT via Airia)

Actions: Calls Slack conversations.history API
           → fetches last 50 messages from #incidents
         Calls GitHub REST API
           → fetches last 10 commits from the repo

Output:  Structured string passed to AI Model 1:

         === SLACK #incidents CHANNEL (last 50 messages) ===
         <raw messages with timestamps>

         === GITHUB COMMITS (last 10) ===
         [2026-03-19T15:58:00Z] 3b952bf by Anshuk Jirli: hotfix: increase DB pool size

         === INCIDENT REPORT ===
         <original user input>
```

### Node 2 - AI Model 1: Core Investigator (GPT-4o mini)

Receives the full combined context. Investigates and drafts the post-mortem.

```
Tools enabled:
  Sequential Thinking MCP  - step-by-step evidence reasoning
  Slack MCP                - supplemental search if needed
  Notion MCP               - available for downstream node

Output: Complete 6-section post-mortem (800+ words minimum)
  - Incident Summary
  - Timeline of Events       (exact Slack timestamps)
  - Root Cause Analysis      (Slack quotes + GitHub commit SHAs as evidence)
  - Contributing Factors
  - Impact Assessment
  - Action Items & Prevention (Immediate / Medium Term / Long Term)
```

### Node 3 - Human Approval (HITL)

Hard gate. Nothing reaches Notion until an engineer explicitly approves.

```
Approved → AI Model 2 (Notion Publisher)
Denied   → Output node (rejection returned to engineer)
```

### Node 4 - AI Model 2: Notion Publisher (GPT-5 Nano)

Receives the approved post-mortem. Publishes to Notion in two API calls.

```
Step 1: POST /pages
        Creates blank page under parent (no children in this call)
        parent: { "page_id": "<your-notion-page-id>" }

Step 2: POST /blocks/{page_id}/children
        Appends paragraph blocks only (≤500 chars each)
        Format: { "object": "block", "type": "paragraph",
                  "paragraph": { "rich_text": [...] } }

Note: Heading blocks are not used - Notion MCP requires
      paragraph-only blocks for reliable publishing.
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent platform | [Airia](https://airia.com) | Orchestration, HITL, credential store, MCP gateway |
| Data fetching | Python 3.x (`urllib`, `json`) | Guaranteed Slack + GitHub data ingestion |
| LLM - investigation | GPT-4o mini | Reasoning, evidence synthesis, post-mortem drafting |
| LLM - publishing | GPT-5 Nano | Notion API formatting and page creation |
| Reasoning | Anthropic Sequential Thinking MCP | Step-by-step evidence analysis |
| Incident data | Slack API (`conversations.history`) | Real incident thread with exact timestamps |
| Commit data | GitHub REST API (`GET /commits`) | Code changes correlated to incident window |
| Publishing | Notion MCP | Automated page creation and content publishing |
| Approval gate | Airia HITL Node | Human review before any publishing occurs |

---

## Prerequisites

- [Airia](https://airia.com) account (free tier sufficient)
- Slack workspace with a `#incidents` channel
- GitHub repository for incident-correlated commits
- Notion workspace with a "Post-Mortem Reports" parent page

### Required API Tokens

| Token | Source | Required Scopes |
|-------|--------|----------------|
| GitHub PAT (classic) | GitHub → Settings → Developer Settings → Tokens (classic) | `repo` |
| Slack Bot Token (`xoxb-`) | api.slack.com/apps → OAuth & Permissions | `channels:history`, `channels:read`, `chat:write`, `search:read` |
| Notion Integration Secret (`secret_`) | notion.so/profile/integrations → New Integration | Read content, Insert content, Update content |

---

## Getting Started

### 1. Clone This Repository

```bash
git clone https://github.com/geeked-anshuk666/autopsy-labs-demo.git
cd autopsy-labs-demo
```

### 2. Create an Airia Project

1. Sign up at [airia.com](https://airia.com)
2. Create a new **Project** → name it `Autopsy Labs`
3. **Models tab** → add `GPT-4o mini` and `GPT-5 Nano`

### 3. Add Credentials in Airia

**MCP & Tools** → **New Tool** → add each credential:

```
GitHub MCP
  Name (credential key): autopsy_labs
  Type: GitHub Access Token
  Token: ghp_your_token_here

Slack MCP
  Name (credential key): autopsy_labs_demo
  Type: Slack Bot Access Token
  Token: xoxb-your-bot-token-here

Notion MCP
  Name (credential key): autopsy_labs_notion
  Type: Notion Integration Secret
  Token: secret_your_notion_token_here
```

### 4. Add MCP Servers

**MCP & Tools** → add from Tool Library:
- `Sequential Thinking MCP` - Anthropic, no auth required
- `Slack MCP` - use `autopsy_labs_demo` credential
- `Notion MCP` - use `autopsy_labs_notion` credential

### 5. Build the Agent Canvas

**Agents** → **Add a New Agent** → build this node chain:

```
Input → Python Code Block → AI Model 1 → Approval Request → AI Model 2 → Output
```

**Python Code Block:**
- Add credentials: `autopsy_labs` (GitHub), `autopsy_labs_demo` (Slack)
- Paste code from [`agent/python_node.py`](agent/python_node.py)
- Update `SLACK_CHANNEL_ID` with your channel ID (see below)
- Update `GITHUB_REPO` with your `owner/repo`

**AI Model 1 - GPT-4o mini:**
- Paste system prompt from [`agent/system_prompt_core.md`](agent/system_prompt_core.md)
- Enable tools: Sequential Thinking MCP, Slack MCP, Notion MCP

**Approval Request Node:**
- Set yourself as approver
- Connect `Approved` → AI Model 2
- Connect `Denied` → Output

**AI Model 2 - GPT-5 Nano:**
- Paste system prompt from [`agent/system_prompt_notion.md`](agent/system_prompt_notion.md)
- Replace `YOUR_NOTION_PAGE_ID_HERE` with your actual Notion page ID
- Enable tools: Notion MCP only

### 6. Connect Notion Integration

Open your "Post-Mortem Reports" page in Notion:
```
... (top right) → Connections → Add connection → Autopsy Labs
```

Get your page ID from the share URL:
```
https://notion.so/Post-Mortem-Reports-328786eb539e80018cd4c8897db1aee9
                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                       This is your page ID (add hyphens):
                                       328786eb-539e-8001-8cd4-c8897db1aee9
```

### 7. Get Your Slack Channel ID

In Slack: right-click `#incidents` → **View channel details** → scroll to bottom → **Channel ID** (format: `C0XXXXXXXXX`)

### 8. Seed the Slack Channel

In `#incidents`, post a realistic incident thread. Example:

```
🚨 INCIDENT INC-2026-001: Database connection pool exhausted
3:42pm - seeing 500 errors on /api/orders endpoint
3:44pm - CPU normal, checking database
3:51pm - confirmed: DB connection pool maxed out at limit of 10
3:58pm - deployed hotfix, increased pool size to 50
4:15pm - all systems normal, incident resolved
4:20pm - root cause confirmed: traffic spike from marketing campaign
```

Invite the bot: `/invite @Autopsy Labs`

### 9. Run the Agent

In the Airia Playground, use this input:

```
Incident INC-2026-001: Database connection pool exhausted. Investigate and generate post-mortem.
```

When the approval notification arrives, review the draft and click **Approve**. The post-mortem will be published to Notion automatically.

---

## Configuration

### Python Node Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_CHANNEL_ID` | `C0AMS5RRLLC` | Slack `#incidents` channel ID |
| `GITHUB_REPO` | `geeked-anshuk666/autopsy-labs-demo` | Target repo in `owner/repo` format |
| `limit` (Slack) | `50` | Max messages to fetch |
| `per_page` (GitHub) | `10` | Max commits to fetch |

### Airia Credential Key Structure

Airia stores credentials with the following structure (verified via diagnostic run):

```python
# GitHub classic PAT
github_token = credentials['autopsy_labs']['data']['accesstoken']

# Slack Bot Token - stored as Authorization header value
slack_token = credentials['autopsy_labs_demo']['data']['headervalue']
```

> **Note:** All credential data keys are lowercase in Airia's store.
> `accesstoken` not `AccessToken`, `headervalue` not `HeaderValue`.

---

## Project Structure

```
autopsy-labs/
│
├── README.md                       # This file
│
├── agent/
│   ├── python_node.py              # Data fetcher - Slack + GitHub via Python
│   ├── system_prompt_core.md       # AI Model 1 system prompt (investigator)
│   └── system_prompt_notion.md     # AI Model 2 system prompt (publisher)
│
├── docs/
│   └── ARCHITECTURE.md             # Extended architecture + design decisions
│
├── incidents/
│   └── INC-2026-001.md             # Demo incident report
│
├── config/
│   └── database.yml                # Updated DB config (referenced in post-mortem)
│
├── middleware/
│   └── db_middleware.py            # Connection timeout fix (referenced in post-mortem)
│
└── queries/
    └── orders.sql                  # Query optimization (referenced in post-mortem)
```

---

### Sample Output

```markdown
# Post-Mortem: INC-2026-001 - 2026-03-19

## Incident Summary
On 2026-03-19 at 3:42 PM, monitoring detected a surge of 500 errors on
/api/orders caused by the DB connection pool reaching its configured limit
of 10 connections. The incident lasted 33 minutes and was triggered by a
traffic spike from a concurrent marketing campaign...

## Timeline of Events
- 15:42 - 500 errors detected on /api/orders
- 15:44 - CPU confirmed normal; database investigation begins
- 15:51 - Root cause identified: connection pool maxed at 10
- 15:58 - Hotfix deployed (commit 3b952bf): pool increased to 50
- 16:15 - All systems normal, incident declared resolved
- 16:20 - Root cause confirmed: marketing campaign traffic spike

## Root Cause Analysis
The database connection pool was statically configured to 10 concurrent
connections - insufficient for peak traffic. Commit 3b952bf
("hotfix: increase DB connection pool size from 10 to 50") confirms
the applied fix. Long-running queries held connections open longer than
expected, compounding pool exhaustion under load...
```

---

## Design Decisions

### Why Python for data fetching instead of MCP tool calling?

During development, smaller models (GPT-5 Nano and occasionally GPT-4o mini) would skip Slack MCP tool calls when the model believed it could generate a plausible answer from its training data. This produced hallucinated timelines that appeared correct but contained fabricated timestamps and events.

By moving data fetching into a **Python Code Block** that executes before the AI model, real data is guaranteed to be in the context on every run. The model cannot bypass it - it receives structured evidence and must reason from it.

**Trade-off:** Data is fetched unconditionally on every run (no dynamic tool selection). For post-mortem generation, this is acceptable - you always want both data sources for a complete investigation.

### Why two AI models instead of one?

Notion's API is strict about block formatting, and mixing content generation with API formatting instructions in a single model produced inconsistent publishing results. Separating into two purpose-built models improved reliability significantly:

- **Model 1** focuses entirely on investigation and reasoning - no API concerns
- **Model 2** focuses entirely on Notion formatting compliance - no reasoning required

### Why GPT-5 Nano for the publisher?

In testing, GPT-5 Nano proved more consistent at following the strict paragraph-only block structure required by the Notion MCP than GPT-4o mini. Since publishing requires precise formatting rather than complex reasoning, the smaller and cheaper model outperformed the larger one for this specific task.

---

## Limitations

- **Single channel scope** - fetches from `#incidents` only. Multi-channel incidents require code changes.
- **Single repository** - GitHub fetch is repo-specific. Cross-service incidents require additional fetches.
- **Flat Notion formatting** - heading blocks cause MCP compatibility errors; all content uses paragraph blocks.
- **Pre-seeded demo data** - real deployment requires an active Slack incident workflow.
- **Email-only HITL notifications** - no Slack DM for the approval request in current implementation.

---

## Roadmap

- [ ] PagerDuty integration - automatic incident triggering without manual input
- [ ] Multi-channel and multi-repo support
- [ ] Slack bot interface - `/postmortem INC-XXX` directly from Slack
- [ ] Pattern analysis across multiple incidents to identify recurring root causes
- [ ] Jira integration - auto-create follow-up tickets from Action Items section
- [ ] Notion heading block support pending MCP compatibility updates
- [ ] Approval via Slack DM instead of email

---

## Built By

**Anshuk Jirli** - Backend & AI Engineer

[![GitHub](https://img.shields.io/badge/GitHub-geeked--anshuk666-181717?logo=github)](https://github.com/geeked-anshuk666)
[![Portfolio](https://img.shields.io/badge/Portfolio-anshuk.dev-blue)](https://geeked-anshuk666.github.io/personal-portfolio-anshuk.dev)

---

## License

MIT - see [LICENSE](LICENSE) for details.

---

*Built for the [Airia AI Agents Hackathon](https://airia-hackathon.devpost.com) - Track 2: Active Agents*
