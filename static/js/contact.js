document.getElementById('contactForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const subject = document.getElementById('subject').value.trim();
    const message = document.getElementById('message').value.trim();
    const status = document.getElementById('formStatus');

    if (!name || !email || !subject || !message) {
        status.textContent = "Please fill in all fields.";
        status.style.color = "red";
        return;
    }

    status.textContent = "Sending message...";
    status.style.color = "#555";

    fetch('/send-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            name: name,
            email: email,
            subject: subject,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            status.textContent = data.message;
            status.style.color = "green";
            document.getElementById('contactForm').reset();
        } else {
            status.textContent = data.message;
            status.style.color = "red";
        }
    })
    .catch(error => {
        console.error('Error:', error);
        status.textContent = "Could not send message. Please try again.";
        status.style.color = "red";
    });
});