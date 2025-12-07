import requests
import socket
import sqlite3
import datetime
import config
import logging
from logging.handlers import RotatingFileHandler

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(console_handler)

file_handler = RotatingFileHandler('notify.log', maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

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
    """Check the DB for today's news stats per persona."""
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    
    stats = {}
    total_critical = 0
    
    # Get total articles ingested today
    c.execute("SELECT COUNT(*) FROM articles WHERE date = ?", (today,))
    total_articles = c.fetchone()[0]
    
    # Get stats per persona
    for persona in config.PERSONAS.keys():
        # Join to ensure we only count today's articles
        query = """
            SELECT COUNT(*) FROM article_impacts i
            JOIN articles a ON i.article_link = a.link
            WHERE i.persona = ? AND a.date = ? AND i.impact_score >= 7
        """
        c.execute(query, (persona, today))
        crit_count = c.fetchone()[0]
        stats[persona] = crit_count
        total_critical += crit_count
    
    conn.close()
    return total_articles, total_critical, stats

def send_alert():
    total_articles, total_critical, stats = get_daily_stats()
    
    if total_articles == 0:
        logger.info("📭 No news today. Skipping Notification.")
        return

    # Prefer the Tailscale IP if set, otherwise fall back to auto-detect
    if config.TAILSCALE_IP:
        ip = config.TAILSCALE_IP
    else:
        ip = get_ip()

    url = f"http://{ip}:8501"

    # Build Message
    if total_critical > 0:
        title = f"🚨 {total_critical} Critical Updates"
        priority = 1
    else:
        title = "☕ Morning Briefing"
        priority = 0

    message = f"Morning Briefing Ready.\n📰 {total_articles} New Articles\n\n"
    
    for persona, count in stats.items():
        if count > 0:
            message += f"🔥 {persona}: {count} Critical\n"
        else:
            message += f"✅ {persona}: All Clear\n"

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
        logger.info(f"📨 Sending Pushover Notification...")
        r = requests.post("https://api.pushover.net/1/messages.json", data=payload, timeout=10)
        if r.status_code == 200:
            logger.info("✅ Notification Sent!")
        else:
            logger.error(f"❌ Pushover Error: {r.status_code} - {r.text}")
    except requests.exceptions.Timeout:
        logger.error("❌ Pushover API timeout")
    except Exception as e:
        logger.error(f"❌ Network Error: {e}", exc_info=True)

if __name__ == "__main__":
    send_alert()
