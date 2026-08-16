function togglePassword(fieldId, icon) {
    const field = document.getElementById(fieldId);
    if (field.type === "password") {
        field.type = "text";
        icon.classList.remove("fa-lock");
        icon.classList.add("fa-lock-open");
    } else {
        field.type = "password";
        icon.classList.remove("fa-lock-open");
        icon.classList.add("fa-lock");
    }
}

function handleLogin() {
    const email = document.getElementById('login-email').value.trim();
    const pass = document.getElementById('login-pass').value.trim();

    if (!email || !pass) {
        alert("Please fill in both fields.");
        return false;
    }

    // TODO: replace with real fetch() call to Flask backend once DB is ready
    window.location.href = '/studio';
    return false;
}