// ==========================================
// PixelAura Configuration & Authentication
// ==========================================

// Google OAuth 2.0 Client ID (Replace with your own from Google Cloud Console if needed)
const GOOGLE_CLIENT_ID = "1055745163148-pohm3i29a1f5o7m7q7f9rkm4q5n9p2f1.apps.googleusercontent.com"; 

// Google Sheets Script Webhook URL (Paste your URL from GOOGLE_SHEETS_DATABASE_GUIDE.md)
const SHEETS_WEBHOOK_URL = "YOUR_GOOGLE_SHEETS_WEBHOOK_URL";

let pendingDownload = null;

function getLoggedInUser() {
    return JSON.parse(localStorage.getItem("pixel_user") || "null");
}

function openLoginModal() {
    const modal = document.getElementById("login-modal");
    if (modal) modal.classList.add("active");
    initGoogleLoginButton();
}

function closeLoginModal() {
    const modal = document.getElementById("login-modal");
    if (modal) modal.classList.remove("active");
}

function initGoogleLoginButton() {
    if (typeof google === "undefined") {
        console.warn("Google Identity client script not loaded.");
        return;
    }
    google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse
    });
    const btnContainer = document.getElementById("google-login-btn");
    if (btnContainer) {
        google.accounts.id.renderButton(
            btnContainer,
            { theme: "dark", size: "large", width: 240 }
        );
    }
}

function handleCredentialResponse(response) {
    const payload = parseJwt(response.credential);
    if (!payload || !payload.email) return;
    
    const user = {
        email: payload.email,
        name: payload.name || payload.email.split("@")[0],
        picture: payload.picture || ""
    };
    
    localStorage.setItem("pixel_user", JSON.stringify(user));
    logUserSession(user.email, user.name);
    
    closeLoginModal();
    updateAuthUI();
    
    // If user was waiting to download a file, proceed now
    if (pendingDownload) {
        const { url, filename } = pendingDownload;
        pendingDownload = null;
        const dl = document.createElement("a");
        dl.href = url;
        dl.download = filename;
        document.body.appendChild(dl);
        dl.click();
        document.body.removeChild(dl);
    }
}

