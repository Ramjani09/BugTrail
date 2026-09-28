# BugTrail 🐛🧠
> **AI Bug Investigation Memory Agent for Software Development Teams**

BugTrail is an AI bug-investigation memory agent that helps software development teams resolve recurring bugs faster by recalling past root causes and proven fixes stored in **Hindsight Cloud**.

---

## 💡 Why Persistent Memory Matters

When production bugs strike, engineering teams often spend hours re-diagnosing issues that were already resolved in previous deployments or sprints. Traditional LLMs lack long-term memory across developer sessions and cannot recall past team incident post-mortems.

**BugTrail solves this using Hindsight Cloud:**
1. **Retain Experience**: When a developer resolves a bug, the resolution (root cause, fix, context, lesson) is retained in Hindsight.
2. **Recall Context**: When a new or recurring bug appears, BugTrail queries Hindsight for past similar incidents.
3. **Memory-Guided Reasoning**: The AI LLM incorporates recalled memories into its reasoning context, prioritizing checks that fixed similar bugs in the past.

---

## 🏗️ Architecture

```
Frontend (HTML / CSS / JS Dark Dashboard)
   ↓
FastAPI Backend (/api/investigate, /api/resolve)
   ↓
BugTrail AI Agent
   ↓
Hindsight Memory (bugtrail-memory bank)
   ↓
Relevant Past Bug Experiences
   ↓
LLM Reasoning (Google Gemini 2.5 Flash / Demo Mode)
   ↓
Investigation Recommendation
```

---

## 🧠 Hindsight SDK Integration

BugTrail uses the official `hindsight-client` Python SDK (`base_url="https://api.hindsight.vectorize.io"`).

### 1. Store Memory (`retain`)
When a bug resolution is saved:
```python
client.retain(
    bank_id="bugtrail-memory",
    content="[BUG INCIDENT]: API returns HTTP 500...\n[ROOT CAUSE]: Incorrect DB config...\n[FIX APPLIED]: Restored DB config...",
    metadata={"type": "bug_resolution"}
)
```

### 2. Retrieve Memory (`recall`)
When investigating a new bug report:
```python
res = client.recall(
    bank_id="bugtrail-memory",
    query="API returns HTTP 500 after deployment",
    budget="mid"
)
```

---

## ⚡ Hackathon Demo Flow

1. **Bug 1 (Initial Incident)**:
   - **Title**: `API returns HTTP 500 after deployment`
   - **Recent Change**: `Database configuration was modified during deployment.`
   - **Result**: Standard heuristic investigation recommendation (no prior memory in Hindsight).
2. **Resolve & Retain Bug 1**:
   - **Root Cause**: `Incorrect database configuration after deployment.`
   - **Fix**: `Restored the correct database configuration.`
   - Click **"Save Resolution to Memory"** -> Hindsight retains the bug resolution.
3. **Bug 2 (Recurring Incident)**:
   - **Title**: `API returns HTTP 500 again after deployment`
   - **Recent Change**: `Deployment configuration changed.`
   - Click **"Investigate Bug"** -> BugTrail recalls Bug 1 from Hindsight and **prominently displays the past experience** in the Memory Panel!
   - **AI Recommendation**: Prioritizes checking database configuration first based on past experience.

---

## ⚙️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and fill in your keys:
```env
HINDSIGHT_API_KEY=your_hindsight_cloud_api_key
GEMINI_API_KEY=your_gemini_api_key
```

> **Note**: If API keys are omitted, BugTrail gracefully runs in **Demo Mode** with clear UI badges indicating status.

---

## 🚀 How to Run

Run using Python:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Or run the batch launcher on Windows:
```cmd
run.bat
```

Open your browser at:
`http://localhost:8000`

---

## 📸 Screenshots & UI Preview
*(Placeholder for UI screenshots of BugTrail Dark Dashboard)*

---

## 📜 License
MIT License - Built for Hackathon MVP
