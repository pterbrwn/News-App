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

# 4. Self-Healing: Ensure Dashboard is Up
if ! pgrep -f "streamlit run app.py" > /dev/null; then
    echo "🔄 Dashboard down. Restarting..."
    nohup streamlit run app.py --server.port 8501 > streamlit.log 2>&1 &
else
    echo "✅ Dashboard is running."
fi
