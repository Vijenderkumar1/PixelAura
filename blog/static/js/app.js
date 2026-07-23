document.addEventListener("DOMContentLoaded", () => {
    // ---------------------------------------------------------
    // Globals and State
    // ---------------------------------------------------------
    let currentTab = "dashboard";
    let allPosts = [];
    let loadedSettings = {};
    let isAgentRunning = false;
    let logsCache = "";
    
    // Polling Intervals
    let logsInterval = null;
    let postsInterval = null;
    let statusInterval = null;

    // ---------------------------------------------------------
    // DOM Elements Cache
    // ---------------------------------------------------------
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanels = document.querySelectorAll(".tab-panel");
    const pageTitle = document.getElementById("page-title");
    const currentTimeText = document.getElementById("current-time");
    
    // Dashboard Stats
    const statTotalPosts = document.getElementById("stat-total-posts");
    const statAvgSeo = document.getElementById("stat-avg-seo");
    const statAvgReadability = document.getElementById("stat-avg-readability");
    const statNextRun = document.getElementById("stat-next-run");
    
    // Scheduler Info Cards
    const schedEnabledBadge = document.getElementById("sched-enabled-badge");
    const schedTargetTime = document.getElementById("sched-target-time");
    const schedLastRun = document.getElementById("sched-last-run");
    const schedNiche = document.getElementById("sched-niche");
    const schedPlatform = document.getElementById("sched-platform");
    
    // Agent Progress Elements
    const agentPulse = document.getElementById("agent-pulse");
    const agentProgressFill = document.getElementById("agent-progress-fill");
    const btnTriggerRun = document.getElementById("btn-trigger-run");
    const sidebarSchedulerStatus = document.getElementById("sidebar-scheduler-status");
    
    // Post Elements
    const recentPostsContainer = document.getElementById("recent-posts-container");
    const postsTableBody = document.getElementById("posts-table-body");
    const inputSearchPosts = document.getElementById("input-search-posts");
    const linkViewAllPosts = document.getElementById("link-view-all-posts");
    
    // Logs Elements
    const terminalLogs = document.getElementById("terminal-logs");
    const btnClearLogs = document.getElementById("btn-clear-logs");
    
    // Settings Elements
    const settingsForm = document.getElementById("settings-form");
    const settingGeminiKey = document.getElementById("setting-gemini-key");
    const settingNiche = document.getElementById("setting-niche");
    const settingTone = document.getElementById("setting-tone");
    const settingWordCount = document.getElementById("setting-word-count");
    const settingSeoScore = document.getElementById("setting-seo-score");
    const settingSchedEnabled = document.getElementById("setting-sched-enabled");
    const settingSchedTime = document.getElementById("setting-sched-time");
    const settingPostsPerDay = document.getElementById("setting-posts-per-day");
    const settingPlatform = document.getElementById("setting-platform");
    
    // Platform configurations
    const wpConfigCard = document.getElementById("platform-config-wordpress");
    const bloggerConfigCard = document.getElementById("platform-config-blogger");
    const settingWpUrl = document.getElementById("setting-wp-url");
    const settingWpUser = document.getElementById("setting-wp-user");
    const settingWpPassword = document.getElementById("setting-wp-password");
    const settingBloggerId = document.getElementById("setting-blogger-id");
    const settingBloggerClientId = document.getElementById("setting-blogger-client-id");
    const settingBloggerClientSecret = document.getElementById("setting-blogger-client-secret");
    const btnOauthBlogger = document.getElementById("btn-oauth-blogger");
    const bloggerTokenStatus = document.getElementById("blogger-token-status");
    
    // Modal Elements
    const modalPostViewer = document.getElementById("modal-post-viewer");
    const modalTitle = document.getElementById("modal-title");
    const modalBtnClose = document.getElementById("modal-btn-close");
    const modalBtnDone = document.getElementById("modal-btn-done");
    const modalBtnDeletePost = document.getElementById("modal-btn-delete-post");
    const modalTabs = document.querySelectorAll(".modal-tab-btn");
    const modalTabPanels = document.querySelectorAll(".modal-tab-panel");
    
    // Modal Fields
    const modalPostDate = document.getElementById("modal-post-date");
    const modalPostWordcount = document.getElementById("modal-post-wordcount");
    const modalPostPubPlatform = document.getElementById("modal-post-pub-platform");
    const modalArticleBody = document.getElementById("modal-article-body");
    const modalSeoCircleScore = document.getElementById("modal-seo-circle-score");
    const modalSeoAuditItems = document.getElementById("modal-seo-audit-items");
    const modalMetaTitle = document.getElementById("modal-meta-title");
    const modalMetaDesc = document.getElementById("modal-meta-desc");
    const modalMetaSlug = document.getElementById("modal-meta-slug");
    const modalSchemaArticle = document.getElementById("modal-schema-article");
    const modalSchemaFaq = document.getElementById("modal-schema-faq");
    const modalSchemaBreadcrumb = document.getElementById("modal-schema-breadcrumb");
    const modalImgPromptFeatured = document.getElementById("modal-img-prompt-featured");
    const modalImgAltFeatured = document.getElementById("modal-img-alt-featured");
    const modalInContentPromptsContainer = document.getElementById("modal-in-content-prompts-container");

    let activeModalPostId = null;

    // ---------------------------------------------------------
    // Time Indicator Clock
    // ---------------------------------------------------------
    function startClock() {
        setInterval(() => {
            const now = new Date();
            currentTimeText.textContent = now.toTimeString().split(' ')[0];
        }, 1000);
    }

    // ---------------------------------------------------------
    // Navigation / Tabs switching
    // ---------------------------------------------------------
    function setupNavigation() {
        navItems.forEach(item => {
            item.addEventListener("click", (e) => {
                e.preventDefault();
                const target = item.getAttribute("data-tab");
                switchTab(target);
            });
        });
        
        linkViewAllPosts.addEventListener("click", (e) => {
            e.preventDefault();
            switchTab("posts");
        });
    }

    function switchTab(tabId) {
        currentTab = tabId;
        
        // Toggle Sidebar Active
        navItems.forEach(item => {
            if (item.getAttribute("data-tab") === tabId) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        });

        // Toggle Content Panels Active
        tabPanels.forEach(panel => {
            if (panel.id === `tab-${tabId}`) {
                panel.classList.add("active");
            } else {
                panel.classList.remove("active");
            }
        });

        // Update Title Header
        const titles = {
            "dashboard": "Dashboard Overview",
            "posts": "Generated Blog Articles",
            "logs": "Agent Execution Terminal Logs",
            "settings": "Agent Configuration Control"
        };
        pageTitle.textContent = titles[tabId] || "Dashboard";
        
        // Specific tab operations
        if (tabId === "posts") {
            fetchPosts();
        } else if (tabId === "logs") {
            fetchLogs();
        } else if (tabId === "settings") {
            fetchSettings();
        }
    }

    // ---------------------------------------------------------
    // API Interactivity
    // ---------------------------------------------------------
    
    // Fetch Settings
    function fetchSettings() {
        fetch("/api/settings")
            .then(res => res.json())
            .then(data => {
                loadedSettings = data;
                
                // Populate fields
                settingGeminiKey.value = data.gemini_api_key || "";
                settingNiche.value = data.niche || "";
                settingTone.value = data.writing_tone || "";
                settingWordCount.value = data.word_count_target || "";
                settingSeoScore.value = data.seo_target_score || "90";
                settingSchedEnabled.checked = data.scheduler_enabled === "1";
                settingSchedTime.value = data.scheduler_time || "09:00";
                settingPostsPerDay.value = data.posts_per_day || "1";
                settingPlatform.value = data.publishing_platform || "none";
                
                settingWpUrl.value = data.wp_url || "";
                settingWpUser.value = data.wp_username || "";
                settingWpPassword.value = data.wp_app_password || "";
                
                settingBloggerId.value = data.blogger_blog_id || "";
                settingBloggerClientId.value = data.blogger_client_id || "";
                settingBloggerClientSecret.value = data.blogger_client_secret || "";
                
                // Toggle sub configs visibility
                togglePlatformVisibility(data.publishing_platform);
                
                // Update Blogger Connect status
                if (data.blogger_refresh_token) {
                    bloggerTokenStatus.innerHTML = '<i class="fa-solid fa-circle-check text-green"></i> Blogger Connected';
                    btnOauthBlogger.textContent = "Reconnect Blogger";
                } else {
                    bloggerTokenStatus.innerHTML = '<i class="fa-solid fa-circle-exclamation text-yellow"></i> Not Connected';
                    btnOauthBlogger.textContent = "Connect Blogger (Authorize)";
                }
            })
            .catch(err => console.error("Error loading settings:", err));
    }

    function togglePlatformVisibility(platform) {
        if (platform === "wordpress") {
            wpConfigCard.style.display = "block";
            bloggerConfigCard.style.display = "none";
        } else if (platform === "blogger") {
            wpConfigCard.style.display = "none";
            bloggerConfigCard.style.display = "block";
        } else if (platform === "both") {
            wpConfigCard.style.display = "block";
            bloggerConfigCard.style.display = "block";
        } else {
            wpConfigCard.style.display = "none";
            bloggerConfigCard.style.display = "none";
        }
    }

    // Save Settings
    settingsForm.addEventListener("submit", (e) => {
        e.preventDefault();
        
        const payload = {
            "gemini_api_key": settingGeminiKey.value,
            "niche": settingNiche.value,
            "writing_tone": settingTone.value,
            "word_count_target": settingWordCount.value,
            "seo_target_score": settingSeoScore.value,
            "scheduler_enabled": settingSchedEnabled.checked ? "1" : "0",
            "scheduler_time": settingSchedTime.value,
            "posts_per_day": settingPostsPerDay.value,
            "publishing_platform": settingPlatform.value,
            "wp_url": settingWpUrl.value,
            "wp_username": settingWpUser.value,
            "wp_app_password": settingWpPassword.value,
            "blogger_blog_id": settingBloggerId.value,
            "blogger_client_id": settingBloggerClientId.value,
            "blogger_client_secret": settingBloggerClientSecret.value
        };
        
        fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                alert("Settings saved successfully.");
                fetchSettings();
                fetchSchedulerStatus();
            } else {
                alert("Error: " + data.detail);
            }
        })
        .catch(err => {
            console.error("Save error:", err);
            alert("Failed to save settings.");
        });
    });

    settingPlatform.addEventListener("change", (e) => {
        togglePlatformVisibility(e.target.value);
    });

    // Blogger OAuth Authentication
    btnOauthBlogger.addEventListener("click", () => {
        // Save settings first, as Client ID and Secret are needed to authenticate
        const payload = {
            "blogger_client_id": settingBloggerClientId.value,
            "blogger_client_secret": settingBloggerClientSecret.value,
            "blogger_blog_id": settingBloggerId.value
        };
        
        fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(() => {
            // Redirect to auth
            window.location.href = "/api/blogger/auth";
        })
        .catch(err => {
            console.error("Blogger save error:", err);
            alert("Failed to save credentials before OAuth redirect.");
        });
    });

    // Check URL parameters for Blogger OAuth response
    function checkOauthResponse() {
        const urlParams = new URLSearchParams(window.location.search);
        const authStatus = urlParams.get("blogger_auth");
        if (authStatus) {
            if (authStatus === "success") {
                alert("Google Blogger connected successfully!");
            } else if (authStatus === "warning_no_refresh") {
                alert("Google Blogger connected but did not return a refresh token. If it doesn't work, disconnect and clear permissions on your Google Account, then connect again.");
            } else {
                const reason = urlParams.get("reason") || "Unknown error";
                alert("Google Blogger connection failed: " + reason);
            }
            // Strip parameters
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    // Fetch Posts
    function fetchPosts() {
        fetch("/api/posts")
            .then(res => res.json())
            .then(posts => {
                allPosts = posts;
                updateStats(posts);
                renderRecentPosts(posts);
                renderPostsTable(posts);
            })
            .catch(err => console.error("Error loading posts:", err));
    }

    function updateStats(posts) {
        statTotalPosts.textContent = posts.length;
        
        if (posts.length > 0) {
            const sumSeo = posts.reduce((sum, p) => sum + (p.seo_score || 0), 0);
            const sumRead = posts.reduce((sum, p) => sum + (p.readability_score || 0), 0);
            
            statAvgSeo.textContent = `${Math.round(sumSeo / posts.length)}/100`;
            statAvgReadability.textContent = Math.round(sumRead / posts.length);
        } else {
            statAvgSeo.textContent = "0/100";
            statAvgReadability.textContent = "0";
        }
    }

    function renderRecentPosts(posts) {
        recentPostsContainer.innerHTML = "";
        const recents = posts.slice(0, 5);
        
        if (recents.length === 0) {
            recentPostsContainer.innerHTML = `<div class="empty-state">No articles generated yet. Click "Run Agent Now" to generate one.</div>`;
            return;
        }

        recents.forEach(post => {
            const item = document.createElement("div");
            item.className = "post-row-item";
            item.addEventListener("click", () => openPostModal(post.id));
            
            const dateStr = post.published_at ? new Date(post.published_at).toLocaleDateString() : new Date(post.created_at).toLocaleDateString();
            const platformText = post.platform_published !== "none" ? post.platform_published : "Draft Only";
            const scoreClass = post.seo_score >= 90 ? "green" : "orange";
            
            item.innerHTML = `
                <div class="post-row-details">
                    <span class="post-row-title">${post.topic}</span>
                    <span class="post-row-meta">
                        <span><i class="fa-regular fa-calendar"></i> ${dateStr}</span>
                        <span><i class="fa-solid fa-globe"></i> ${platformText}</span>
                    </span>
                </div>
                <div class="post-row-scores">
                    <span class="score-badge ${scoreClass}"><i class="fa-solid fa-gauge-high"></i> ${post.seo_score}</span>
                    <span class="badge ${getPostStatusClass(post.status)}">${post.status}</span>
                </div>
            `;
            recentPostsContainer.appendChild(item);
        });
    }

    function getPostStatusClass(status) {
        switch(status.toLowerCase()) {
            case "published": return "badge-success";
            case "draft": return "badge-info";
            case "failed": return "badge-danger";
            case "in progress": return "badge-warning";
            default: return "badge-warning";
        }
    }

    function renderPostsTable(posts) {
        const query = inputSearchPosts.value.toLowerCase().trim();
        const filtered = posts.filter(post => {
            return post.topic.toLowerCase().includes(query) || 
                   (post.primary_keyword && post.primary_keyword.toLowerCase().includes(query));
        });

        postsTableBody.innerHTML = "";
        if (filtered.length === 0) {
            postsTableBody.innerHTML = `<tr><td colspan="8"><div class="empty-state">No articles match your search filter.</div></td></tr>`;
            return;
        }

        filtered.forEach(post => {
            const tr = document.createElement("tr");
            const dateStr = post.published_at ? new Date(post.published_at).toLocaleDateString() : new Date(post.created_at).toLocaleDateString();
            const platformText = post.platform_published !== "none" ? post.platform_published : "Draft";
            
            tr.innerHTML = `
                <td class="post-title-cell" title="${post.topic}">${post.topic}</td>
                <td><code>${post.primary_keyword || "--"}</code></td>
                <td class="text-capitalize">${platformText}</td>
                <td><strong class="${post.seo_score >= 90 ? 'text-green' : 'text-yellow'}">${post.seo_score || 0}</strong></td>
                <td>${post.readability_score || 0}</td>
                <td><span class="badge ${getPostStatusClass(post.status)}">${post.status}</span></td>
                <td>${dateStr}</td>
                <td>
                    <button class="btn-icon" onclick="event.stopPropagation(); openPostModal(${post.id})">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                    <button class="btn-icon delete" onclick="event.stopPropagation(); deletePostAction(${post.id})">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            `;
            postsTableBody.appendChild(tr);
        });
    }

    inputSearchPosts.addEventListener("input", () => {
        renderPostsTable(allPosts);
    });

    // Delete post helper (placed globally so it can trigger from row)
    window.deletePostAction = function(id) {
        if (confirm("Are you sure you want to delete this article from the database? This won't delete it from Blogger or WordPress if it was already published.")) {
            fetch(`/api/posts/${id}`, { method: "DELETE" })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "success") {
                        fetchPosts();
                        if (modalPostViewer.classList.contains("active") && activeModalPostId === id) {
                            closePostModal();
                        }
                    }
                })
                .catch(err => console.error("Error deleting post:", err));
        }
    };

    // Fetch Logs
    function fetchLogs() {
        fetch("/api/logs?limit=200")
            .then(res => res.json())
            .then(logs => {
                let html = "";
                logs.forEach(log => {
                    const time = log.timestamp.split('T')[1].split('.')[0];
                    html += `
                        <div class="log-line">
                            <span class="log-time">[${time}]</span>
                            <span class="log-level ${log.level}">${log.level}</span>
                            <span class="log-message">${log.message}</span>
                        </div>
                    `;
                });
                
                // Only update if changes to prevent cursor flashing on scrolling
                if (logsCache !== html) {
                    logsCache = html;
                    terminalLogs.innerHTML = html || `<div class="empty-state">Terminal is clear. Active agent logs will show up here.</div>`;
                    terminalLogs.scrollTop = terminalLogs.scrollHeight;
                }
            })
            .catch(err => console.error("Error loading logs:", err));
    }

    btnClearLogs.addEventListener("click", () => {
        if (confirm("Clear logs database?")) {
            fetch("/api/logs/clear", { method: "POST" })
                .then(() => {
                    terminalLogs.innerHTML = "";
                    logsCache = "";
                });
        }
    });

    // Fetch Scheduler Status & Agent State
    function fetchSchedulerStatus() {
        fetch("/api/scheduler/status")
            .then(res => res.json())
            .then(data => {
                // Update sidebars
                if (data.enabled) {
                    sidebarSchedulerStatus.className = "scheduler-status-pill";
                    sidebarSchedulerStatus.innerHTML = '<span class="status-dot green"></span> <span class="status-text">Scheduler: Active</span>';
                    schedEnabledBadge.innerHTML = '<span class="badge badge-success">Active</span>';
                } else {
                    sidebarSchedulerStatus.className = "scheduler-status-pill";
                    sidebarSchedulerStatus.innerHTML = '<span class="status-dot grey"></span> <span class="status-text">Scheduler: Disabled</span>';
                    schedEnabledBadge.innerHTML = '<span class="badge badge-danger">Disabled</span>';
                }
                
                schedTargetTime.textContent = data.time;
                schedLastRun.textContent = data.last_run || "Never";
                statNextRun.textContent = data.enabled ? data.time : "Disabled";
                
                // Try to infer active niche and platform from settings
                schedNiche.textContent = loadedSettings.niche || "Tech & AI";
                schedPlatform.textContent = loadedSettings.publishing_platform || "none";
                
                // Read logs to determine if agent thread is running
                checkAgentRunningState();
            })
            .catch(err => console.error("Error loading scheduler status:", err));
    }

    function checkAgentRunningState() {
        // Read active threads or check logs
        fetch("/api/logs?limit=5")
            .then(res => res.json())
            .then(logs => {
                // Simple state heuristic: look at latest logs
                const inProgressLog = logs.some(l => l.message.includes("Starting blogging agent") || l.message.includes("Step ") || l.message.includes("Generating"));
                const finishedLog = logs.some(l => l.message.includes("run completed successfully") || l.message.includes("Publishing failed") || l.message.includes("Blogging agent run completed"));
                
                // Find chronological positions
                let inProgressIdx = -1;
                let finishedIdx = -1;
                
                for(let i=0; i<logs.length; i++) {
                    if (logs[i].message.includes("Starting blogging agent") || logs[i].message.includes("Step 1:") || logs[i].message.includes("Step 2:") || logs[i].message.includes("Step 3:") || logs[i].message.includes("Step 4:") || logs[i].message.includes("Step 5:") || logs[i].message.includes("Step 6:") || logs[i].message.includes("Step 7:")) {
                        inProgressIdx = i;
                        break;
                    }
                }
                for(let i=0; i<logs.length; i++) {
                    if (logs[i].message.includes("run completed successfully") || logs[i].message.includes("Publishing failed") || logs[i].message.includes("No publishing platform was configured")) {
                        finishedIdx = i;
                        break;
                    }
                }
                
                // If inProgress is more recent (lower index) than finished, agent is active
                if (inProgressIdx !== -1 && (finishedIdx === -1 || inProgressIdx < finishedIdx)) {
                    isAgentRunning = true;
                    agentPulse.className = "pulse-indicator active";
                    agentPulse.innerHTML = '<span class="pulse-ring"></span> Running';
                    btnTriggerRun.disabled = true;
                    btnTriggerRun.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Agent Working...';
                    
                    // Parse which step we are on based on log content
                    updateAgentProgressBar(logs);
                } else {
                    isAgentRunning = false;
                    agentPulse.className = "pulse-indicator idle";
                    agentPulse.innerHTML = '<span class="pulse-ring"></span> Idle';
                    btnTriggerRun.disabled = false;
                    btnTriggerRun.innerHTML = '<i class="fa-solid fa-play"></i> Run Agent Now';
                    
                    // Reset progress bar
                    agentProgressFill.style.width = "0%";
                    document.querySelectorAll(".progress-steps .step").forEach(s => s.className = "step");
                }
            });
    }

    function updateAgentProgressBar(logs) {
        const messages = logs.map(l => l.message).join("\n");
        const fill = agentProgressFill;
        
        const stepDiscover = document.getElementById("step-discover");
        const stepResearch = document.getElementById("step-research");
        const stepWrite = document.getElementById("step-write");
        const stepPublish = document.getElementById("step-publish");
        
        // Reset steps
        stepDiscover.className = "step";
        stepResearch.className = "step";
        stepWrite.className = "step";
        stepPublish.className = "step";
        
        if (messages.includes("Step 6:") || messages.includes("Publishing to")) {
            fill.style.width = "85%";
            stepDiscover.className = "step done";
            stepResearch.className = "step done";
            stepWrite.className = "step done";
            stepPublish.className = "step current";
        } else if (messages.includes("Step 3:") || messages.includes("Step 4:") || messages.includes("Step 5:") || messages.includes("Generating")) {
            fill.style.width = "55%";
            stepDiscover.className = "step done";
            stepResearch.className = "step done";
            stepWrite.className = "step current";
        } else if (messages.includes("Step 2:") || messages.includes("SEO Research")) {
            fill.style.width = "30%";
            stepDiscover.className = "step done";
            stepResearch.className = "step current";
        } else if (messages.includes("Step 1:") || messages.includes("Finding today")) {
            fill.style.width = "10%";
            stepDiscover.className = "step current";
        }
    }

    // Manual Agent Run Trigger
    btnTriggerRun.addEventListener("click", () => {
        if (isAgentRunning) return;
        
        fetch("/api/agent/run", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    alert("Agent successfully started in background! Check logs for real-time progress.");
                    isAgentRunning = true;
                    // Instantly update UI states
                    agentPulse.className = "pulse-indicator active";
                    agentPulse.innerHTML = '<span class="pulse-ring"></span> Running';
                    btnTriggerRun.disabled = true;
                    btnTriggerRun.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Agent Working...';
                    switchTab("logs");
                } else {
                    alert("Trigger failed: " + data.detail);
                }
            })
            .catch(err => {
                console.error("Trigger run failed:", err);
                alert("Failed to connect to agent server.");
            });
    });

    // ---------------------------------------------------------
    // Modals: Post Viewer
    // ---------------------------------------------------------
    function openPostModal(postId) {
        activeModalPostId = postId;
        
        // Reset tabs
        modalTabs.forEach(t => t.classList.remove("active"));
        modalTabPanels.forEach(p => p.classList.remove("active"));
        modalTabs[0].classList.add("active");
        modalTabPanels[0].classList.add("active");
        
        // Fetch specific post data
        fetch(`/api/posts/${postId}`)
            .then(res => res.json())
            .then(post => {
                modalTitle.textContent = post.topic;
                
                const date = post.published_at ? new Date(post.published_at).toLocaleString() : new Date(post.created_at).toLocaleString();
                modalPostDate.innerHTML = `<i class="fa-regular fa-calendar"></i> Generated: ${date}`;
                
                const words = post.content ? post.content.split(/\s+/).length : 0;
                modalPostWordcount.innerHTML = `<i class="fa-solid fa-calculator"></i> Words: ${words}`;
                
                const platforms = post.platform_published !== "none" ? post.platform_published : "Draft Mode";
                const pubIdText = post.platform_post_id ? ` (ID: ${post.platform_post_id})` : "";
                modalPostPubPlatform.innerHTML = `<i class="fa-solid fa-globe"></i> Platform: <span class="text-capitalize">${platforms}${pubIdText}</span>`;
                
                // Build HTML body. The server serves markdown so we can do simple rendering here.
                // Since server.py is modifying it or we can do a simple translation:
                // Actually, let's write a quick, robust client markdown parser in case the endpoint doesn't render it.
                // But wait! If we modify server.py, we can just fetch rendered HTML. Let's do a simple client translation:
                modalArticleBody.innerHTML = simpleMarkdownToHTML(post.content || "");
                
                // SEO tab
                modalSeoCircleScore.textContent = post.seo_score || 0;
                if (post.seo_score >= 90) {
                    modalSeoCircleScore.style.color = "var(--color-success)";
                } else if (post.seo_score >= 70) {
                    modalSeoCircleScore.style.color = "var(--color-warning)";
                } else {
                    modalSeoCircleScore.style.color = "var(--color-danger)";
                }
                
                // SEO Checkmarks
                populateSeoAuditList(post);
                
                // Meta tab
                modalMetaTitle.value = post.seo_title || "";
                modalMetaDesc.value = post.meta_description || "";
                modalMetaSlug.value = post.slug || "";
                
                const schemas = post.schema_data || {};
                modalSchemaArticle.textContent = JSON.stringify(schemas.Article || {}, null, 2);
                modalSchemaFaq.textContent = JSON.stringify(schemas.FAQ || {}, null, 2);
                modalSchemaBreadcrumb.textContent = JSON.stringify(schemas.Breadcrumb || {}, null, 2);
                
                // Image Prompts tab
                const imgPrompts = post.image_prompts || {};
                let featuredPromptText = imgPrompts.featured?.prompt || "No prompt generated.";
                if (imgPrompts.featured?.url) {
                    featuredPromptText += `<div style="margin-top:12px; text-align:center;"><img src="${imgPrompts.featured.url}" alt="${imgPrompts.featured.alt_text || 'Featured'}" style="max-width:100%; max-height:240px; border-radius:8px; object-fit:cover; border: 1px solid var(--glass-border);"></div>`;
                }
                modalImgPromptFeatured.innerHTML = featuredPromptText;
                modalImgAltFeatured.textContent = imgPrompts.featured?.alt_text || "None";
                
                // in-content prompts
                modalInContentPromptsContainer.innerHTML = "";
                const contentImgs = imgPrompts.content_images || imgPrompts.content || [];
                if (contentImgs.length === 0) {
                    modalInContentPromptsContainer.innerHTML = "<p class='help-text'>No in-content image prompts found.</p>";
                } else {
                    contentImgs.forEach((img, index) => {
                        const card = document.createElement("div");
                        card.className = "image-prompt-card";
                        let imgPreview = "";
                        if (img.url) {
                            imgPreview = `<div style="margin-top:10px; text-align:center;"><img src="${img.url}" alt="${img.alt_text || 'Illustration'}" style="max-width:100%; max-height:180px; border-radius:6px; object-fit:cover; border: 1px solid var(--glass-border);"></div>`;
                        }
                        card.innerHTML = `
                            <h5>Image #${index+1} (Target Section: ${img.section_heading || img.section || "Body"})</h5>
                            <div class="prompt-text">
                                <strong>AI Prompt:</strong>
                                <p>${img.prompt}</p>
                                ${imgPreview}
                            </div>
                            <div class="alt-text-label">
                                <strong>ALT Text:</strong> <span>${img.alt_text}</span>
                            </div>
                        `;
                        modalInContentPromptsContainer.appendChild(card);
                    });
                }
                
                // Show modal
                modalPostViewer.classList.add("active");
            })
            .catch(err => {
                console.error("Error opening post:", err);
                alert("Failed to load post details.");
            });
    }

    function closePostModal() {
        modalPostViewer.classList.remove("active");
        activeModalPostId = null;
    }

    modalBtnClose.addEventListener("click", closePostModal);
    modalBtnDone.addEventListener("click", closePostModal);
    modalBtnDeletePost.addEventListener("click", () => {
        if (activeModalPostId) {
            deletePostAction(activeModalPostId);
        }
    });

    // Close on backdrop click
    modalPostViewer.addEventListener("click", (e) => {
        if (e.target === modalPostViewer) {
            closePostModal();
        }
    });

    // Modal Tabs logic
    modalTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            modalTabs.forEach(t => t.classList.remove("active"));
            modalTabPanels.forEach(p => p.classList.remove("active"));
            
            tab.classList.add("active");
            const panelId = `modal-panel-${tab.getAttribute("data-modal-tab")}`;
            document.getElementById(panelId).classList.add("active");
        });
    });

    // Simple parser for Markdown to HTML
    function simpleMarkdownToHTML(md) {
        if (!md) return "";
        let html = md;
        // Block headers
        html = html.replace(/^#\s+(.*?)$/gm, '<h1>$1</h1>');
        html = html.replace(/^##\s+(.*?)$/gm, '<h2>$1</h2>');
        html = html.replace(/^###\s+(.*?)$/gm, '<h3>$1</h3>');
        html = html.replace(/^####\s+(.*?)$/gm, '<h4>$1</h4>');
        
        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Links
        html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" class="text-highlight">$1</a>');
        
        // Code Blocks
        html = html.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
        html = html.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Bullet Lists
        // Simple lines replace
        html = html.replace(/^\-\s+(.*?)$/gm, '<li>$1</li>');
        
        // Wrap contiguous list items in <ul>
        // This is a naive translation but sufficient for markdown bodies
        html = html.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');
        
        // Convert double returns to paragraphs (ignoring headings/pre blocks)
        html = html.replace(/\n\n(?!<h|<pre|<ul|<li)(.*?)\n\n/g, '<p>$1</p>');
        // Single newlines to breaks
        html = html.replace(/\n/g, '<br>');
        
        return html;
    }

    // Populate SEO Checkmarks in modal
    function populateSeoAuditList(post) {
        modalSeoAuditItems.innerHTML = "";
        
        const title = (post.seo_title || "").toLowerCase();
        const content = (post.content || "").toLowerCase();
        const p_kw = (post.primary_keyword || "").toLowerCase();
        const kws = post.related_keywords || [];
        const schemas = post.schema_data || {};
        const imgs = post.image_prompts || {};
        
        const checks = [
            {
                label: `Primary keyword "${post.primary_keyword}" present in Meta Title`,
                success: p_kw && title.includes(p_kw)
            },
            {
                label: `Primary keyword present in article introduction`,
                success: p_kw && content.slice(0, 800).includes(p_kw)
            },
            {
                label: `Primary keyword used in structural headings (H1/H2)`,
                success: p_kw && (content.includes("# " + p_kw) || content.includes("## " + p_kw) || content.includes("h1") && content.includes(p_kw)) // simple check
            },
            {
                label: `Comprehensive article length (word count is ${post.content ? post.content.split(/\s+/).length : 0} >= 2000 words)`,
                success: post.content && post.content.split(/\s+/).length >= 2000
            },
            {
                label: `High LSI keyword coverage (targeted related keywords: ${kws.length} identified)`,
                success: kws.length > 0
            },
            {
                label: `Optimized Schema JSON-LD Markups (FAQ, Article, Breadcrumbs active)`,
                success: schemas.Article || schemas.FAQ
            },
            {
                label: `Automated Image ALT texts and prompts generated`,
                success: imgs.featured?.prompt
            },
            {
                label: `Flesch Reading Ease score (${post.readability_score}) is high-quality and readable`,
                success: post.readability_score >= 50
            }
        ];

        checks.forEach(check => {
            const li = document.createElement("li");
            const icon = check.success ? '<i class="fa-solid fa-circle-check text-green"></i>' : '<i class="fa-solid fa-circle-xmark text-danger"></i>';
            li.innerHTML = `${icon} <span>${check.label}</span>`;
            modalSeoAuditItems.appendChild(li);
        });
    }

    // ---------------------------------------------------------
    // Init Operations
    // ---------------------------------------------------------
    startClock();
    setupNavigation();
    checkOauthResponse();
    fetchSettings();
    fetchPosts();
    fetchSchedulerStatus();
    
    // Set active polling loops
    postsInterval = setInterval(fetchPosts, 5000);
    logsInterval = setInterval(fetchLogs, 2000);
    statusInterval = setInterval(fetchSchedulerStatus, 5000);
});
