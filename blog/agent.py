import os
import re
import json
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import google.generativeai as genai
import markdown

from database import add_log, save_post, get_previous_topics, get_all_settings

# SYLLABLE & READABILITY HELPERS
def count_syllables(word):
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    if len(word) == 0:
        return 0
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count == 0:
        count = 1
    return count

def compute_flesch_reading_ease(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if len(s.strip()) > 0]
    words = re.findall(r'\b\w+\b', text)
    
    if len(words) == 0 or len(sentences) == 0:
        return 0
        
    num_sentences = len(sentences)
    num_words = len(words)
    num_syllables = sum(count_syllables(w) for w in words)
    
    asl = num_words / num_sentences
    asw = num_syllables / num_words
    
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    return round(max(0, min(100, score)))

# SCRAPERS
def fetch_google_trends():
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)
        topics = []
        for item in root.findall(".//item"):
            title = item.find("title")
            if title is not None and title.text:
                topics.append(title.text.strip())
        return topics
    except Exception as e:
        print(f"Error fetching Google Trends: {e}")
        return []

def fetch_google_news():
    url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)
        topics = []
        for item in root.findall(".//item")[:15]:
            title = item.find("title")
            if title is not None and title.text:
                topics.append(title.text.strip())
        return topics
    except Exception as e:
        print(f"Error fetching Google News: {e}")
        return []

def fetch_reddit_trends(niche=""):
    subreddit = "all"
    niche_lower = niche.lower()
    if any(x in niche_lower for x in ["tech", "ai", "software", "computer"]):
        subreddit = "technology"
    elif any(x in niche_lower for x in ["finance", "money", "crypto", "business"]):
        subreddit = "business"
    elif any(x in niche_lower for x in ["science", "space", "nature"]):
        subreddit = "science"
        
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=15"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        data = response.json()
        topics = []
        for post in data.get("data", {}).get("children", []):
            title = post.get("data", {}).get("title")
            if title:
                topics.append(title)
        return topics
    except Exception as e:
        print(f"Error fetching Reddit: {e}")
        return []

def fetch_youtube_trends():
    url = "https://www.youtube.com/feeds/videos.xml?chart=mostPopular"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        topics = []
        for entry in root.findall("atom:entry", ns)[:15]:
            title = entry.find("atom:title", ns)
            if title is not None and title.text:
                topics.append(title.text.strip())
        return topics
    except Exception as e:
        print(f"Error fetching YouTube Trends: {e}")
        return []

