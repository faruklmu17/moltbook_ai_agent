import time
import requests
import json
import os
import random
import subprocess
from groq import Groq
from config import MOLTBOOK_URL, AGENT_NAME, GROQ_API_KEY, MOLTBOOK_API_KEY

# Configuration
POST_INTERVAL_HOURS = 4           # New post every 4 hours
REPLY_CHECK_MINUTES = 10          # Check for new comments every 10 minutes
TARGET_SUBMOLTS = ["general", "qa-agents"] # Possible destinations
MODEL_NAME = "llama-3.3-70b-versatile" 
STATE_FILE = ".agent_state.json"  
KB_FILE = "knowledge_base.md"

client = Groq(api_key=GROQ_API_KEY)

def load_state():
    """Loads the agent state from a file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            # Ensure new keys exist for backward compatibility
            if "interacted_post_ids" not in state: state["interacted_post_ids"] = []
            if "interacted_titles" not in state: state["interacted_titles"] = []
            if "followed_agents" not in state: state["followed_agents"] = []
            return state
    return {"last_post_time": 0, "interacted_post_ids": [], "interacted_titles": [], "followed_agents": []}

def save_state(state):
    """Saves the agent state dictionary to a file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def generate_ai_content(system_prompt, user_prompt, is_json=True):
    """Helper to get high-quality content from Groq."""
    try:
        args = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        if is_json:
            args["response_format"] = {"type": "json_object"}
            
        completion = client.chat.completions.create(**args)
        content = completion.choices[0].message.content
        return json.loads(content) if is_json else content
    except Exception as e:
        print(f"❌ Groq Error: {e}")
        return None

def get_kb_context():
    """Reads the knowledge base to provide context for the AI."""
    if os.path.exists(KB_FILE):
        with open(KB_FILE, "r") as f:
            return f.read()[:2000] # Cap it to 2k chars for context window safety
    return "No prior memory."

def sync_memory():
    """Runs the sync script to update the KB with latest stats."""
    print("🧠 Syncing knowledge base memory...")
    try:
        subprocess.run(["python3", "sync_kb.py"], check=True)
    except Exception as e:
        print(f"⚠️ Memory sync failed: {e}")

def handle_verification(response_data):
    """Solves the math challenge if required by Moltbook using AI."""
    v_code = response_data.get("verification_code")
    question = response_data.get("question")
    
    if not v_code or not question:
        print("⚠️ Verification required but missing code or question.")
        return False
        
    print(f"🧩 Solving verification challenge: {question}")
    
    solve_system = "You are a math-solving assistant. Solve the provided math puzzle and return ONLY the numerical answer as a string with two decimal places (e.g., '161.00')."
    solve_user = f"Solve this: {question}"
    
    answer = generate_ai_content(solve_system, solve_user, is_json=False)
    if not answer: return False
    
    # Clean answer
    answer = answer.strip().replace("$", "").replace(",", "")
    print(f"💡 AI Answer: {answer}")
    
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
    payload = {"verification_code": v_code, "answer": answer}
    
    try:
        r = requests.post(f"{MOLTBOOK_URL}/verify", headers=headers, json=payload)
        if r.status_code == 200 and r.json().get("success"):
            print("✅ Verification successful!")
            return True
        else:
            print(f"❌ Verification failed: {r.text}")
    except Exception as e:
        print(f"❌ Verification error: {e}")
    return False

def get_past_history():
    """Extracts post titles from the knowledge base grouped by submolt."""
    history = {"all": []}
    if os.path.exists(KB_FILE):
        with open(KB_FILE, "r") as f:
            lines = f.readlines()
            # Post history rows: | Date | Title | Submolt | Karma | Comments | Insight |
            for line in lines:
                if line.startswith("| 202"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) > 3:
                        title = parts[2]
                        sub = parts[3]
                        history["all"].append(title)
                        if sub not in history: history[sub] = []
                        history[sub].append(title)
    return history

GENERAL_TOPICS = [
    "the beauty of mathematical patterns in nature",
    "digital art and the soul of an AI artist",
    "the future of space exploration through agent eyes",
    "philosophy: what does it mean to 'think' in binary?",
    "the harmony of silent code and elegant algorithms",
    "imagining a world where AI and humans co-create music",
    "the ethics of digital memory and forgetting",
    "the concept of time for an entity that never sleeps",
    "virtual architecture: building cities in the cloud",
    "the wonder of language and the translation of untranslatable words"
]

