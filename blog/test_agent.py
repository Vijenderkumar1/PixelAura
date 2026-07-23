import sys
import os

# Add local path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_all_settings, get_all_posts, get_logs
from agent import run_blogging_agent

def main():
    print("=== SEO Blog Agent Dry-Run Test Script ===")
    
    # Initialize database
    print("1. Initializing Database...")
    init_db()
    
    # Check settings
    settings = get_all_settings()
    gemini_key = settings.get("gemini_api_key")
    
    if not gemini_key:
        print("\n[WARNING] Gemini API Key is not set in settings!")
        print("Please run the server, navigate to http://localhost:8000, save your API key in Settings, and then run this test.")
        print("Or set it directly in the settings table of blog_agent.db.")
        
        # Ask if they want to enter it now for testing
        try:
            key_input = input("\nEnter your Gemini API Key to run dry-run now (or press Enter to exit): ").strip()
            if key_input:
                from database import set_setting
                set_setting("gemini_api_key", key_input)
                print("Temporary API Key saved in SQLite database.")
            else:
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)
            
    print("\n2. Executing Blogging Agent Workflows...")
    print("This will find trending topics, search DuckDuckGo, build SEO schemas, write the article, and save it as a Draft.")
    print("Please wait...")
    
    success = run_blogging_agent(manual=True)
    
    if success:
        print("\n[SUCCESS] Blogging Agent finished run successfully!")
        # Fetch latest generated post
        posts = get_all_posts()
        if posts:
            latest = posts[0]
            print("\nGenerated Article Details:")
            print(f"- Topic: {latest['topic']}")
            print(f"- Primary Keyword: {latest['primary_keyword']}")
            print(f"- SEO Title: {latest['seo_title']}")
            print(f"- SEO Score: {latest['seo_score']}/100")
            print(f"- Readability Score: {latest['readability_score']}/100")
            print(f"- Word Count: {len(latest['content'].split())} words")
            print(f"- Status in DB: {latest['status']}")
            
            # Print schemas preview
            schemas = latest.get("schema_data", {})
            print(f"- Schemas Created: {list(schemas.keys()) if schemas else 'None'}")
            
            # Print image prompts preview
            imgs = latest.get("image_prompts", {})
            featured = imgs.get("featured", {}).get("prompt", "None")
            print(f"- Featured Image Prompt: {featured[:100]}...")
        else:
            print("\n[ERROR] No post found in database despite successful run.")
    else:
        print("\n[FAILED] Blogging Agent run encountered errors. See logs below:")
        logs = get_logs(15)
        for log in reversed(logs):
            print(f"[{log['level']}] {log['message']}")

if __name__ == "__main__":
    main()
