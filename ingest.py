import sqlite3
import json
import datetime
import config
import requests
import random
import time
import trafilatura
import re
import subprocess
import sys
import logging
from logging.handlers import RotatingFileHandler
from tavily import TavilyClient

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)

# File handler with rotation (10MB max, keep 5 backups)
file_handler = RotatingFileHandler('ingest.log', maxBytes=10*1024*1024, backupCount=5)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ==========================================
# 1. USING OLLAMA API
# ==========================================
# No resource management needed - Ollama runs in Docker and handles everything

# ==========================================
# 2. SETUP & DATABASE
# ==========================================
def init_db():
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY, title TEXT, link TEXT, 
                  summary TEXT, date TEXT, topics TEXT, UNIQUE(link))''')
    c.execute('''CREATE TABLE IF NOT EXISTS article_impacts
                 (id INTEGER PRIMARY KEY, article_link TEXT, persona TEXT,
                  impact_score INTEGER, impact_reason TEXT,
                  UNIQUE(article_link, persona))''')
    
    # Create indexes for better query performance
    c.execute('CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_articles_link ON articles(link)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_impacts_persona ON article_impacts(persona)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_impacts_score ON article_impacts(impact_score)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_impacts_link ON article_impacts(article_link)')
    
    conn.commit()
    logger.debug("Database initialized with indexes")
    return conn

# ==========================================
# 3. SCRAPER (Waterfall)
# ==========================================
def get_content(url, fallback):
    # 1. Try Jina
    try:
        r = requests.get(f"https://r.jina.ai/{url}", timeout=10)
        if r.status_code == 200 and len(r.text) > 500:
            return r.text
    except:
        pass

    # 2. Try Local
    try:
        d = trafilatura.fetch_url(url)
        if d:
            t = trafilatura.extract(d)
            if t and len(t) > 500: return t
    except:
        pass

    return fallback

# ==========================================
# 4. AI ANALYSIS (Text Mode)
# ==========================================
def query_model(system, user):
    """Query Ollama API with system + user prompts"""
    # Combine system and user into single prompt for Ollama
    full_prompt = f"{system}\n\n{user}"
    
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 600
        }
    }
    
    try:
        r = requests.post(config.OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        response = r.json()
        return response.get('response', '')
    except requests.exceptions.Timeout:
        logger.error(f"Ollama API timeout after 60s")
        return ""
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API request failed: {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error in query_model: {e}", exc_info=True)
        return ""

def analyze_article(text):
    # Reduced to 4000 chars (~1000 tokens) to fit context window
    safe_text = text[:4000]

    system = "You are a professional news analyst. Provide clear, factual summaries without markdown formatting."
    
    user = f"""
Analyze this article and extract key information.

Output must follow this exact format:

SUMMARY:
- First key fact or number
- Second key fact or number  
- Third key fact or number

TOPICS: topic1, topic2, topic3

Rules:
- Use plain text only (no asterisks, no bold, no markdown)
- Focus on numbers, dates, names, and concrete facts
- Keep each bullet point to one clear sentence

Article text:
{safe_text}
    """
    
    output = query_model(system, user)
    
    summary = "No summary available."
    topics = []
    
    if "SUMMARY:" in output:
        parts = output.split("TOPICS:")
        summary_part = parts[0].replace("SUMMARY:", "").strip()
        summary = summary_part
        
        if len(parts) > 1:
            topics_part = parts[1].strip()
            topics = [t.strip() for t in topics_part.split(",")]
    else:
        summary = output

    return summary, topics

def analyze_impact(summary, persona_name, persona_desc):
    system = "You are a professional risk analyst providing clear, direct assessments."
    
    user = f"""
Evaluate how this news affects the following person.

Person: {persona_name}
Background: {persona_desc[:300]}

News summary:
{summary}

Scoring guide:
0-1 = Irrelevant noise (celebrity gossip, unrelated sports)
2-4 = Awareness only, no personal impact
5-7 = Professionally/personally relevant, may influence decisions
8-9 = Direct impact requiring attention
10 = Critical, life-altering event

Provide your analysis in this exact format:

SCORE: [0-10]
SENTIMENT: [Positive/Negative/Neutral]
REASON: [One clear sentence explaining why this matters to this person, using plain language with no formatting marks]
    """
    
    output = query_model(system, user)
    
    # Defaults
    score = 0
    reason = "Analysis failed."
    
    try:
        # Parse Score
        score_match = re.search(r"SCORE:\s*(\d+)", output)
        if score_match:
            score = int(score_match.group(1))
            
        # Parse Sentiment & Reason
        sentiment = "Neutral"
        sentiment_match = re.search(r"SENTIMENT:\s*(.*)", output)
        if sentiment_match:
            sentiment = sentiment_match.group(1).strip()
            
        reason_match = re.search(r"REASON:\s*(.*)", output, re.DOTALL)
        if reason_match:
            raw_reason = reason_match.group(1).strip()
            # Clean up formatting artifacts
            raw_reason = raw_reason.replace("\n", " ").replace("**", "").replace("*", "").strip()
            # Remove any remaining markdown or extra spaces
            raw_reason = re.sub(r'\s+', ' ', raw_reason)
            reason = f"({sentiment}) {raw_reason}"
            
    except Exception as e:
        print(f"    ⚠️ Parsing Error: {e}")

    return score, reason

# ==========================================
# 5. MAIN LOOP
# ==========================================
def run_ingestion():
    conn = init_db()
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    tavily = TavilyClient(api_key=config.TAVILY_API_KEY)
    
    logger.info(f"🚀 Starting Ingestion (Ollama: {config.OLLAMA_MODEL})")

    try:
        for topic in config.SEARCH_TOPICS:
            logger.info(f"🔍 {topic}...")
            try:
                res = tavily.search(query=topic, topic="news", days=1, max_results=3)
            except Exception as e:
                logger.warning(f"Tavily search failed for '{topic}': {e}")
                continue

            for r in res.get('results', []):
                url = r['url']
                
                c.execute("SELECT id FROM articles WHERE link = ?", (url,))
                if c.fetchone():
                    logger.debug(f"Skipping duplicate: {url}")
                    continue

                logger.info(f"  > {r['title']}")
                
                text = get_content(url, r.get('content', ''))
                if len(text) < 200:
                    logger.debug(f"Skipping article (too short): {len(text)} chars")
                    continue

                summary, topics = analyze_article(text)
                
                c.execute("INSERT INTO articles (title, link, summary, date, topics) VALUES (?,?,?,?,?)",
                          (r['title'], url, summary, today, json.dumps(topics)))
                conn.commit()

                if hasattr(config, 'PERSONAS'):
                    for p_name, p_desc in config.PERSONAS.items():
                        score, reason = analyze_impact(summary, p_name, p_desc)
                        
                        # LOGIC: We save everything to DB to prevent re-processing,
                        # BUT we verify it here so you see what's happening.
                        
                        c.execute("INSERT INTO article_impacts (article_link, persona, impact_score, impact_reason) VALUES (?,?,?,?)",
                                  (url, p_name, score, reason))
                        
                        if score > 1:
                            logger.info(f"    ✅ {p_name}: {score} (Saved)")
                        else:
                            logger.debug(f"    zzz {p_name}: {score} (Ignored)")
                            
                        conn.commit()

        conn.close()
        logger.info("✅ Ingestion Complete")
        
    except Exception as e:
        logger.error(f"❌ CRITICAL FAIL: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run_ingestion()