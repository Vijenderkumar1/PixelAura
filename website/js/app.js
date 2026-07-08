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
// NOTE: The #gallery div does NOT have .reveal so this observer
// is only used for static section elements (headings, stats, etc.)
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
                    >
                `;
            }
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

        card.innerHTML = `
            <img
                class="gallery-card-img"
                src="${item.image}"
                alt="${item.title}"
                loading="lazy"
            >

            <div class="gallery-card-overlay">
                <span class="gallery-tag">${item.category}</span>
                <a
                    class="download-btn"
                    href="${item.download}"
                    download="${item.title}"
                    title="Download ${item.title}"
                    onclick="event.stopPropagation()"
                >
                    ↓ Download
                </a>
            </div>

            <span class="gallery-free-badge">FREE</span>
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

// ── Init ──
loadWallpapers();