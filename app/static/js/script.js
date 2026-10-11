
document.addEventListener("DOMContentLoaded", function () {
  "use strict";

  // ==========================================
  // 1. MOBILE NAVIGATION
  // ==========================================
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const mobileMenu = document.getElementById("mobileMenu");
  const mobileMenuIcon = document.getElementById("mobileMenuIcon");

  function closeMobileMenu() {
    if (!mobileMenu || !mobileMenuBtn) return;

    mobileMenu.classList.add("hidden");
    mobileMenuBtn.setAttribute("aria-expanded", "false");
    mobileMenuBtn.setAttribute("aria-label", "Open navigation menu");

    if (mobileMenuIcon) {
      mobileMenuIcon.classList.remove("fa-xmark");
      mobileMenuIcon.classList.add("fa-bars");
    }
  }

  function openMobileMenu() {
    if (!mobileMenu || !mobileMenuBtn) return;

    mobileMenu.classList.remove("hidden");
    mobileMenuBtn.setAttribute("aria-expanded", "true");
    mobileMenuBtn.setAttribute("aria-label", "Close navigation menu");

    if (mobileMenuIcon) {
      mobileMenuIcon.classList.remove("fa-bars");
      mobileMenuIcon.classList.add("fa-xmark");
    }
  }

  if (mobileMenuBtn && mobileMenu) {
    // Toggle the mobile menu.
    mobileMenuBtn.addEventListener("click", function () {
      const isOpen =
        mobileMenuBtn.getAttribute("aria-expanded") === "true";

      if (isOpen) {
        closeMobileMenu();
      } else {
        openMobileMenu();
      }
    });

    // Close menu when a mobile navigation link is clicked.
    mobileMenu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeMobileMenu);
    });

    // Close menu when Escape is pressed.
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeMobileMenu();
      }
    });

    // Close mobile menu when switching to desktop width.
    window.addEventListener("resize", function () {
      if (window.innerWidth >= 1024) {
        closeMobileMenu();
      }
    });

    // Close menu when clicking outside it.
    document.addEventListener("click", function (event) {
      if (
        mobileMenuBtn.getAttribute("aria-expanded") === "true" &&
        !mobileMenu.contains(event.target) &&
        !mobileMenuBtn.contains(event.target)
      ) {
        closeMobileMenu();
      }
    });
  }


  // ==========================================
  // 2. NAVBAR SCROLL EFFECT
  // ==========================================
  const mainNavbar = document.getElementById("mainNavbar");

  function updateNavbar() {
    if (!mainNavbar) return;

    if (window.scrollY > 20) {
      mainNavbar.classList.add("shadow-md");
    } else {
      mainNavbar.classList.remove("shadow-md");
    }
  }

  window.addEventListener("scroll", updateNavbar, { passive: true });
  updateNavbar();


  // ==========================================
  // 3. SMOOTH SCROLL FOR INTERNAL LINKS
  // ==========================================
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (event) {
      const href = this.getAttribute("href");

      // Ignore empty hash links.
      if (!href || href === "#") return;

      let target;

      try {
        target = document.querySelector(href);
      } catch (error) {
        return;
      }

      // Allow normal browser behaviour if no target exists.
      if (!target) return;

      event.preventDefault();

      const navbar = document.getElementById("mainNavbar");
      const navbarHeight = navbar ? navbar.offsetHeight : 0;

      const targetPosition =
        target.getBoundingClientRect().top +
        window.scrollY -
        navbarHeight -
        8;

      window.scrollTo({
        top: Math.max(0, targetPosition),
        behavior: "smooth"
      });

      // Close the mobile menu after selecting a section.
      if (mobileMenu && mobileMenu.contains(anchor)) {
        closeMobileMenu();
      }
    });
  });


  // ==========================================
  // 4. SCROLL-REVEAL ANIMATIONS
  // ==========================================
  const animatedElements = document.querySelectorAll(
    ".animate-fade-up, .animate-fade-in"
  );

  function handleScrollAnimation() {
    const triggerBottom = window.innerHeight * 0.85;

    animatedElements.forEach(function (element) {
      const elementTop = element.getBoundingClientRect().top;

      if (elementTop < triggerBottom) {
        element.classList.add("active");
      }
    });
  }

  // Run on initial load.
  handleScrollAnimation();

  // Run as the user scrolls.
  window.addEventListener("scroll", handleScrollAnimation, {
    passive: true
  });

  // Recheck when the window is resized.
  window.addEventListener("resize", handleScrollAnimation);


  // ==========================================
  // 5. STATS COUNTER ANIMATION
  // ==========================================
  const counters = document.querySelectorAll(".counter");
  const animatedCounters = new WeakSet();

  function animateCounter(counter) {
    if (animatedCounters.has(counter)) return;

    const target = Number.parseInt(
      counter.getAttribute("data-target"),
      10
    );

    if (!Number.isFinite(target) || target < 0) return;

    animatedCounters.add(counter);

    const duration = 1800;
    const startTime = performance.now();

    function updateCount(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out effect for a smoother count-up animation.
      const easedProgress = 1 - Math.pow(1 - progress, 3);

      const currentCount = Math.floor(target * easedProgress);

      counter.textContent = currentCount;

      if (progress < 1) {
        requestAnimationFrame(updateCount);
      } else {
        counter.textContent = target;
      }
    }

    requestAnimationFrame(updateCount);
  }

  if ("IntersectionObserver" in window && counters.length > 0) {
    const counterObserver = new IntersectionObserver(
      function (entries, observer) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.4
      }
    );

    counters.forEach(function (counter) {
      counterObserver.observe(counter);
    });
  } else {
    // Fallback for browsers without IntersectionObserver.
    counters.forEach(animateCounter);
  }


  // ==========================================
  // 6. BACK-TO-TOP BUTTON
  // ==========================================
  const backToTopBtn = document.getElementById("backToTop");

  if (backToTopBtn) {
    function updateBackToTopButton() {
      if (window.scrollY > 300) {
        backToTopBtn.classList.remove("hidden");
      } else {
        backToTopBtn.classList.add("hidden");
      }
    }

    window.addEventListener("scroll", updateBackToTopButton, {
      passive: true
    });

    updateBackToTopButton();

    backToTopBtn.addEventListener("click", function () {
      window.scrollTo({
        top: 0,
        behavior: "smooth"
      });
    });
  }


  // ==========================================
  // 7. TESTIMONIAL MODAL
  // ==========================================
  const testimonialModal = document.getElementById("testimonialModal");
  const addTestimonialBtn = document.getElementById("addTestimonialBtn");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const cancelTestimonialBtn = document.getElementById(
    "cancelTestimonialBtn"
  );
  const testimonialForm = document.getElementById("testimonialForm");

  const starRatingButtons = document.querySelectorAll(".star-rating");

  let selectedRating = 0;
  let previousBodyOverflow = "";
  let previousBodyPosition = "";
  let previousBodyWidth = "";
  let previousScrollY = 0;

  // Find an optional form field used to submit the selected rating.
  const ratingInput = testimonialForm
    ? testimonialForm.querySelector(
        'input[name="rating"], select[name="rating"]'
      )
    : null;

  function syncRatingInput() {
    if (ratingInput) {
      ratingInput.value = selectedRating;
    }
  }

  function updateStarRating(hoverRating = 0) {
    const displayedRating = hoverRating || selectedRating;

    starRatingButtons.forEach(function (star) {
      const rating = Number.parseInt(star.dataset.rating, 10);
      const isActive = rating <= displayedRating;

      star.classList.toggle("text-yellow-400", isActive);
      star.classList.toggle("text-gray-300", !isActive);

      star.setAttribute(
        "aria-pressed",
        String(rating === selectedRating)
      );
    });
  }

  function openTestimonialModal() {
    if (!testimonialModal) return;

    testimonialModal.classList.remove("hidden");

    previousScrollY = window.scrollY;
    previousBodyOverflow = document.body.style.overflow;
    previousBodyPosition = document.body.style.position;
    previousBodyWidth = document.body.style.width;

    document.body.style.overflow = "hidden";

    // Focus the first suitable field inside the modal.
    const firstInput = testimonialModal.querySelector(
      'input:not([type="hidden"]), textarea, select, button'
    );

    if (firstInput) {
      firstInput.focus();
    }
  }

  function closeTestimonialModal() {
    if (!testimonialModal) return;

    testimonialModal.classList.add("hidden");

    document.body.style.overflow = previousBodyOverflow;
    document.body.style.position = previousBodyPosition;
    document.body.style.width = previousBodyWidth;

    if (testimonialForm) {
      testimonialForm.reset();
    }

    selectedRating = 0;
    syncRatingInput();
    updateStarRating();

    // Restore focus and the previous scroll position.
    if (addTestimonialBtn) {
      addTestimonialBtn.focus();
    }

    window.scrollTo({
      top: previousScrollY,
      behavior: "instant"
    });
  }

  if (addTestimonialBtn && testimonialModal) {
    addTestimonialBtn.addEventListener(
      "click",
      openTestimonialModal
    );
  }

  if (closeModalBtn) {
    closeModalBtn.addEventListener(
      "click",
      closeTestimonialModal
    );
  }

  if (cancelTestimonialBtn) {
    cancelTestimonialBtn.addEventListener(
      "click",
      closeTestimonialModal
    );
  }

  if (testimonialModal) {
    // Close when the overlay is clicked.
    testimonialModal.addEventListener("click", function (event) {
      if (event.target === testimonialModal) {
        closeTestimonialModal();
      }
    });

    // Close with Escape while the modal is open.
    document.addEventListener("keydown", function (event) {
      if (
        event.key === "Escape" &&
        !testimonialModal.classList.contains("hidden")
      ) {
        closeTestimonialModal();
      }
    });

    // Prevent clicks inside the modal content from closing it.
    const modalContent = testimonialModal.querySelector(".relative");

    if (modalContent) {
      modalContent.addEventListener("click", function (event) {
        event.stopPropagation();
      });
    }
  }


  // ==========================================
  // 8. TESTIMONIAL STAR RATING
  // ==========================================
  starRatingButtons.forEach(function (star) {
    star.addEventListener("click", function () {
      const rating = Number.parseInt(star.dataset.rating, 10);

      if (!Number.isFinite(rating) || rating < 1 || rating > 5) {
        return;
      }

      selectedRating = rating;

      syncRatingInput();
      updateStarRating();
    });

    star.addEventListener("mouseenter", function () {
      const rating = Number.parseInt(star.dataset.rating, 10);

      if (Number.isFinite(rating)) {
        updateStarRating(rating);
      }
    });

    star.addEventListener("focus", function () {
      const rating = Number.parseInt(star.dataset.rating, 10);

      if (Number.isFinite(rating)) {
        updateStarRating(rating);
      }
    });

    star.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        star.click();
      }
    });
  });

  const starRatingContainer =
    document.querySelector(".star-rating")?.parentElement;

  if (starRatingContainer) {
    starRatingContainer.addEventListener("mouseleave", function () {
      updateStarRating();
    });

    starRatingContainer.addEventListener("focusout", function () {
      updateStarRating();
    });
  }

  // Initialise the rating display.
  updateStarRating();


  // ==========================================
  // 9. REMOVE DARK-MODE PREFERENCE
  // ==========================================
  // The redesigned navbar has no dark-mode toggle.
  // Remove the old dark class so the page stays light.
  document.documentElement.classList.remove("dark");

});
