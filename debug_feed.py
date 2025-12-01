import feedparser
import config

url = "https://news.google.com/rss/search?q=Grand+Rapids+MI&hl=en-US&gl=US&ceid=US:en"
feed = feedparser.parse(url)

for entry in feed.entries[:3]:
    print(f"Title: {entry.title}")
    print(f"Link: {entry.link}")
    print(f"Description keys: {entry.keys()}")
    if 'description' in entry:
        print(f"Description length: {len(entry.description)}")
        print(f"Description start: {entry.description[:50]}")
    if 'summary' in entry:
        print(f"Summary length: {len(entry.summary)}")
    if 'content' in entry:
        print(f"Content: {entry.content}")
    print("-" * 20)
