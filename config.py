import os
from dotenv import load_dotenv

# Load secrets
load_dotenv()

# Secrets
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# Database
DB_NAME = "news.db"

# The "Brain" Settings
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# Feeds (Add your favorites)
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "https://techcrunch.com/feed/",
    "https://news.ycombinator.com/rss",
    "https://www.theverge.com/rss/index.xml"
]

# Your Persona (Tweak this to change how the AI rates news)
USER_PERSONA = """
I am a Sr. Technical Product Owner at Meijer, a Midwest retailer. I work in the Digital IT organization under Scott Pallas. 
I am a white male. 
I am 28 years old. 
I am interested in the stock market for my retirement funds. 
I am interested in the stock market for future investment opportunities. 
I own a rental property on the Northwest side of Grand Rapids, MI. 
I live in Grand Rapids, MI. 
I vote republican, however, I consider myself moderate. 
I do not want opinionated news. 
I do want fact-based news. 
I want to know cause and effect of the news. 
"""
