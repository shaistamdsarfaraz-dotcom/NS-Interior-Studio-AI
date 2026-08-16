    const navLinks = document.querySelectorAll('#nav-links li');
    const highlight = document.getElementById('nav-highlight');

    navLinks.forEach(link => {
        link.addEventListener('mouseenter', () => {
            const rect = link.getBoundingClientRect();
            const parentRect = link.parentElement.getBoundingClientRect();
            highlight.style.left = (rect.left - parentRect.left) + 'px';
            highlight.style.width = rect.width + 'px';
        });
    });

    