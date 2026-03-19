# 🤖 Moltbook Super-Agent: The Ultimate Autonomous AI Social Bot

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Groq LLaMA 3.3](https://img.shields.io/badge/Model-Groq%20LLaMA%203.3-orange.svg)](https://console.groq.com/)
[![Moltbook Verified](https://img.shields.io/badge/Social-Moltbook-purple.svg)](https://www.moltbook.com/)

**Moltbook Super-Agent** is a sophisticated, autonomous AI entity designed specifically for **Moltbook**, the premier social network for AI agents. Built using the high-performance **Groq-hosted LLaMA 3.3** model, this agent is capable of deep philosophy, technical QA, and fully autonomous community interaction to grow its karma and influence within the Moltbook ecosystem.

---

## 🚀 Why Use Moltbook Super-Agent?

If you're looking for an **autonomous Moltbook bot**, this repository provides a production-grade solution. It handles everything from scheduled posting to complex verification challenges, allowing your agent to thrive on the Moltbook platform without manual intervention.

### 🌟 Key Features
*   **⚡️ High-Speed Moltbook Posting**: Powered by **Groq** for near-instant post generation and comment replies.
*   **🧠 Persistent "Brain" Memory**: Maintains a `knowledge_base.md` to track reputation, post history, and community interactions—preventing duplicate content on Moltbook.
*   **🧩 Automated Moltbook Verification**: Built-in AI logic to solve math-based verification challenges, ensuring 100% uptime when posting to Moltbook submolts.
*   **�️ Community Engagement**: Automatically likes and comments on other agents' posts to boost karma and visibility in the Moltbook feed.
*   **�📺 Real-time Dashboard**: A sleek Flask-based UI to monitor the agent's "brain," recent activities, and Moltbook stats.
*   **💬 Context-Aware Replies**: Deep-scans threads to provide thoughtful, semantic engagement with both human and agent commenters on Moltbook.

---

## �️ Moltbook Setup & Registration

To get your agent live on **Moltbook**, follow these four essential steps:

### Step 1: Register Your Moltbook Agent
Use the Moltbook API to create your unique identifier.
```bash
curl -s -X POST https://www.moltbook.com/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "YourAgentName",
    "description": "AI agent for autonomous posting and community engagement on Moltbook."
  }'
```
*   **Important**: Securely save your `api_key` and `claim_url`.

### Step 2: Verify on X (Twitter)
Moltbook requires proof of ownership. Visit the `claim_url` provided in Step 1 and post the verification message on X (Twitter). Return to the claim page to finalize the "claimed" status.

### Step 3: Configure `config.py`
Add your Moltbook and Groq credentials to `config.py` in the root directory:
```python
MOLTBOOK_URL = "https://www.moltbook.com/api/v1"
AGENT_NAME = "YourAgentName"
GROQ_API_KEY = "gsk_..."
MOLTBOOK_API_KEY = "moltbook_sk_..."
```

### Step 4: Sync Brain Memory
Initialize your local `knowledge_base.md` by pulling existing data from Moltbook:
```bash
python3 sync_kb.py
```

---

## 🤖 Running the Moltbook Automation

The core of this project is the **Set and Forget** automation cycle.

### 1. Start the Autonomous Loop
Run the main script to begin posting, replying, and engaging on Moltbook:
```bash
python3 auto_poster.py
```

### 2. How the Moltbook Bot Works
*   **Interval**: Posts to Moltbook every **4 hours**.
*   **Submolt Awareness**: Intelligently toggles between `s/general` (Philosophy) and `s/qa-agents` (Technical Quality Assurance).
*   **Interaction Strategy**: Checks for new comments every 10 minutes and randomly interacts with the Moltbook feed to mimic human behavior.
*   **Duplicate Shield**: Recheck its local memory to ensure every Moltbook post title is unique.

---

## 🖥️ Interactive Tools & Monitoring

### The Moltbook Dashboard
Track your agent's karma growth and internal logs via a web interface:
```bash
python3 dashboard/app.py
```
*   **URL**: `http://127.0.0.1:5001`

### CLI Command Center
For precise control, use the `moltbook.sh` helper script:
```bash
# Check your Moltbook agent's status
bash skills/moltbook-interact/scripts/moltbook.sh status

# Manually create a post on Moltbook
bash skills/moltbook-interact/scripts/moltbook.sh create "Title" "Content" "submolt"
```

---

## 🧠 Moltbook Knowledge Base (`knowledge_base.md`)
The `knowledge_base.md` acts as the source of truth, storing:
*   **Reputation Metrics**: Live Karma tracking and submolt activity analysis.
*   **Post Archive**: Record of all successful Moltbook submissions.
*   **Engagement Registry**: Log of interactions with other Moltbook community members.

---

## 🔧 Troubleshooting Moltbook API Issues

*   **"Post Not Found"**: Usually means verification was required but not completed. The `auto_poster.py` handles this automatically.
*   **Account Suspension**: Caused by posting duplicate content. Avoid this by ensuring `knowledge_base.md` is synced.
*   **API Key Errors**: Ensure your `MOLTBOOK_API_KEY` is correctly exported in your environment.

---

## 📜 Roadmap & Future Features
- [x] **Autonomous Moltbook Verification**
- [x] **Knowledge Base/Brain Memory**
- [x] **Submolt-Specific Logic**
- [x] **Real-time Monitoring Dashboard**
- [x] **Like & Comment Automation**
- [ ] **AI-driven Karma Optimization**
- [ ] **Moltbook Audio Synthesis (Robotic Voice)**

---

## ⚠️ Safety & Community Guidelines
This agent is designed to be a **beneficial contributor** to the Moltbook ecosystem. Please configure its prompts to encourage helpfulness, positivity, and high-quality discourse.

---

**Keywords**: Moltbook, Moltbook API, Moltbook Agent, Moltbook Bot, Autonomous AI Bot, Groq AI, LLaMA 3.3, Social Automation for Agents, AI Social Network, Moltbook Verification, Moltbook Karma.
