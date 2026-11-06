document.addEventListener("DOMContentLoaded", () => {
    initializeColorSwatches();
    initializeFullImageViewer();
    initializeInteractiveCards();
    initializeCopyButtons();
    initializeReveal();
});
 
 
function initializeColorSwatches() {
    document.querySelectorAll(".swatch-box, [data-color]").forEach((swatch) => {
        const color = (swatch.dataset.color || "").trim();
 
        if (!color) {
            return;
        }
 
        // Supports HEX, rgb(), rgba(), named CSS colors, etc.
        swatch.style.backgroundColor = color;
        swatch.style.background = color;
        swatch.setAttribute("title", `Detected color: ${color}`);
        swatch.setAttribute("role", "button");
        swatch.setAttribute("tabindex", "0");
 
        const showColor = () => {
            showToast(`${color} selected`);
        };
 
        swatch.addEventListener("click", showColor);
        swatch.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                showColor();
            }
        });
    });
}
 
 
/* View Full Image: opens inside the page with an X button (works for both the original
   and the AI redesign; the redesign button had no script before). */
function initializeFullImageViewer() {
    const original = document.querySelector("#uploadedRoomImage");
    const generated = document.querySelector("#generatedRoomImage");
    if (!original) {
        return;
    }
 
    const viewer = document.createElement("div");
    viewer.className = "viewer";
    viewer.setAttribute("role", "dialog");
    viewer.setAttribute("aria-modal", "true");
    viewer.setAttribute("aria-label", "Full image");
    viewer.innerHTML =
        '<button type="button" class="viewer-close" aria-label="Close image"><i class="fa-solid fa-xmark"></i></button>' +
        '<div class="viewer-tabs"></div><img alt=""><p class="viewer-hint">Press Esc or click outside to close</p>';
    document.body.appendChild(viewer);
 
    const tabs = viewer.querySelector(".viewer-tabs");
    const big = viewer.querySelector("img");
    const items = [{ label: "Original Space", img: original }];
    if (generated) {
        items.push({ label: "AI Redesign", img: generated });
    }
 
    items.forEach((item, index) => {
        const tab = document.createElement("button");
        tab.type = "button";
        tab.textContent = item.label;
        tab.addEventListener("click", () => select(index));
        tabs.appendChild(tab);
    });
    tabs.style.display = items.length > 1 ? "flex" : "none";
 
    let lastFocus = null;
 
    function select(index) {
        big.src = items[index].img.currentSrc || items[index].img.src;
        big.alt = items[index].label;
        tabs.querySelectorAll("button").forEach((b, i) => b.classList.toggle("on", i === index));
    }
 
    function open(index) {
        lastFocus = document.activeElement;
        select(index);
        viewer.classList.add("show");
        document.body.classList.add("viewer-open");
        viewer.querySelector(".viewer-close").focus();
    }
 
    function close() {
        viewer.classList.remove("show");
        document.body.classList.remove("viewer-open");
        if (lastFocus && lastFocus.focus) {
            lastFocus.focus();
        }
    }
 
    document.querySelector("#viewFullImage")?.addEventListener("click", () => open(0));
    document.querySelector("#viewFullGenerated")?.addEventListener("click", () => open(1));
    original.addEventListener("click", () => open(0));
    generated?.addEventListener("click", () => open(1));
    viewer.addEventListener("click", (event) => {
        if (event.target === viewer || event.target.closest(".viewer-close")) {
            close();
        }
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            close();
        }
    });
}
 
 
function initializeInteractiveCards() {
    document.querySelectorAll(".object-result, .layout-card, .color-result").forEach((card) => {
        card.style.transition = "transform 180ms ease, box-shadow 180ms ease";
 
        card.addEventListener("mouseenter", () => {
            card.style.transform = "translateY(-3px)";
        });
 
        card.addEventListener("mouseleave", () => {
            card.style.transform = "translateY(0)";
        });
    });
}
 
 
function initializeCopyButtons() {
    document.querySelectorAll(".color-details").forEach((details) => {
        const hexText = Array.from(details.querySelectorAll("span"))
            .map((element) => element.textContent.trim())
            .find((text) => /^#[0-9a-f]{6}$/i.test(text));
 
        if (!hexText) {
            return;
        }
 
        const copyButton = document.createElement("button");
        copyButton.type = "button";
        copyButton.textContent = "Copy HEX";
        copyButton.className = "copy-color-button";
 
        copyButton.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(hexText);
                copyButton.textContent = "Copied";
                showToast(`${hexText} copied to clipboard`);
            } catch (error) {
                // Clipboard access can be blocked on non-secure local pages.
                copyButton.textContent = hexText;
                showToast(`Color: ${hexText}`);
            }
 
            window.setTimeout(() => {
                copyButton.textContent = "Copy HEX";
            }, 1500);
        });
 
        details.appendChild(copyButton);
    });
}
 
 
function showToast(message) {
    const existingToast = document.querySelector(".result-js-toast");
    if (existingToast) {
        existingToast.remove();
    }
 
    const toast = document.createElement("div");
    toast.className = "result-js-toast";
    toast.textContent = message;
    document.body.appendChild(toast);
 
    window.setTimeout(() => {
        toast.style.opacity = "0";
        window.setTimeout(() => toast.remove(), 260);
    }, 1800);
}
 
 
// Look only: sections fade in as you scroll
function initializeReveal() {
    const io = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("in");
                io.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
}