function parseJwt(token) {
    try {
        const base64Url = token.split(".")[1];
        const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
        const jsonPayload = decodeURIComponent(window.atob(base64).split("").map(c => {
            return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(""));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

function logUserSession(email, name) {
    if (!SHEETS_WEBHOOK_URL || SHEETS_WEBHOOK_URL.includes("YOUR_GOOGLE_SHEETS")) return;
    fetch(SHEETS_WEBHOOK_URL, {
        method: "POST",
        mode: "no-cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name })
    }).catch(e => console.error("Database log error:", e));
}

function updateAuthUI() {
    const container = document.getElementById("nav-auth-container");
    if (!container) return;
    
    const user = getLoggedInUser();
    if (user) {
        container.innerHTML = `
            <div class="nav-user-profile">
                ${user.picture ? `<img class="nav-user-avatar" src="${user.picture}" alt="${user.name}">` : `<div class="nav-user-avatar" style="background:#7B4FFF; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; color:#fff;">${user.name[0].toUpperCase()}</div>`}
                <button class="nav-logout-btn" onclick="logoutUser()">Sign Out</button>
            </div>
        `;
    } else {
        container.innerHTML = `
            <button class="nav-login-btn" onclick="openLoginModal()">Sign In</button>
        `;
    }
}

function logoutUser() {
    localStorage.removeItem("pixel_user");
    updateAuthUI();
}

function handleDownload(event, url, filename) {
    event.preventDefault();
    event.stopPropagation();
    
    const user = getLoggedInUser();
    if (!user) {
        pendingDownload = { url, filename };
        openLoginModal();
        return;
    }
    
    const dl = document.createElement("a");
    dl.href = url;
    dl.download = filename;
    document.body.appendChild(dl);
    dl.click();
    document.body.removeChild(dl);
}

// Export functions to global scope
window.openLoginModal = openLoginModal;
window.closeLoginModal = closeLoginModal;
window.logoutUser = logoutUser;
window.handleDownload = handleDownload;

// ==========================================


// ── NAV scroll glass effect ──
const nav = document.getElementById("nav");
window.addEventListener("scroll", () => {
    nav.classList.toggle("scrolled", window.scrollY > 50);
}, { passive: true });

// ── Scroll reveal animation ──
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            setTimeout(() => entry.target.classList.add("visible"), index * 60);
            revealObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });
document.querySelectorAll(".reveal").forEach((el) => revealObserver.observe(el));

// ===============================
// Gallery State
// ===============================

const galleryEl    = document.getElementById("gallery");
const paginationEl = document.getElementById("pagination");
const searchInput  = document.getElementById("search-input");
const resultCount  = document.getElementById("result-count");
const CARDS_PER_PAGE  = 24;
const DRAWER_PER_PAGE = 20;

let wallpapers         = [];
let filteredWallpapers = [];
let currentPage        = 1;
let currentCategory    = "all";
let searchQuery        = "";

let activeCategoryForUnlock = "";
let activeTitleForUnlock    = "";

// Drawer state
let drawerCategory = "";
let drawerFiltered = [];
let drawerPage     = 1;

// ===============================
// Load wallpapers.json
// ===============================

async function loadWallpapers() {
    try {
        updateAuthUI();
        const response = await fetch("data/wallpapers.json");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        wallpapers = await response.json();

        // Update stats bar
        const statTotal = document.getElementById("stat-total");
        if (statTotal) statTotal.textContent = wallpapers.length + "+";

        // Hero preview cards
        document.querySelectorAll(".hero-preview .wp-card").forEach((card, index) => {
            if (wallpapers[index]) {
                card.innerHTML = `<img src="${wallpapers[index].image}" alt="${wallpapers[index].title}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;pointer-events:none;" oncontextmenu="return false;" ondragstart="return false;">`;
                card.addEventListener("contextmenu", (e) => e.preventDefault());
                card.addEventListener("dragstart",   (e) => e.preventDefault());
            }
        });

        // Build the dynamic category grid
        buildCategoryGrid();
        applyFilters();

    } catch (error) {
        console.error("Failed to load wallpapers.json:", error);
        if (galleryEl) galleryEl.innerHTML = `<p class="gallery-empty">No wallpapers found.<br>Run <code>python ai_engine/run.py</code> to generate wallpapers.</p>`;
    }
}

// ===============================
// 20-Category Dynamic Grid
// ===============================

const ALL_CATEGORIES = [
    { name: "AMOLED",       gradient: "g1"  },
    { name: "Space",        gradient: "g7"  },
    { name: "Nature",       gradient: "g5"  },
    { name: "Cyberpunk",    gradient: "g4"  },
    { name: "Minimal",      gradient: "g6"  },
    { name: "Fantasy",      gradient: "g3"  },
    { name: "Ocean",        gradient: "g9"  },
    { name: "Galaxy",       gradient: "g12" },
    { name: "Cars",         gradient: "g10" },
    { name: "Forest",       gradient: "g8"  },
    { name: "Anime",        gradient: "g2"  },
    { name: "Abstract",     gradient: "g11" },
    { name: "Neon",         gradient: "g1"  },
    { name: "Tech",         gradient: "g7"  },
    { name: "Texture",      gradient: "g5"  },
    { name: "Architecture", gradient: "g4"  },
    { name: "Retro",        gradient: "g6"  },
    { name: "Pastel",       gradient: "g3"  },
    { name: "Aurora",       gradient: "g9"  },
    { name: "3D Render",    gradient: "g12" },
];

function buildCategoryGrid() {
    const catGrid        = document.getElementById("cat-grid");
    const catSearchInput = document.getElementById("cat-search-input");
    if (!catGrid) return;

    function renderCatGrid(query) {
        const q        = (query || "").toLowerCase().trim();
        const filtered = ALL_CATEGORIES.filter(c => q === "" || c.name.toLowerCase().includes(q));
        catGrid.innerHTML = "";

        if (filtered.length === 0) {
            catGrid.innerHTML = `<p class="gallery-empty" style="grid-column:1/-1">No categories match "${q}"</p>`;
            return;
        }

        filtered.forEach(cat => {
            const matched  = wallpapers.filter(w => w.category.toLowerCase() === cat.name.toLowerCase());
            const coverImg = matched.length > 0 ? matched[0].image : null;
            const count    = matched.length;

            const card = document.createElement("div");
            card.className   = "cat-card";
            card.style.cursor = "pointer";
            card.innerHTML = `
                <div class="cat-card-bg ${cat.gradient}" ${coverImg ? `style="background:url(${coverImg}) no-repeat center center/cover;"` : ""}></div>
                <span class="cat-card-label">${cat.name}</span>
                <span class="cat-card-count">${count}</span>
            `;

            card.addEventListener("contextmenu", e => e.preventDefault());
            card.addEventListener("dragstart",   e => e.preventDefault());
            card.addEventListener("click", () => openCategoryDrawer(cat.name));

            catGrid.appendChild(card);
        });
    }

    renderCatGrid("");

    if (catSearchInput) {
        catSearchInput.addEventListener("input", () => renderCatGrid(catSearchInput.value));
    }
}

// ===============================
// Category Drawer
// ===============================

function openCategoryDrawer(categoryName) {
    drawerCategory = categoryName;
    drawerPage     = 1;
    drawerFiltered = wallpapers.filter(w => w.category.toLowerCase() === categoryName.toLowerCase());

    const drawerEl    = document.getElementById("cat-drawer");
    const drawerTitle = document.getElementById("drawer-title");
    const drawerCount = document.getElementById("drawer-count");
    if (!drawerEl) return;

    drawerTitle.textContent = categoryName;
    drawerCount.textContent = `${drawerFiltered.length} wallpaper${drawerFiltered.length !== 1 ? "s" : ""}`;

    renderDrawerGallery();

    drawerEl.classList.add("active");
    document.body.style.overflow = "hidden";
}

function closeDrawer() {
    const drawerEl = document.getElementById("cat-drawer");
    if (!drawerEl) return;
    drawerEl.classList.remove("active");
    document.body.style.overflow = "";
}

function renderDrawerGallery() {
    const drawerGrid  = document.getElementById("drawer-gallery");
    const drawerPages = document.getElementById("drawer-pagination");
    if (!drawerGrid) return;

    drawerGrid.innerHTML = "";

    if (drawerFiltered.length === 0) {
        drawerGrid.innerHTML = `
            <div class="drawer-empty" style="grid-column:1/-1; text-align:center; padding:60px 20px; color:var(--muted);">
                <div style="font-size:48px; margin-bottom:16px;">🎨</div>
                <p style="font-size:16px; font-weight:600; color:var(--text); margin-bottom:8px;">Coming Soon</p>
                <p style="font-size:13px; line-height:1.7;">AI is generating ${drawerCategory} wallpapers right now.<br>Check back tomorrow for new drops!</p>
            </div>
        `;
        if (drawerPages) drawerPages.innerHTML = "";
        return;
    }

    const start     = (drawerPage - 1) * DRAWER_PER_PAGE;
    const pageItems = drawerFiltered.slice(start, start + DRAWER_PER_PAGE);

    pageItems.forEach(item => {
        const isFree    = item.id <= 10;
        const hasAccess = isFree || isUnlocked(item.category);

        const card = document.createElement("div");
        card.className = "gallery-card";
        card.addEventListener("contextmenu", e => e.preventDefault());
        card.addEventListener("dragstart",   e => e.preventDefault());

        card.innerHTML = `
            <img class="gallery-card-img" src="${item.image}" alt="${item.title}" loading="lazy" oncontextmenu="return false;" ondragstart="return false;">
            <div class="gallery-card-overlay" oncontextmenu="return false;">
                <span class="gallery-tag">${item.category}</span>
                ${hasAccess
                    ? `<button class="download-btn" onclick="handleDownload(event, '${item.download}', '${item.title}')">↓ Download</button>`
                    : `<button class="download-btn" onclick="openPaymentModal('${item.category}','${item.title}');event.stopPropagation();">🔒 Unlock</button>`
                }
            </div>
            <span class="gallery-free-badge ${hasAccess ? "free" : "premium"}">${hasAccess ? "FREE" : "🔒 PREMIUM"}</span>
        `;
        drawerGrid.appendChild(card);
    });

    // Pagination
    const totalPages = Math.ceil(drawerFiltered.length / DRAWER_PER_PAGE);
    if (drawerPages) {
        if (totalPages <= 1) {
            drawerPages.innerHTML = "";
        } else {
            let ph = `<button class="page-btn${drawerPage===1?" disabled":""}" onclick="changeDrawerPage(${drawerPage-1})" ${drawerPage===1?"disabled":""}>← Prev</button>`;
            for (let i = 1; i <= totalPages; i++) {
                ph += `<button class="page-btn${i===drawerPage?" active":""}" onclick="changeDrawerPage(${i})">${i}</button>`;
            }
            ph += `<button class="page-btn${drawerPage===totalPages?" disabled":""}" onclick="changeDrawerPage(${drawerPage+1})" ${drawerPage===totalPages?"disabled":""}>Next →</button>`;
            drawerPages.innerHTML = ph;
        }
    }
}

function changeDrawerPage(page) {
    const totalPages = Math.ceil(drawerFiltered.length / DRAWER_PER_PAGE);
    if (page < 1 || page > totalPages) return;
    drawerPage = page;
    renderDrawerGallery();
    const drawerEl = document.getElementById("cat-drawer");
    if (drawerEl) drawerEl.querySelector(".cat-drawer-panel").scrollTo({ top: 0, behavior: "smooth" });
}

// Close on backdrop click
document.getElementById("cat-drawer").addEventListener("click", (e) => {
    if (e.target.id === "cat-drawer") closeDrawer();
});
document.getElementById("login-modal").addEventListener("click", (e) => {
    if (e.target.id === "login-modal") closeLoginModal();
});

// Close on Escape
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeDrawer();
        closePaymentModal();
        closeLoginModal();
    }
});

