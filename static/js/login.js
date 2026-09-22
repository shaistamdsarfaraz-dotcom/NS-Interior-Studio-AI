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

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            email: email,
            password: pass
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Login successful!");
            window.location.href = '/studio'; // Redirects to Studio (upload) page after login
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Something went wrong. Please try again.");
    });

    return false; // Prevents traditional page refresh
}
// Modal Toggle Functions
function openResetModal() {
    document.getElementById('reset-modal').style.display = 'flex';
}

function closeResetModal() {
    document.getElementById('reset-modal').style.display = 'none';
}

// Password Reset Request
function handleResetPassword() {
    const email = document.getElementById('reset-email').value.trim();
    const newPass = document.getElementById('reset-pass').value.trim();

    if (!email || !newPass) {
        alert("Please fill in all fields.");
        return false;
    }

    fetch('/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            email: email,
            new_password: newPass
        })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.success) {
            closeResetModal();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Could not reset password. Please try again.");
    });

    return false;
}