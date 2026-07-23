import os
import threading
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import requests

from database import (
    get_all_settings, set_setting, get_setting, get_all_posts, get_post,
    delete_post, get_logs, clear_logs, add_log
)
from agent import run_blogging_agent
from scheduler import start_scheduler, stop_scheduler

app = FastAPI(title="Autonomous AI SEO Blogging Agent API")

# Startup Event: Start the scheduler background loop
@app.on_event("startup")
def startup_event():
    start_scheduler()

# 1. API: Settings
@app.get("/api/settings")
def api_get_settings():
    return get_all_settings()

@app.post("/api/settings")
async def api_save_settings(request: Request):
    try:
        data = await request.json()
        for key, value in data.items():
            set_setting(key, value)
        add_log("INFO", "Configuration settings updated via dashboard.")
        return {"status": "success", "message": "Settings saved."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 2. API: Posts
@app.get("/api/posts")
def api_get_posts():
    return get_all_posts()

@app.get("/api/posts/{post_id}")
def api_get_single_post(post_id: int):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return post

@app.delete("/api/posts/{post_id}")
def api_delete_post(post_id: int):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    delete_post(post_id)
    add_log("INFO", f"Deleted post: '{post['topic']}' (ID: {post_id}).")
    return {"status": "success", "message": "Post deleted."}

# 3. API: Logs
@app.get("/api/logs")
def api_get_logs(limit: int = 100):
    return get_logs(limit)

@app.post("/api/logs/clear")
def api_clear_logs():
    clear_logs()
    add_log("INFO", "Logs database cleared by user.")
    return {"status": "success", "message": "Logs cleared."}

# 4. API: Run Agent Now (Manual Trigger)
@app.post("/api/agent/run")
def api_trigger_agent_run():
    # Check if key is configured
    key = get_setting("gemini_api_key")
    if not key:
        raise HTTPException(status_code=400, detail="Gemini API Key is not configured. Please add it in settings first.")
        
    # Check if there is an active running thread for the blogging agent to prevent concurrent issues
    for thread in threading.enumerate():
        if thread.name == "BloggingAgentRun":
            raise HTTPException(status_code=400, detail="Blogging agent is already running a task. Please wait for it to complete.")
            
    # Spawn background task in separate thread
    agent_thread = threading.Thread(target=run_blogging_agent, kwargs={"manual": True}, name="BloggingAgentRun")
    agent_thread.daemon = True
    agent_thread.start()
    
    add_log("INFO", "Blogging agent manually triggered from dashboard.")
    return {"status": "success", "message": "Agent execution started in the background."}

# 5. API: Scheduler status check / toggle
@app.get("/api/scheduler/status")
def api_get_scheduler_status():
    enabled = get_setting("scheduler_enabled", "0") == "1"
    time_str = get_setting("scheduler_time", "09:00")
    last_run = get_setting("last_scheduler_run_date", "Never")
    
    # Check if thread is alive
    active = False
    for thread in threading.enumerate():
        if thread.name == "DailyBlogScheduler":
            active = thread.is_alive()
            
    return {
        "enabled": enabled,
        "time": time_str,
        "last_run": last_run,
        "thread_active": active
    }

# 6. Blogger OAuth Flow Helper
@app.get("/api/blogger/auth")
def api_blogger_auth_redirect():
    client_id = get_setting("blogger_client_id")
    if not client_id:
        raise HTTPException(status_code=400, detail="Blogger Client ID is missing in settings.")
        
    redirect_uri = "http://localhost:8000/api/blogger/callback"
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=https://www.googleapis.com/auth/blogger&"
        "access_type=offline&"
        "prompt=consent"
    )
    return RedirectResponse(auth_url)

@app.get("/api/blogger/callback")
def api_blogger_oauth_callback(code: str = None, error: str = None):
    if error:
        add_log("ERROR", f"Blogger OAuth error returned from Google: {error}")
        return RedirectResponse("/index.html?blogger_auth=error&reason=" + error)
        
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing.")
        
    client_id = get_setting("blogger_client_id")
    client_secret = get_setting("blogger_client_secret")
    redirect_uri = "http://localhost:8000/api/blogger/callback"
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=15)
        if response.status_code == 200:
            tokens = response.json()
            refresh_token = tokens.get("refresh_token")
            if refresh_token:
                set_setting("blogger_refresh_token", refresh_token)
                add_log("INFO", "Blogger OAuth2 refresh token retrieved and saved successfully.")
                return RedirectResponse("/index.html?blogger_auth=success")
            else:
                # In some cases Google won't return refresh token if prompt=consent is missing or already authorized
                add_log("WARNING", "Authorization succeeded but no refresh token was returned. Try re-authorizing or forcing consent.")
                return RedirectResponse("/index.html?blogger_auth=warning_no_refresh")
        else:
            add_log("ERROR", f"Failed to exchange OAuth code: {response.text}")
            return RedirectResponse("/index.html?blogger_auth=failed")
    except Exception as e:
        add_log("ERROR", f"Exception in Blogger OAuth callback: {e}")
        return RedirectResponse("/index.html?blogger_auth=error")

# Mount Static Files dashboard (make sure the 'static' folder exists first)
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
