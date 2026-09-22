document.addEventListener("DOMContentLoaded", () => {
    initializeColorSwatches();
    initializeFullImageViewer();
    initializeInteractiveCards();
    initializeCopyButtons();
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


function initializeFullImageViewer() {
    const image = document.querySelector("#uploadedRoomImage");
    const button = document.querySelector("#viewFullImage");

    if (!image || !button) {
        return;
    }

    button.addEventListener("click", () => {
        if (image.requestFullscreen) {
            image.requestFullscreen().catch(() => {
                window.open(image.currentSrc || image.src, "_blank", "noopener,noreferrer");
            });
        } else {
            window.open(image.currentSrc || image.src, "_blank", "noopener,noreferrer");
        }
    });
}


function initializeInteractiveCards() {
    document.querySelectorAll(".object-result, .layout-card, .color-result").forEach((card) => {
        card.style.transition = "transform 180ms ease, box-shadow 180ms ease";

        card.addEventListener("mouseenter", () => {
            card.style.transform = "translateY(-3px)";
            card.style.boxShadow = "0 8px 22px rgba(73, 49, 125, 0.12)";
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = "translateY(0)";
            card.style.boxShadow = "";
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
        copyButton.style.cssText = [
            "width: fit-content",
            "margin-top: 4px",
            "padding: 4px 8px",
            "border: 0",
            "border-radius: 10px",
            "background: #eee8ff",
            "color: #624499",
            "font-size: 10px",
            "cursor: pointer"
        ].join(";");

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
    toast.style.cssText = [
        "position: fixed",
        "right: 20px",
        "bottom: 20px",
        "z-index: 9999",
        "padding: 11px 15px",
        "border-radius: 12px",
        "background: #302451",
        "color: #fff",
        "font: 12px Poppins, sans-serif",
        "box-shadow: 0 8px 24px rgba(48, 36, 81, .28)"
    ].join(";");

    document.body.appendChild(toast);

    window.setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 180ms ease";
        window.setTimeout(() => toast.remove(), 200);
    }, 1800);
}
document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("generatedImageModal");
    const fullImage = document.getElementById("fullGeneratedImage");
    const openButton = document.querySelector(".view-full-image-button");
    const closeButton = document.querySelector(".close-image-modal");

    if (!modal || !fullImage || !openButton || !closeButton) {
        return;
    }

    function openImageModal() {
        const imageUrl = openButton.dataset.fullImage;

        if (!imageUrl) {
            return;
        }

        fullImage.src = imageUrl;
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
    }

    function closeImageModal() {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        fullImage.src = "";
        document.body.style.overflow = "";
    }

    openButton.addEventListener("click", openImageModal);

    document
        .getElementById("generatedRoomImage")
        .addEventListener("click", openImageModal);

    closeButton.addEventListener("click", closeImageModal);

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeImageModal();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeImageModal();
        }
    });
});
