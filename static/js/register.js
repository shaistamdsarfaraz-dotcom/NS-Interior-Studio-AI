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

    function handleRegister() {
    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const pass = document.getElementById('reg-pass').value.trim();

    if (!name || !email || !pass) {
        alert("Please fill in all fields.");
        return false;
    }

    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            username: name,
            email: email,
            password: pass
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Registration successful! Please login.");
            window.location.href = '/login';
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Something went wrong. Please try again.");
    });

    return false; // stop normal form submission
}
