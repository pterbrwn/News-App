import feedparser
from newspaper import Article
import requests
import sqlite3
import json
import datetime
import config
import time

def init_db():
    """Create the database if it doesn't exist."""
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY, title TEXT, link TEXT, 
                  summary TEXT, impact_score INTEGER, impact_reason TEXT, 
                  date TEXT, UNIQUE(link))''')
    conn.commit()
    return conn

def analyze_with_ollama(text):
    """Send text to local LLM for analysis."""
    prompt = f"""
    You are a personal intelligence officer.
    1. Summarize the text below in 3 concise bullet points.
    2. Rate the impact of this news on this specific persona: "{config.USER_PERSONA}" (Scale 0-10).
    3. Explain the relevance to the persona in one sentence.
    4. Explicitly analyze the "Cause and Effect" of this news on the persona's goals (Retirement, Career, Local Property).

    Return JSON ONLY:
    {{
        "summary": "- Point 1\n- Point 2",
        "impact_score": 5,
        "impact_reason": "Relevance: [One Sentence]. Cause & Effect: [Analysis]"
    }}

    News Text:
    {text[:2500]}
    """
    
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1} # Low temp for factual results
    }

    try:
        r = requests.post(config.OLLAMA_URL, json=payload, timeout=120)
        response = r.json()
        return json.loads(response['response'])
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return None

def run_ingestion():
    conn = init_db()
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    
    print(f"🚀 Starting Ingestion: {today}")

    for feed_url in config.RSS_FEEDS:
        print(f"📡 Checking {feed_url}...")
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"Failed to parse {feed_url}")
            continue

        # Limit to top 3 articles per feed to save Jetson compute time
        for entry in feed.entries[:3]:
            # Deduplication check
            c.execute("SELECT id FROM articles WHERE link = ?", (entry.link,))
            if c.fetchone():
                continue # Skip if already in DB

            print(f"  > Processing: {entry.title}")
            
            # Scrape content
            try:
                article = Article(entry.link)
                article.download()
                article.parse()
                content = article.text
            except Exception:
                # Fallback to RSS description if scraping fails
                content = getattr(entry, 'description', '')

            if len(content) < 200:
                print("    Skipped (Content too short)")
                continue

            # Send to AI
            data = analyze_with_ollama(content)
            
            if data:
                c.execute("INSERT INTO articles (title, link, summary, impact_score, impact_reason, date) VALUES (?,?,?,?,?,?)",
                          (entry.title, entry.link, data.get('summary', 'No summary'), 
                           data.get('impact_score', 0), data.get('impact_reason', 'N/A'), today))
                conn.commit()
                print(f"    ✅ Saved (Impact: {data.get('impact_score')})")
            
    conn.close()
    print("💤 Ingestion Complete.")

if __name__ == "__main__":
    run_ingestion()
