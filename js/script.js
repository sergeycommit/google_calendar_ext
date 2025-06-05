// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
    }

    // FAQ Accordion
    const faqItems = document.querySelectorAll('.faq-item');

    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');

        question.addEventListener('click', function() {
            const isActive = item.classList.contains('active');

            // Close all other FAQ items
            faqItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('active');
                }
            });

            // Toggle current item
            item.classList.toggle('active', !isActive);
        });
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');

    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
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

    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        // Hide/show header on scroll
        if (scrollTop > lastScrollTop && scrollTop > 200) {
            header.style.transform = 'translateY(-100%)';
        } else {
            header.style.transform = 'translateY(0)';
        }

        lastScrollTop = scrollTop;
    });

    // Install button click tracking
    const installButtons = document.querySelectorAll('a[href*="chrome.google.com/webstore"]');

    installButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Track installation attempt
            if (typeof gtag !== 'undefined') {
                gtag('event', 'click', {
                    event_category: 'Extension',
                    event_label: 'Install Button',
                    value: 1
                });
            }

            // Optional: Show installation guide popup
            showInstallationGuide();
        });
    });

    // Contact form submission (if contact form exists)
    const contactForm = document.querySelector('#contact-form');

    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
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
        feedbackLink.addEventListener('click', function(e) {
            e.preventDefault();
            openFeedbackForm();
        });
    }

    // Copy to clipboard functionality
    function copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                showNotification('Copied to clipboard!', 'success');
            }).catch(function() {
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
                    <button class="btn btn-primary" onclick="this.closest('.installation-modal').remove()">Got it!</button>
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

        document.body.appendChild(modal);
    }

    // Feedback form
    function openFeedbackForm() {
        const subject = encodeURIComponent('Quick Calendar Access - Feedback');
        const body = encodeURIComponent('Hi! I have feedback about the Quick Calendar Access extension:\n\n');
        window.open(`mailto:tdallstr@gmail.com?subject=${subject}&body=${body}`);
    }

    // Performance monitoring
    function trackPerformance() {
        if ('performance' in window) {
            window.addEventListener('load', function() {
                setTimeout(function() {
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

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        .animate {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
        
        .feature-card,
        .screenshot-item,
        .step {
            opacity: 0;
            transform: translateY(30px);
            transition: all 0.6s ease;
        }
        
        .header.scrolled {
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }
        
        .header {
            transition: all 0.3s ease;
        }
        
        @media (max-width: 768px) {
            .nav-menu.active {
                display: flex;
                flex-direction: column;
                position: absolute;
                top: 100%;
                left: 0;
                width: 100%;
                background: white;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 1rem 0;
            }
            
            .hamburger.active span:nth-child(1) {
                transform: rotate(-45deg) translate(-5px, 6px);
            }
            
            .hamburger.active span:nth-child(2) {
                opacity: 0;
            }
            
            .hamburger.active span:nth-child(3) {
                transform: rotate(45deg) translate(-5px, -6px);
            }
        }
    `;
    document.head.appendChild(style);

    // --- ВОССТАНОВЛЕНИЕ Intersection Observer для анимаций всех секций ---
    const animatedItems = document.querySelectorAll('.feature-card, .screenshot-item, .step, .faq-item');
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
});

// Error handling
window.addEventListener('error', function(e) {
    if (typeof gtag !== 'undefined') {
        gtag('event', 'exception', {
            description: e.error.toString(),
            fatal: false
        });
    }
});

// Service Worker registration (if available)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Register service worker for offline capabilities
        // This would require a separate service-worker.js file
    });
}