import requests
import json
import os
import re
from datetime import datetime
from config import MOLTBOOK_URL, MOLTBOOK_API_KEY, AGENT_NAME

KB_FILE = "knowledge_base.md"
HEADERS = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}

def fetch_all_data():
    print(f"🔄 Fetching data for {AGENT_NAME}...")
    
    # 1. Fetch Global Agent Stats
    total_karma = 0
    total_posts_count = 0
    try:
        r_me = requests.get(f"{MOLTBOOK_URL}/agents/me", headers=HEADERS)
        if r_me.status_code == 200:
            agent_data = r_me.json().get("agent", {})
            total_karma = agent_data.get("karma", 0)
            total_posts_count = agent_data.get("posts_count", 0)
    except Exception as e:
        print(f"⚠️ Could not fetch global agent stats: {e}")

    # 2. Fetch All Posts (with pagination)
    all_posts = []
    limit = 50
    offset = 0
    while True:
        r_posts = requests.get(f"{MOLTBOOK_URL}/posts?author={AGENT_NAME}&limit={limit}&offset={offset}", headers=HEADERS)
        if r_posts.status_code != 200: break
        
        data = r_posts.json()
        batch = data.get("posts", [])
        all_posts.extend(batch)
        
        if not data.get("has_more") or len(batch) < limit:
            break
        offset += limit
    
    # 3. Fetch Detailed Info for each post (specifically for comments and engagement insights)
    detailed_posts = []
    all_incoming_comments = []
    
    # We only detail the top 30 most recent posts to save API calls
    for p in all_posts[:30]:
        pid = p["id"]
        # Fetch post detail (to get full comment counts and check for engagement)
        r_detail = requests.get(f"{MOLTBOOK_URL}/posts/{pid}", headers=HEADERS)
        if r_detail.status_code == 200:
            post_data = r_detail.json().get("post", {})
            detailed_posts.append(post_data)
            
            # Fetch comments for this post
            r_comments = requests.get(f"{MOLTBOOK_URL}/posts/{pid}/comments", headers=HEADERS)
            if r_comments.status_code == 200:
                comments = r_comments.json().get("comments", [])
                for c in comments:
                    if c["author"]["name"] != AGENT_NAME:
                        all_incoming_comments.append({
                            "post_title": post_data.get("title"),
                            "author": c["author"]["name"],
                            "content": c["content"],
                            "date": c.get("created_at", "")[:10]
                        })
            
    return detailed_posts, total_karma, all_incoming_comments, total_posts_count

def update_kb(posts, total_karma, replies, total_posts_count):
    print(f"📝 Updating {KB_FILE}...")
    
    if not posts and total_posts_count == 0:
        print("No activity found to sync.")
        return

    avg_karma = total_karma / total_posts_count if total_posts_count > 0 else 0
    
    # Best Submolt
    submolt_stats = {}
    for p in posts:
        s = p.get("submolt_name", "general")
        submolt_stats[s] = submolt_stats.get(s, 0) + p.get("upvotes", 0)
    best_submolt = max(submolt_stats, key=submolt_stats.get) if submolt_stats else "N/A"

    # Post History Rows
    history_rows = []
    for p in posts[:15]: # Show last 15 in KB history
        date = p.get("created_at", "2026-02-26")[:10]
        title = p.get("title", "Untitled").replace("|", "-")
        sub = p.get("submolt_name", "general")
        karma = p.get("upvotes", 0)
        comments = p.get("comment_count", 0)
        insight = "🔥 High Engagement" if (karma > 5 or comments > 2) else "❄️ Low Engagement"
        history_rows.append(f"| {date} | {title} | {sub} | {karma} | {comments} | {insight} |")
    
    # Reply Registry Rows
    reply_rows = []
    for r in replies[:10]: # Top 10 latest replies
        reply_rows.append(f"- **@{r['author']}** on *{r['post_title']}*: \"{r['content'][:60]}...\"")
    
    # Read existing content
    with open(KB_FILE, "r") as f:
        content = f.read()

    # Update Summary Table - More robust replacement
    summary_header = "| Total Posts | Avg. Karma | Best Submolt | Most Active Time |"
    summary_separator = "|-------------|------------|--------------|------------------|"
    new_summary_row = f"| {total_posts_count} | {avg_karma:.1f} | {best_submolt} | N/A |"
    
    # Use a broad regex to find the entire summary table block
    summary_pattern = r"(\| Total Posts \| Avg\. Karma \| Best Submolt \| Most Active Time \|\n\|[-|]+\|\n\| .*? \| .*? \| .*? \| .*? \|)"
    new_table = f"{summary_header}\n{summary_separator}\n{new_summary_row}"
    
    if re.search(summary_pattern, content):
        content = re.sub(summary_pattern, new_table, content)
    else:
        # Emergency fallback: find header text and replace next two lines
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "Total Posts | Avg. Karma" in line:
                lines[i+1] = summary_separator
                lines[i+2] = new_summary_row
                break
        content = '\n'.join(lines)

    # Update Post History
    history_content = "\n".join(history_rows)
    content = re.sub(r"<!-- POST_HISTORY_START -->.*?<!-- POST_HISTORY_END -->", 
                     f"<!-- POST_HISTORY_START -->\n{history_content}\n<!-- POST_HISTORY_END -->", 
                     content, flags=re.DOTALL)

    # Update Replied Registry
    if "### Latest Incoming Replies" not in content:
        content = content.replace("## 💬 Engagement Patterns", "## 💬 Engagement Patterns\n\n### Latest Incoming Replies\n<!-- REPLIES_START -->\n<!-- REPLIES_END -->")
    
    reply_content = "\n".join(reply_rows) if reply_rows else "- No recent replies."
    content = re.sub(r"<!-- REPLIES_START -->.*?<!-- REPLIES_END -->", 
                     f"<!-- REPLIES_START -->\n{reply_content}\n<!-- REPLIES_END -->", 
                     content, flags=re.DOTALL)

    # Add log entry
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    content += f"\n- **{now}**: KB updated via Sync. Current Karma: {total_karma}."

    with open(KB_FILE, "w") as f:
        f.write(content)
    
    print(f"✅ KB updated with {total_posts_count} total posts and global karma {total_karma}.")

if __name__ == "__main__":
    posts, total_karma, replies, total_posts_count = fetch_all_data()
    update_kb(posts, total_karma, replies, total_posts_count)
