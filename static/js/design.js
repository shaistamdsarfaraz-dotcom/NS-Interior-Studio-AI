// Function to update card images when room filter chips are clicked
function filterByRoom(chipElement) {
    // 1. Remove 'active' class from all chips and set active on clicked chip
    document.querySelectorAll('.filter-chip').forEach(chip => chip.classList.remove('active'));
    chipElement.classList.add('active');

    // 2. Get the room category key (e.g., 'all', 'living-room', 'bedroom', etc.)
    const filterKey = chipElement.getAttribute('data-filter');

    // 3. Update the image for every style card
    const styleCards = document.querySelectorAll('.style-card');

    styleCards.forEach(card => {
        const newImgUrl = card.getAttribute(`data-${filterKey}`);
        const cardImg = card.querySelector('img.card-img') || card.querySelector('img');

        if (newImgUrl && cardImg) {
            cardImg.style.opacity = '0.3';
            setTimeout(() => {
                cardImg.src = newImgUrl;
                cardImg.style.opacity = '1';
            }, 150);
        }
    });
}

function populateModalGallery(title, roomFilter) {
    const gallery = document.getElementById('styleModalGallery');
    let favorites = JSON.parse(localStorage.getItem('favorites')) || [];

    let images = null;
    if (styleGalleries[roomFilter] && styleGalleries[roomFilter][title]) {
        images = styleGalleries[roomFilter][title];
    }

    if (!images) {
        const activeCard = [...document.querySelectorAll('.style-card')]
            .find(c => c.dataset.title === title);
        const fallbackImg = activeCard
            ? (activeCard.getAttribute(`data-${roomFilter}`) || activeCard.getAttribute('data-all') || activeCard.querySelector('img').src)
            : '';
        images = fallbackImg ? [fallbackImg] : [];
    }

    gallery.innerHTML = images.map(url => {
        if (!url) return '';
        const isFav = favorites.some(f => f.image === url);
        return `
            <div class="gallery-item">
                <img src="${url}" alt="${title}">
                <i class="fa-${isFav ? 'solid' : 'regular'} fa-heart gallery-heart-icon ${isFav ? 'active' : ''}"
                   onclick="toggleGalleryFavorite(this, '${title}', '${url}')"></i>
            </div>
        `;
    }).join('');
}

function toggleGalleryFavorite(icon, title, imageUrl) {
    let favorites = JSON.parse(localStorage.getItem('favorites')) || [];
    const exists = favorites.some(f => f.image === imageUrl);

    if (exists) {
        favorites = favorites.filter(f => f.image !== imageUrl);
        icon.classList.remove('active', 'fa-solid');
        icon.classList.add('fa-regular');
    } else {
        favorites.push({ title, image: imageUrl });
        icon.classList.add('active', 'fa-solid');
        icon.classList.remove('fa-regular');
    }

    localStorage.setItem('favorites', JSON.stringify(favorites));
    updateFavCount();
}

// Function to handle style card modal opening


function closeStyleModal() {
    document.getElementById('styleModal').classList.remove('show');
}

// Attach event listeners after DOM content loads
document.addEventListener('DOMContentLoaded', () => {
    // Enable opening style modals when clicking style cards
    const styleCards = document.querySelectorAll('.style-card');
    styleCards.forEach(card => {
        card.addEventListener('click', (e) => {
            // Prevent opening modal if user clicked the heart favorite icon
            if (!e.target.classList.contains('heart-icon')) {
                openStyleModal(card);
            }
        });
    });
});
let currentRoom = 'all'; // Default to show all room styles

const slides = document.querySelectorAll('.slideshow .slide');
let currentSlide = 0;

