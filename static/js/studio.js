document.addEventListener('DOMContentLoaded', function () {
    // 1. User Dropdown Toggle
    const userChip = document.getElementById('userChip');
    const userDropdown = document.getElementById('userDropdown');

    if (userChip && userDropdown) {
        userChip.addEventListener('click', function (event) {
            event.stopPropagation();
            event.preventDefault();
            userDropdown.classList.toggle('show');
        });

        document.addEventListener('click', function (event) {
            if (!userChip.contains(event.target) && !userDropdown.contains(event.target)) {
                userDropdown.classList.remove('show');
            }
        });
    }

    // 2. Room Photo File Input Label Updater
    const roomPhotoInput = document.getElementById('roomPhoto');
    const uploadLabel = document.getElementById('uploadLabel');
    if (roomPhotoInput && uploadLabel) {
        roomPhotoInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                uploadLabel.textContent = this.files[0].name;
            }
        });
    }

    // 3. Form Submission with Dynamic Loading Spinner
    const uploadForm = document.getElementById('uploadForm');
    const submitBtn = uploadForm ? uploadForm.querySelector('button[type="submit"]') : null;

    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            // Set Loading UI State
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Analyzing Interior & Generating Redesign...
                `;
            }

            const formData = new FormData(this);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const html = await response.text();
                    document.open();
                    document.write(html);
                    document.close();
                } else {
                    const errorData = await response.json().catch(() => ({ message: 'Upload failed. Please try again.' }));
                    alert(errorData.message || 'Upload failed. Please try again.');
                    resetSubmitButton(submitBtn);
                }
            } catch (error) {
                console.error('Error uploading design:', error);
                alert('Connection error or timeout during AI processing. Please try again.');
                resetSubmitButton(submitBtn);
            }
        });
    }

    // 4. Color Swatches Background Initialization
    document.querySelectorAll('.swatch-box[data-color]').forEach(box => {
        box.style.backgroundColor = box.dataset.color;
    });

    // Helper: Reset Submit Button State
    function resetSubmitButton(btn) {
        if (btn) {
            btn.disabled = false;
            if (btn.dataset.originalText) {
                btn.innerHTML = btn.dataset.originalText;
            }
        }
    }
});
    document.addEventListener("DOMContentLoaded", function () {
        const form = document.getElementById("uploadForm");
        const input = document.getElementById("roomPhoto");
        const box = document.getElementById("uploadBox");
        const preview = document.getElementById("uploadPreview");
        const fileMeta = document.getElementById("fileMeta");
        const fileName = document.getElementById("fileName");
        const clearFile = document.getElementById("clearFile");
        const label = document.getElementById("uploadLabel");
        const button = document.getElementById("analyzeButton");
        const progress = document.getElementById("analysisProgress");
        const maxSize = 10 * 1024 * 1024;

        function showFile(file) {
            if (!file) return;
            if (!file.type.startsWith("image/")) { alert("Please choose an image file."); return; }
            if (file.size > maxSize) { alert("Please choose an image smaller than 10MB."); return; }
            const reader = new FileReader();
            reader.onload = function (event) {
                preview.src = event.target.result;
                preview.classList.add("visible");
                fileMeta.classList.add("visible");
                box.classList.add("has-file");
                fileName.textContent = file.name;
                label.textContent = "Room photo selected";
            };
            reader.readAsDataURL(file);
        }

        input.addEventListener("change", function () { showFile(input.files[0]); });
        ["dragenter", "dragover"].forEach(function (eventName) { box.addEventListener(eventName, function (event) { event.preventDefault(); box.classList.add("is-dragging"); }); });
        ["dragleave", "drop"].forEach(function (eventName) { box.addEventListener(eventName, function (event) { event.preventDefault(); box.classList.remove("is-dragging"); }); });
        box.addEventListener("drop", function (event) { showFile(event.dataTransfer.files[0]); });
        clearFile.addEventListener("click", function () { input.value = ""; preview.src = ""; preview.classList.remove("visible"); fileMeta.classList.remove("visible"); box.classList.remove("has-file"); label.textContent = "Choose Room Photo"; });
        form.addEventListener("submit", function (event) { if (!input.files.length) { event.preventDefault(); alert("Please choose a room photo first."); return; } button.disabled = true; button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing your room…'; progress.classList.add("visible"); });
    });
    document.addEventListener("DOMContentLoaded", function () {
        const form = document.getElementById("uploadForm");
        const input = document.getElementById("roomPhoto");
        const box = document.getElementById("uploadBox");
        const preview = document.getElementById("uploadPreview");
        const fileMeta = document.getElementById("fileMeta");
        const fileName = document.getElementById("fileName");
        const clearFile = document.getElementById("clearFile");
        const label = document.getElementById("uploadLabel");
        const button = document.getElementById("analyzeButton");
        const progress = document.getElementById("analysisProgress");
        const maxSize = 10 * 1024 * 1024;

        function showFile(file) {
            if (!file) return;
            if (!file.type.startsWith("image/")) { alert("Please choose an image file."); return; }
            if (file.size > maxSize) { alert("Please choose an image smaller than 10MB."); return; }
            const reader = new FileReader();
            reader.onload = function (event) {
                preview.src = event.target.result;
                preview.classList.add("visible");
                fileMeta.classList.add("visible");
                box.classList.add("has-file");
                fileName.textContent = file.name;
                label.textContent = "Room photo selected";
            };
            reader.readAsDataURL(file);
        }

        input.addEventListener("change", function () { showFile(input.files[0]); });
        ["dragenter", "dragover"].forEach(function (eventName) { box.addEventListener(eventName, function (event) { event.preventDefault(); box.classList.add("is-dragging"); }); });
        ["dragleave", "drop"].forEach(function (eventName) { box.addEventListener(eventName, function (event) { event.preventDefault(); box.classList.remove("is-dragging"); }); });
        box.addEventListener("drop", function (event) { showFile(event.dataTransfer.files[0]); });
        clearFile.addEventListener("click", function () { input.value = ""; preview.src = ""; preview.classList.remove("visible"); fileMeta.classList.remove("visible"); box.classList.remove("has-file"); label.textContent = "Choose Room Photo"; });
        const budgetRange = document.getElementById("budgetRange");
        const estimatedCost = document.getElementById("estimatedCost");
        function syncBudgetValue() {
            const parts = budgetRange.value.split("-").map(Number);
            estimatedCost.value = parts[1] || parts[0] || 300000;
        }
        budgetRange.addEventListener("change", syncBudgetValue);
        syncBudgetValue();
        form.addEventListener("submit", function (event) { if (!input.files.length) { event.preventDefault(); alert("Please choose a room photo first."); return; } syncBudgetValue(); button.disabled = true; button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing your room…'; progress.classList.add("visible"); });
    });
