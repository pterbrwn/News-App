import os
from dotenv import load_dotenv

# Load secrets
load_dotenv()

# Secrets
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
TAILSCALE_IP = os.getenv("TAILSCALE_IP")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

# Database
DB_NAME = "news.db"

# The "Brain" Settings
OLLAMA_URL = "http://localhost:11434/api/generate"
# OLLAMA_MODEL = "llama3" # Uncomment this line to use llama3 if desireable
OLLAMA_MODEL = "phi3.5"
# Feeds (Add your favorites)
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml", # Global News
    "https://thehill.com/feed/", # US Politics (Fact-based/Moderate)
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664", # Finance & Markets
    "https://techcrunch.com/feed/", # Tech Industry
    "https://news.google.com/rss/search?q=Grand+Rapids+MI&hl=en-US&gl=US&ceid=US:en" # Local Grand Rapids News
]

# Personas
PERSONAS = {
    "Peter": """
    I am a Sr. Technical Product Owner at Meijer, a Midwest retailer. I work in the Digital IT organization under Scott Pallas. 
    I am a white male. 
    I am 28 years old. 
    I am interested in the stock market for my retirement funds. 
    I am interested in the stock market for future investment opportunities. 
    I am interested in United States politics as it affects my career and investments.
    I am interested in Global politics as it affects my career and investments. 
    I am interested in the technology industry as it affects my career and investments.
    I own a rental property on the Northwest side of Grand Rapids, MI. 
    I live in Grand Rapids, MI. 
    I vote republican, however, I consider myself moderate. 
    I do not want opinionated news. 
    I do want fact-based news. 
    I want to know cause and effect of the news. 
    """,
    
    "Maddie": """
    I am an Education Professional teaching at Northview High School in Grand Rapids, MI. as a spanish teacher.
    I am interested in local news and major global headlines.
    I am interested in how United States politics affects education and community well-being.
    I am interested in how United States politics affect financial markets.
    I am a white female. 
    I am 28 years old. 
    I vote democrat, however, I consider myself moderate. 
    I do not want opinionated news. 
    I do want fact-based news. 
    I want to know cause and effect of the news.
    I care about health, wellness, and travel.
    I do not care deeply about technical details of the stock market or deep tech industry news.
    I want to know about things happening in my community and major world events that might affect my daily life.
    """
}

# End of configuration