if (slides.length > 0) {
    setInterval(() => {
        slides[currentSlide].classList.remove('active');
        currentSlide = (currentSlide + 1) % slides.length;
        slides[currentSlide].classList.add('active');
    }, 1500);
}
// Room and Style Image Database
const styleGalleries = {
    "living-room": {
        "Modern": [
            "https://i.pinimg.com/736x/22/60/d7/2260d772551c63fc67c8eecf6aaac0c9.jpg",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=600&q=80",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRRGn9Jdhk6cEnAGhKuHkQGD-U0mevCPe8qtNkaB-zgvR7r1ibl2FqaZB0&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRfIy9lDVj9Q6UGvX65EucXW7X1obGxj4hbRz-CP22IEehqOGWXNQrXnntu&s=10",
            "https://interiorplus.asia/wp-content/uploads/2023/11/Modern-vs.-Contemporary-Interior-Design-Key-Differences.jpg",
            "https://i.pinimg.com/736x/f7/7e/ed/f77eedcad25dd4b503da4231fb9e9cb7.jpg",
            "https://i.pinimg.com/736x/84/bd/69/84bd69b611b38e585e3e05980d405aa8.jpg",
            "https://i.pinimg.com/736x/fb/a4/f8/fba4f8ceac7c8fb75876aea6b1c704da.jpg"
        ],
        "Minimalist": [
            "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=600&q=80",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQzO7WnjosENUDbMOthLdLaJzfN5LnUtwzCm4pXzkRd2A&s=10",
            "https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=600&q=80",
            "https://i.pinimg.com/736x/b9/2d/77/b92d77f589d4165c04c2358a67467f91.jpg",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRu_2osFEUodNvT-dbv030F41kAfh7JWB4YapH0Yi1ZpmOvw6u1k3z-Fzw&s=10",
            "https://i.pinimg.com/1200x/de/8e/01/de8e012e9b1fd2de3675990307fd0ea3.jpg",
            "https://i.pinimg.com/736x/cf/e0/f8/cfe0f8a842c8750652722c2cb936f634.jpg"
        ],
        "Scandinavian": [
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSFf5ps3IWuYIJFpCJ2QeIGSd5sQoQJJgK45r0FM4jPHe-zG9a482Yahgdj&s=10",
            "https://assets.vogue.com/photos/675acd5e1e16d14435474635/1:1/w_5357,h_5357,c_limit/GettyImages-1436398636.jpg",
            "https://thearchitectsdiary.com/wp-content/uploads/2023/07/Studio-Tilt-25-1024x683.webp",
            "https://i.pinimg.com/736x/af/de/94/afde94388ac162e300b3dbd9db16c160.jpg",
            "https://i.pinimg.com/736x/7f/be/c2/7fbec224e749d57868f7216dc88d5343.jpg",
            "https://i.pinimg.com/736x/72/ed/57/72ed5783528d540ecb6c5329c05d4549.jpg",
            "https://i.pinimg.com/736x/ad/e0/4b/ade04b15d0a3f8ecdf3a87c8234859ff.jpg",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGOBlQCcCeZpLo9VrOQB0Oy-xV0zvM3fVRKms_yFE8WGuXsRu0LWv7WWOV&s=10"
        ],
        "Luxury": [
            "https://i.pinimg.com/736x/38/7e/0a/387e0a67275ac1cb32a77f8e502bdd01.jpg",
            "https://i.pinimg.com/736x/e1/78/1f/e1781fd706ea7a6bd1ddf7a0d0a6b873.jpg",
            "https://i.pinimg.com/736x/f1/5d/7c/f15d7c202c0198704c5a129bdfed7294.jpg",
            "https://www.greenply.com:5001/originalfile1769165379328-6117.jpg",
            "https://antonovich-design.com/uploads/page/2018/11/thumb20187p8RQeR1eQLs.jpg",
            "https://i.pinimg.com/1200x/85/95/cf/8595cfb145c0ad3d82c42e921c0d538f.jpg",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSEaiU7WdbIJ-Gq8BKbAVvYFjMwKGzxYGy3PB96WnCM7oUfpm8hRglbIg0H&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSao8dPEYDbUsWF4w_q9PsOy8EIeg06LDn-CvP0if1QZIKaS-0gDLhFzrZC&s=10"
        ]
    },
    "bedroom": {
        "Modern": [
            "https://i.pinimg.com/736x/2d/d2/0f/2dd20f91923379485dd04dbaf00f6451.jpg",
            "https://i.pinimg.com/736x/fe/bb/40/febb4002e29bd7b7f73bbde302f2fef8.jpg",
            "https://i.pinimg.com/736x/c8/50/27/c8502753fd2209b0323833d1c7968fe1.jpg",
            "https://i.pinimg.com/736x/25/8b/85/258b85914e8fdac22db6dab8ddcce112.jpg",
            "https://www.designatak.com/getattachment/Navrh-privatnich-interieru/Navrhy-loznic/Design-moderni-tmave-loznice-s-mramorovou-stenou/Design-moderni-tmave-loznice-s-mramorovou-stenou01.jpg.aspx",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQLOadOhetcDXrZPJCyY4TazjMY9GIy30f50oCWwrtRwG8UHdYaj94SbsA&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQlWpA2T4iK1tbMueToQqAevvwJERVeM1GAQYq6JJnjfcZv5rJJAPcaepM&s=10",
            ""
        ],
        "Minimalist": [
            "https://i.pinimg.com/1200x/a6/d0/c8/a6d0c83edde86226b8397578eeae3c19.jpg",
            "https://i.pinimg.com/736x/4d/8c/5a/4d8c5a7254bb16b1b83aea927f1f8096.jpg",
            "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=600&q=80",
            "https://i.pinimg.com/736x/27/62/a3/2762a3f3e1472a07620ed4234155255f.jpg",
            "https://assets.architecturaldigest.in/photos/63dcd0d043759bc4edc842c1/3:2/w_1620,h_1080,c_limit/11%20minimalist%20bedroom%20design%20tricks%20to%20create%20a%20calming%20space.jpg",
            "https://i.pinimg.com/originals/2c/a1/e1/2ca1e14b7f4f816ce974b67be8773469.jpg",
            "https://images.surferseo.art/4bd5863e-a7c2-4cbc-90c3-8efe5f0c72fd.jpeg",
            "https://d28pk2nlhhgcne.cloudfront.net/assets/app/uploads/sites/3/2021/11/minimalist-room-cover-1-1-720x533.png"
        ],
        "Scandinavian": [
            "https://i.pinimg.com/1200x/49/40/45/4940455296d966321a3b67834966086e.jpg",
            "https://i.pinimg.com/1200x/6c/d4/e6/6cd4e6cbe5df54756920c74271a0ac40.jpg",
            "https://i.pinimg.com/736x/c7/7a/a7/c77aa77722c8723dc56f607e60aa0634.jpg",
            "https://i.pinimg.com/736x/8a/ab/3f/8aab3fa7b3cb4adb442e52699ef9237e.jpg",
            "https://i.pinimg.com/736x/4f/4e/a5/4f4ea5efa4e3e47a4e93884511f6da15.jpg",
            "https://i.pinimg.com/1200x/3d/b4/9a/3db49a86ccb76bf7c794d7d84cfd4c6c.jpg",
            "https://images.livspace-cdn.com/w:3840/plain/https://d3gq2merok8n5r.cloudfront.net/abhinav/ond-1634120396-Obfdc/jas-2026-1785330024-pzKMk/kbr-1785331489-GdYBd/04-1785331513-4Yrho.jpg",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQHF81Lw7P2nAbGIIfvsJJBkL7coPluQMcjQ6JCpPHzlrIT5vhFe65eR5o&s=10"
        ],
        "Luxury": [
            "https://i.pinimg.com/736x/63/f3/05/63f305555bb46367b3bdb5b15ed10b28.jpg",
            "https://i.pinimg.com/736x/f8/a1/e2/f8a1e24f2386f92942d89512c2c0980e.jpg",
            "https://i.pinimg.com/736x/32/0e/09/320e094a9bd5feb76c50ecfa4d4f100f.jpg",
            "https://5.imimg.com/data5/SELLER/Default/2024/9/451168135/ZU/GK/NQ/91179016/luxury-bedroom-interior-design.jpeg",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRLDN-YoYFuMPhaUnopN36NE5iQ0TIbamooAZ_sTxtCZK2eGlaRXDNtS70&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQSK7sKupSsayZzAEtCGZ1HsohxFc7bsQtlxbC7GKHF3vaPYYiXMF05K22Q&s=10",
            "https://i.pinimg.com/736x/2d/cb/db/2dcbdb2bf0dd648940baa155762116c8.jpg",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQR2W-zAQcrfn3NvqB3VGsm2_qeiHjwBbHCteh0hLOetlkA5TFjKBvE5DIT&s=10"
        ]
    },
    "kitchen": {
        "Modern": [
            "https://www.thespruce.com/thmb/BnQpJN5DuH4OVRdi8Pmmrak257c=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/SPR-modern-kitchen-ideas-7110474-hero-e78cb87316b847fb87fe807ffd4a0921.jpg",
            "https://www.homworks.com/wp-content/uploads/2023/05/06_Lighting-and-Ventilation.jpg",
            "https://images.stockcake.com/public/f/0/a/f0a9652d-f99c-4f80-b758-c912017f5158_large/modern-kitchen-interior-stockcake.jpg",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT3kCckemvpNs68csK4JCvUv87iGmiry_PBXnMsAZg7k9nqqXx1xS2JGxtk&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQVuoNFg40pRDiG-NNqRW_m5VtCsvSVeBjtKNQIOhUYtqPMuhxvRlBu8AEK&s=10",
            "https://cdn.mos.cms.futurecdn.net/u6ZENaxzUiJu4ttGVWJPBF.jpg",
            "https://www.wedezinestudio.com/blogs/wp-content/uploads/2025/09/485729500_980619370850286_7961696058709108110_n-1.webp",
            "https://www.asenseinterior.com/assets/mediafile/luxury_modern_kitchen_designs.webp"
        ],
        "Minimalist": [
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRGX1pcLWYr8WTpXbbYt0703iLefDcYi4TrEAOKCvWd0w&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS7pBhp0FVC83l7FRmfr1yAfdmV7TOWLysNqyjTUWvzcw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQLCgdjO9GF3JxYqocNrYz-fJ3GFynuQS5-ALarTZD9DA&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSo6ChuS4NqOBqLjpCDfB7DqRUF8Y6ma_8_Qfn0chWxjw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRqYy6D1aPZ-8MD5JLAkERXWSb45HPIZY-EwaAKiPYCw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSFGoM8bZWOFjp1aFO5hRVjupMIIy5tT7DbtvXYYPQWqA&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-2PsM3FmJ7ysxP0fVi2NfMCv2KdoUBEFxEesYWkZCYQ&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSsO9BjzsV1qKhb-Hf0O1QC5Ai0hnWmPyUkgqeOFyu2AA&s=10"
        ],
        "Scandinavian": [
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSK-AOvA3ehs-Wol8N8YJGYQdaklQM4Tx--E55Q2EI7Pw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSZm1eqV5hx1vzjK-tkokiDBO0u3kOsiOX3n9XxiLRViQ&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRm0vKzLKM24l-x-uUVurcQ28QXImgUqBEEVQ0JdM-wvA&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRjXVgQ8L6vTZ9OE-KG9snROZqP7UL6UxABdEkEOm33Qg&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRwiOJNzkvc-pWKtt3PtBlBDZeaJXDYm1xL9YWOfLoJ8Q&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQSr5umPaqzPLDtI19urJh8GQftJkfLozbEmmBsvjtSJg&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTYnwsXU2PTjjtqafScxJlKI6FRg-vbYDFcCNTDKvgn2w&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ23y4_MdBIW7cvlHwkvvYCHJIvhW-nkHwWcpCtmIcfzQ&s=10"
        ],
        "Luxury": [
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQAOMPIxADS3s2BUKsz2tXPX11uPMEVy4hpT_kItmrxgQ&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQst7Uuut5fQFuGUlz7ojC8fMpvuuTDBTaYBqLSk6dSIg&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR2pwAJVvmnQTfn0OQ4pgnESM7N5vTDcrzP5d7b60yKLw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSXuWWLDfWBYCyLdpU4qmqPMvAm6zs_CY_uMSp79rtyog&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTEhh3ZyMu1-Kiqz3HoL5vDb07wb113NvBNxz2MaTJAyQ&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQdFdGw7OLOnA8T66bIkqYTCQWpSN-GDFT_hMpEFrKv7Q&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT8C2wW827ubPirYBMEDTJ0_t1JKAcuE2TpXdAqrFWTElL-z-m1K-6A0Tc&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTvdGgAMlqz_9_af48Ey645j6sx8BFj6gVTR3DpAI58Cw&s=10"
        ]
    },
    "bathroom": {
        "Modern": [
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRStIngOUi5KBAho8zNs9hAnj5eRCFFQEpMhOSfB39pRw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQFDcYai84rUOc1WGppv5IC4h61G9WlIpqleFEr1RISLw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQyr2Jd-heKnBsCo4koQ1d85ot1eH5sWR5OhkUPfsBLLw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRX5eUx55jiN7FNzDb9PvVIUcesqRqMFKaAPs_lBt9q4w&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSSmtDOaJAOHrSVNAIqNo1Fqn8n2B1BKoBQ82-lmrNpuw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTGzYyVB3sTgocTlx3saUTE9o-lh0hJhj8OfbREXYzdbg&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ8lzSbf_29MtPgpmA_3RCPYjqXrI8BLaOsFeVj32Vu4g&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQSopgSY0TX0EdL1HLO2OloLlAPUt1Yf8bAdsepAs3O3w&s=10"
        ],
        "Minimalist": [
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTHfieYGtgt_HXvlFQKv56pYtndOSVaA68jm3rgFmr-3Q&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQavrQ5CYCkMmyEmEbKjmZxeX2YMCE9vpnF5s-YzvxQPevWBXtcq2cFGfA&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTAqB0_u0rnKIdyHzTYzMcayCGBXnrewiDKtf3911mDpg&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcThVR67Du93cXM87xRbihjN4LzYM28Ziq3vjnTNlp2ZeQ&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSDNrMDf5nZrWqJhgRZdDOJExahU40ktLDZYKDqqom65g&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTHaQG6yIpcizuehhyWWUgPnTb593VgY5JTQv6rXvOUwQ&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTRcaVto6GrYTwfPn93Yn0iuhDRgTsG9jr2rBvTN10-dA&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTjTD3t7nK5eXUvJuNtlj-1RJ-qIzyRn1y4a6uiJn7Ltg&s=10"
        ],
        "Scandinavian": [
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTllSL5yUz7GvYcLbzf7-TVAfpPDnuWOkqTzNJAfy5DnA&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQkRa3gHcCBiT9-oSWGhn7EH4Wedn8TqfMw64_lO5IC8A&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTMpGsXFQUaSoFivj0FhDQpfJiaRPWI3BZE_F1YO4vpyg&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTqIsFmXjvSUdef_sHi8KPftvOEX5nvUdV9Naj2rP3suQ&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQuMM2RTcTIrYBUbpFyFauvUdRtmjxKw-5QCksCfdIp3w&s=10",
            "https://i0.wp.com/newbury-home.com/wp-content/uploads/2024/12/cozy-cabin-bathroom.jpg?resize=768%2C1024&ssl=1",
            "https://images.ctfassets.net/j4m9q0fykyy4/5HoUso2Yo2457Aar59hJVo/2301768400588a9f66c2cdaa5fac5b74/25fceaae8e81.jpg",
            "https://t3.ftcdn.net/jpg/04/32/80/14/360_F_432801489_y1RfOKO5wmrsDlNeNS5LsaLOVHSF3wtr.jpg"
        ],
        "Luxury": [
            "https://i.pinimg.com/1200x/e8/1b/b4/e81bb41cd554f502af92103aacca4677.jpg",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS68CY5QlG1z2OV06WLrZiaB5ebetaMiYXFt6FlJhqdmw&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRNQCCe7Lo3VBrfaa2aUMy_fhS8wezH-GTrxPiJh_IwsQ&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTUyrw4W9Ukp5ywEh0NQdKRMCvjHJNRu3dQkjshHS9zwA&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9WktiuTGP9lTXbEuEhqNJEdB49UKtmYe0qLaR1U9-lA&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRr0fUUiSnwgueU9aglOXI-fT8yUuw4RBCdioVfW3dWrQ&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSpyu_IE2k4LjiuaCoq9NN9AaiSF6j46b7gCS_e9OkQ-g&s=10",
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRLxIfh_ciQFcGbB2SeCJ0VZ6rDXdZUVjmqHrSOJviv8A&s=10"
        ]
    }
};

