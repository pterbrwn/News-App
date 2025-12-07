import os
from dotenv import load_dotenv

# Load secrets
load_dotenv()

# Secrets
TAILSCALE_IP = os.getenv("TAILSCALE_IP")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Validate required secrets
required_secrets = {
    "PUSHOVER_USER_KEY": PUSHOVER_USER_KEY,
    "PUSHOVER_API_TOKEN": PUSHOVER_API_TOKEN,
    "TAVILY_API_KEY": TAVILY_API_KEY
}

missing = [k for k, v in required_secrets.items() if not v]
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Database
DB_NAME = "news.db"

# The "Brain" Settings
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"  # Best balance: powerful reasoning + fits Jetson 8GB RAM

# What you want the agent to search for every morning

SEARCH_TOPICS = [
    "Top breaking news headlines global and US today",
    "Latest artificial intelligence LLM model releases and benchmarks",
    "Stock market tech sector performance and major moves today",
    "Local news and events in Grand Rapids, MI today"
]

# Personas
PERSONAS = {
     "Peter": """
    Role: Sr. Technical Product Owner at Meijer (Midwest retailer), Digital IT org.
    Demographics: 28, White Male, Republican (Moderate).
    Location: Grand Rapids, MI (Northeast side). Owns rental property on Northwest Side of Grand Rapids.
    Financials: Interested in Stock Market (Retirement & Future Opps), Tech Industry. My roth IRA and Rollover IRA are tied up in EFTs and Mutual Funds. I have a nest egg of cash to invest in potential stocks. 
    Interests: US/Global Politics (Cause & Effect on career/money), Tech Industry, AI/ML developments, Stock Market (Tech Focus), Local Grand Rapids News.
    Lifestyle: Fitness, Health, Work. 
    Dislikes: Opinion pieces, gossip, pop culture, news with a lack of substance and meaning.
    Wants: Fact-based news, Cause and Effect analysis containing the who, what, where, and why.
    """,
    
    "Maddie": """
    Role: Spanish Teacher at Northview High School, Grand Rapids, MI.
    Demographics: 28, White Female, Democrat (Moderate).
    Location: Grand Rapids, MI.
    Interests: Local News, Education Policy, Community Well-being, US Politics (effect on markets/education).
    Lifestyle: Health, Wellness, Travel.
    Dislikes: Deep technical stock/tech details, Opinion pieces.
    Wants: Fact-based news, Community impact, World events affecting daily life.
    """
}

# End of configuration
