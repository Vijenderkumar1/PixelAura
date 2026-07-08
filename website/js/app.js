// ===============================
// PixelAura — app.js v1.0
// ===============================

// ── NAV scroll glass effect ──
const nav = document.getElementById("nav");

window.addEventListener(
    "scroll",
    () => {
        nav.classList.toggle("scrolled", window.scrollY > 50);
    },
    { passive: true }
);

// ── Scroll reveal animation ──
const revealObserver = new IntersectionObserver(
    (entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.classList.add("visible");
                }, index * 60);
                revealObserver.unobserve(entry.target);
            }
        });
    },
    { threshold: 0.1 }
);

document
    .querySelectorAll(".reveal")
    .forEach((el) => revealObserver.observe(el));

// ===============================
// Gallery State
// ===============================

const gallery      = document.getElementById("gallery");
const paginationEl = document.getElementById("pagination");
const searchInput  = document.getElementById("search-input");
const resultCount  = document.getElementById("result-count");

const CARDS_PER_PAGE = 24;

let wallpapers         = [];   // full dataset from JSON
let filteredWallpapers = [];   // after category + search filters
let currentPage        = 1;
let currentCategory    = "all";
let searchQuery        = "";

let activeCategoryForUnlock = "";
let activeTitleForUnlock = "";

// ===============================
// Load wallpapers.json
// ===============================

async function loadWallpapers() {
    try {
        const response = await fetch("data/wallpapers.json");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        wallpapers = await response.json();

        // Update the stats bar with actual wallpaper count
        const statTotal = document.getElementById("stat-total");
        if (statTotal) {
            statTotal.textContent = wallpapers.length + "+";
        }

        // Populate the hero preview cards with the first 5 wallpapers dynamically
        const previewCards = document.querySelectorAll(".hero-preview .wp-card");
        previewCards.forEach((card, index) => {
            if (wallpapers[index]) {
                card.innerHTML = `
                    <img 
                        src="${wallpapers[index].image}" 
                        alt="${wallpapers[index].title}" 
                        class="gallery-card-img" 
                        style="width:100%; height:100%; object-fit:cover; border-radius:inherit;"
                        oncontextmenu="return false;"
                        ondragstart="return false;"
                    >
                `;
                // Add right-click and drag-start prevention to hero preview card container
                card.addEventListener("contextmenu", (e) => e.preventDefault());
                card.addEventListener("dragstart", (e) => e.preventDefault());
            }
        });

        // Populate categories cards with actual wallpaper counts and category background previews
        const catCards = document.querySelectorAll(".cat-card");
        catCards.forEach((card) => {
            const labelEl = card.querySelector(".cat-card-label");
            const countEl = card.querySelector(".cat-card-count");
            const bgEl    = card.querySelector(".cat-card-bg");

            if (labelEl && countEl) {
                const category = labelEl.textContent.trim();
                const matched = wallpapers.filter(
                    (w) => w.category.toLowerCase() === category.toLowerCase()
                );

                // Set actual count
                countEl.textContent = matched.length;

                // Set preview from the first wallpaper of this category
                if (matched.length > 0 && bgEl) {
                    bgEl.style.background = `url(${matched[0].image}) no-repeat center center/cover`;
                    bgEl.style.pointerEvents = "none";
                    bgEl.style.userSelect = "none";
                }
            }

            // Disable drag and right click on categories card
            card.addEventListener("contextmenu", (e) => e.preventDefault());
            card.addEventListener("dragstart", (e) => e.preventDefault());
        });

        applyFilters();

    } catch (error) {
        console.error("Failed to load wallpapers.json:", error);

        gallery.innerHTML = `
            <p class="gallery-empty">
                No wallpapers found.<br>
                Run <code>python ai_engine/run.py</code> to generate wallpapers.
            </p>
        `;
    }
}

// ===============================
// Filter Logic (category + search)
// ===============================

