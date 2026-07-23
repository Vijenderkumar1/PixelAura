import time
import threading
from datetime import datetime
from database import get_setting, set_setting, add_log
from agent import run_blogging_agent

scheduler_thread = None
scheduler_running = False

def scheduler_loop():
    global scheduler_running
    add_log("INFO", "Background scheduler daemon loop started.")
    scheduler_running = True
    
    while scheduler_running:
        try:
            enabled = get_setting("scheduler_enabled", "0")
            if enabled == "1":
                posts_per_day_str = get_setting("posts_per_day", "1")
                try:
                    posts_per_day = int(posts_per_day_str)
                    if posts_per_day < 1:
                        posts_per_day = 1
                except ValueError:
                    posts_per_day = 1
                
                now = datetime.now()
                should_run = False
                
                if posts_per_day <= 1:
                    # Clock time scheduling (once daily)
                    sched_time_str = get_setting("scheduler_time", "09:00")
                    last_run_date = get_setting("last_scheduler_run_date", "")
                    today_str = now.strftime("%Y-%m-%d")
                    
                    if last_run_date != today_str:
                        try:
                            sched_time = datetime.strptime(sched_time_str, "%H:%M").time()
                        except ValueError:
                            sched_time = datetime.strptime("09:00", "%H:%M").time()
                            
                        if now.time() >= sched_time:
                            should_run = True
                            set_setting("last_scheduler_run_date", today_str)
                            set_setting("last_scheduler_run_timestamp", now.isoformat())
                            add_log("INFO", f"Scheduler trigger: clock time {sched_time_str} reached.")
                else:
                    # Dynamic interval spacing (multiple posts daily)
                    interval_hours = 24.0 / posts_per_day
                    last_run_time_str = get_setting("last_scheduler_run_timestamp", "")
                    
                    if not last_run_time_str:
                        should_run = True
                    else:
                        try:
                            last_run_time = datetime.fromisoformat(last_run_time_str)
                            elapsed_hours = (now - last_run_time).total_seconds() / 3600.0
                            if elapsed_hours >= interval_hours:
                                should_run = True
                        except Exception:
                            should_run = True
                            
                    if should_run:
                        set_setting("last_scheduler_run_timestamp", now.isoformat())
                        set_setting("last_scheduler_run_date", now.strftime("%Y-%m-%d"))
                        add_log("INFO", f"Scheduler trigger: Interval of {interval_hours:.2f} hours (for {posts_per_day} posts/day) elapsed.")
                
                if should_run:
                    add_log("INFO", "Initiating scheduled blog post run.")
                    agent_thread = threading.Thread(target=run_blogging_agent, kwargs={"manual": False}, name="BloggingAgentRun")
                    agent_thread.daemon = True
                    agent_thread.start()
            
        except Exception as e:
            add_log("ERROR", f"Exception in scheduler heartbeat: {e}")
            
        # Heartbeat check every 60 seconds
        time.sleep(60)

def start_scheduler():
    global scheduler_thread, scheduler_running
    if scheduler_thread is not None and scheduler_thread.is_alive():
        add_log("INFO", "Scheduler thread is already running.")
        return
        
    scheduler_thread = threading.Thread(target=scheduler_loop, name="DailyBlogScheduler")
    scheduler_thread.daemon = True
    scheduler_thread.start()
    add_log("INFO", "Scheduler thread spawned.")

def stop_scheduler():
    global scheduler_running
    scheduler_running = False
    add_log("INFO", "Scheduler thread stop signal sent.")
