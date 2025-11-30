import requests
import socket
import sqlite3
import datetime
import config

def get_ip():
    """Finds the local IP address of the Jetson."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually connect, just determines route
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_daily_stats():
    """Check the DB for today's news stats."""
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    
    # Count total and critical
    c.execute("SELECT COUNT(*) FROM articles WHERE date = ?", (today,))
    total = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM articles WHERE date = ? AND impact_score >= 7", (today,))
    critical = c.fetchone()[0]
    
    conn.close()
    return total, critical

def send_alert():
    total, critical = get_daily_stats()
    
    if total == 0:
        print("📭 No news today. Skipping Notification.")
        return

    # Prefer the Tailscale IP if set, otherwise fall back to auto-detect
    if config.TAILSCALE_IP:
        ip = config.TAILSCALE_IP
    else:
        ip = get_ip()

    url = f"http://{ip}:8501"

    # Dynamic Message based on urgency
    if critical > 0:
        title = f"🚨 {critical} Critical Updates"
        message = f"Morning Briefing Ready.\n\n🔥 {critical} Critical Items\n📰 {total} Total Articles"
        priority = 1 # High priority (red background in Pushover)
    else:
        title = "☕ Morning Briefing"
        message = f"Morning Briefing Ready.\n\n📰 {total} New Articles"
        priority = 0 # Normal priority

    # Send via Pushover
    payload = {
        "token": config.PUSHOVER_API_TOKEN,
        "user": config.PUSHOVER_USER_KEY,
        "title": title,
        "message": message,
        "url": url,
        "url_title": "Open Dashboard",
        "priority": priority
    }

    try:
        print(f"📨 Sending Pushover Notification...")
        r = requests.post("https://api.pushover.net/1/messages.json", data=payload)
        if r.status_code == 200:
            print("✅ Notification Sent!")
        else:
            print(f"❌ Pushover Error: {r.text}")
    except Exception as e:
        print(f"❌ Network Error: {e}")

if __name__ == "__main__":
    send_alert()
