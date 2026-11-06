const bios = {
    shaista: {
        name: "Shaista Mohammadi",
        text: "Founder and developer of NS Design AI, Shaista led the technical build of the platform — from the Flask backend to the AI-based colour detection and room analysis features.",
        instagram: "https://www.instagram.com/"
    },
    nida: {
        name: "Nida Fathima",
        text: "Founder of NS Design AI, Nida worked on shaping the design direction and user experience of the platform, ensuring the tool stays simple, intuitive, and genuinely useful.",
        instagram: "https://www.instagram.com/"
    }
};
 
function openBio(person) {
    const bio = bios[person];
    if (!bio) return;
    document.getElementById("bio-name").textContent = bio.name;
    document.getElementById("bio-text").textContent = bio.text;
    document.getElementById("bio-instagram").href = bio.instagram;
    document.getElementById("bio-modal").classList.add("active");
}
function closeBio() {
    const modal = document.getElementById("bio-modal");
    if (modal) modal.classList.remove("active");
}
 
/* ---------- image lightbox (unchanged behaviour) ---------- */
function getLightbox() {
    let overlay = document.getElementById("nsWorkLightbox");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "nsWorkLightbox";
        document.body.appendChild(overlay);
    }
    overlay.innerHTML = `
        <div class="ns-lightbox-card" role="dialog" aria-modal="true" aria-label="Full size interior design image">
            <button type="button" class="ns-lightbox-close" aria-label="Close image">&times;</button>
            <div class="ns-lightbox-title"></div>
            <img class="ns-lightbox-image" alt="Full size interior design image">
        </div>`;
    return overlay;
}
function openWorkImage(image) {
    if (!image || !image.src) return;
    const overlay = getLightbox();
    const big = overlay.querySelector(".ns-lightbox-image");
    big.src = image.currentSrc || image.src;
    big.alt = image.alt || "Full size interior design image";
    overlay.querySelector(".ns-lightbox-title").textContent =
        image.closest(".after-image") ? "AFTER — AI DESIGN CONCEPT" : "BEFORE — ORIGINAL SPACE";
    overlay.classList.add("ns-lightbox-visible");
    document.body.classList.add("ns-lightbox-page-lock");
}
function closeWorkImage() {
    const overlay = document.getElementById("nsWorkLightbox");
    if (overlay) overlay.classList.remove("ns-lightbox-visible");
    document.body.classList.remove("ns-lightbox-page-lock");
}
function setupWorkViewer() {
    document.querySelectorAll(".work-image img").forEach(function (image) {
        image.setAttribute("tabindex", "0");
        image.setAttribute("role", "button");
        image.setAttribute("aria-label", "View full-size image");
        image.onclick = function (e) { e.preventDefault(); e.stopPropagation(); openWorkImage(image); };
        image.onkeydown = function (e) {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openWorkImage(image); }
        };
    });
    getLightbox();
}
 
/* ---------- motion ---------- */
function setupMotion() {
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const bar = document.querySelector(".progress");
    function onScroll() {
        const max = document.documentElement.scrollHeight - innerHeight;
        if (bar) bar.style.width = (scrollY / max * 100) + "%";
    }
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
 
    const io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
            if (!en.isIntersecting) return;
            en.target.classList.add("in");
            en.target.querySelectorAll("[data-count]").forEach(countUp);
            io.unobserve(en.target);
        });
    }, { threshold: 0.15 });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
 
    function countUp(el) {
        const end = +el.dataset.count, t0 = performance.now();
        (function tick(t) {
            const p = Math.min((t - t0) / 1400, 1);
            el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
            if (p < 1) requestAnimationFrame(tick);
        })(t0);
    }
    if (still) return;
 
    document.querySelectorAll(".tilt, .team-card, .arch").forEach(function (c) {
        const amt = c.classList.contains("arch") ? 8 : 8;
        c.addEventListener("mousemove", function (e) {
            const r = c.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
            c.style.setProperty("--mx", x + "px");
            c.style.setProperty("--my", y + "px");
            c.style.transform = "perspective(900px) rotateY(" + ((x / r.width - .5) * amt) +
                "deg) rotateX(" + (-(y / r.height - .5) * amt) + "deg) translateY(-6px)";
        });
        c.addEventListener("mouseleave", function () { c.style.transform = ""; });
    });
 
    // chat starter chips are handled by chatbot.js
}
 
function startAboutInteractions() {
    setupWorkViewer();
    setupMotion();
    document.addEventListener("click", function (event) {
        const target = event.target;
        if (!(target instanceof Element)) return;
        if (target.closest(".ns-lightbox-close")) { event.preventDefault(); closeWorkImage(); return; }
        if (target.id === "nsWorkLightbox") closeWorkImage();
        if (target.id === "bio-modal") closeBio();
    });
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") { closeWorkImage(); closeBio(); }
    });
}
 
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startAboutInteractions, { once: true });
} else {
    startAboutInteractions();
}
 