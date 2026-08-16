    const bios = {
        shaista: {
            name: "Shaista Mohammadi",
            text: "Co-founder and developer of NS Design AI, Shaista led the technical build of the platform — from the Flask backend to the AI-based colour detection and room analysis features. Passionate about combining practical design thinking with technology to make interior planning accessible to everyone.",
        },
        nida: {
            name: "Nida Fathima",
            text: "Co-founder of NS Design AI, Nida worked on shaping the design direction and user experience of the platform, ensuring the tool stays simple, intuitive, and genuinely useful for anyone planning a room makeover.",
        }
    };

    function openBio(person) {
        document.getElementById('bio-name').innerText = bios[person].name;
        document.getElementById('bio-text').innerText = bios[person].text;
        document.getElementById('bio-instagram').href = bios[person].instagram;
        document.getElementById('bio-modal').classList.add('active');
    }

    function closeBio() {
        document.getElementById('bio-modal').classList.remove('active');
    }