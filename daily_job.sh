#!/bin/bash
# Navigate to project folder
cd /home/peter/News-App  # <--- UPDATE THIS PATH to your actual path

# Activate virtual environment
source venv/bin/activate

# Run ingestion
python3 ingest.py

# Send notification
python3 notify.pyy
