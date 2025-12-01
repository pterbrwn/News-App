import streamlit as st
import sqlite3
import pandas as pd
import datetime
import config
import json
import re

# -----------------------------------------------------------------------------
# 1. APP CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Jetson Briefing", 
    page_icon="☕", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Expert Level" UI
st.markdown("""
<style>
    /* Import Inter font for a clean, modern look */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0E1117; /* Deep dark background */
    }

    /* Hide Streamlit Default Chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ---------------------------------------------------------------------
       CARD COMPONENT (Inside Expander)
       --------------------------------------------------------------------- */
    .news-card-content {
        background-color: #1C1F26;
        border-radius: 8px;
        padding: 20px;
        margin-top: 0px;
        border: 1px solid #2E333D;
    }

    /* IMPACT BADGES */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-right: 8px;
        margin-bottom: 12px;
    }
    
    .badge-critical { background-color: rgba(255, 75, 75, 0.15); color: #FF4B4B; border: 1px solid rgba(255, 75, 75, 0.3); }
    .badge-high { background-color: rgba(255, 165, 0, 0.15); color: #FFA500; border: 1px solid rgba(255, 165, 0, 0.3); }
    .badge-low { background-color: rgba(255, 255, 255, 0.05); color: #888; border: 1px solid rgba(255, 255, 255, 0.1); }
    
    .topic-tag {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        background-color: #262A35;
        color: #A0A0A0;
        border: 1px solid #3E4451;
        margin-right: 6px;
    }

    /* TYPOGRAPHY */
    .card-summary {
        font-size: 0.95rem;
        color: #C0C0C0;
        line-height: 1.6;
        margin-bottom: 20px;
    }
    
    .card-summary ul {
        padding-left: 20px;
        margin: 0;
    }
    
    .card-summary li {
        margin-bottom: 8px;
    }
    
    .source-link {
        font-size: 0.85rem;
        color: #4DA6FF;
        text-decoration: none;
        display: inline-block;
        margin-top: 10px;
    }
    
    .source-link:hover {
        text-decoration: underline;
    }

    /* AI ANALYSIS BOX */
    .analysis-box {
        background-color: #262A35;
        border-left: 3px solid #4DA6FF;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-top: 16px;
    }
    
    .analysis-header {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: #4DA6FF;
        font-weight: 700;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .analysis-content {
        font-size: 0.9rem;
        color: #E0E0E0;
        font-style: italic;
    }

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATA LOGIC
# -----------------------------------------------------------------------------
def get_data(persona_name):
    conn = sqlite3.connect(config.DB_NAME)
    today = datetime.date.today().isoformat()
    
    # Join articles with impacts for the specific persona
    query = f"""
        SELECT 
            a.title, a.link, a.summary, a.topics, a.date,
            i.impact_score, i.impact_reason
        FROM articles a
        JOIN article_impacts i ON a.link = i.article_link
        WHERE i.persona = '{persona_name}' AND a.date = '{today}'
        ORDER BY i.impact_score DESC
    """
    
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        df = pd.DataFrame()
    
    # Fallback: If no news today, show latest 10 items for this persona
    if df.empty:
        query = f"""
            SELECT 
                a.title, a.link, a.summary, a.topics, a.date,
                i.impact_score, i.impact_reason
            FROM articles a
            JOIN article_impacts i ON a.link = i.article_link
            WHERE i.persona = '{persona_name}'
            ORDER BY a.date DESC, i.impact_score DESC LIMIT 10
        """
        try:
            df = pd.read_sql_query(query, conn)
        except Exception:
            pass
        
    conn.close()
    return df

def render_content_html(row):
    """Generates the HTML content INSIDE the expander."""
    score = row['impact_score']
    
    # Badge Logic
    if score >= 8:
        badge_html = f'<span class="badge badge-critical">Critical • {score}/10</span>'
    elif score >= 5:
        badge_html = f'<span class="badge badge-high">Important • {score}/10</span>'
    else:
        badge_html = f'<span class="badge badge-low">Noise • {score}/10</span>'
    
    # Date Logic
    date_str = row.get('date', 'Unknown Date')
    date_html = f'<span style="color: #666; font-size: 0.75rem; white-space: nowrap;">📅 {date_str}</span>'

    # Topics Logic (Handle missing column or JSON errors)
    topics_html = ""
    if 'topics' in row and row['topics']:
        try:
            topics_list = json.loads(row['topics'])
            for topic in topics_list:
                topics_html += f'<span class="topic-tag">{topic}</span>'
        except:
            pass

    # Summary Formatting
    summary_text = str(row['summary'])
    
    # If summary looks like HTML (from RSS fallback), strip tags to keep it clean
    if "<" in summary_text and ">" in summary_text:
        summary_text = re.sub('<[^<]+?>', '', summary_text) # Simple regex to strip tags
    
    # Escape HTML special characters to prevent rendering issues
    import html
    summary_text = html.escape(summary_text)
    
    if "-" in summary_text or "•" in summary_text:
        items = [s.strip().replace("- ", "").replace("* ", "").replace("• ", "") for s in summary_text.split('\n') if s.strip()]
        summary_html = "<ul>" + "".join([f"<li>{item}</li>" for item in items if item]) + "</ul>"
    else:
        summary_html = f"<p>{summary_text}</p>"
    
    # Escape the impact reason as well
    impact_reason_escaped = html.escape(str(row['impact_reason']))

    return f"""<div class="news-card-content">
<div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
    <div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">
        {badge_html}
        {topics_html}
    </div>
    {date_html}
</div>
<div class="card-summary">{summary_html}</div>
<div class="analysis-box">
<div class="analysis-header">
<span>⚡ Impact Analysis</span>
</div>
<div class="analysis-content">
{impact_reason_escaped}
</div>
</div>
<a href="{row['link']}" target="_blank" class="source-link">🔗 Read Original Source</a>
</div>"""

# -----------------------------------------------------------------------------
# 3. MAIN UI LAYOUT
# -----------------------------------------------------------------------------

# Top Layout: Title & Persona Selector
col1, col2 = st.columns([3, 1])

with col1:
    st.title("☕ Morning Brief")
    st.caption(f"Date: {datetime.date.today().strftime('%A, %B %d')}")

with col2:
    # Persona Selector (Main UI)
    selected_persona = st.selectbox(
        "👤 Viewing as:",
        options=list(config.PERSONAS.keys()),
        index=0
    )

# Sidebar (Extra Info)
with st.sidebar:
    st.title("⚙️ Controls")
    if st.button("🔄 Refresh Feed"):
        st.rerun()
    
    st.divider()
    st.markdown(f"**Profile: {selected_persona}**")
    desc = config.PERSONAS[selected_persona]
    st.info(desc[:150] + "...")

# Main Feed
try:
    df = get_data(selected_persona)
    
    if df.empty:
        st.container().warning(f"Waiting for intelligence for **{selected_persona}**... Run `./daily_job.sh` to ingest.")
    else:
        # Header
        st.markdown(f"### 🌍 Daily Intelligence Report: {selected_persona}")
        st.markdown(f"Found **{len(df)}** relevant articles based on your profile.")
        st.markdown("---")

        # Render all items as Expanders
        for _, row in df.iterrows():
            # Determine Icon based on score
            if row['impact_score'] >= 8:
                icon = "🚨"
            elif row['impact_score'] >= 5:
                icon = "🔥"
            else:
                icon = "📰"
            
            # Expander Header: Icon + Title
            # We can't put HTML in the expander label easily, so we keep it clean text
            label = f"{icon} [{row['impact_score']}/10] {row['title']}"
            
            # Default expand critical items
            is_expanded = (row['impact_score'] >= 7)
            
            with st.expander(label, expanded=is_expanded):
                st.markdown(render_content_html(row), unsafe_allow_html=True)

except Exception as e:
    st.error(f"System Error: {e}")