document.addEventListener('DOMContentLoaded', () => {
    let favorites = JSON.parse(localStorage.getItem('favorites')) || [];
    updateFavCount();

    // Favorites highlighters
    document.querySelectorAll('.style-card').forEach(card => {
        const title = card.dataset.title;
        const heart = card.querySelector('.heart-icon');
        const imageUrl = card.querySelector('img').src;
        if (favorites.some(f => f.image === imageUrl && f.title === title)) {
            if (heart) heart.classList.add('active');
        }
    });

    // Toggle heart active state
    document.querySelectorAll('.heart-icon').forEach(heart => {
        heart.addEventListener('click', (e) => {
            e.stopPropagation();
            const card = heart.closest('.style-card');
            const title = card.dataset.title;
            const image = card.querySelector('img').src;

            const exists = favorites.some(f => f.title === title);
            if (exists) {
                favorites = favorites.filter(f => f.title !== title);
                heart.classList.remove('active');
            } else {
                favorites.push({ title, image });
                heart.classList.add('active');
            }
            localStorage.setItem('favorites', JSON.stringify(favorites));
            updateFavCount();
        });
    });

    // Handle Card Clicks to Open Modal Gallery
    document.querySelectorAll('.style-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.classList.contains('heart-icon')) return;
            openStyleModal(card);
        });
    });
});


