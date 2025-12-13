# ☕ Jetson Morning Briefing Agent

**A private, self-hosted AI news analyst running on the NVIDIA Jetson Orin Nano.**

This application autonomously scrapes RSS feeds, uses a local Large Language Model (Llama 3 via Ollama) to analyze articles against a specific user persona, and delivers a prioritized daily briefing via **Pushover** notifications and a mobile-responsive web dashboard.

---

## 🚀 Key Features

*   **100% Private & Local:** All AI inference runs on-device using the Jetson's GPU. No data is sent to OpenAI or third-party APIs.
*   **Persona-Driven Analysis:** The AI rates news on a 0-10 scale based on *your* specific interests (defined in a config file) and explains *why* it matters to you.
*   **Deep Intelligence:** Generates "Key Intelligence" summaries (4-6 detailed bullet points) and identifies "Cause & Effect" impacts on your career and investments.
*   **Expert UI:** A sleek, dark-mode dashboard with card-based layouts, topic tagging, and critical alert badges.
*   **Reliable Notifications:** Uses **Pushover** for instant, unblockable push notifications to your phone.
*   **Self-Healing:** Automated watchdog ensures the dashboard is always running and accessible.

## 🏗️ Architecture

1.  **Ingestion:** Python (`feedparser`, `newspaper3k`) fetches articles from configured RSS feeds.
2.  **The Brain:** Articles are sent to **Ollama (Llama 3)** running in a Docker container for analysis.
3.  **Storage:** Processed insights are stored in a local SQLite database (`news.db`) with auto-cleanup of old data.
4.  **Frontend:** A **Streamlit** web application serves a scrollable, prioritized dashboard.
5.  **Access:** Accessible remotely via **Tailscale** VPN.

---

## 🛠️ Prerequisites

*   **Hardware:** NVIDIA Jetson Orin Nano (8GB recommended) or any Linux machine with an NVIDIA GPU.
*   **Software:**
    *   Python 3.10+
    *   [Ollama](https://ollama.com) (Running via Docker with GPU access)
    *   [Tailscale](https://tailscale.com) (For secure remote access)
    *   [Pushover Account](https://pushover.net) (For notifications)

---

## ⚙️ Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/pterbrwn/News-App.git
    cd News-App
    ```

2.  **Set up Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure Secrets (.env)**
    Create a `.env` file in the root directory:
    ```ini
    # Pushover Credentials (https://pushover.net)
    PUSHOVER_USER_KEY=your_user_key
    PUSHOVER_API_TOKEN=your_api_token
    
    # Your Jetson's Tailscale IP
    TAILSCALE_IP=100.x.x.x
    
    # Optional AI dependencies
    TAVILY_API_KEY=your_tavily_api_key
    ```

4.  **Configure Persona (config.py)**
    Edit `config.py` to define who you are. The AI uses this to score relevance.
    ```python
    USER_PERSONA = """
    I am a software engineer interested in AI, edge computing, and geopolitical events.
    I do NOT care about sports or celebrity gossip.
    """
    ```

---

## 🏃 Usage

### Manual Run (Testing)
To trigger the ingestion and notification manually:
```bash
./daily_job.sh
```

### Dashboard (systemd service)
Service mode is the recommended way to keep the Streamlit UI running 24/7. The project ships with `jetson-briefing.service` that wraps `streamlit run app.py`.

```bash
sudo cp jetson-briefing.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable jetson-briefing.service
sudo systemctl start jetson-briefing.service
sudo journalctl -u jetson-briefing.service -f
```
Once the service is active, the dashboard is visible at `http://<TAILSCALE_IP>:8501` or `http://localhost:8501`.

---

## 🤖 Automation (Cron)

The application is designed to run on a schedule. The repository includes a `daily_job.sh` wrapper which handles ingestion, notifications, and ensures the dashboard is running.

**Recommended Crontab Configuration (run as the app owner):**
```bash
# Run the briefing every morning at 7:00 AM
0 7 * * * /bin/bash /home/peter/News-App/daily_job.sh >> /home/peter/News-App/cron.log 2>&1
```

`daily_job.sh` now interacts with the `jetson-briefing.service`. If the service is not active, it automatically restarts it via `sudo systemctl restart jetson-briefing.service`. To avoid password prompts when cron runs this script, consider adding a sudoers rule such as:

```bash
peter ALL=(root) NOPASSWD: /bin/systemctl restart jetson-briefing.service
```

This keeps the systemd service in sync with the ingestion cron without duplicating Streamlit processes.

---

## 🧠 AI Model Setup (Ollama)

Ensure your Docker container has the model pulled:

```bash
# Check if container is running
docker ps

# Pull the model inside the container
docker exec -it ollama ollama pull llama3
```

---

## 📄 License

This project is open-source. Feel free to fork and modify for your own daily intelligence needs.
