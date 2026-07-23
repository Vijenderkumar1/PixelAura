import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blog_agent.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # 2. Posts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        trend_source TEXT,
        search_intent TEXT,
        primary_keyword TEXT,
        related_keywords TEXT, -- JSON array of strings
        seo_title TEXT,
        meta_description TEXT,
        slug TEXT,
        content TEXT,          -- Markdown or HTML body
        faq TEXT,              -- JSON array of FAQ objects
        image_prompts TEXT,    -- JSON object {featured, content:[]}
        schema_data TEXT,      -- JSON object containing FAQ, Article, Breadcrumb schemas
        seo_score INTEGER,
        readability_score INTEGER,
        status TEXT DEFAULT 'Draft', -- Draft, Published, Scheduled, Failed
        published_at TEXT,
        platform_post_id TEXT, -- ID from WP or Blogger
        platform_published TEXT DEFAULT 'none', -- wordpress, blogger, both, none
        error_message TEXT,
        created_at TEXT NOT NULL
    )
    """)
    
    # 3. Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE SET NULL
    )
    """)
    
    # Initialize default settings if they don't exist
    default_settings = {
        "gemini_api_key": "",
        "niche": "Tech & Artificial Intelligence",
        "writing_tone": "Informative, Engaging & Professional",
        "word_count_target": "2000-3000",
        "seo_target_score": "90",
        "publishing_platform": "none", # wordpress, blogger, both, none
        "wp_url": "",
        "wp_username": "",
        "wp_app_password": "",
        "blogger_blog_id": "6866056087413867375",
        "blogger_client_id": "",
        "blogger_client_secret": "",
        "blogger_refresh_token": "",
        "scheduler_enabled": "0", # 0=disabled, 1=enabled
        "scheduler_time": "09:00", # HH:MM daily
        "last_scheduler_run_date": "", # YYYY-MM-DD
        "last_scheduler_run_timestamp": "",
        "posts_per_day": "1"
    }
    
    for key, value in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
    
    # Auto-migrate: update to default user blog ID if it is currently empty
    cursor.execute("UPDATE settings SET value = '6866056087413867375' WHERE key = 'blogger_blog_id' AND value = ''")
        
    conn.commit()
    conn.close()

# Helper Settings functions
def get_setting(key, default=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["value"]
    return default

def set_setting(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_all_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

# Helper Posts functions
def save_post(post_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if this is an update or create
    post_id = post_data.get("id")
    now_str = datetime.now().isoformat()
    
    related_keywords = json.dumps(post_data.get("related_keywords", []))
    faq = json.dumps(post_data.get("faq", []))
    image_prompts = json.dumps(post_data.get("image_prompts", {}))
    schema_data = json.dumps(post_data.get("schema_data", {}))
    
    if post_id:
        cursor.execute("""
        UPDATE posts SET
            topic = ?, trend_source = ?, search_intent = ?, primary_keyword = ?,
            related_keywords = ?, seo_title = ?, meta_description = ?, slug = ?,
            content = ?, faq = ?, image_prompts = ?, schema_data = ?,
            seo_score = ?, readability_score = ?, status = ?, published_at = ?,
            platform_post_id = ?, platform_published = ?, error_message = ?
        WHERE id = ?
        """, (
            post_data["topic"], post_data.get("trend_source"), post_data.get("search_intent"),
            post_data.get("primary_keyword"), related_keywords, post_data.get("seo_title"),
            post_data.get("meta_description"), post_data.get("slug"), post_data["content"],
            faq, image_prompts, schema_data, post_data.get("seo_score"), post_data.get("readability_score"),
            post_data.get("status", "Draft"), post_data.get("published_at"), post_data.get("platform_post_id"),
            post_data.get("platform_published", "none"), post_data.get("error_message"), post_id
        ))
    else:
        cursor.execute("""
        INSERT INTO posts (
            topic, trend_source, search_intent, primary_keyword, related_keywords,
            seo_title, meta_description, slug, content, faq, image_prompts, schema_data,
            seo_score, readability_score, status, published_at, platform_post_id,
            platform_published, error_message, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post_data["topic"], post_data.get("trend_source"), post_data.get("search_intent"),
            post_data.get("primary_keyword"), related_keywords, post_data.get("seo_title"),
            post_data.get("meta_description"), post_data.get("slug"), post_data["content"],
            faq, image_prompts, schema_data, post_data.get("seo_score"), post_data.get("readability_score"),
            post_data.get("status", "Draft"), post_data.get("published_at"), post_data.get("platform_post_id"),
            post_data.get("platform_published", "none"), post_data.get("error_message"), now_str
        ))
        post_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return post_id

def get_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        post = dict(row)
        post["related_keywords"] = json.loads(post["related_keywords"] or "[]")
        post["faq"] = json.loads(post["faq"] or "[]")
        post["image_prompts"] = json.loads(post["image_prompts"] or "{}")
        post["schema_data"] = json.loads(post["schema_data"] or "{}")
        return post
    return None

def delete_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

def get_all_posts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    posts = []
    for row in rows:
        post = dict(row)
        post["related_keywords"] = json.loads(post["related_keywords"] or "[]")
        post["faq"] = json.loads(post["faq"] or "[]")
        post["image_prompts"] = json.loads(post["image_prompts"] or "{}")
        post["schema_data"] = json.loads(post["schema_data"] or "{}")
        posts.append(post)
    return posts

# Helper Logs functions
def add_log(level, message, post_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    cursor.execute("INSERT INTO logs (post_id, level, message, timestamp) VALUES (?, ?, ?, ?)",
                   (post_id, level, message, now_str))
    conn.commit()
    conn.close()
    # Print to console as well
    print(f"[{now_str}] [{level}] {message}")

def get_logs(limit=200):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logs")
    conn.commit()
    conn.close()

def get_previous_topics():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT topic FROM posts")
    rows = cursor.fetchall()
    conn.close()
    return [row["topic"] for row in rows]

# Initialize DB on load
init_db()