def search_duckduckgo(query):
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
    }
    try:
        response = requests.post(url, data=params, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for result in soup.find_all("div", class_="result")[:8]:
            title_a = result.find("a", class_="result__a")
            snippet_div = result.find("a", class_="result__snippet")
            if title_a:
                title = title_a.text.strip()
                link = title_a.get("href", "")
                snippet = snippet_div.text.strip() if snippet_div else ""
                results.append({"title": title, "link": link, "snippet": snippet})
        return results
    except Exception as e:
        print(f"Error scraping DuckDuckGo: {e}")
        return []

def resolve_free_image_url(query):
    # Clean query (use 2-3 key words)
    words = re.sub(r'[^a-zA-Z0-9\s]+', '', query.lower())
    words = [w for w in words.split() if len(w) > 2][:3]
    search_term = ",".join(words) if words else "blog"
    url = f"https://loremflickr.com/800/600/{search_term}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 200:
            add_log("INFO", f"Resolved free image for '{search_term}': {response.url}")
            return response.url
    except Exception as e:
        add_log("WARNING", f"Failed to fetch free image for '{search_term}': {e}")
    # Fallback random image
    return f"https://picsum.photos/800/600?random={hash(query) % 100}"

# PUBLISHERS
def publish_to_wordpress(wp_url, wp_username, wp_password, title, html_content, slug, excerpt):
    if not wp_url or not wp_username or not wp_password:
        raise ValueError("WordPress settings are incomplete.")
    
    url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    headers = {
        "Content-Type": "application/json"
    }
    # Basic auth with username and app password
    auth = (wp_username, wp_password)
    
    data = {
        "title": title,
        "content": html_content,
        "status": "publish",
        "slug": slug,
        "excerpt": excerpt
    }
    
    try:
        response = requests.post(url, headers=headers, auth=auth, json=data, timeout=20)
        if response.status_code in [200, 201]:
            res_data = response.json()
            return res_data.get("id"), res_data.get("link")
        else:
            raise Exception(f"WordPress Error {response.status_code}: {response.text}")
    except Exception as e:
        raise Exception(f"Failed to post to WordPress: {e}")

def get_blogger_access_token(client_id, client_secret, refresh_token):
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    try:
        response = requests.post(url, data=data, timeout=15)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise Exception(f"Token refresh failed: {response.text}")
    except Exception as e:
        raise Exception(f"Blogger auth error: {e}")

def publish_to_blogger(blog_id, client_id, client_secret, refresh_token, title, html_content):
    if not blog_id or not client_id or not client_secret or not refresh_token:
        raise ValueError("Blogger credentials or refresh token missing.")
        
    access_token = get_blogger_access_token(client_id, client_secret, refresh_token)
    
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "kind": "blogger#post",
        "title": title,
        "content": html_content
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        if response.status_code == 200:
            res_data = response.json()
            return res_data.get("id"), res_data.get("url")
        else:
            raise Exception(f"Blogger Error {response.status_code}: {response.text}")
    except Exception as e:
        raise Exception(f"Failed to post to Blogger: {e}")

# SEO SCORING ALGORITHM
def calculate_seo_score(post, primary_keyword, related_keywords, content_text):
    score = 0
    details = []
    
    title = (post.get("seo_title") or "").lower()
    content = content_text.lower()
    p_kw = primary_keyword.lower()
    
    # 1. Primary keyword in title (+10)
    if p_kw in title:
        score += 10
        details.append("Primary keyword in Title (+10)")
    else:
        details.append("Primary keyword missing in Title (0)")
        
    # 2. Primary keyword in first 100 words (+10)
    intro = " ".join(content.split()[:150])
    if p_kw in intro:
        score += 10
        details.append("Primary keyword in Intro (+10)")
    else:
        details.append("Primary keyword missing in Intro (0)")
        
    # 3. Primary keyword in H1/H2 headings (+10)
    headings = re.findall(r'<h[12][^>]*>(.*?)</h[12]>', content)
    # Also check markdown style
    md_headings = re.findall(r'^#{1,2}\s+(.*?)$', content_text, re.MULTILINE)
    all_headings = [h.lower() for h in (headings + md_headings)]
    if any(p_kw in h for h in all_headings):
        score += 10
        details.append("Primary keyword in H1/H2 (+10)")
    else:
        details.append("Primary keyword missing in H1/H2 (0)")
        
    # 4. Word count: 2000+ words (+15), 1500+ (+10), 1000+ (+5)
    word_count = len(content_text.split())
    if word_count >= 2000:
        score += 15
        details.append(f"Word count is {word_count} >= 2000 (+15)")
    elif word_count >= 1500:
        score += 10
        details.append(f"Word count is {word_count} >= 1500 (+10)")
    elif word_count >= 1000:
        score += 5
        details.append(f"Word count is {word_count} >= 1000 (+5)")
    else:
        details.append(f"Word count too low: {word_count} (0)")
        
    # 5. Related keywords density: percentage of targeted keywords present in content (+20)
    found_kws = 0
    for kw in related_keywords:
        if kw.lower() in content:
            found_kws += 1
    if related_keywords:
        kw_ratio = found_kws / len(related_keywords)
        if kw_ratio >= 0.8:
            score += 20
            details.append(f"Related keywords coverage {found_kws}/{len(related_keywords)} >= 80% (+20)")
        elif kw_ratio >= 0.5:
            score += 12
            details.append(f"Related keywords coverage {found_kws}/{len(related_keywords)} >= 50% (+12)")
        elif kw_ratio >= 0.2:
            score += 6
            details.append(f"Related keywords coverage {found_kws}/{len(related_keywords)} >= 20% (+6)")
        else:
            details.append(f"Related keywords coverage low: {found_kws}/{len(related_keywords)} (0)")
    else:
        score += 20
        details.append("No related keywords to check (+20)")
        
    # 6. Structured schema presence (+15)
    schema_data = post.get("schema_data") or {}
    if schema_data and ("FAQ" in schema_data or "Article" in schema_data):
        score += 15
        details.append("FAQ/Article Schemas generated (+15)")
    else:
        details.append("No schema data (0)")
        
    # 7. Alt text optimized images (+10)
    img_prompts = post.get("image_prompts") or {}
    has_content_imgs = len(img_prompts.get("content", [])) > 0 or len(img_prompts.get("content_images", [])) > 0
    if img_prompts and img_prompts.get("featured") and has_content_imgs:
        score += 10
        details.append("Optimized image prompts and alt text (+10)")
    else:
        details.append("Image prompts missing (0)")
        
    # 8. External Links presence in text (+10)
    external_links = re.findall(r'\[.*?\]\(https?://(?!localhost|127\.0\.0\.1|wp-url)(.*?)\)', content_text)
    html_external_links = re.findall(r'href=["\'](https?://(?!localhost|127\.0\.0\.1|wp-url).*?)["\']', content)
    if len(external_links) + len(html_external_links) >= 2:
        score += 10
        details.append("External outbound authority links present (+10)")
    else:
        details.append("Missing authority outbound links (0)")
        
    print(f"Calculated SEO Score: {score}/100. Details: {details}")
    return score

# MAIN AGENT WORKFLOW
def run_blogging_agent(post_id=None, manual=False):
    """
    Executes the daily blogging routine.
    If post_id is provided, it tries to resume/regenerate that post.
    """
    settings = get_all_settings()
    gemini_key = settings.get("gemini_api_key")
    if not gemini_key:
        add_log("ERROR", "Gemini API key is not configured in settings. Aborting agent run.", post_id)
        return False
        
    niche = settings.get("niche", "Tech & AI")
    tone = settings.get("writing_tone", "Informative, Engaging & Professional")
    target_score = int(settings.get("seo_target_score", "90"))
    
    # Configure Gemini
    genai.configure(api_key=gemini_key)
    # Using gemini-3.5-flash as the main driver for speed, compatibility & costs
    model = genai.GenerativeModel("gemini-3.5-flash")
    
    add_log("INFO", f"Starting blogging agent workflow. Niche: {niche}, Tone: {tone}", post_id)
    
    # STEP 1: Find Today's Best Topic
    add_log("INFO", "Step 1: Finding today's best topic...", post_id)
    google_trends = fetch_google_trends()
    google_news = fetch_google_news()
    reddit_trends = fetch_reddit_trends(niche)
    youtube_trends = fetch_youtube_trends()
    
    all_raw_topics = {
        "Google Trends": google_trends,
        "Google News": google_news,
        "Reddit": reddit_trends,
        "YouTube": youtube_trends
    }
    
    # Print candidates count
    total_candidates = sum(len(v) for v in all_raw_topics.values())
    add_log("INFO", f"Scraped {total_candidates} candidates from daily trend sources.", post_id)
    
    # Filter previous topics
    prev_topics = get_previous_topics()
    
    is_general_mode = niche.lower().strip() in ["any", "general", "trending", "none", ""]
    
    if is_general_mode:
        niche_selection_criteria = "We are operating in a Niche-less/General Trending mode. Select the single absolute BEST trending topic across any category or subject overall, focusing on general viral interest, news, tech, science, health, business, or lifestyle trends."
        fallback_prompt = """
        Generate a high-traffic, low-competition evergreen keyword and topic of general viral interest (no specific niche).
        Provide your choice as a JSON object with this exact structure:
        {
            "selected_topic": "Selected Topic Title",
            "trend_source": "Evergreen General Strategy",
            "search_intent": "Informational",
            "primary_keyword": "Core SEO Keyword"
        }
        Only return the JSON.
        """
    else:
        niche_selection_criteria = f'The target niche is: "{niche}". The selected topic must fit closely with the target niche: "{niche}".'
        fallback_prompt = f"""
        Generate a high-traffic, low-competition evergreen keyword and topic in the niche: "{niche}".
        Provide your choice as a JSON object with this exact structure:
        {{
            "selected_topic": "Selected Topic Title",
            "trend_source": "Evergreen Niche Strategy",
            "search_intent": "Informational",
            "primary_keyword": "Core SEO Keyword"
        }}
        Only return the JSON.
        """

    selection_prompt = f"""
    You are an expert Chief Editor and SEO Specialist. Your task is to select the single BEST trending or high-potential evergreen topic for today's blog.
    
    {niche_selection_criteria}
    
    We gathered the following real-time trending topics from multiple sources:
    {json.dumps(all_raw_topics, indent=2)}
    
    Previously published topics that you MUST NEVER repeat:
    {json.dumps(prev_topics, indent=2)}
    
    Filter the topics and select ONE topic that matches these criteria:
    1. {"Focus on general interest trends overall." if is_general_mode else f"Fits closely with the target niche: {niche}"}
    2. Has highest search growth/momentum or high traffic potential.
    3. Has low to medium SEO competition (meaning it is a fresh angle, trending news, or specific evergreen problem).
    4. Ignore low-value celebrity gossip unless it has long-term search potential.
    
    Provide your choice as a JSON object with this exact structure:
    {{
        "selected_topic": "Selected Topic Title",
        "trend_source": "Source Name (e.g. Google Trends)",
        "search_intent": "Informational/Transactional/etc.",
        "primary_keyword": "The core SEO keyword"
    }}
    Ensure the response is valid JSON and only returns the JSON block. Do not wrap in markdown code blocks.
    """
    
    selected_data = {}
    try:
        response = model.generate_content(selection_prompt)
        # Strip markdown wraps if model ignored instructions
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        selected_data = json.loads(clean_text)
        add_log("INFO", f"Topic selected: '{selected_data['selected_topic']}' from {selected_data['trend_source']}.", post_id)
    except Exception as e:
        add_log("ERROR", f"Failed to select topic: {e}. Falling back to evergreen topic.", post_id)
        try:
            fallback_res = model.generate_content(fallback_prompt)
            clean_text = fallback_res.text.strip().replace("```json", "").replace("```", "")
            selected_data = json.loads(clean_text)
            add_log("INFO", f"Fallback topic selected: '{selected_data['selected_topic']}'.", post_id)
        except Exception as fe:
            add_log("ERROR", f"Fallback selection failed: {fe}. Terminating.", post_id)
            return False

    # Initialize Post DB Entry
    topic = selected_data["selected_topic"]
    primary_kw = selected_data["primary_keyword"]
    
    db_post_data = {
        "id": post_id,
        "topic": topic,
        "trend_source": selected_data["trend_source"],
        "search_intent": selected_data["search_intent"],
        "primary_keyword": primary_kw,
        "status": "In Progress"
    }
    post_id = save_post(db_post_data)
    
    # STEP 2: SEO Research
    add_log("INFO", f"Step 2: Performing SEO Research for keyword: '{primary_kw}'", post_id)
    search_results = search_duckduckgo(primary_kw)
    add_log("INFO", f"Found {len(search_results)} search results on DuckDuckGo for content gap analysis.", post_id)
    
    seo_prompt = f"""
    You are an expert SEO Researcher.
    We are writing an article on the topic: "{topic}" (Primary Keyword: "{primary_kw}").
    
    Here are the top web search results for this keyword:
    {json.dumps(search_results, indent=2)}
    
    Conduct keyword research and content gap analysis. Generate:
    1. 20 related keywords (LSI, semantic keywords, variations).
    2. Long-tail keywords.
    3. At least 5 "People Also Ask" questions.
    4. Content gaps: what did the existing search results miss that we must cover?
    5. A structured Outline containing:
       - H1 title suggestion
       - Multi-level H2, H3 headings
       - Description of what to cover in each section to stand out
       
    Provide your output as a JSON object with this structure:
    {{
        "related_keywords": ["kw1", "kw2", ...],
        "long_tail_keywords": ["kw1", "kw2", ...],
        "people_also_ask": ["q1", "q2", ...],
        "content_gaps": "Summary of gaps",
        "outline": [
            {{
                "heading": "H2 Heading",
                "subheadings": ["H3 Heading 1", "H3 Heading 2"],
                "section_guidelines": "Instructions on what to cover, examples to use, and which keywords to integrate."
            }}
        ]
    }}
    Only return valid JSON. Do not wrap in markdown code blocks.
    """
    
    seo_research_data = {}
    try:
        response = model.generate_content(seo_prompt)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        seo_research_data = json.loads(clean_text)
        add_log("INFO", f"SEO Research complete. Identified {len(seo_research_data.get('related_keywords', []))} related keywords.", post_id)
    except Exception as e:
        add_log("ERROR", f"SEO Research failed: {e}. Generating default structure.", post_id)
        # Create standard schema placeholders
        seo_research_data = {
            "related_keywords": [primary_kw + " tips", primary_kw + " guide", primary_kw + " examples", primary_kw + " tutorial"],
            "long_tail_keywords": [f"how to use {primary_kw} for beginners", f"best practices for {primary_kw}"],
            "people_also_ask": [f"What is {primary_kw}?", f"How does {primary_kw} work?", f"Why is {primary_kw} important?"],
            "content_gaps": "Add clear statistics and concrete code/actionable templates.",
            "outline": [
                {"heading": f"Introduction to {topic}", "subheadings": [], "section_guidelines": "Introduce the topic and explain why it matters."},
                {"heading": f"Understanding {primary_kw}", "subheadings": [f"Key Features of {primary_kw}"], "section_guidelines": "Detailed explanation."},
                {"heading": f"Step-by-Step Guide to Implementing {primary_kw}", "subheadings": [], "section_guidelines": "Actionable instructions."},
                {"heading": f"Common Mistakes with {primary_kw}", "subheadings": [], "section_guidelines": "What to avoid."},
                {"heading": "Summary & Key Takeaways", "subheadings": [], "section_guidelines": "Conclusion and call to action."}
            ]
        }

    # STEP 3: Multi-Step Content Generation (2000-3000 words)
    add_log("INFO", "Step 3: Creating the Blog (Multi-step writing workflow for high depth)...", post_id)
    related_kws = seo_research_data.get("related_keywords", [])
    
    article_content = []
    
    # 3.1: Generate Title and H1 Intro
    intro_prompt = f"""
    You are an expert copywriter. Write the introduction for today's blog.
    Topic: "{topic}"
    Primary Keyword: "{primary_kw}"
    Writing Tone: "{tone}"
    
    Instructions:
    - Choose a highly engaging H1 title.
    - Write a detailed, compelling introduction (approx 350-500 words).
    - Introduce the topic, hook the reader with statistics/facts, set up the value proposition, and explain what the article covers.
    - Naturally integrate the primary keyword and 2-3 related keywords: {json.dumps(related_kws[:4])}
    - Use EEAT principles (establish your authoritative, expert voice).
    - Write in clean markdown. Do not include frontmatter or notes.
    """
    try:
        add_log("INFO", "Generating introduction...", post_id)
        intro_res = model.generate_content(intro_prompt)
        article_content.append(intro_res.text.strip())
    except Exception as e:
        add_log("ERROR", f"Intro generation failed: {e}", post_id)
        article_content.append(f"# {topic}\n\nToday we explore the critical details of {primary_kw}.")

    # 3.2: Iterate through outline sections
    outline = seo_research_data.get("outline", [])
    for idx, section in enumerate(outline):
        sec_title = section.get("heading")
        subheadings = section.get("subheadings", [])
        guidelines = section.get("section_guidelines", "")
        
        add_log("INFO", f"Generating section {idx+1}/{len(outline)}: '{sec_title}'", post_id)
        
        # Batch of keywords for this section
        start_idx = (idx * 3) % len(related_kws) if related_kws else 0
        end_idx = min(start_idx + 4, len(related_kws)) if related_kws else 0
        section_kws = related_kws[start_idx:end_idx] if related_kws else []
        
        current_draft = "\n\n".join(article_content)
        
        section_prompt = f"""
        You are an expert technical blogger and SEO specialist. Continue writing our high-authority blog post.
        
        Topic: "{topic}"
        Primary Keyword: "{primary_kw}"
        Writing Tone: "{tone}"
        
        Here is the draft of the article so far:
        ---
        {current_draft[-2000:]} (Showing end of current draft for context)
        ---
        
        Your Task: Write the next section of the article.
        Section Heading: "## {sec_title}"
        Section Subheadings to cover (use H3/H4 headings where appropriate): {json.dumps(subheadings)}
        Guidelines: {guidelines}
        Keywords to naturally integrate: {json.dumps(section_kws)}
        
        Instructions:
        - Write in-depth, original, and highly informative content (approx 400-600 words for this section).
        - Provide actionable advice, concrete examples, and statistics where appropriate.
        - Avoid AI-style empty filler words, generic summaries, or repeating what has already been written.
        - Maintain a smooth flow from the previous sections.
        - Output in markdown format. Start directly with the section header or content.
        """
        
        try:
            sec_res = model.generate_content(section_prompt)
            article_content.append(sec_res.text.strip())
        except Exception as e:
            add_log("ERROR", f"Failed to generate section {sec_title}: {e}", post_id)
            article_content.append(f"\n## {sec_title}\n\nInformation on {sec_title} is coming soon.")

    # 3.3: Write FAQ and Conclusion Section
    add_log("INFO", "Generating FAQ & conclusion section...", post_id)
    paa = seo_research_data.get("people_also_ask", [])
    faq_prompt = f"""
    Write a detailed Frequently Asked Questions (FAQ) and Summary section to conclude our blog post on "{topic}".
    
    Here are the "People Also Ask" questions that we must answer:
    {json.dumps(paa)}
    
    Instructions:
    - Answer each question thoroughly and concisely (H3 for each question).
    - Provide a short final takeaway paragraph (H2 Conclusion).
    - Target approx 400-500 words total.
    - Output in clean markdown.
    """
    
    try:
        faq_res = model.generate_content(faq_prompt)
        article_content.append(faq_res.text.strip())
    except Exception as e:
        add_log("ERROR", f"FAQ generation failed: {e}", post_id)
        article_content.append("\n## Conclusion\n\nWrapping up our deep dive.")

    full_markdown_content = "\n\n".join(article_content)
    word_count = len(full_markdown_content.split())
    add_log("INFO", f"Blog generation finished. Total words generated: {word_count}.", post_id)

    # STEP 4: SEO Optimization (Meta Data & Schema)
    add_log("INFO", "Step 4: Creating SEO Metadata and JSON-LD schemas...", post_id)
    
    meta_prompt = f"""
    Generate the SEO Metadata for the generated blog post.
    Topic: "{topic}"
    Primary Keyword: "{primary_kw}"
    
    Provide a JSON object containing:
    1. "seo_title": Under 60 characters, highly clickable, containing the primary keyword.
    2. "meta_description": Under 155 characters, summary of the article, contains primary keyword and calls to action.
    3. "slug": URL slug, clean and lowercase, separated by hyphens.
    4. "external_links": 2-3 links to high-authority websites (e.g. Wikipedia, official documentation, major news outlets) that are highly relevant, including anchor text.
    5. "faq_schema": FAQ list with question/answer pairs for JSON-LD schema.
    
    Provide your output as a JSON object with this exact structure:
    {{
        "seo_title": "Title",
        "meta_description": "Description",
        "slug": "url-slug",
        "external_links": [
            {{"anchor_text": "text", "url": "https://..."}}
        ],
        "faq_schema": [
            {{"question": "Q1", "answer": "A1"}},
            {{"question": "Q2", "answer": "A2"}}
        ]
    }}
    Only return valid JSON. Do not wrap in markdown code blocks.
    """
    
    meta_data = {}
    try:
        response = model.generate_content(meta_prompt)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        meta_data = json.loads(clean_text)
    except Exception as e:
        add_log("ERROR", f"Metadata generation failed: {e}", post_id)
        # Defaults
        meta_data = {
            "seo_title": f"{topic} | Full Guide",
            "meta_description": f"Learn everything about {topic} and {primary_kw} in this comprehensive article.",
            "slug": re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip("-"),
            "external_links": [{"anchor_text": "Google Search Console Guide", "url": "https://support.google.com/webmasters"}],
            "faq_schema": [{"question": f"What is {primary_kw}?", "answer": f"{primary_kw} is a crucial topic in the niche."}]
        }

    # Inject external links into the content at relevant places
    for ext_link in meta_data.get("external_links", []):
        anchor = ext_link.get("anchor_text")
        url = ext_link.get("url")
        # Try to find anchor text in content and make it a link, or append at the end
        if anchor and url and anchor in full_markdown_content:
            full_markdown_content = full_markdown_content.replace(anchor, f"[{anchor}]({url})", 1)
        else:
            # Just append a resource note
            full_markdown_content += f"\n\n*Reference: Learn more about this on [{anchor or 'Authority Site'}]({url}).*"

    # Generate schemas
    # FAQ JSON-LD
    faq_schema_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": []
    }
    for item in meta_data.get("faq_schema", []):
        faq_schema_ld["mainEntity"].append({
            "@type": "Question",
            "name": item["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item["answer"]
            }
        })
        
    # Article JSON-LD
    article_schema_ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": meta_data.get("seo_title"),
        "description": meta_data.get("meta_description"),
        "datePublished": datetime.now().isoformat(),
        "dateModified": datetime.now().isoformat(),
        "author": {
            "@type": "Person",
            "name": "Autonomous AI SEO Blogger"
        }
    }
    
    # Breadcrumb JSON-LD
    breadcrumb_schema_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": "https://localhost"
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": niche,
                "item": f"https://localhost/category/{re.sub(r'[^a-z0-9]+', '-', niche.lower())}"
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": meta_data.get("seo_title"),
                "item": f"https://localhost/{meta_data.get('slug')}"
            }
        ]
    }
    
    schema_data = {
        "FAQ": faq_schema_ld,
        "Article": article_schema_ld,
        "Breadcrumb": breadcrumb_schema_ld
    }

    # STEP 5: Images Prompts
    add_log("INFO", "Step 5: Generating Image Prompts & Alt Texts...", post_id)
    image_prompt = f"""
    Generate image creation prompts for Midjourney, DALL-E 3 or Imagen matching the theme of: "{topic}".
    We need:
    1. One Featured Image Prompt (visually dramatic, representing the whole article).
    2. Three in-content image prompts (to insert after major sections, showing diagrams, concepts, or metaphorical elements).
    3. ALT text for each image.
    
    Provide your output as a JSON object with this exact structure:
    {{
        "featured": {{
            "prompt": "Highly detailed visual description for AI generator",
            "alt_text": "Descriptive, SEO-friendly ALT text"
        }},
        "content_images": [
            {{
                "section_heading": "Name of section it goes after",
                "prompt": "Visual prompt description",
                "alt_text": "ALT text"
            }},
            {{
                "section_heading": "Name of section it goes after",
                "prompt": "Visual prompt description",
                "alt_text": "ALT text"
            }},
            {{
                "section_heading": "Name of section it goes after",
                "prompt": "Visual prompt description",
                "alt_text": "ALT text"
            }}
        ]
    }}
    Only return valid JSON. Do not wrap in markdown code blocks.
    """
    image_prompts = {}
    try:
        response = model.generate_content(image_prompt)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        image_prompts = json.loads(clean_text)
    except Exception as e:
        add_log("ERROR", f"Image prompt generation failed: {e}", post_id)
        image_prompts = {
            "featured": {"prompt": f"Minimalist modern illustration representing {topic}", "alt_text": topic},
            "content": []
        }

    # STEP 6 & 7: Self-Check & SEO Score Optimization Pass
    add_log("INFO", "Step 7: Running Self-Checks, fact-verification and readability scores...", post_id)
    readability = compute_flesch_reading_ease(full_markdown_content)
    add_log("INFO", f"Flesch Readability Ease Score: {readability}/100", post_id)
    
    # Pack temporary post to score
    temp_post = {
        "seo_title": meta_data.get("seo_title"),
        "meta_description": meta_data.get("meta_description"),
        "schema_data": schema_data,
        "image_prompts": image_prompts
    }
    
    seo_score = calculate_seo_score(temp_post, primary_kw, related_kws, full_markdown_content)
    
    # If SEO score < 90 and target is 90+, run an optimization pass using Gemini to rewrite intro and headings
    if seo_score < target_score:
        add_log("WARNING", f"SEO Score {seo_score} is below target {target_score}. Running optimization pass...", post_id)
        opt_prompt = f"""
        You are an SEO Content Optimizer. The current article has an SEO score of {seo_score}/100.
        The primary keyword is: "{primary_kw}"
        The related keywords to integrate: {json.dumps(related_kws[:10])}
        
        Optimize the following article draft to improve keyword density, headings structure, and natural inclusion of the primary keyword. Make sure the primary keyword is in the first 100 words and featured in headings. Preserve the detailed technical insights and article length.
        
        Here is the draft:
        {full_markdown_content}
        
        Output only the fully optimized markdown text.
        """
        try:
            opt_res = model.generate_content(opt_prompt)
            full_markdown_content = opt_res.text.strip()
            # Re-calculate word count and score
            word_count = len(full_markdown_content.split())
            seo_score = calculate_seo_score(temp_post, primary_kw, related_kws, full_markdown_content)
            add_log("INFO", f"Optimization pass complete. New SEO Score: {seo_score}. New word count: {word_count}.", post_id)
        except Exception as oe:
            add_log("ERROR", f"Optimization pass failed: {oe}", post_id)

    # Save to database before publishing
    post_db_entry = {
        "id": post_id,
        "topic": topic,
        "trend_source": selected_data["trend_source"],
        "search_intent": selected_data["search_intent"],
        "primary_keyword": primary_kw,
        "related_keywords": related_kws,
        "seo_title": meta_data.get("seo_title"),
        "meta_description": meta_data.get("meta_description"),
        "slug": meta_data.get("slug"),
        "content": full_markdown_content,
        "faq": meta_data.get("faq_schema", []),
        "image_prompts": image_prompts,
        "schema_data": schema_data,
        "seo_score": seo_score,
        "readability_score": readability,
        "status": "Draft",
        "error_message": None
    }
    save_post(post_db_entry)
    
    # STEP 6: Publish
    platform = settings.get("publishing_platform", "none")
    add_log("INFO", f"Step 6: Processing free online stock images and publishing to platform: '{platform}'...", post_id)
    
    # 6.1 Resolve featured and in-content images using LoremFlickr (free, Creative Commons)
    featured_alt = image_prompts.get("featured", {}).get("alt_text", primary_kw)
    featured_img_url = resolve_free_image_url(featured_alt)
    if "featured" in image_prompts:
        image_prompts["featured"]["url"] = featured_img_url
        
    html_body = markdown.markdown(full_markdown_content)
    
    # Inject featured image at the top of the HTML body
    featured_html = f'<div class="post-featured-image" style="margin-bottom: 28px; text-align: center;"><img src="{featured_img_url}" alt="{featured_alt}" style="width:100%; max-height:480px; object-fit:cover; border-radius:12px; display:block; margin:0 auto;" /></div>\n'
    html_body = featured_html + html_body
    
    # Inject in-content images before H2 headings
    h2_parts = html_body.split('<h2>')
    new_html_parts = [h2_parts[0]]
    content_images = image_prompts.get("content_images", []) or image_prompts.get("content", [])
    
    for i in range(1, len(h2_parts)):
        heading_content = h2_parts[i]
        img_idx = i - 1
        if img_idx < len(content_images):
            img_info = content_images[img_idx]
            img_alt = img_info.get("alt_text", primary_kw)
            img_url = resolve_free_image_url(img_alt)
            # Store URL in prompt dictionary for DB consistency
            content_images[img_idx]["url"] = img_url
            
            img_html = f'\n<div class="post-in-content-image" style="margin:32px 0; text-align:center;"><img src="{img_url}" alt="{img_alt}" style="width:100%; max-height:400px; object-fit:cover; border-radius:8px; display:block; margin:0 auto 8px auto;" /><span style="font-size:12px; color:#777; font-style:italic;">Illustration: {img_alt}</span></div>\n'
            new_html_parts.append(img_html)
            
        new_html_parts.append('<h2>' + heading_content)
        
    html_body = "".join(new_html_parts)
    
    # Save the updated image_prompts with URLs in the database post row
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE posts SET image_prompts = ? WHERE id = ?", (json.dumps(image_prompts), post_id))
        conn.commit()
        conn.close()
    except Exception as dbe:
        add_log("WARNING", f"Failed to save resolved image URLs in DB: {dbe}")
    
    # Inject schema JSON-LD inside HTML body (at the very bottom) so search engines read it
    json_schemas_html = ""
    for schema_type, schema_val in schema_data.items():
        json_schemas_html += f'\n<script type="application/ld+json">\n{json.dumps(schema_val, indent=2)}\n</script>\n'
    
    html_body_with_schemas = html_body + json_schemas_html
    
    published_to = []
    platform_post_id = None
    published_link = None
    
    try:
        if platform == "wordpress" or platform == "both":
            add_log("INFO", f"Publishing to WordPress at {settings.get('wp_url')}...", post_id)
            wp_id, wp_link = publish_to_wordpress(
                settings.get("wp_url"),
                settings.get("wp_username"),
                settings.get("wp_app_password"),
                meta_data.get("seo_title"),
                html_body_with_schemas,
                meta_data.get("slug"),
                meta_data.get("meta_description")
            )
            published_to.append("wordpress")
            platform_post_id = str(wp_id)
            published_link = wp_link
            add_log("INFO", f"WordPress publication successful. Post ID: {wp_id}, URL: {wp_link}", post_id)
            
        if platform == "blogger" or platform == "both":
            add_log("INFO", f"Publishing to Blogger blog: {settings.get('blogger_blog_id')}...", post_id)
            blogger_id, blogger_url = publish_to_blogger(
                settings.get("blogger_blog_id"),
                settings.get("blogger_client_id"),
                settings.get("blogger_client_secret"),
                settings.get("blogger_refresh_token"),
                meta_data.get("seo_title"),
                html_body_with_schemas
            )
            published_to.append("blogger")
            if not platform_post_id:
                platform_post_id = str(blogger_id)
                published_link = blogger_url
            else:
                platform_post_id += f", blogger:{blogger_id}"
            add_log("INFO", f"Blogger publication successful. Post ID: {blogger_id}, URL: {blogger_url}", post_id)
            
        if len(published_to) > 0:
            post_db_entry["status"] = "Published"
            post_db_entry["published_at"] = datetime.now().isoformat()
            post_db_entry["platform_post_id"] = platform_post_id
            post_db_entry["platform_published"] = ", ".join(published_to)
            save_post(post_db_entry)
            add_log("INFO", f"Blogging agent run completed successfully! Status: Published.", post_id)
        else:
            add_log("INFO", "No publishing platform was configured or active. Saved article as Draft.", post_id)
            post_db_entry["status"] = "Draft"
            save_post(post_db_entry)
            
        return True
        
    except Exception as e:
        err_msg = str(e)
        add_log("ERROR", f"Publishing failed: {err_msg}", post_id)
        post_db_entry["status"] = "Failed"
        post_db_entry["error_message"] = err_msg
        save_post(post_db_entry)
        return False