window.closeDrawer      = closeDrawer;
window.changeDrawerPage = changeDrawerPage;

// ===============================
// Filter Logic
// ===============================

function applyFilters() {
    currentPage = 1;
    filteredWallpapers = wallpapers.filter(item => {
        const matchCat    = currentCategory === "all" || item.category.toLowerCase() === currentCategory.toLowerCase();
        const query       = searchQuery.toLowerCase();
        const matchSearch = query === "" || item.title.toLowerCase().includes(query) || item.category.toLowerCase().includes(query);
        return matchCat && matchSearch;
    });
    renderGallery();
    renderPagination();
    updateResultCount();
}

// ===============================
// Unlock Storage
// ===============================

function unlockCategory(cat) {
    let unlocked = JSON.parse(localStorage.getItem("unlocked_packs") || "[]");
    if (!unlocked.includes(cat.toLowerCase())) {
        unlocked.push(cat.toLowerCase());
        localStorage.setItem("unlocked_packs", JSON.stringify(unlocked));
    }
}

function isUnlocked(category) {
    let unlocked = JSON.parse(localStorage.getItem("unlocked_packs") || "[]");
    return unlocked.includes("ultimate") || unlocked.includes(category.toLowerCase());
}

// ===============================
// Render Gallery Cards
// ===============================

