import os
import database
from agent import run_blogging_agent

def main():
    # Map environment variables to database settings
    env_mappings = {
        "GEMINI_API_KEY": "gemini_api_key",
        "BLOGGER_BLOG_ID": "blogger_blog_id",
        "BLOGGER_CLIENT_ID": "blogger_client_id",
        "BLOGGER_CLIENT_SECRET": "blogger_client_secret",
        "BLOGGER_REFRESH_TOKEN": "blogger_refresh_token",
        "WRITING_NICHE": "niche",
        "WRITING_TONE": "writing_tone",
        "PUBLISHING_PLATFORM": "publishing_platform"
    }
    
    # Initialize the database structure
    database.init_db()
    
    print("Populating database settings from Environment Variables/Secrets...")
    for env_var, setting_key in env_mappings.items():
        val = os.getenv(env_var)
        if val:
            database.set_setting(setting_key, val)
            # Mask sensitive values in log printout
            masked = val[:5] + "..." if len(val) > 8 and env_var in ["GEMINI_API_KEY", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN"] else val
            print(f"  Set {setting_key} = {masked}")
            
    # Default to blogger publishing if not set
    if not database.get_setting("publishing_platform") or database.get_setting("publishing_platform") == "none":
        database.set_setting("publishing_platform", "blogger")
        
    print("\nTriggering Blogging Agent...")
    success = run_blogging_agent(manual=True)
    if success:
        print("Blogging Agent completed successfully!")
    else:
        print("Blogging Agent execution failed. Check logs above.")

if __name__ == "__main__":
    main()