function openStyleModal(card) {
    const title = card.getAttribute('data-title');
    const desc = card.getAttribute('data-desc');
    
    // Get the currently active filter chip's text
    const activeChip = document.querySelector('.filter-chip.active');
    const roomName = activeChip ? activeChip.textContent.trim() : 'All Rooms';
    
    // Update title dynamically (e.g., "Modern" or "Modern — Bedroom")
    const modalTitleEl = document.getElementById('styleModalTitle');
    if (roomName === 'All Rooms') {
        modalTitleEl.textContent = title;
    } else {
        modalTitleEl.textContent = `${title} — ${roomName}`;
    }

    document.getElementById('styleModalDesc').textContent = desc;
    
    // Populate gallery images based on active filter
    const activeFilter = activeChip ? activeChip.getAttribute('data-filter') : 'all';
    populateModalGallery(title, activeFilter);

    document.getElementById('styleModal').classList.add('show');
}

function closeStyleModal() {
    document.getElementById('styleModal').classList.remove('show');
}

function openFavoritesModal() {
    renderFavoritesGrid();
    document.getElementById('favoritesModal').classList.add('show');
}

function closeFavoritesModal() {
    document.getElementById('favoritesModal').classList.remove('show');
}

function removeFavorite(image) {
    let favorites = JSON.parse(localStorage.getItem('favorites')) || [];
    favorites = favorites.filter(f => f.image !== image);
    localStorage.setItem('favorites', JSON.stringify(favorites));

    document.querySelectorAll('.style-card img').forEach(img => {
        if (img.src === image) {
            const heart = img.closest('.style-card').querySelector('.heart-icon');
            if (heart) heart.classList.remove('active');
        }
    });

    document.querySelectorAll('.gallery-item img').forEach(img => {
        if (img.src === image) {
            const heart = img.parentElement.querySelector('.gallery-heart-icon');
            if (heart) { heart.classList.remove('active', 'fa-solid'); heart.classList.add('fa-regular'); }
        }
    });

    renderFavoritesGrid();
    updateFavCount();
}

