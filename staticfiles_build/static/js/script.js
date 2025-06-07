// Mobile Menu Toggle
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const mobileMenu = document.getElementById("mobileMenu");

mobileMenuBtn.addEventListener("click", () => {
  mobileMenu.classList.toggle("hidden");
});

// Dark Mode Toggle
const darkModeToggle = document.getElementById("darkModeToggle");
const html = document.documentElement;

darkModeToggle.addEventListener("click", () => {
  html.classList.toggle("dark");
  localStorage.setItem("darkMode", html.classList.contains("dark"));
});

// Check for saved dark mode preference
if (localStorage.getItem("darkMode") === "true") {
  html.classList.add("dark");
}

// Stats Counter Animation
const counters = document.querySelectorAll(".counter");
const speed = 200;

const animateCounter = (counter) => {
  const target = parseInt(counter.getAttribute("data-target"));
  let count = 0;
  const increment = target / speed;

  const updateCount = () => {
    if (count < target) {
      count += increment;
      counter.innerText = Math.ceil(count);
      setTimeout(updateCount, 1);
    } else {
      counter.innerText = target;
    }
  };

  updateCount();
};

// Scroll Animation Handler
const handleScrollAnimation = () => {
  const elements = document.querySelectorAll(
    ".animate-fade-up, .animate-fade-in"
  );
  const windowHeight = window.innerHeight;
  const triggerBottom = windowHeight * 0.8;

  elements.forEach((element) => {
    const elementTop = element.getBoundingClientRect().top;

    if (elementTop < triggerBottom) {
      element.classList.add("active");
    } else {
      element.classList.remove("active");
    }
  });
};

// Initial check for elements in view
handleScrollAnimation();

// Add scroll event listener
window.addEventListener("scroll", handleScrollAnimation);

// Stats counter observer
const counterObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  },
  {
    threshold: 0.5,
  }
);

// Observe counters
counters.forEach((counter) => {
  counterObserver.observe(counter);
});

// Back to Top Button
const backToTopBtn = document.getElementById("backToTop");

window.addEventListener("scroll", () => {
  if (window.pageYOffset > 300) {
    backToTopBtn.classList.remove("hidden");
  } else {
    backToTopBtn.classList.add("hidden");
  }
});

backToTopBtn.addEventListener("click", () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
});


// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
      });
      // Close mobile menu if open
      mobileMenu.classList.add("hidden");
    }
  });
});

// Testimonial Modal Functionality
const testimonialModal = document.getElementById("testimonialModal");
const addTestimonialBtn = document.getElementById("addTestimonialBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const cancelTestimonialBtn = document.getElementById("cancelTestimonialBtn");
const testimonialForm = document.getElementById("testimonialForm");
const starRatingButtons = document.querySelectorAll(".star-rating");

let selectedRating = 0;

// Open modal
addTestimonialBtn.addEventListener("click", () => {
  testimonialModal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
  document.body.style.position = "fixed";
  document.body.style.width = "100%";
});

// Close modal functions
function closeModal() {
  testimonialModal.classList.add("hidden");
  document.body.style.overflow = "";
  document.body.style.position = "";
  document.body.style.width = "";
  testimonialForm.reset();
  selectedRating = 0;
  updateStarRating();
}

closeModalBtn.addEventListener("click", closeModal);
cancelTestimonialBtn.addEventListener("click", closeModal);

// Close modal when clicking outside
testimonialModal.addEventListener("click", (e) => {
  if (e.target === testimonialModal) {
    closeModal();
  }
});

// Prevent modal from closing when clicking inside the modal content
testimonialModal.querySelector(".relative").addEventListener("click", (e) => {
  e.stopPropagation();
});

// Update star rating display
function updateStarRating() {
  starRatingButtons.forEach((star, index) => {
    if (index < selectedRating) {
      star.classList.add("text-yellow-400");
      star.classList.remove("text-gray-300");
    } else {
      star.classList.remove("text-yellow-400");
      star.classList.add("text-gray-300");
    }
  });
}

starRatingButtons.forEach((star) => {
  star.addEventListener("click", () => {
    selectedRating = parseInt(star.dataset.rating);
    updateStarRating();
  });

  star.addEventListener("mouseover", () => {
    const rating = parseInt(star.dataset.rating);
    starRatingButtons.forEach((s, index) => {
      if (index < rating) {
        s.classList.add("text-yellow-400");
        s.classList.remove("text-gray-300");
      }
    });
  });

  star.addEventListener("mouseout", () => {
    updateStarRating();
  });
});
