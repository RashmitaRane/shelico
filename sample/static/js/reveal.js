document.addEventListener("DOMContentLoaded", function () {
    function revealElements() {
        let elements = document.querySelectorAll(".reveal");
        elements.forEach((element) => {
            let windowHeight = window.innerHeight;
            let elementTop = element.getBoundingClientRect().top;
            let revealPoint = 100;

            if (elementTop < windowHeight - revealPoint) {
                element.classList.add("active");
            } else {
                element.classList.remove("active"); // Repeats on scroll up/down
            }
        });
    }

    window.addEventListener("scroll", revealElements);
    revealElements(); // Run once on page load
});
