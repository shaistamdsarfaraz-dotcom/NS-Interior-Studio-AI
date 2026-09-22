const bios = {
    shaista: {
        name: "Shaista Mohammadi",
        text: "Co-founder and developer of NS Design AI, Shaista led the technical build of the platform — from the Flask backend to the AI-based colour detection and room analysis features.",
        instagram: "https://www.instagram.com/"
    },
    nida: {
        name: "Nida Fathima",
        text: "Co-founder of NS Design AI, Nida worked on shaping the design direction and user experience of the platform, ensuring the tool stays simple, intuitive, and genuinely useful.",
        instagram: "https://www.instagram.com/"
    }
};

function openBio(person) {
    const bio = bios[person];
    if (!bio) return;
    const name = document.getElementById("bio-name");
    const text = document.getElementById("bio-text");
    const instagram = document.getElementById("bio-instagram");
    const modal = document.getElementById("bio-modal");
    if (name) name.textContent = bio.name;
    if (text) text.textContent = bio.text;
    if (instagram) instagram.href = bio.instagram;
    if (modal) modal.classList.add("active");
}

function closeBio() {
    const modal = document.getElementById("bio-modal");
    if (modal) modal.classList.remove("active");
}

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
        </div>
    `;

    return overlay;
}

function openWorkImage(image) {
    if (!image || !image.src) return;

    const overlay = getLightbox();
    const largeImage = overlay.querySelector(".ns-lightbox-image");
    const title = overlay.querySelector(".ns-lightbox-title");
    const isAfter = image.closest(".after-image") !== null;

    largeImage.src = image.currentSrc || image.src;
    largeImage.alt = image.alt || "Full size interior design image";
    title.textContent = isAfter ? "AFTER — AI DESIGN CONCEPT" : "BEFORE — ORIGINAL SPACE";

    overlay.classList.add("ns-lightbox-visible");
    document.body.classList.add("ns-lightbox-page-lock");
}

function closeWorkImage() {
    const overlay = document.getElementById("nsWorkLightbox");
    if (overlay) overlay.classList.remove("ns-lightbox-visible");
    document.body.classList.remove("ns-lightbox-page-lock");
}

function setupWorkViewer() {
    const images = document.querySelectorAll(".work-image img");

    images.forEach(function (image) {
        image.style.cursor = "zoom-in";
        image.setAttribute("tabindex", "0");
        image.setAttribute("role", "button");
        image.setAttribute("aria-label", "View full-size image");

        image.onclick = function (event) {
            event.preventDefault();
            event.stopPropagation();
            openWorkImage(image);
        };

        image.onkeydown = function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openWorkImage(image);
            }
        };

        const box = image.closest(".work-image");
        if (box && !box.querySelector(".view-work-button")) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "view-work-button";
            button.innerHTML = '<i class="fa-solid fa-expand"></i> View Full Image';
            button.onclick = function (event) {
                event.preventDefault();
                event.stopPropagation();
                openWorkImage(image);
            };
            box.appendChild(button);
        }
    });

    getLightbox();
}

function startAboutInteractions() {
    setupWorkViewer();

    document.addEventListener("click", function (event) {
        const target = event.target;
        if (!(target instanceof Element)) return;

        if (target.closest(".ns-lightbox-close")) {
            event.preventDefault();
            closeWorkImage();
            return;
        }

        if (target.id === "nsWorkLightbox") {
            closeWorkImage();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeWorkImage();
            closeBio();
        }
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startAboutInteractions, { once: true });
} else {
    startAboutInteractions();
}
