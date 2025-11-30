import smtplib
from email.mime.text import MIMEText
import socket
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

def send_alert():
    ip = get_ip()
    url = f"http://{ip}:8501"
    
    msg_body = f"Morning Briefing Ready.\n\nImpact Report: {url}"
    msg = MIMEText(msg_body)
    msg['Subject'] = "Jetson Intel"
    msg['From'] = config.SMTP_EMAIL
    msg['To'] = config.PHONE_NUMBER

    try:
        print("📨 Sending SMS...")
        # Using Gmail's SSL port
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(config.SMTP_EMAIL, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_EMAIL, config.PHONE_NUMBER, msg.as_string())
        server.quit()
        print("✅ SMS Sent!")
    except Exception as e:
        print(f"❌ SMS Failed: {e}")

if __name__ == "__main__":
    send_alert()
