// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function () {
    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    const navOverlay = document.querySelector('.nav-overlay');

    if (hamburger && navMenu) {
        function toggleMenu(open) {
            const isOpen = open !== undefined ? open : !hamburger.classList.contains('active');

            if (isOpen) {
                hamburger.classList.add('active');
                navMenu.classList.add('active');
                hamburger.setAttribute('aria-expanded', 'true');
                document.body.classList.add('menu-open');
                if (navOverlay) {
                    navOverlay.classList.add('active');
                }
            } else {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
                hamburger.setAttribute('aria-expanded', 'false');
                document.body.classList.remove('menu-open');
                if (navOverlay) {
                    navOverlay.classList.remove('active');
                }
            }
        }

        hamburger.addEventListener('click', function () {
            toggleMenu();
        });

        // Close menu when clicking overlay
        if (navOverlay) {
            navOverlay.addEventListener('click', function () {
                toggleMenu(false);
            });
        }

        // Close menu when clicking a link
        const navLinks = navMenu.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', function () {
                toggleMenu(false);
            });
        });
    }

    // Make non-linked brand blocks behave like a consistent home affordance.
    const brandBlocks = document.querySelectorAll('.nav-brand');

    function findBrandTarget() {
        const homeLink = document.querySelector('.nav-menu a[href*="index.html"], .footer-links a[href*="index.html"]');

        if (homeLink) {
            return homeLink.getAttribute('href');
        }

        if (document.body.classList.contains('schedule-home')) {
            return '#page-top';
        }

        return './index.html';
    }

    const brandTarget = findBrandTarget();

    brandBlocks.forEach(block => {
        if (block.querySelector('a.brand-name, a.footer-brand-name')) {
            return;
        }

        const activateBrand = () => {
            if (brandTarget === '#page-top') {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            } else {
                window.location.href = brandTarget;
            }
        };

        block.setAttribute('role', 'link');
        block.setAttribute('tabindex', '0');
        block.dataset.clickable = 'true';

        block.addEventListener('click', function (e) {
            if (e.target.closest('a')) {
                return;
            }

            activateBrand();
        });

        block.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                activateBrand();
            }
        });
    });

    // Scroll progress bar
    const progressBar = document.querySelector('.scroll-progress');
    window.addEventListener('scroll', function () {
        const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (window.scrollY / windowHeight) * 100;
        if (progressBar) {
            progressBar.style.width = scrolled + '%';
        }
    });

    // Active navigation highlighting
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-menu a');

    function highlightNavigation() {
        const scrollY = window.scrollY;

        sections.forEach(section => {
            const sectionHeight = section.offsetHeight;
            const sectionTop = section.offsetTop - 100;
            const sectionId = section.getAttribute('id');

            if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${sectionId}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }

    window.addEventListener('scroll', highlightNavigation);

    // Back to top button
    const backToTop = document.querySelector('.back-to-top');
    if (backToTop) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });

        backToTop.addEventListener('click', function () {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Animated counters
    function animateCounter(element, target, duration = 2000, isDecimal = false) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            if (isDecimal) {
                element.textContent = current.toFixed(1);
            } else {
                element.textContent = Math.floor(current).toLocaleString();
            }
        }, 16);
    }

    // Initialize counters when hero is visible
    const statSection = document.querySelector('.hero-stats[data-animate="true"]');
    const statNumbers = statSection ? statSection.querySelectorAll('.stat-number') : [];
    let countersAnimated = false;

    const observerOptions = {
        threshold: 0.5
    };

    const counterObserver = new IntersectionObserver(function (entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting && !countersAnimated) {
                countersAnimated = true;
                statNumbers.forEach(stat => {
                    const target = parseFloat(stat.getAttribute('data-count'));
                    const isDecimal = target < 10;
                    animateCounter(stat, target, 2000, isDecimal);
                });
            }
        });
    }, observerOptions);

    if (statNumbers.length > 0 && statSection) {
        counterObserver.observe(statSection);
    }

    // FAQ Search
    const faqSearch = document.querySelector('.faq-search');
    const faqItems = document.querySelectorAll('.faq-item');
    const faqNoResults = document.querySelector('.faq-no-results');

    if (faqSearch) {
        faqSearch.addEventListener('input', function (e) {
            const searchTerm = e.target.value.toLowerCase();
            let visibleCount = 0;

            faqItems.forEach(item => {
                const question = item.querySelector('.faq-question h3').textContent.toLowerCase();
                const answer = item.querySelector('.faq-answer p').textContent.toLowerCase();

                if (question.includes(searchTerm) || answer.includes(searchTerm)) {
                    item.style.display = 'block';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });

            if (faqNoResults) {
                if (visibleCount === 0 && searchTerm !== '') {
                    faqNoResults.classList.add('visible');
                } else {
                    faqNoResults.classList.remove('visible');
                }
            }
        });
    }

    // FAQ Accordion
    faqItems.forEach((item, index) => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');

        if (!question || !answer) {
            return;
        }

        const questionId = question.id || `faq-question-${index + 1}`;
        const answerId = answer.id || question.getAttribute('aria-controls') || `faq-answer-${index + 1}`;
        const isActive = item.classList.contains('active');

        question.id = questionId;
        answer.id = answerId;
        question.setAttribute('aria-controls', answerId);
        question.setAttribute('aria-expanded', isActive ? 'true' : 'false');
        answer.setAttribute('role', 'region');
        answer.setAttribute('aria-labelledby', questionId);
        answer.setAttribute('aria-hidden', isActive ? 'false' : 'true');

        if (question.tagName !== 'BUTTON') {
            question.setAttribute('role', 'button');
            if (!question.hasAttribute('tabindex')) {
                question.setAttribute('tabindex', '0');
            }
        }

        question.addEventListener('click', function () {
            const itemIsActive = item.classList.contains('active');

            // Close all other FAQ items
            faqItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('active');
                    const otherQuestion = otherItem.querySelector('.faq-question');
                    const otherAnswer = otherItem.querySelector('.faq-answer');
                    if (otherQuestion) {
                        otherQuestion.setAttribute('aria-expanded', 'false');
                    }
                    if (otherAnswer) {
                        otherAnswer.setAttribute('aria-hidden', 'true');
                    }
                }
            });

            // Toggle current item
            item.classList.toggle('active', !itemIsActive);
            question.setAttribute('aria-expanded', String(!itemIsActive));
            answer.setAttribute('aria-hidden', itemIsActive ? 'true' : 'false');
        });
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');

    anchorLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                const headerHeight = document.querySelector('.header').offsetHeight;
                const targetPosition = targetElement.offsetTop - headerHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Header scroll effect
    let lastScrollTop = 0;
    const header = document.querySelector('.header');

    window.addEventListener('scroll', function () {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        // Keep header always visible (removed hide/show on scroll)
        lastScrollTop = scrollTop;
    });



    // Install button click tracking
    const installButtons = document.querySelectorAll('a[href*="chromewebstore.google.com"]');

    installButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            // Track installation attempt
            if (typeof gtag !== 'undefined') {
                gtag('event', 'click', {
                    event_category: 'Extension',
                    event_label: 'Install Button',
                    value: 1
                });
            }


        });
    });

    // Contact form submission (if contact form exists)
    const contactForm = document.querySelector('#contact-form');

    if (contactForm) {
        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();

            // Get form data
            const formData = new FormData(this);
            const formObject = {};
            formData.forEach((value, key) => {
                formObject[key] = value;
            });

            // Track form submission
            if (typeof gtag !== 'undefined') {
                gtag('event', 'submit', {
                    event_category: 'Contact',
                    event_label: 'Support Form',
                    value: 1
                });
            }

            // Show success message
            showNotification('Thank you for your message! We\'ll get back to you soon.', 'success');

            // Reset form
            this.reset();
        });
    }

    // Feedback link functionality
    const feedbackLink = document.querySelector('#feedback-link');

    if (feedbackLink) {
        feedbackLink.addEventListener('click', function (e) {
            e.preventDefault();
            openFeedbackForm();
        });
    }

    // Copy to clipboard functionality
    function copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function () {
                showNotification('Copied to clipboard!', 'success');
            }).catch(function () {
                fallbackCopyTextToClipboard(text);
            });
        } else {
            fallbackCopyTextToClipboard(text);
        }
    }

    function fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success');
        } catch (err) {
            showNotification('Failed to copy to clipboard', 'error');
        }

        document.body.removeChild(textArea);
    }

    // Notification system
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            zIndex: '10000',
            opacity: '0',
            transform: 'translateX(100%)',
            transition: 'all 0.3s ease'
        });

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';

            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Installation guide popup
    function showInstallationGuide() {
        const modal = document.createElement('div');
        modal.className = 'installation-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Installation Guide</h3>
                    <button class="close-modal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="install-step">
                        <h4>Step 1</h4>
                        <p>Click "Add to Chrome" on the Chrome Web Store page</p>
                    </div>
                    <div class="install-step">
                        <h4>Step 2</h4>
                        <p>Click "Add extension" when prompted</p>
                    </div>
                    <div class="install-step">
                        <h4>Step 3</h4>
                        <p>Look for the extension icon in your browser toolbar</p>
                    </div>
                    <div class="install-step">
                        <h4>Step 4</h4>
                        <p>Click the icon and sign in with your Google account</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary modal-close-btn">Got it!</button>
                </div>
            </div>
        `;

        // Style the modal
        Object.assign(modal.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100%',
            height: '100%',
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: '10000'
        });

        const modalContent = modal.querySelector('.modal-content');
        Object.assign(modalContent.style, {
            background: 'white',
            borderRadius: '12px',
            maxWidth: '500px',
            width: '90%',
            maxHeight: '90%',
            overflow: 'auto'
        });

        const modalHeader = modal.querySelector('.modal-header');
        Object.assign(modalHeader.style, {
            padding: '20px',
            borderBottom: '1px solid #eee',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
        });

        const modalBody = modal.querySelector('.modal-body');
        Object.assign(modalBody.style, {
            padding: '20px'
        });

        const installSteps = modal.querySelectorAll('.install-step');
        installSteps.forEach(step => {
            Object.assign(step.style, {
                marginBottom: '15px',
                padding: '15px',
                background: '#f8f9fa',
                borderRadius: '8px'
            });
        });

        const modalFooter = modal.querySelector('.modal-footer');
        Object.assign(modalFooter.style, {
            padding: '20px',
            borderTop: '1px solid #eee',
            textAlign: 'center'
        });

        const closeButton = modal.querySelector('.close-modal');
        Object.assign(closeButton.style, {
            background: 'none',
            border: 'none',
            fontSize: '24px',
            cursor: 'pointer',
            color: '#666'
        });

        closeButton.addEventListener('click', () => modal.remove());
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });

        const closeModalBtn = modal.querySelector('.modal-close-btn');
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => modal.remove());
        }

        document.body.appendChild(modal);
    }

    // Feedback form
    function openFeedbackForm() {
        const subject = encodeURIComponent('Schedule Calendar - Feedback');
        const body = encodeURIComponent('Hi! I have feedback about the Schedule Calendar extension:\n\n');
        window.open(`mailto:tdallstr@gmail.com?subject=${subject}&body=${body}`);
    }

    // Performance monitoring
    function trackPerformance() {
        if ('performance' in window) {
            window.addEventListener('load', function () {
                setTimeout(function () {
                    const perfData = performance.getEntriesByType('navigation')[0];

                    if (typeof gtag !== 'undefined' && perfData) {
                        gtag('event', 'timing_complete', {
                            name: 'page_load',
                            value: Math.round(perfData.loadEventEnd - perfData.loadEventStart)
                        });
                    }
                }, 0);
            });
        }
    }

    // Initialize performance tracking
    trackPerformance();

    // --- Intersection Observer для анимаций всех секций ---
    const animatedItems = document.querySelectorAll('.feature-card, .screenshot-item, .step, .faq-item, .testimonial-card');
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    obs.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.15
        });
        animatedItems.forEach(item => observer.observe(item));
    } else {
        animatedItems.forEach(item => item.classList.add('visible'));
    }

    // Keyboard navigation improvements
    document.addEventListener('keydown', function (e) {
        // Escape to close mobile menu
        if (e.key === 'Escape') {
            if (hamburger && navMenu && hamburger.classList.contains('active')) {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
                hamburger.setAttribute('aria-expanded', 'false');
                if (navOverlay) {
                    navOverlay.classList.remove('active');
                }
            }
        }

        // Enter/space to toggle FAQ when the trigger is not a native button.
        if ((e.key === 'Enter' || e.key === ' ') && e.target.closest('.faq-question[role="button"]')) {
            e.preventDefault();
            e.target.closest('.faq-question').click();
        }
    });

    // Make hamburger keyboard accessible
    if (hamburger) {
        hamburger.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    }

    // Language switcher
    const languageSwitcher = document.querySelector('.language-switcher');
    const languageBtn = document.querySelector('.language-btn');

    if (languageBtn && languageSwitcher) {
        languageBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            languageSwitcher.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function (e) {
            if (!languageSwitcher.contains(e.target)) {
                languageSwitcher.classList.remove('active');
            }
        });

        // Close on ESC key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && languageSwitcher.classList.contains('active')) {
                languageSwitcher.classList.remove('active');
            }
        });
    }

    // Lazy loading for images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.add('loaded');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Comparison Slider
    const sliderContainer = document.querySelector('.slider-container');
    const afterImage = document.querySelector('.after-image');
    const sliderHandle = document.querySelector('.slider-handle');

    if (sliderContainer && afterImage && sliderHandle) {
        sliderContainer.addEventListener('mousemove', function (e) {
            const rect = sliderContainer.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const percent = (x / rect.width) * 100;

            if (percent >= 0 && percent <= 100) {
                afterImage.style.clipPath = `inset(0 0 0 ${percent}%)`;
                sliderHandle.style.left = `${percent}%`;
            }
        });

        sliderContainer.addEventListener('touchmove', function (e) {
            const rect = sliderContainer.getBoundingClientRect();
            const touch = e.touches[0];
            const x = touch.clientX - rect.left;
            const percent = (x / rect.width) * 100;

            if (percent >= 0 && percent <= 100) {
                afterImage.style.clipPath = `inset(0 0 0 ${percent}%)`;
                sliderHandle.style.left = `${percent}%`;
            }
        });
    }

    // Scrolly-telling
    const scrollySection = document.querySelector('.scrolly-section');
    const scrollSteps = document.querySelectorAll('.scroll-step');

    if (scrollySection && scrollSteps.length > 0) {
        const scrollyObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const feature = entry.target.dataset.feature;
                    scrollySection.setAttribute('data-active', feature);

                    scrollSteps.forEach(step => step.classList.remove('active'));
                    entry.target.classList.add('active');
                }
            });
        }, {
            threshold: 0.8
        });

        scrollSteps.forEach(step => scrollyObserver.observe(step));
    }

    // Fade-in animations on scroll
    const fadeSections = document.querySelectorAll('.fade-in-section');
    if (fadeSections.length > 0) {
        const fadeObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    fadeObserver.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1
        });

        fadeSections.forEach(section => {
            fadeObserver.observe(section);
        });
    }

    // Workflow switcher for the refreshed homepage
    const workflowShell = document.querySelector('.workflow-shell');
    const workflowToggles = document.querySelectorAll('.workflow-toggle');
    const workflowPanels = document.querySelectorAll('.workflow-panel');

    if (workflowShell && workflowToggles.length > 0 && workflowPanels.length > 0) {
        const workflowMeterLabel = workflowShell.querySelector('.workflow-meter-label');
        const workflowMeterTitle = workflowShell.querySelector('.workflow-meter-title');
        const workflowMeterCopy = workflowShell.querySelector('.workflow-meter-copy');
        const workflowCalloutPill = workflowShell.querySelector('.workflow-callout-pill');
        const workflowCalloutTitle = workflowShell.querySelector('.workflow-callout-title');
        const workflowCalloutCopy = workflowShell.querySelector('.workflow-callout-copy');

        workflowPanels.forEach(panel => {
            panel.id = panel.id || `workflow-panel-${panel.dataset.mode}`;

            const matchingToggle = Array.from(workflowToggles).find(toggle => toggle.dataset.mode === panel.dataset.mode);
            if (matchingToggle) {
                matchingToggle.setAttribute('aria-controls', panel.id);
            }
        });

        function applyWorkflowState(activeToggle) {
            const mode = activeToggle.dataset.mode;

            workflowShell.dataset.mode = mode;

            workflowToggles.forEach(button => {
                const isActive = button === activeToggle;
                button.classList.toggle('active', isActive);
                button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
            });

            workflowPanels.forEach(panel => {
                const isActive = panel.dataset.mode === mode;
                panel.classList.toggle('active', isActive);
                panel.hidden = !isActive;
            });

            if (workflowMeterLabel && activeToggle.dataset.meterLabel) {
                workflowMeterLabel.textContent = activeToggle.dataset.meterLabel;
            }

            if (workflowMeterTitle && activeToggle.dataset.meterTitle) {
                workflowMeterTitle.textContent = activeToggle.dataset.meterTitle;
            }

            if (workflowMeterCopy && activeToggle.dataset.meterCopy) {
                workflowMeterCopy.textContent = activeToggle.dataset.meterCopy;
            }

            if (workflowCalloutPill && activeToggle.dataset.calloutPill) {
                workflowCalloutPill.textContent = activeToggle.dataset.calloutPill;
            }

            if (workflowCalloutTitle && activeToggle.dataset.calloutTitle) {
                workflowCalloutTitle.textContent = activeToggle.dataset.calloutTitle;
            }

            if (workflowCalloutCopy && activeToggle.dataset.calloutCopy) {
                workflowCalloutCopy.textContent = activeToggle.dataset.calloutCopy;
            }
        }

        workflowToggles.forEach(toggle => {
            toggle.addEventListener('click', function () {
                applyWorkflowState(this);
            });
        });

        const defaultToggle = workflowShell.querySelector('.workflow-toggle.active') || workflowToggles[0];
        if (defaultToggle) {
            applyWorkflowState(defaultToggle);
        }
    }
});

// Error handling
window.addEventListener('error', function (e) {
    if (typeof gtag !== 'undefined') {
        gtag('event', 'exception', {
            description: e.error.toString(),
            fatal: false
        });
    }
});

// Service Worker registration (if available)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
        // Register service worker for offline capabilities
        // This would require a separate service-worker.js file
    });
}
