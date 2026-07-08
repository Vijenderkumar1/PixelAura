// ===============================
// PixelAura — app.js v2.0
// ===============================

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

const gallery      = document.getElementById("gallery");
const paginationEl = document.getElementById("pagination");
const searchInput  = document.getElementById("search-input");
const resultCount  = document.getElementById("result-count");
const CARDS_PER_PAGE = 24;

let wallpapers         = [];
let filteredWallpapers = [];
let currentPage        = 1;
let currentCategory    = "all";
let searchQuery        = "";
let activeCategoryForUnlock = "";
let activeTitleForUnlock    = "";

// ===============================
// Load wallpapers.json
// ===============================

async function loadWallpapers() {
    try {
        const response = await fetch("data/wallpapers.json");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        wallpapers = await response.json();

        // Update stats bar
        const statTotal = document.getElementById("stat-total");
        if (statTotal) statTotal.textContent = wallpapers.length + "+";

        // Hero preview cards
        const previewCards = document.querySelectorAll(".hero-preview .wp-card");
        previewCards.forEach((card, index) => {
            if (wallpapers[index]) {
                card.innerHTML = `<img src="${wallpapers[index].image}" alt="${wallpapers[index].title}" class="gallery-card-img" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" oncontextmenu="return false;" ondragstart="return false;">`;
                card.addEventListener("contextmenu", (e) => e.preventDefault());
                card.addEventListener("dragstart", (e) => e.preventDefault());
            }
        });

        // Build category cards dynamically from all 20 categories
        buildCategoryGrid();

        applyFilters();

    } catch (error) {
        console.error("Failed to load wallpapers.json:", error);
        gallery.innerHTML = `<p class="gallery-empty">No wallpapers found.<br>Run <code>python ai_engine/run.py</code> to generate wallpapers.</p>`;
    }
}

// ===============================
// Build 20-Category Dynamic Grid
// ===============================

const ALL_CATEGORIES = [
    { name: "AMOLED",        gradient: "g1"  },
    { name: "Space",         gradient: "g7"  },
    { name: "Nature",        gradient: "g5"  },
    { name: "Cyberpunk",     gradient: "g4"  },
    { name: "Minimal",       gradient: "g6"  },
    { name: "Fantasy",       gradient: "g3"  },
    { name: "Ocean",         gradient: "g9"  },
    { name: "Galaxy",        gradient: "g12" },
    { name: "Cars",          gradient: "g10" },
    { name: "Forest",        gradient: "g8"  },
    { name: "Anime",         gradient: "g2"  },
    { name: "Abstract",      gradient: "g11" },
    { name: "Neon",          gradient: "g1"  },
    { name: "Tech",          gradient: "g7"  },
    { name: "Texture",       gradient: "g5"  },
    { name: "Architecture",  gradient: "g4"  },
    { name: "Retro",         gradient: "g6"  },
    { name: "Pastel",        gradient: "g3"  },
    { name: "Aurora",        gradient: "g9"  },
    { name: "3D Render",     gradient: "g12" },
];

function buildCategoryGrid() {
    const catGrid        = document.getElementById("cat-grid");
    const catSearchInput = document.getElementById("cat-search-input");
    if (!catGrid) return;

    function renderCatGrid(query) {
        const q = (query || "").toLowerCase().trim();
        const filtered = ALL_CATEGORIES.filter(c => q === "" || c.name.toLowerCase().includes(q));

        catGrid.innerHTML = "";

        if (filtered.length === 0) {
            catGrid.innerHTML = `<p class="gallery-empty" style="grid-column:1/-1">No categories match "${q}"</p>`;
            return;
        }

        filtered.forEach(cat => {
            const matched = wallpapers.filter(w => w.category.toLowerCase() === cat.name.toLowerCase());
            const coverImg = matched.length > 0 ? matched[0].image : null;

            const card = document.createElement("div");
            card.className = "cat-card";
            card.innerHTML = `
                <div class="cat-card-bg ${cat.gradient}" style="${coverImg ? `background:url(${coverImg}) no-repeat center center/cover;pointer-events:none;user-select:none;` : ""}"></div>
                <span class="cat-card-label">${cat.name}</span>
                <span class="cat-card-count">${matched.length}</span>
            `;

            card.addEventListener("contextmenu", e => e.preventDefault());
            card.addEventListener("dragstart",   e => e.preventDefault());

            // ── CLICK → open Category Drawer ──
            card.addEventListener("click", () => openCategoryDrawer(cat.name));

            catGrid.appendChild(card);
        });
    }

    // Initial render
    renderCatGrid("");

    // Search inside categories
    if (catSearchInput) {
        catSearchInput.addEventListener("input", () => renderCatGrid(catSearchInput.value));
    }
}