function renderGallery() {
    if (!galleryEl) return;
    galleryEl.innerHTML = "";

    if (filteredWallpapers.length === 0) {
        galleryEl.innerHTML = `<p class="gallery-empty">No wallpapers match your search.</p>`;
        return;
    }

    const start     = (currentPage - 1) * CARDS_PER_PAGE;
    const pageItems = filteredWallpapers.slice(start, start + CARDS_PER_PAGE);

    pageItems.forEach(item => {
        const isFree    = item.id <= 10;
        const hasAccess = isFree || isUnlocked(item.category);

        const card = document.createElement("div");
        card.className   = "gallery-card";
        card.dataset.cat = item.category.toLowerCase();
        card.addEventListener("contextmenu", e => e.preventDefault());
        card.addEventListener("dragstart",   e => e.preventDefault());

        card.innerHTML = `
            <img class="gallery-card-img" src="${item.image}" alt="${item.title}" loading="lazy" oncontextmenu="return false;" ondragstart="return false;">
            <div class="gallery-card-overlay" oncontextmenu="return false;">
                <span class="gallery-tag">${item.category}</span>
                ${hasAccess
                    ? `<button class="download-btn" onclick="handleDownload(event, '${item.download}', '${item.title}')">↓ Download</button>`
                    : `<button class="download-btn" style="background:var(--grad);" onclick="openPaymentModal('${item.category}','${item.title}');event.stopPropagation();">🔒 Unlock</button>`
                }
            </div>
            <span class="gallery-free-badge ${hasAccess ? "free" : "premium"}">${hasAccess ? "FREE" : "🔒 PREMIUM"}</span>
        `;
        galleryEl.appendChild(card);
    });
}