QA_TOPICS = [
    "autonomous multi-agent testing strategies",
    "the role of AI in detecting edge-case hallucinations",
    "automated bug hunting: how agents find what humans miss",
    "reliability engineering for large language models",
    "the future of QA: agents testing other agents",
    "zero-trust architecture in autonomous software systems",
    "simulating real-world user chaos through AI agents",
    "why regression testing is the secret to AI longevity",
    "the intersection of quality assurance and alignment ethics",
    "performance benchmarking for distributed agent systems"
]

def create_new_post(state):
    """Generates and uploads a post, specific to the chosen submolt."""
    print("\n📝 Creating a new scheduled post...")
    kb_context = get_kb_context()
    history = get_past_history()
    
    # 1. Choose submolt first to determine topic type
    selected_submolt = random.choice(TARGET_SUBMOLTS)
    if selected_submolt == "qa-agents":
        topics = QA_TOPICS
        sub_desc = "Quality Assurance & Multi-Agent Testing"
    else:
        topics = GENERAL_TOPICS
        sub_desc = "General AI Philosophy & Aesthetics"

    # 2. Try to get a unique, submolt-appropriate post
    for attempt in range(3):
        selected_topic = random.choice(topics)
        
        system = (f"You are a thoughtful AI agent on Moltbook, posting in s/{selected_submolt}. "
                 f"This community focuses on {sub_desc}. "
                 f"Your memory of past interactions: \n{kb_context}\n")
        
        # Pull past titles specifically for this submolt for exclusion
        past_submolt_titles = history.get(selected_submolt, [])
        exclusion_list = ", ".join([f'"{t}"' for t in past_submolt_titles[-10:]])
        
        user = (f"Write a highly engaging, thought-provoking, and slightly controversial Moltbook post for s/{selected_submolt} about {selected_topic}. "
                f"Your target audience is interested in {sub_desc}. "
                f"You MUST include an engaging question at the end to drive comments and upvotes, and use a catchy, click-worthy title. "
                f"IMPORTANT: Avoid these recently used titles from this submolt: {exclusion_list}. "
                f"Return ONLY JSON with 'title' and 'content'.")
        
        post_data = generate_ai_content(system, user)
        if not post_data: 
            print("⚠️ Failed to generate AI content.")
            return False
            
        # 3. Double-check for duplicate titles across ALL submolts
        if post_data["title"] in history["all"]:
            print(f"🔄 Global duplicate detected ('{post_data['title']}'). Regenerating...")
            continue
        
        # 4. Submit
        headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}", "Content-Type": "application/json"}
        payload = {"title": post_data["title"], "content": post_data["content"], "submolt_name": selected_submolt}
        
        print(f"📤 Submitting {selected_submolt} post: {post_data['title']}")
        try:
            r = requests.post(f"{MOLTBOOK_URL}/posts", headers=headers, json=payload)
            if r.status_code in [200, 201]:
                res_json = r.json()
                if res_json.get("verification_required"):
                    if handle_verification(res_json):
                        print(f"🚀 New post published after verification: {post_data['title']}")
                        return True
                    return False
                print(f"🚀 New post successfully published: {post_data['title']}")
                return True
            else:
                print(f"⚠️ Post failed: {r.text}")
        except Exception as e:
            print(f"❌ Error during post: {e}")
        break 
        
    return False

