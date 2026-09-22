function toggleChatbot() {
    document.getElementById('chatbotWindow').classList.toggle('open');
}

const botReplies = [
    { keywords: ["upload", "photo", "picture", "image"], reply: "Just click 'Get Started' on the homepage, log in, and you'll be taken to the Studio page where you can upload a photo of your room." },
    { keywords: ["colour", "color", "wall"], reply: "Once you upload a room photo, our AI detects the existing wall colour and suggests new colour options based on colour theory." },
    { keywords: ["cost", "price", "budget", "estimate"], reply: "We calculate an approximate renovation cost based on the furniture and paint suggested for your room." },
    { keywords: ["shopping", "buy", "list"], reply: "After your design suggestions are ready, we generate a shopping list with links to where you can buy the recommended items." },
    { keywords: ["login", "sign up", "register", "account"], reply: "You can create an account or log in using the 'Login' / 'Sign Up' buttons in the top right corner of the homepage." },
    { keywords: ["design ideas", "inspiration", "gallery"], reply: "Check out our 'Design Ideas' page for style inspiration across Living Room, Bedroom, Kitchen, and Bathroom!" },
    { keywords: ["contact", "email", "phone", "reach"], reply: "You can reach us through the Contact page — we usually reply within 24 hours." },
    { keywords: ["about", "team", "who"], reply: "NS Design AI was built by Shaista Mohammadi and Nida Fathima as an AI-powered interior design assistant project." },
    { keywords: ["hi", "hello", "hey"], reply: "Hello! 😊 How can I help you plan your dream room today?" },
    { keywords: ["thank", "thanks"], reply: "You're welcome! Happy designing! 🏡" }
];

function getBotReply(userText) {
    const text = userText.toLowerCase();
    for (const entry of botReplies) {
        if (entry.keywords.some(word => text.includes(word))) {
            return entry.reply;
        }
    }
    return "I'm not sure about that one, but you can explore the Design Ideas or Contact page for more help!";
}

function sendChatMessage() {
    const input = document.getElementById('chatbotInput');
    const text = input.value.trim();
    if (!text) return;

    const messages = document.getElementById('chatbotMessages');

    messages.innerHTML += `<div class="user-msg">${text}</div>`;
    input.value = '';

    setTimeout(() => {
        const reply = getBotReply(text);
        messages.innerHTML += `<div class="bot-msg">${reply}</div>`;
        messages.scrollTop = messages.scrollHeight;
    }, 500);

    messages.scrollTop = messages.scrollHeight;
}