function applyFilters() {
    currentPage = 1;

    filteredWallpapers = wallpapers.filter((item) => {
        const matchCat =
            currentCategory === "all" ||
            item.category.toLowerCase() === currentCategory.toLowerCase();

        const query = searchQuery.toLowerCase();
        const matchSearch =
            query === "" ||
            item.title.toLowerCase().includes(query) ||
            item.category.toLowerCase().includes(query);

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
        gallery.innerHTML = `
            <p class="gallery-empty">
                No wallpapers match your search.
            </p>
        `;
        return;
    }

    const start     = (currentPage - 1) * CARDS_PER_PAGE;
    const end       = Math.min(start + CARDS_PER_PAGE, filteredWallpapers.length);
    const pageItems = filteredWallpapers.slice(start, end);

    pageItems.forEach((item) => {
        const card = document.createElement("div");
        card.className = "gallery-card";
        card.dataset.cat = item.category.toLowerCase();

        // ── FULL FILE ACCESS & RIGHT CLICK PROTECTION ──
        card.addEventListener("contextmenu", (e) => e.preventDefault());
        card.addEventListener("dragstart", (e) => e.preventDefault());

        // First 10 wallpapers in database are free. Others require pack/bundle purchase
        const isFree = item.id <= 10;
        const hasAccess = isFree || isUnlocked(item.category);

        card.innerHTML = `
            <img
                class="gallery-card-img"
                src="${item.image}"
                alt="${item.title}"
                loading="lazy"
                oncontextmenu="return false;"
                ondragstart="return false;"
            >

            <div class="gallery-card-overlay" oncontextmenu="return false;">
                <span class="gallery-tag">${item.category}</span>
                ${
                    hasAccess
                        ? `
                    <a
                        class="download-btn"
                        href="${item.download}"
                        download="${item.title}"
                        title="Download ${item.title}"
                        onclick="event.stopPropagation()"
                    >
                        ↓ Download
                    </a>
                `
                        : `
                    <button
                        class="download-btn"
                        style="background: var(--grad);"
                        onclick="openPaymentModal('${item.category}', '${item.title}'); event.stopPropagation();"
                    >
                        🔒 Unlock
                    </button>
                `
                }
            </div>

            <span class="gallery-free-badge ${hasAccess ? "free" : "premium"}">
                ${hasAccess ? "FREE" : "🔒 PREMIUM"}
            </span>
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

    if (totalPages <= 1) {
        paginationEl.innerHTML = "";
        return;
    }

    const MAX_VISIBLE = 5;
    let startPage = Math.max(1, currentPage - Math.floor(MAX_VISIBLE / 2));
    let endPage   = Math.min(totalPages, startPage + MAX_VISIBLE - 1);

    // Shift start back if we hit the end
    if (endPage - startPage < MAX_VISIBLE - 1) {
        startPage = Math.max(1, endPage - MAX_VISIBLE + 1);
    }

    let html = "";

    // ← Prev
    html += `
        <button
            class="page-btn${currentPage === 1 ? " disabled" : ""}"
            onclick="changePage(${currentPage - 1})"
            ${currentPage === 1 ? "disabled" : ""}
        >← Prev</button>
    `;

    // First page + ellipsis
    if (startPage > 1) {
        html += `<button class="page-btn" onclick="changePage(1)">1</button>`;
        if (startPage > 2) {
            html += `<span class="page-dots">…</span>`;
        }
    }

    // Page number buttons
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button
                class="page-btn${i === currentPage ? " active" : ""}"
                onclick="changePage(${i})"
            >${i}</button>
        `;
    }

    // Last page + ellipsis
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<span class="page-dots">…</span>`;
        }
        html += `<button class="page-btn" onclick="changePage(${totalPages})">${totalPages}</button>`;
    }

    // Next →
    html += `
        <button
            class="page-btn${currentPage === totalPages ? " disabled" : ""}"
            onclick="changePage(${currentPage + 1})"
            ${currentPage === totalPages ? "disabled" : ""}
        >Next →</button>
    `;

    paginationEl.innerHTML = html;
}

function changePage(page) {
    const totalPages = Math.ceil(filteredWallpapers.length / CARDS_PER_PAGE);
    if (page < 1 || page > totalPages) return;

    currentPage = page;
    renderGallery();
    renderPagination();

    // Scroll smoothly back to the wallpapers section
    document
        .getElementById("wallpapers")
        .scrollIntoView({ behavior: "smooth", block: "start" });
}

window.changePage = changePage;

// ===============================
// Result Count
// ===============================

function updateResultCount() {
    if (!resultCount) return;
    const total = filteredWallpapers.length;
    resultCount.textContent =
        total === 1 ? "1 wallpaper" : `${total} wallpapers`;
}

// ===============================
// Category Filter
// ===============================

function filterCat(button, category) {
    document
        .querySelectorAll(".cat-pill")
        .forEach((pill) => pill.classList.remove("active"));

    button.classList.add("active");
    currentCategory = category;
    applyFilters();
}

window.filterCat = filterCat;

// ===============================
// Search
// ===============================

if (searchInput) {
    searchInput.addEventListener("input", () => {
        searchQuery = searchInput.value.trim();
        applyFilters();
    });
}

// ── Mobile hamburger ──
const hamburger = document.querySelector(".nav-hamburger");
const navLinks  = document.querySelector(".nav-links");

if (hamburger && navLinks) {
    hamburger.addEventListener("click", () => {
        navLinks.classList.toggle("open");
    });
}

// ===============================
// Payment & Unlock Modal Logic
// ===============================

const paymentModal = document.getElementById("payment-modal");
const modalTitle   = document.getElementById("modal-title");
const modalDesc    = document.getElementById("modal-desc");
const packBtn      = document.getElementById("modal-btn-pack");
const bundleBtn    = document.getElementById("modal-btn-bundle");
const mainIcon     = document.getElementById("modal-main-icon");
const optionsWrapper = document.getElementById("modal-options-wrapper");

function openPaymentModal(category, title) {
    activeCategoryForUnlock = category;
    activeTitleForUnlock = title;

    if (paymentModal) {
        // Reset modal structure to default choices
        mainIcon.textContent = "🔒";
        mainIcon.style.animation = "none";
        mainIcon.style.color = "inherit";
        modalTitle.textContent = `Unlock ${title}`;
        modalDesc.textContent = `This wallpaper belongs to the premium ${category} Pack. Unlock all ${category} wallpapers, or upgrade to the Ultimate Bundle to unlock all categories.`;
        optionsWrapper.style.display = "flex";
        if (packBtn) {
            packBtn.style.display = "block";
            packBtn.textContent = `Unlock ${category} Pack (₹99)`;
        }
        paymentModal.classList.add("active");
    }
}

function openPricingModal(category, title, type) {
    activeCategoryForUnlock = category;
    activeTitleForUnlock = title;

    if (paymentModal) {
        // Reset modal structure to default choices
        mainIcon.textContent = "🔒";
        mainIcon.style.animation = "none";
        mainIcon.style.color = "inherit";
        modalTitle.textContent = `Unlock ${title}`;
        optionsWrapper.style.display = "flex";

        if (type === "bundle") {
            modalDesc.textContent = "Unlock the Ultimate Bundle with lifetime download access to all 10 wallpaper categories instantly.";
            if (packBtn) packBtn.style.display = "none";
        } else {
            modalDesc.textContent = `Unlock the premium ${category} Pack with all matching wallpapers, or upgrade to the Ultimate Bundle with lifetime access to all categories.`;
            if (packBtn) {
                packBtn.style.display = "block";
                packBtn.textContent = `Unlock ${category} Pack (₹99)`;
            }
        }
        paymentModal.classList.add("active");
    }
}

function closePaymentModal() {
    if (paymentModal) {
        paymentModal.classList.remove("active");
    }
}

function processMockPayment(type) {
    if (!paymentModal) return;

    // Show processing screen inside the modal
    mainIcon.textContent = "⏳";
    mainIcon.style.animation = "spin 1s linear infinite";
    mainIcon.style.color = "var(--a1)";
    modalTitle.textContent = "Processing Secure Payment...";
    modalDesc.textContent = "Connecting to billing gateway. Please do not refresh or close this window.";
    optionsWrapper.style.display = "none";

    setTimeout(() => {
        // Show success screen
        mainIcon.textContent = "✓";
        mainIcon.style.animation = "none";
        mainIcon.style.color = "var(--a5)";
        modalTitle.textContent = "Payment Successful!";
        modalDesc.textContent = "Your purchase is complete! The gallery has been unlocked and your pack is downloading now.";

        // Append a single button to reload and close
        const continueBtn = document.createElement("button");
        continueBtn.className = "modal-btn primary";
        continueBtn.textContent = "Continue";
        continueBtn.style.marginTop = "20px";
        continueBtn.onclick = () => closeAndReloadModal(type);
        modalDesc.parentNode.insertBefore(continueBtn, modalDesc.nextSibling);

        // Execute dynamic unlocking and trigger download
        let zipUrl = "";
        let zipName = "";
        if (type === "bundle") {
            zipUrl = "assets/bundles/ultimate_bundle.zip";
            zipName = "ultimate_bundle.zip";
            unlockCategory("ultimate");
        } else {
            const catLower = activeCategoryForUnlock.toLowerCase();
            zipUrl = `assets/bundles/${catLower}_pack.zip`;
            zipName = `${catLower}_pack.zip`;
            unlockCategory(catLower);
        }

        // Trigger ZIP bundle download
        const dLink = document.createElement("a");
        dLink.href = zipUrl;
        dLink.download = zipName;
        document.body.appendChild(dLink);
        dLink.click();
        document.body.removeChild(dLink);

    }, 2000);
}

function closeAndReloadModal(type) {
    closePaymentModal();
    // Re-render gallery to reflect unlocked status immediately
    renderGallery();
}

window.openPaymentModal = openPaymentModal;
window.openPricingModal  = openPricingModal;
window.closePaymentModal = closePaymentModal;
window.processMockPayment = processMockPayment;
window.closeAndReloadModal = closeAndReloadModal;

// ── Init ──
loadWallpapers();