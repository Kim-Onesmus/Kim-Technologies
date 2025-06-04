// Initialize AOS (Animate On Scroll)
AOS.init({
  duration: 1000,
  once: true,
  offset: 100,
});

// Counter Animation
function animateCounter(element) {
  const target = parseInt(element.textContent);
  const duration = 2000; // 2 seconds
  const step = target / (duration / 16); // 60fps
  let current = 0;

  const timer = setInterval(() => {
    current += step;
    if (current >= target) {
      element.textContent = target + "+";
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current) + "+";
    }
  }, 16);
}

// Intersection Observer for Counter Animation
const counterObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const counter = entry.target;
        animateCounter(counter);
        counterObserver.unobserve(counter);
      }
    });
  },
  { threshold: 0.5 }
);

// Initialize Counter Animation
document.querySelectorAll(".counter").forEach((counter) => {
  counterObserver.observe(counter);
});

// Smooth Scrolling for Navigation Links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  });
});

// Navbar Background Change on Scroll
window.addEventListener("scroll", function () {
  const navbar = document.querySelector(".navbar");
  if (window.scrollY > 50) {
    navbar.classList.add("bg-white");
    navbar.classList.remove("bg-light");
  } else {
    navbar.classList.add("bg-light");
    navbar.classList.remove("bg-white");
  }
});

// Form Submission Handler
const contactForm = document.getElementById("contactForm");
if (contactForm) {
  contactForm.addEventListener("submit", function (e) {
    e.preventDefault();
    // Add your form submission logic here
    alert("Thank you for your message! We will get back to you soon.");
    this.reset();
  });
}

// Newsletter Form Handler
const newsletterForm = document.querySelector(".newsletter-form");
if (newsletterForm) {
  newsletterForm.addEventListener("submit", function (e) {
    e.preventDefault();
    // Add your newsletter subscription logic here
    alert("Thank you for subscribing to our newsletter!");
    this.reset();
  });
}

// Image Lazy Loading
document.addEventListener("DOMContentLoaded", function () {
  const lazyImages = document.querySelectorAll("img[data-src]");

  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute("data-src");
        observer.unobserve(img);
      }
    });
  });

  lazyImages.forEach((img) => imageObserver.observe(img));
});

// Mobile Menu Toggle
const navbarToggler = document.querySelector(".navbar-toggler");
const navbarCollapse = document.querySelector(".navbar-collapse");

if (navbarToggler && navbarCollapse) {
  navbarToggler.addEventListener("click", function () {
    navbarCollapse.classList.toggle("show");
  });

  // Close mobile menu when clicking outside
  document.addEventListener("click", function (e) {
    if (
      !navbarToggler.contains(e.target) &&
      !navbarCollapse.contains(e.target)
    ) {
      navbarCollapse.classList.remove("show");
    }
  });
}

// Add active class to current navigation item
function setActiveNavItem() {
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll(".nav-link");

  window.addEventListener("scroll", () => {
    let current = "";
    sections.forEach((section) => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.clientHeight;
      if (window.scrollY >= sectionTop - 200) {
        current = section.getAttribute("id");
      }
    });

    navLinks.forEach((link) => {
      link.classList.remove("active");
      if (link.getAttribute("href").slice(1) === current) {
        link.classList.add("active");
      }
    });
  });
}

// Initialize active navigation
setActiveNavItem();

// Add loading animation
window.addEventListener("load", function () {
  document.body.classList.add("loaded");
});

// Back to Top Button
const backToTopButton = document.getElementById("backToTop");

window.addEventListener("scroll", () => {
  if (window.pageYOffset > 100) {
    backToTopButton.classList.add("show");
  } else {
    backToTopButton.classList.remove("show");
  }
});

backToTopButton.addEventListener("click", () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
});


// Loading Overlay
window.addEventListener("load", () => {
  const loadingOverlay = document.querySelector(".loading-overlay");
  loadingOverlay.classList.add("fade-out");
  setTimeout(() => {
    loadingOverlay.style.display = "none";
  }, 500);
});
