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
            const confirm = document.getElementById('reg-confirm').value.trim();

            if (!name || !email || !pass || !confirm) {
                alert("Please fill in all fields.");
                return false;
            }
            if (pass !== confirm) {
                alert("Passwords do not match.");
                return false;
            }

            // TODO: send data to Flask backend via fetch() once DB is ready
            window.location.href = '/studio';
            return false;
        }