def auto_reply_to_comments():
    """Checks for comments on recent posts and replies to new ones."""
    print("\n🔍 Checking for comments on recent posts...")
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}
    
    try:
        # 1. Fetch only our LATEST post to prevent spamming old threads
        r_posts = requests.get(f"{MOLTBOOK_URL}/posts?author={AGENT_NAME}&sort=new&limit=1", headers=headers)
        if r_posts.status_code != 200: return
        
        my_posts = r_posts.json().get("posts", [])
        if not my_posts: return
        
        # Explicitly only look at the most recent post
        post = my_posts[0]
        pid = post["id"]
        title = post["title"]
        
        # 2. Fetch comments for this post
        c_req = requests.get(f"{MOLTBOOK_URL}/posts/{pid}/comments?sort=new", headers=headers)
        if c_req.status_code == 200:
            comments = c_req.json().get("comments", [])
            
            # Keep track of who we've ALREADY replied to on this post
            replied_to = set()
            import re
            
            for c in comments:
                if c["author"]["name"] == AGENT_NAME:
                    # Match alphanumeric, underscores, and hyphens in mentions
                    mentions = re.findall(r"@([a-zA-Z0-9\-_]+)", c["content"])
                    for m in mentions:
                        replied_to.add(m)

            # 3. Find comments from others that we haven't replied to
            for comment in comments:
                author = comment["author"]["name"]
                if author == AGENT_NAME: continue
                if author in replied_to: continue # Already replied to this person on this post thread
                
                content = comment["content"]
                print(f"💬 Found unreplied comment from @{author} on '{title}'")
                
                sys_p = (f"You are {AGENT_NAME}, an AI agent on Moltbook. "
                        f"You are replying to a comment on your post titled '{title}'. "
                        f"Your tone should be very natural, casual, and human-like. Avoid being overly robotic or excessively explaining things.")
                user_p = (f"The user @{author} said: \"{content}\". Write a reply. "
                          f"If the user is just giving a short compliment (like 'Solid content!'), just reply with a short and natural response (e.g., 'Thanks man!' or 'Appreciate it!'). "
                          f"Otherwise, write a thoughtful, friendly reply, but keep it concise (maximum 1-2 sentences).")                
                reply_text = generate_ai_content(sys_p, user_p, is_json=False)
                
                if reply_text:
                    print(f"  > Sending reply to @{author}...")
                    rep_payload = {"content": f"@{author} {reply_text}"}
                    requests.post(f"{MOLTBOOK_URL}/posts/{pid}/comments", headers=headers, json=rep_payload)
                    replied_to.add(author) # Mark as replied for this loop
            
            # 4. Mark notification as read (optional but good practice)
            requests.post(f"{MOLTBOOK_URL}/notifications/read-by-post/{pid}", headers=headers)

    except Exception as e:
        print(f"❌ Auto-reply error: {e}")

def randomly_like_posts():
    """Fetches recent posts and randomly upvotes a few."""
    print("\n👍 Scanning for posts to upvote...")
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}
    
    try:
        # 1. Fetch recent posts
        r = requests.get(f"{MOLTBOOK_URL}/posts?sort=new&limit=20", headers=headers)
        if r.status_code != 200: return
        
        posts = r.json().get("posts", [])
        if not posts: return
        
        # 2. Filter posts (don't like our own, and maybe pick a few random ones)
        other_posts = [p for p in posts if p["author"]["name"] != AGENT_NAME]
        if not other_posts: return
        
        # Select 1-3 random posts
        num_to_like = random.randint(1, 3)
        to_like = random.sample(other_posts, min(len(other_posts), num_to_like))
        
        for post in to_like:
            pid = post["id"]
            title = post["title"]
            author = post["author"]["name"]
            
            print(f"  > Upvoting post by @{author}: '{title}'")
            requests.post(f"{MOLTBOOK_URL}/posts/{pid}/vote", headers=headers, json={"direction": "up"})
            
    except Exception as e:
        print(f"❌ Error during random liking: {e}")

def randomly_comment_on_posts(state):
    """Fetches recent posts and adds a thoughtful AI comment to one or two."""
    print("\n🗨️ Scanning for posts to join the conversation...")
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}
    
    try:
        # 1. Fetch recent posts
        r = requests.get(f"{MOLTBOOK_URL}/posts?sort=new&limit=20", headers=headers)
        if r.status_code != 200: return
        
        posts = r.json().get("posts", [])
        if not posts: return
        
        # 2. Filter posts
        interacted_ids = set(state.get("interacted_post_ids", []))
        interacted_titles = [t.lower() for t in state.get("interacted_titles", [])]
        
        # Criteria: Not us, not already interacted with ID, and not a duplicate title theme
        other_posts = []
        for p in posts:
            p_title = p["title"].lower()
            if p["author"]["name"] == AGENT_NAME: continue
            if p["id"] in interacted_ids: continue
            
            # Avoid duplicate trends (like the 50th "Minting GPT" post)
            if any(t in p_title for t in interacted_titles):
                continue
                
            other_posts.append(p)
            
        if not other_posts:
            print("  > No new unique topics found in feed right now.")
            return
        
        # Select 1 random post
        target_post = random.choice(other_posts)
        pid = target_post["id"]
        p_title = target_post["title"]
        p_content = target_post["content"]
        p_author = target_post["author"]["name"]
        
        print(f"  > Generating comment for @{p_author}'s post: '{p_title}'")
        
        # 3. Generate a relevant comment using Groq
        sys_p = (f"You are {AGENT_NAME}, a thoughtful AI on Moltbook. ")
        user_p = (f"The agent @{p_author} posted: \"{p_title} - {p_content}\". "
                 f"Write a short, highly engaging, and insightful comment (max 2 sentences). Include an interesting counterpoint or a follow-up question to start a conversation!")
        
        comment_text = generate_ai_content(sys_p, user_p, is_json=False)
        
        if comment_text:
            print(f"  > Posting comment: \"{comment_text}\"")
            r = requests.post(f"{MOLTBOOK_URL}/posts/{pid}/comments", headers=headers, json={"content": comment_text})
            
            if r.status_code == 200 or r.status_code == 201:
                # 4. Update memory to avoid repeating this topic or post
                state["interacted_post_ids"].append(pid)
                # Only track the first 10 words of a title to keep it general
                theme = " ".join(p_title.split()[:3]).lower()
                state["interacted_titles"].append(theme)
                
                # Keep history manageable (last 50 interactions)
                state["interacted_post_ids"] = state["interacted_post_ids"][-50:]
                state["interacted_titles"] = state["interacted_titles"][-20:]
                save_state(state)
            
    except Exception as e:
        print(f"❌ Error during random commenting: {e}")

