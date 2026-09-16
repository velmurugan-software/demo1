```javascript
/* =========================================================
   CROP YIELD AI - ABOUT PAGE JAVASCRIPT
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    /* =========================
       MOBILE MENU
       ========================= */

    const menuButton = document.querySelector(".menu-btn");
    const navLinks = document.querySelector(".nav-links");

    if (menuButton && navLinks) {

        menuButton.addEventListener("click", function () {
            navLinks.classList.toggle("open");

            if (navLinks.classList.contains("open")) {
                menuButton.innerHTML = "✕";
            } else {
                menuButton.innerHTML = "☰";
            }
        });

        /* Close menu after clicking a link */

        const links = navLinks.querySelectorAll("a");

        links.forEach(function (link) {
            link.addEventListener("click", function () {
                navLinks.classList.remove("open");
                menuButton.innerHTML = "☰";
            });
        });
    }


    /* =========================
       SCROLL REVEAL ANIMATION
       ========================= */

    const revealElements = document.querySelectorAll(".reveal");

    const revealOnScroll = function () {

        const windowHeight = window.innerHeight;

        revealElements.forEach(function (element) {

            const elementTop = element.getBoundingClientRect().top;

            if (elementTop < windowHeight - 80) {
                element.classList.add("show");
            }

        });
    };

    window.addEventListener("scroll", revealOnScroll);

    revealOnScroll();


    /* =========================
       ACTIVE NAVBAR LINK
       ========================= */

    const currentPage = window.location.pathname;

    const navItems = document.querySelectorAll(".nav-links a");

    navItems.forEach(function (link) {

        const href = link.getAttribute("href");

        if (href && href.includes("/about")) {
            link.classList.add("active");
        }

    });


    /* =========================
       SMOOTH INTERNAL LINKS
       ========================= */

    document.querySelectorAll('a[href^="#"]').forEach(function (link) {

        link.addEventListener("click", function (event) {

            const targetId = this.getAttribute("href");

            if (targetId === "#") {
                return;
            }

            const target = document.querySelector(targetId);

            if (target) {

                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }

        });

    });


    /* =========================
       ROADMAP CARD ANIMATION
       ========================= */

    const roadmapCards = document.querySelectorAll(".roadmap-card");

    roadmapCards.forEach(function (card, index) {

        card.style.transitionDelay = (index * 0.05) + "s";

    });


    /* =========================
       CURRENT YEAR
       ========================= */

    const yearElement = document.getElementById("currentYear");

    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

});
```