// ===============================
// Pagination
// ===============================

function renderPagination() {
    if (!paginationEl) return;
    const totalPages = Math.ceil(filteredWallpapers.length / CARDS_PER_PAGE);
    if (totalPages <= 1) { paginationEl.innerHTML = ""; return; }

    let html = `<button class="page-btn${currentPage===1?" disabled":""}" onclick="changePage(${currentPage-1})" ${currentPage===1?"disabled":""}>← Prev</button>`;
    for (let i = 1; i <= Math.min(totalPages, 7); i++) {
        html += `<button class="page-btn${i===currentPage?" active":""}" onclick="changePage(${i})">${i}</button>`;
    }
    html += `<button class="page-btn${currentPage===totalPages?" disabled":""}" onclick="changePage(${currentPage+1})" ${currentPage===totalPages?"disabled":""}>Next →</button>`;
    paginationEl.innerHTML = html;
}

function changePage(page) {
    const totalPages = Math.ceil(filteredWallpapers.length / CARDS_PER_PAGE);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderGallery();
    renderPagination();
    document.getElementById("wallpapers").scrollIntoView({ behavior: "smooth", block: "start" });
}
window.changePage = changePage;

function updateResultCount() {
    if (!resultCount) return;
    resultCount.textContent = filteredWallpapers.length === 1 ? "1 wallpaper" : `${filteredWallpapers.length} wallpapers`;
}

// ── Category pill filter ──
function filterCat(button, category) {
    document.querySelectorAll(".cat-pill").forEach(p => p.classList.remove("active"));
    button.classList.add("active");
    currentCategory = category;
    applyFilters();
}
window.filterCat = filterCat;

// ── Search ──
if (searchInput) {
    searchInput.addEventListener("input", () => {
        searchQuery = searchInput.value.trim();
        applyFilters();
    });
}

// ── Mobile hamburger ──
const hamburger = document.querySelector(".nav-hamburger");
const navLinks  = document.querySelector(".nav-links");
if (hamburger && navLinks) hamburger.addEventListener("click", () => navLinks.classList.toggle("open"));

// ===============================
// Payment Modal
// ===============================

const paymentModal   = document.getElementById("payment-modal");
const modalTitle     = document.getElementById("modal-title");
const modalDesc      = document.getElementById("modal-desc");
const packBtn        = document.getElementById("modal-btn-pack");
const mainIcon       = document.getElementById("modal-main-icon");
const optionsWrapper = document.getElementById("modal-options-wrapper");

