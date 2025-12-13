# ☕ Jetson Morning Briefing Agent

**A private, self-hosted AI news analyst for the NVIDIA Jetson Orin Nano.**

This application autonomously searches for news using the Tavily API, analyzes articles with a local Large Language Model (Qwen 2.5 via Ollama), and delivers personalized briefings via **Pushover** notifications and a Streamlit web dashboard. Multiple personas are supported, each receiving a customized impact score based on their unique interests.

---

## 🚀 Key Features

*   **100% Local AI:** All inference runs on-device using Ollama + Qwen 2.5:7b. No data sent to OpenAI or external LLM APIs.
*   **Multi-Persona Analysis:** Define multiple users (e.g., "Peter", "Maddie") with different interests. Each article is scored (0-10) independently for each persona.
*   **Intelligent Scraping:** Uses Tavily API for news discovery and Trafilatura + Jina AI for robust content extraction.
*   **Dark-Mode Dashboard:** Sleek Streamlit UI with topic tags, impact badges, and per-persona filtering.
*   **Push Notifications:** Pushover alerts with daily stats and direct dashboard links.
*   **Production-Ready:** Runs as a systemd service with auto-restart and cron-based daily ingestion.

---

## 🏗️ Architecture

### Data Flow
1.  **News Discovery:** `ingest.py` queries Tavily API with topics from `config.py` (e.g., "AI model releases", "stock market tech sector").
2.  **Content Extraction:** Falls back from Jina AI → Trafilatura for full article text.
3.  **AI Analysis:** Ollama (Qwen 2.5:7b) generates:
    - Article summary (3-4 key facts)
    - Topic tags
    - Per-persona impact scores + reasoning
4.  **Storage:** SQLite database (`news.db`) with indexed tables for articles and impacts.
5.  **Notifications:** `notify.py` sends daily Pushover alerts with critical article counts.
6.  **Dashboard:** Streamlit app (`app.py`) displays all articles with filtering and persona-specific impact scores.

### Components
- **`ingest.py`**: Core ingestion engine (Tavily → Ollama → SQLite)
- **`notify.py`**: Pushover notification sender
- **`app.py`**: Streamlit dashboard
- **`config.py`**: Personas, search topics, Ollama settings
- **`daily_job.sh`**: Cron wrapper script (runs ingestion + notification + health check)
- **`jetson-briefing.service`**: systemd service for 24/7 dashboard uptime

---

## 🛠️ Prerequisites

### Hardware
- **NVIDIA Jetson Orin Nano** (8GB recommended) or any Linux machine with GPU
- Ollama requires ~4GB VRAM for Qwen 2.5:7b

