#!/bin/bash
# Navigate to project folder
cd /home/peter/News-App

# Activate virtual environment
source venv/bin/activate

# 1. Check if Ollama is running (The Brain)
if ! pgrep -x "ollama" > /dev/null && ! docker ps | grep -q ollama; then
    echo "⚠️ Ollama not found! Attempting to start..."
    # Add your start command here if needed, or just warn
fi

# 2. Run Ingestion (The Work)
echo "🚀 Starting Daily Ingestion..."
python3 ingest.py

# 3. Send Notification (The Result)
python3 notify.py

# 4. Self-Healing: Ensure Dashboard is Up (via systemd)
if ! systemctl is-active --quiet jetson-briefing.service; then
    echo "🔄 Dashboard service down. Restarting via systemd..."
    sudo systemctl restart jetson-briefing.service
else
    echo "✅ Dashboard service is running."
fi
