/* =========================================================
   MOBILE MENU
========================================================= */

const menuButton = document.getElementById("menuButton");
const navMenu = document.getElementById("navMenu");

if (menuButton && navMenu) {

    menuButton.addEventListener("click", function (event) {

        event.stopPropagation();

        navMenu.classList.toggle("show");

    });


    const navLinks = navMenu.querySelectorAll(".nav-link");

    navLinks.forEach(function (link) {

        link.addEventListener("click", function () {

            navMenu.classList.remove("show");

        });

    });

}


/* =========================================================
   ELEMENTS
========================================================= */

const modeSelection =
    document.getElementById("modeSelection");

const normalSection =
    document.getElementById("normalSection");

const aiSection =
    document.getElementById("aiSection");

const predictionSection =
    document.getElementById("prediction");


/* =========================================================
   SHOW NORMAL PREDICTION
========================================================= */

function showNormal() {

    if (!modeSelection || !normalSection) {
        return;
    }

    modeSelection.classList.add("hidden");

    normalSection.classList.remove("hidden");

    if (aiSection) {
        aiSection.classList.add("hidden");
    }

    normalSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


/* =========================================================
   SHOW AI PREDICTION
========================================================= */

function showAI() {

    if (!modeSelection || !aiSection) {
        return;
    }

    modeSelection.classList.add("hidden");

    aiSection.classList.remove("hidden");

    if (normalSection) {
        normalSection.classList.add("hidden");
    }

    aiSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


/* =========================================================
   BACK TO MODES
========================================================= */

function backToModes() {

    if (!modeSelection) {
        return;
    }

    modeSelection.classList.remove("hidden");

    if (normalSection) {
        normalSection.classList.add("hidden");
    }

    if (aiSection) {
        aiSection.classList.add("hidden");
    }

    if (predictionSection) {

        predictionSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }

}


/* =========================================================
   AI FORM LOADING
========================================================= */

const aiForm =
    document.getElementById("aiForm");

const aiButton =
    document.getElementById("aiButton");

if (aiForm && aiButton) {

    aiForm.addEventListener("submit", function () {

        aiButton.disabled = true;

        aiButton.innerHTML = `
            <span>⏳</span>
            Processing AI...
            <span>●</span>
        `;

    });

}


/* =========================================================
   ACTIVE NAVIGATION
========================================================= */

const sections =
    document.querySelectorAll("section[id]");

const links =
    document.querySelectorAll(".nav-link");


function updateActiveNavigation() {

    let current = "";

    sections.forEach(function (section) {

        const sectionTop =
            section.offsetTop - 150;

        if (window.scrollY >= sectionTop) {

            current =
                section.getAttribute("id");

        }

    });


    links.forEach(function (link) {

        link.classList.remove("active");

        const href =
            link.getAttribute("href");

        /*
         * Only activate internal section links.
         *
         * Examples:
         * #home
         * #about
         * #prediction
         *
         * Flask routes such as:
         * /history
         * /analytics
         * /solutions
         * /for-whom
         * /careers
         *
         * are NOT handled here.
         */

        if (
            href &&
            href.startsWith("#") &&
            href === "#" + current
        ) {

            link.classList.add("active");

        }

    });

}


/* Run when page loads */

updateActiveNavigation();


/* Run while scrolling */

window.addEventListener(
    "scroll",
    updateActiveNavigation
);


/* =========================================================
   CLOSE MOBILE MENU WHEN CLICKING OUTSIDE
========================================================= */

document.addEventListener("click", function (event) {

    if (!menuButton || !navMenu) {
        return;
    }

    if (
        !navMenu.contains(event.target) &&
        !menuButton.contains(event.target)
    ) {

        navMenu.classList.remove("show");

    }

});