### Software Dependencies
- **Python 3.10+**
- **Ollama** (running locally, tested with Docker)
- **Tavily API Account** (free tier sufficient) - [tavily.com](https://tavily.com)
- **Pushover Account** (one-time $5 purchase) - [pushover.net](https://pushover.net)
- **Tailscale** (optional, for remote access) - [tailscale.com](https://tailscale.com)

---

## ⚙️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/pterbrwn/News-App.git
cd News-App
```

### 2. Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Note:** `requirements.txt` includes:
- `streamlit`, `pandas` (dashboard)
- `tavily-python` (news search)
- `trafilatura` (content extraction)
- `requests`, `python-dotenv`

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:

```ini
# Pushover (Required)
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_API_TOKEN=your_api_token

# Tavily API (Required)
TAVILY_API_KEY=your_tavily_key

# Tailscale IP (Optional - leave empty for auto-detect)
TAILSCALE_IP=100.x.x.x
```

### 4. Configure Personas and Topics
Edit `config.py` to customize:

```python
SEARCH_TOPICS = [
    "Top breaking news headlines global and US today",
    "Latest artificial intelligence LLM model releases",
    "Stock market tech sector performance"
]

PERSONAS = {
    "Peter": """
    Role: Sr. Technical Product Owner at Meijer
    Interests: AI/ML, stock market, geopolitics
    Dislikes: Opinion pieces, gossip
    """,
    "Maddie": """
    Role: High School Spanish Teacher
    Interests: Local news, education policy
    Dislikes: Technical stock details
    """
}
```

### 5. Start Ollama
Ensure Ollama is running with Qwen 2.5:

```bash
# If using Docker:
docker ps | grep ollama

# Pull the model (one-time):
docker exec -it ollama ollama pull qwen2.5:7b

# Or if running natively:
ollama serve &
ollama pull qwen2.5:7b
```

The app expects Ollama at `http://localhost:11434/api/generate` (configurable in `config.py`).

---

## 🏃 Usage

### Manual Test Run
```bash
source venv/bin/activate
./daily_job.sh
```

This will:
1. Run ingestion (fetch + analyze news)
2. Send Pushover notification
3. Check systemd service health

### Production Deployment

#### Dashboard as systemd Service
Keep the Streamlit dashboard running 24/7:

```bash
# Copy service file
sudo cp jetson-briefing.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable jetson-briefing.service

# Start now
sudo systemctl start jetson-briefing.service

# Check status
sudo systemctl status jetson-briefing.service

# View logs
sudo journalctl -u jetson-briefing.service -f
```

**Access dashboard:** `http://localhost:8501` or `http://<TAILSCALE_IP>:8501`

#### Daily Automation (Cron)
Add to your crontab (`crontab -e`):

```bash
# Run ingestion every morning at 8:00 AM
0 8 * * * /bin/bash /home/peter/News-App/daily_job.sh >> /home/peter/News-App/cron.log 2>&1
```

**Important:** `daily_job.sh` attempts to restart the systemd service if it detects it's down. To avoid password prompts, add this sudoers rule:

```bash
# Run: sudo visudo
peter ALL=(root) NOPASSWD: /bin/systemctl restart jetson-briefing.service
```

---

## 🧠 How It Works

### Ingestion Pipeline (`ingest.py`)
1. **Tavily Search:** Queries Tavily API with each topic from `config.py` (last 24 hours, top 3 results per topic)
2. **Content Extraction:** 
   - Try Jina AI reader (`https://r.jina.ai/<url>`)
   - Fallback to Trafilatura for local extraction
3. **AI Analysis (Ollama):**
   - **Summary:** 3-4 bullet points of key facts (no markdown)
   - **Topics:** Comma-separated tags (e.g., "AI, Stocks, Regulation")
   - **Impact Scoring:** For each persona:
     - Score 0-10 based on relevance to their interests
     - Reasoning sentence explaining why it matters
4. **Database Storage:** Articles and impacts saved to SQLite with deduplication

### Scoring Guide
- **0-1:** Irrelevant noise (celebrity gossip, unrelated sports)
- **2-4:** Awareness only, no personal impact
- **5-7:** Professionally/personally relevant (most articles)
- **8-9:** Direct impact requiring attention
- **10:** Critical, life-altering event

### Notifications (`notify.py`)
- Checks SQLite for today's articles
- Counts critical items (score ≥ 7) per persona
- Sends Pushover notification with:
  - Total article count
  - Per-persona critical counts
  - Direct link to dashboard

### Dashboard (`app.py`)
- Persona filter sidebar
- Articles sorted by impact score (descending)
- Color-coded badges: Critical (8+), High (5-7), Low (<5)
- Collapsible cards with summaries and AI reasoning
- Topic tags for quick scanning

---

## 📁 Project Structure

```
News-App/
├── app.py                      # Streamlit dashboard
├── ingest.py                   # News ingestion engine
├── notify.py                   # Pushover notification sender
├── config.py                   # Personas, topics, Ollama config
├── daily_job.sh                # Cron wrapper script
├── jetson-briefing.service     # systemd service definition
├── requirements.txt            # Python dependencies
├── .env                        # Secrets (gitignored)
├── .env.example                # Template for secrets
├── cron_schedule.txt           # Example crontab entry
├── news.db                     # SQLite database (auto-created)
└── models/                     # Optional local model storage
    └── qwen2.5-3b-instruct-q5_k_m.gguf
```

---

## 🔧 Configuration Reference

### `config.py` Key Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_URL` | Ollama API endpoint | `http://localhost:11434/api/generate` |
| `OLLAMA_MODEL` | Model name | `qwen2.5:7b` |
| `SEARCH_TOPICS` | List of news queries | See `config.py` |
| `PERSONAS` | Dict of persona names → descriptions | Peter, Maddie |
| `DB_NAME` | SQLite database file | `news.db` |

### Environment Variables (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `PUSHOVER_USER_KEY` | ✅ Yes | Your Pushover user key |
| `PUSHOVER_API_TOKEN` | ✅ Yes | Your Pushover app token |
| `TAVILY_API_KEY` | ✅ Yes | Tavily search API key |
| `TAILSCALE_IP` | ❌ No | Tailscale IP (auto-detects if empty) |

---

## 🚨 Troubleshooting

### Ollama Connection Errors
```bash
# Check if Ollama is running:
curl http://localhost:11434/api/generate

# If using Docker:
docker logs ollama

# Ensure model is pulled:
ollama list
```

### Systemd Service Won't Start
```bash
# Check logs:
sudo journalctl -u jetson-briefing.service -n 50

# Common issues:
# - Port 8501 already in use (kill other Streamlit instances)
# - Virtual environment path incorrect (edit jetson-briefing.service)
```

### Cron Job Not Running
```bash
# Check cron logs:
tail -f /home/peter/News-App/cron.log

# Verify crontab:
crontab -l

# Test script manually:
cd /home/peter/News-App && bash daily_job.sh
```

### No Articles Found
- Verify Tavily API key is correct (`.env`)
- Check `ingest.log` for errors
- Try running `ingest.py` directly: `python3 ingest.py`

---

## 📄 License

This project is open-source under the MIT License. Feel free to fork and customize for your own daily intelligence needs.

---

## 🙏 Acknowledgments

- **Ollama** for local LLM inference
- **Tavily** for news search API
- **Streamlit** for rapid dashboard prototyping
- **Pushover** for reliable mobile notifications