function openPaymentModal(category, title) {
    activeCategoryForUnlock = category;
    activeTitleForUnlock    = title;
    if (!paymentModal) return;
    mainIcon.textContent         = "🔒";
    mainIcon.style.animation     = "none";
    mainIcon.style.color         = "inherit";
    modalTitle.textContent       = `Unlock ${title}`;
    modalDesc.textContent        = `This wallpaper belongs to the premium ${category} Pack. Unlock all ${category} wallpapers, or upgrade to the Ultimate Bundle for all categories.`;
    optionsWrapper.style.display = "flex";
    if (packBtn) { packBtn.style.display = "block"; packBtn.textContent = `Unlock ${category} Pack (₹99)`; }
    paymentModal.classList.add("active");
}

function openPricingModal(category, title, type) {
    activeCategoryForUnlock = category;
    activeTitleForUnlock    = title;
    if (!paymentModal) return;
    mainIcon.textContent         = "🔒";
    mainIcon.style.animation     = "none";
    mainIcon.style.color         = "inherit";
    modalTitle.textContent       = `Unlock ${title}`;
    optionsWrapper.style.display = "flex";
    if (type === "bundle") {
        modalDesc.textContent = "Unlock the Ultimate Bundle with lifetime access to all 20 wallpaper categories instantly.";
        if (packBtn) packBtn.style.display = "none";
    } else {
        modalDesc.textContent = `Unlock the premium ${category} Pack, or upgrade to the Ultimate Bundle for all categories.`;
        if (packBtn) { packBtn.style.display = "block"; packBtn.textContent = `Unlock ${category} Pack (₹99)`; }
    }
    paymentModal.classList.add("active");
}

function closePaymentModal() {
    if (paymentModal) paymentModal.classList.remove("active");
}

function processMockPayment(type) {
    if (!paymentModal) return;
    mainIcon.textContent         = "⏳";
    mainIcon.style.animation     = "spin 1s linear infinite";
    mainIcon.style.color         = "var(--a1)";
    modalTitle.textContent       = "Processing Secure Payment...";
    modalDesc.textContent        = "Connecting to billing gateway. Please do not refresh or close this window.";
    optionsWrapper.style.display = "none";

    // Remove old continue button if exists
    paymentModal.querySelectorAll(".modal-continue-btn").forEach(b => b.remove());

    setTimeout(() => {
        mainIcon.textContent   = "✓";
        mainIcon.style.animation = "none";
        mainIcon.style.color   = "var(--a5)";
        modalTitle.textContent = "Payment Successful!";
        modalDesc.textContent  = "Your purchase is complete! The gallery has been unlocked and your pack is downloading now.";

        const continueBtn = document.createElement("button");
        continueBtn.className   = "modal-btn primary modal-continue-btn";
        continueBtn.textContent = "Continue";
        continueBtn.style.marginTop = "20px";
        continueBtn.onclick = () => closeAndReloadModal();
        modalDesc.after(continueBtn);

        let zipUrl, zipName;
        if (type === "bundle") {
            zipUrl  = "assets/bundles/ultimate_bundle.zip";
            zipName = "ultimate_bundle.zip";
            unlockCategory("ultimate");
        } else {
            const catLower = activeCategoryForUnlock.toLowerCase().replace(/\s+/g, '_');
            zipUrl  = `assets/bundles/${catLower}_pack.zip`;
            zipName = `${catLower}_pack.zip`;
            unlockCategory(catLower);
        }
        const dl = document.createElement("a");
        dl.href = zipUrl; dl.download = zipName;
        document.body.appendChild(dl); dl.click(); document.body.removeChild(dl);
    }, 2000);
}

function closeAndReloadModal() {
    closePaymentModal();
    renderGallery();
    if (drawerCategory) renderDrawerGallery();
}

window.openPaymentModal    = openPaymentModal;
window.openPricingModal    = openPricingModal;
window.closePaymentModal   = closePaymentModal;
window.processMockPayment  = processMockPayment;
window.closeAndReloadModal = closeAndReloadModal;

// ── Init ──
loadWallpapers();