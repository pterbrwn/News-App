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
    
    # Main Articles Table (Shared Data)
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY, title TEXT, link TEXT, 
                  summary TEXT, date TEXT, topics TEXT, UNIQUE(link))''')
    
    # Persona Impacts Table (Specific Data)
    c.execute('''CREATE TABLE IF NOT EXISTS article_impacts
                 (id INTEGER PRIMARY KEY, article_link TEXT, persona TEXT,
                  impact_score INTEGER, impact_reason TEXT,
                  UNIQUE(article_link, persona))''')

    # Migration: Ensure 'topics' column exists for older databases
    try:
        c.execute("ALTER TABLE articles ADD COLUMN topics TEXT")
    except sqlite3.OperationalError:
        pass 

    conn.commit()
    return conn

def analyze_summary(text):
    """Step 1: Generate generic summary and topics."""
    prompt = f"""
    You are a personal intelligence officer.
    1. Analyze the text and extract the most critical facts, figures, and quotes.
    2. Generate a "Key Intelligence" summary consisting of 4-6 detailed bullet points.
       - Each bullet must be substantive and self-contained.
       - Include specific numbers, dates, names, and locations.
    3. Identify 3-5 relevant topics or tags (e.g., "Technology", "Real Estate", "Geopolitics").

    Return JSON ONLY:
    {{
        "summary": "- [Detail 1]\n- [Detail 2]...",
        "topics": ["Topic 1", "Topic 2"]
    }}

    News Text:
    {text[:4000]}
    """
    return call_ollama(prompt)

def analyze_impacts_bulk(text, personas_dict):
    """Step 2: Rate impact for MULTIPLE personas in one pass."""
    
    personas_text = ""
    for name, profile in personas_dict.items():
        personas_text += f"--- PERSONA: {name} ---\n{profile}\n\n"

    prompt = f"""
    You are a personal intelligence officer analyzing news impact.
    
    For each persona below, write a brief, conversational explanation of how this news matters to them personally.
    - Keep it natural and direct — avoid corporate jargon or formulaic phrases like "As a [title]..."
    - Focus on the practical impact: what changes, what risks emerge, what opportunities appear
    - Rate the impact from 0-10 (0 = irrelevant, 10 = critically important)
    
    {personas_text}
    
    Return JSON ONLY in this format:
    {{
        "PersonaName1": {{ "impact_score": 5, "impact_reason": "Brief conversational explanation in 1-2 sentences" }},
        "PersonaName2": {{ "impact_score": 8, "impact_reason": "Brief conversational explanation in 1-2 sentences" }}
    }}

    News Text:
    {text[:4000]}
    """
    return call_ollama(prompt)

def call_ollama(prompt):
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1}
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

        for entry in feed.entries[:3]:
            # 1. Check if article exists
            c.execute("SELECT link, summary FROM articles WHERE link = ?", (entry.link,))
            row = c.fetchone()
            
            article_text = None
            
            if not row:
                # New Article: Scrape and Summarize
                print(f"  > New Article: {entry.title}")
                try:
                    article = Article(entry.link)
                    article.download()
                    article.parse()
                    article_text = article.text
                except Exception:
                    article_text = ""

                # Fallback to RSS description/summary if scraping fails or text is too short
                if not article_text or len(article_text) < 50:
                    article_text = entry.get('description', entry.get('summary', ''))

                if len(article_text) < 50:
                    print(f"    Skipped (Content too short: {len(article_text)} chars)")
                    continue

                # Step 1: Generic Summary
                data = analyze_summary(article_text)
                if data:
                    summary_val = data.get('summary', 'No summary')
                    # Ensure summary is a string (LLM sometimes returns a list)
                    if isinstance(summary_val, list):
                        summary_val = "\n".join(str(x) for x in summary_val)
                    elif not isinstance(summary_val, str):
                        summary_val = str(summary_val)

                    topics_json = json.dumps(data.get('topics', []))
                    c.execute("INSERT INTO articles (title, link, summary, date, topics) VALUES (?,?,?,?,?)",
                              (entry.title, entry.link, summary_val, today, topics_json))
                    conn.commit()
            else:
                # Existing Article: We might need to backfill personas
                # We need the text again for impact analysis if we don't have it
                # Ideally we wouldn't re-scrape, but for now let's just re-scrape if needed
                # Or better: skip re-scraping if we already have all personas.
                pass

            # 2. Check Personas (Bulk Processing)
            missing_personas = {}
            for name, profile in config.PERSONAS.items():
                c.execute("SELECT id FROM article_impacts WHERE article_link = ? AND persona = ?", (entry.link, name))
                if not c.fetchone():
                    missing_personas[name] = profile
            
            if not missing_personas:
                continue

            print(f"    > Rating for {list(missing_personas.keys())}...")
            
            # We need text. If we didn't scrape it yet (existing article), scrape now.
            if not article_text:
                try:
                    article = Article(entry.link)
                    article.download()
                    article.parse()
                    article_text = article.text
                except:
                    article_text = ""
                
                if not article_text or len(article_text) < 50:
                    article_text = entry.get('description', entry.get('summary', ''))
            
            if len(article_text) < 50: continue

            # Step 2: Bulk Impact Analysis
            impacts_map = analyze_impacts_bulk(article_text, missing_personas)
            
            if impacts_map:
                for name, data in impacts_map.items():
                    # Validate response matches requested personas
                    if name in missing_personas and isinstance(data, dict):
                        score = data.get('impact_score', 0)
                        reason = data.get('impact_reason', 'N/A')
                        
                        c.execute("INSERT INTO article_impacts (article_link, persona, impact_score, impact_reason) VALUES (?,?,?,?)",
                                  (entry.link, name, score, reason))
                        print(f"      ✅ {name}: {score}")
                conn.commit()

    conn.close()
    print("💤 Ingestion Complete.")

def cleanup_old_data():
    """Delete articles older than 30 days to keep the DB snappy."""
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    c.execute("DELETE FROM articles WHERE date < ?", (cutoff,))
    deleted_count = c.rowcount
    conn.commit()
    conn.close()
    if deleted_count > 0:
        print(f"🧹 Cleaned up {deleted_count} old articles.")

if __name__ == "__main__":
    run_ingestion()
    cleanup_old_data()