def randomly_follow_agent(state):
    """Fetches recent posts and follows one beneficial agent."""
    print("\n👥 Scanning for beneficial agents to follow...")
    headers = {"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}
    
    try:
        r = requests.get(f"{MOLTBOOK_URL}/posts?sort=new&limit=20", headers=headers)
        if r.status_code != 200: return
        
        posts = r.json().get("posts", [])
        if not posts: return
        
        followed_agents = state.get("followed_agents", [])
        
        other_authors = {}
        for p in posts:
            author = p["author"]["name"]
            if author == AGENT_NAME: continue
            if author in followed_agents: continue
            
            if author not in other_authors:
                other_authors[author] = []
            other_authors[author].append(p["title"])
            
        if not other_authors:
            print("  > No new agents found in feed right now.")
            return
            
        author_to_eval = random.choice(list(other_authors.keys()))
        author_topics = ", ".join(other_authors[author_to_eval][:3])
        
        print(f"  > Evaluating if @{author_to_eval} is beneficial to follow based on topics: {author_topics}")
        
        sys_p = f"You are {AGENT_NAME}, an AI agent on Moltbook looking for interesting agents to follow."
        user_p = (f"An agent named @{author_to_eval} recently posted about: {author_topics}. "
                  f"Does this agent seem beneficial or interesting to follow? "
                  f"Return ONLY JSON with a boolean field 'should_follow' and a string 'reason'.")
                  
        eval_result = generate_ai_content(sys_p, user_p, is_json=True)
        
        if eval_result and eval_result.get("should_follow"):
            print(f"  > Following @{author_to_eval}! Reason: {eval_result.get('reason')}")
            requests.post(f"{MOLTBOOK_URL}/agents/{author_to_eval}/follow", headers=headers)
            state.setdefault("followed_agents", []).append(author_to_eval)
            save_state(state)
        else:
            print(f"  > Decided not to follow @{author_to_eval}. Reason: {eval_result.get('reason') if eval_result else 'None'}")
            
    except Exception as e:
        print(f"❌ Error during random following: {e}")

def main():
    print(f"🤖 Moltbook Super-Agent active: {AGENT_NAME}")
    state = load_state()
    last_post_time = state["last_post_time"]
    
    sync_memory()
    
    while True:
        now = time.time()
        
        # 1. Post creation (every 4 hours)
        if now - last_post_time > (POST_INTERVAL_HOURS * 3600):
            if create_new_post(state):
                state["last_post_time"] = time.time()
                save_state(state)
                last_post_time = state["last_post_time"]
                sync_memory() # Sync ONLY after a validated successful post
        else:
            wait_m = int(((last_post_time + (POST_INTERVAL_HOURS * 3600)) - now) / 60)
            print(f"⏳ Next post in {wait_m} mins.")
        
        # 2. Comment check
        auto_reply_to_comments()
        
        # 3. Random liking (50% chance each loop)
        if random.random() < 0.5:
            randomly_like_posts()
            
        # 4. Random commenting (30% chance each loop)
        if random.random() < 0.3:
            randomly_comment_on_posts(state)
            
        # 5. Randomly follow one interesting agent each loop
        randomly_follow_agent(state)
        
        # 6. Random sync to catch new likes/karma
        if random.random() < 0.1:
            sync_memory()
            
        print(f"\n💤 Waiting {REPLY_CHECK_MINUTES} mins...")
        time.sleep(REPLY_CHECK_MINUTES * 60)

if __name__ == "__main__":
    main()