// ===============================
// Category Drawer (Slide-In Panel)
// ===============================

let drawerCategory = "";
let drawerFiltered = [];
let drawerPage     = 1;
const DRAWER_PER_PAGE = 20;

function openCategoryDrawer(categoryName) {
    drawerCategory = categoryName;
    drawerPage     = 1;
    drawerFiltered = wallpapers.filter(w => w.category.toLowerCase() === categoryName.toLowerCase());

    const drawer      = document.getElementById("cat-drawer");
    const drawerTitle = document.getElementById("drawer-title");
    const drawerCount = document.getElementById("drawer-count");

    if (!drawer) return;

    drawerTitle.textContent = categoryName;
    drawerCount.textContent = `${drawerFiltered.length} wallpaper${drawerFiltered.length !== 1 ? "s" : ""}`;

    renderDrawerGallery();
    drawer.classList.add("active");
    document.body.style.overflow = "hidden";
}

function closeDrawer() {
    const drawer = document.getElementById("cat-drawer");
    if (!drawer) return;
    drawer.classList.remove("active");
    document.body.style.overflow = "";
}

function renderDrawerGallery() {
    const drawerGrid  = document.getElementById("drawer-gallery");
    const drawerPages = document.getElementById("drawer-pagination");
    if (!drawerGrid) return;

    drawerGrid.innerHTML = "";

    if (drawerFiltered.length === 0) {
        drawerGrid.innerHTML = `<p class="gallery-empty" style="grid-column:1/-1">No wallpapers yet in this category. Check back after the next AI generation run!</p>`;
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
                    ? `<a class="download-btn" href="${item.download}" download="${item.title}" onclick="event.stopPropagation()">↓ Download</a>`
                    : `<button class="download-btn" onclick="openPaymentModal('${item.category}','${item.title}');event.stopPropagation();">🔒 Unlock</button>`
                }
            </div>
            <span class="gallery-free-badge ${hasAccess ? "free" : "premium"}">${hasAccess ? "FREE" : "🔒 PREMIUM"}</span>
        `;
        drawerGrid.appendChild(card);
    });

    // Drawer pagination
    const totalPages = Math.ceil(drawerFiltered.length / DRAWER_PER_PAGE);
    if (drawerPages) {
        if (totalPages <= 1) {
            drawerPages.innerHTML = "";
        } else {
            let pHtml = `<button class="page-btn${drawerPage===1?" disabled":""}" onclick="changeDrawerPage(${drawerPage-1})" ${drawerPage===1?"disabled":""}>← Prev</button>`;
            for (let i = 1; i <= totalPages; i++) {
                pHtml += `<button class="page-btn${i===drawerPage?" active":""}" onclick="changeDrawerPage(${i})">${i}</button>`;
            }
            pHtml += `<button class="page-btn${drawerPage===totalPages?" disabled":""}" onclick="changeDrawerPage(${drawerPage+1})" ${drawerPage===totalPages?"disabled":""}>Next →</button>`;
            drawerPages.innerHTML = pHtml;
        }
    }
}

function changeDrawerPage(page) {
    const totalPages = Math.ceil(drawerFiltered.length / DRAWER_PER_PAGE);
    if (page < 1 || page > totalPages) return;
    drawerPage = page;
    renderDrawerGallery();
    document.getElementById("cat-drawer").scrollTo({ top: 0, behavior: "smooth" });
}

window.closeDrawer       = closeDrawer;
window.changeDrawerPage  = changeDrawerPage;

// ===============================
// Filter Logic (category + search)
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
// Purchase Unlocks Storage
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
    gallery.innerHTML = "";
    if (filteredWallpapers.length === 0) {
        gallery.innerHTML = `<p class="gallery-empty">No wallpapers match your search.</p>`;
        return;
    }
    const start     = (currentPage - 1) * CARDS_PER_PAGE;
    const pageItems = filteredWallpapers.slice(start, start + CARDS_PER_PAGE);

    pageItems.forEach(item => {
        const isFree    = item.id <= 10;
        const hasAccess = isFree || isUnlocked(item.category);

        const card = document.createElement("div");
        card.className = "gallery-card";
        card.dataset.cat = item.category.toLowerCase();
        card.addEventListener("contextmenu", e => e.preventDefault());
        card.addEventListener("dragstart",   e => e.preventDefault());

        card.innerHTML = `
            <img class="gallery-card-img" src="${item.image}" alt="${item.title}" loading="lazy" oncontextmenu="return false;" ondragstart="return false;">
            <div class="gallery-card-overlay" oncontextmenu="return false;">
                <span class="gallery-tag">${item.category}</span>
                ${hasAccess
                    ? `<a class="download-btn" href="${item.download}" download="${item.title}" title="Download ${item.title}" onclick="event.stopPropagation()">↓ Download</a>`
                    : `<button class="download-btn" style="background:var(--grad);" onclick="openPaymentModal('${item.category}','${item.title}');event.stopPropagation();">🔒 Unlock</button>`
                }
            </div>
            <span class="gallery-free-badge ${hasAccess ? "free" : "premium"}">${hasAccess ? "FREE" : "🔒 PREMIUM"}</span>
        `;
        gallery.appendChild(card);
    });
}

// ===============================
// Pagination
// ===============================

function renderPagination() {
    if (!paginationEl) return;
    const totalPages = Math.ceil(filteredWallpapers.length / CARDS_PER_PAGE);
    if (totalPages <= 1) { paginationEl.innerHTML = ""; return; }

    const MAX_VISIBLE = 5;
    let startPage = Math.max(1, currentPage - Math.floor(MAX_VISIBLE / 2));
    let endPage   = Math.min(totalPages, startPage + MAX_VISIBLE - 1);
    if (endPage - startPage < MAX_VISIBLE - 1) startPage = Math.max(1, endPage - MAX_VISIBLE + 1);

    let html = `<button class="page-btn${currentPage===1?" disabled":""}" onclick="changePage(${currentPage-1})" ${currentPage===1?"disabled":""}>← Prev</button>`;
    if (startPage > 1) { html += `<button class="page-btn" onclick="changePage(1)">1</button>`; if (startPage > 2) html += `<span class="page-dots">…</span>`; }
    for (let i = startPage; i <= endPage; i++) html += `<button class="page-btn${i===currentPage?" active":""}" onclick="changePage(${i})">${i}</button>`;
    if (endPage < totalPages) { if (endPage < totalPages - 1) html += `<span class="page-dots">…</span>`; html += `<button class="page-btn" onclick="changePage(${totalPages})">${totalPages}</button>`; }
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
    const total = filteredWallpapers.length;
    resultCount.textContent = total === 1 ? "1 wallpaper" : `${total} wallpapers`;
}

// ===============================
// Category Filter (pills)
// ===============================

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

// ── Close drawer on backdrop click ──
const drawer = document.getElementById("cat-drawer");
if (drawer) {
    drawer.addEventListener("click", (e) => {
        if (e.target === drawer) closeDrawer();
    });
}

// ── Close drawer on Escape ──
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeDrawer();
        closePaymentModal();
    }
});

// ===============================
// Payment & Unlock Modal Logic
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
    mainIcon.textContent       = "🔒";
    mainIcon.style.animation   = "none";
    mainIcon.style.color       = "inherit";
    modalTitle.textContent     = `Unlock ${title}`;
    modalDesc.textContent      = `This wallpaper belongs to the premium ${category} Pack. Unlock all ${category} wallpapers, or upgrade to the Ultimate Bundle to unlock all categories.`;
    optionsWrapper.style.display = "flex";
    if (packBtn) { packBtn.style.display = "block"; packBtn.textContent = `Unlock ${category} Pack (₹99)`; }
    paymentModal.classList.add("active");
}

function openPricingModal(category, title, type) {
    activeCategoryForUnlock = category;
    activeTitleForUnlock    = title;
    if (!paymentModal) return;
    mainIcon.textContent       = "🔒";
    mainIcon.style.animation   = "none";
    mainIcon.style.color       = "inherit";
    modalTitle.textContent     = `Unlock ${title}`;
    optionsWrapper.style.display = "flex";
    if (type === "bundle") {
        modalDesc.textContent = "Unlock the Ultimate Bundle with lifetime download access to all 20 wallpaper categories instantly.";
        if (packBtn) packBtn.style.display = "none";
    } else {
        modalDesc.textContent = `Unlock the premium ${category} Pack with all matching wallpapers, or upgrade to the Ultimate Bundle with lifetime access to all categories.`;
        if (packBtn) { packBtn.style.display = "block"; packBtn.textContent = `Unlock ${category} Pack (₹99)`; }
    }
    paymentModal.classList.add("active");
}

function closePaymentModal() {
    if (paymentModal) paymentModal.classList.remove("active");
}

function processMockPayment(type) {
    if (!paymentModal) return;
    mainIcon.textContent       = "⏳";
    mainIcon.style.animation   = "spin 1s linear infinite";
    mainIcon.style.color       = "var(--a1)";
    modalTitle.textContent     = "Processing Secure Payment...";
    modalDesc.textContent      = "Connecting to billing gateway. Please do not refresh or close this window.";
    optionsWrapper.style.display = "none";

    setTimeout(() => {
        mainIcon.textContent   = "✓";
        mainIcon.style.animation = "none";
        mainIcon.style.color   = "var(--a5)";
        modalTitle.textContent = "Payment Successful!";
        modalDesc.textContent  = "Your purchase is complete! The gallery has been unlocked and your pack is downloading now.";

        // Remove any old continue button
        const oldBtn = paymentModal.querySelector(".modal-continue-btn");
        if (oldBtn) oldBtn.remove();

        const continueBtn = document.createElement("button");
        continueBtn.className = "modal-btn primary modal-continue-btn";
        continueBtn.textContent = "Continue";
        continueBtn.style.marginTop = "20px";
        continueBtn.onclick = () => closeAndReloadModal(type);
        modalDesc.parentNode.insertBefore(continueBtn, modalDesc.nextSibling);

        let zipUrl, zipName;
        if (type === "bundle") {
            zipUrl  = "assets/bundles/ultimate_bundle.zip";
            zipName = "ultimate_bundle.zip";
            unlockCategory("ultimate");
        } else {
            const catLower = activeCategoryForUnlock.toLowerCase();
            zipUrl  = `assets/bundles/${catLower}_pack.zip`;
            zipName = `${catLower}_pack.zip`;
            unlockCategory(catLower);
        }
        const dLink = document.createElement("a");
        dLink.href = zipUrl; dLink.download = zipName;
        document.body.appendChild(dLink); dLink.click(); document.body.removeChild(dLink);
    }, 2000);
}

function closeAndReloadModal() {
    closePaymentModal();
    renderGallery();
    if (drawerCategory) renderDrawerGallery();
}

window.openPaymentModal   = openPaymentModal;
window.openPricingModal   = openPricingModal;
window.closePaymentModal  = closePaymentModal;
window.processMockPayment = processMockPayment;
window.closeAndReloadModal = closeAndReloadModal;

// ── Init ──
loadWallpapers();