function renderFavoritesGrid() {
    const favorites = JSON.parse(localStorage.getItem('favorites')) || [];
    const grid = document.getElementById('favoritesGrid');

    if (favorites.length === 0) {
        grid.innerHTML = `
            <div class="favorites-empty">
                <i class="fa-regular fa-heart"></i>
                <p>No favorites yet. Tap the heart on any style to save it here!</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = favorites.map(f => `
    <div class="fav-item">
        <button class="remove-fav" onclick="removeFavorite('${f.image}')">
                <i class="fa-solid fa-xmark"></i>
            </button>
            <img src="${f.image}" alt="${f.title}">
            <div class="fav-title">${f.title}</div>
        </div>
    `).join('');
}

function updateFavCount() {
    const favorites = JSON.parse(localStorage.getItem('favorites')) || [];
    const badge = document.getElementById('favCount');
    if (badge) badge.textContent = favorites.length;
}

// Global Event Listeners for Closing Modals
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        closeStyleModal();
        closeFavoritesModal();
        closePaletteModal();
    }
});


document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeStyleModal();
        closeFavoritesModal();
        closePaletteModal();
    }
});
const allPalettes = [
    { name: "Monochrome", colors: ["#1A1A1A", "#555555", "#999999", "#DDDDDD"] },
    { name: "Blush Pink", colors: ["#B5657A", "#D98BA0", "#EFC1CE", "#FBEAEF"] },
    { name: "Deep Plum", colors: ["#2E1A3D", "#4B3869", "#8A6FA8", "#D6C9E8"] },
    { name: "Sunny Mustard", colors: ["#8A6D1F", "#C79A3C", "#E4C374", "#F5E6BC"] },
    { name: "Charcoal Slate", colors: ["#2B2E33", "#4F5560", "#8C939E", "#DCE0E5"] },
    { name: "Coastal Teal", colors: ["#0F4C4C", "#1E8A8A", "#7FC4C4", "#D6EFEF"] },
    { name: "Dusty Rose", colors: ["#7A4A4A", "#B07575", "#D9A8A8", "#F2DCDC"] },
    { name: "Olive Grove", colors: ["#4A4E23", "#7A7F3E", "#ABAE71", "#DEDFB8"] },
    { name: "Terracotta Sunset", colors: ["#5C2418", "#A44A29", "#D9825B", "#F5CEB8"] },
    { name: "Forest Canopy", colors: ["#1B3B2B", "#386641", "#6A9955", "#C7E5B4"] },
    { name: "Midnight Navy", colors: ["#0B1B3D", "#1D3557", "#457B9D", "#A8DADC"] },
    { name: "Warm Amber", colors: ["#6B3008", "#B85B14", "#E08E45", "#F7D0A3"] },
    { name: "Sage Mist", colors: ["#3D4A3E", "#627563", "#9BB09C", "#E1E8E2"] },
    { name: "Burnt Espresso", colors: ["#2B1704", "#5C3A21", "#9A6B48", "#E6D3C3"] },
    { name: "Oceanic Abyss", colors: ["#081C24", "#124559", "#018E42", "#84C0C6"] },
    { name: "Spiced Cinnamon", colors: ["#4A1208", "#8C2F1D", "#C85A32", "#F2B880"] },
    { name: "Eucalyptus Shadow", colors: ["#2A3A35", "#4B6258", "#839E92", "#D2DDD7"] },
    { name: "Golden Honey", colors: ["#5C3D00", "#9E6B00", "#DDA15E", "#FEFAE0"] }
];

function openPaletteModal() {
    const grid = document.getElementById('allPalettesGrid');
    grid.innerHTML = allPalettes.map(p => `
        <div class="palette-card">
            <div class="palette-name">${p.name}</div>
            <div class="swatch-row">
                ${p.colors.map(c => `<span style="background:${c}"></span>`).join('')}
            </div>
        </div>
    `).join('');

    document.getElementById('paletteModal').classList.add('show');
}

function closePaletteModal() {
    document.getElementById('paletteModal').classList.remove('show');
}
