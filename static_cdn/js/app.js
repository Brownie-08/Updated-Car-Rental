/* ===== BROWNIE CAR RENTAL - OPTIMIZED JAVASCRIPT ===== */

// Performance optimizations
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

const throttle = (func, limit) => {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
};

// Initialize AOS (Animate on Scroll) with performance optimizations
const initAOS = () => {
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true,
            mirror: false,
            anchorPlacement: 'top-bottom',
            disable: 'mobile' // Disable on mobile for better performance
        });
    }
};

// Lazy loading for images
const lazyLoadImages = () => {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('img-lazy');
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => {
        img.classList.add('img-lazy');
        imageObserver.observe(img);
    });
};

// Scroll to top functionality
const initScrollToTop = () => {
    const scrollToTopBtn = document.createElement('button');
    scrollToTopBtn.className = 'scroll-to-top';
    scrollToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    scrollToTopBtn.setAttribute('aria-label', 'Scroll to top');
    document.body.appendChild(scrollToTopBtn);
    
    const toggleScrollToTop = throttle(() => {
        if (window.pageYOffset > 300) {
            scrollToTopBtn.classList.add('visible');
        } else {
            scrollToTopBtn.classList.remove('visible');
        }
    }, 100);
    
    window.addEventListener('scroll', toggleScrollToTop);
    
    scrollToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
};

// Enhanced navbar scroll effect
const initNavbarScroll = () => {
    const navbar = document.getElementById('mainNavbar');
    if (!navbar) return;
    
    const handleScroll = throttle(() => {
        if (window.scrollY > 100) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    }, 50);
    
    window.addEventListener('scroll', handleScroll);
};

// Enhanced search functionality
const initEnhancedSearch = () => {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        const searchContainer = input.closest('.search-container');
        if (!searchContainer) return;
        
        // Create suggestions container
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'search-suggestions';
        searchContainer.appendChild(suggestionsContainer);
        
        const handleSearch = debounce((query) => {
            if (query.length < 2) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            // Sample search suggestions (in real app, this would be an API call)
            const suggestions = [
                'Luxury Cars',
                'SUVs',
                'Economy Cars',
                'BMW',
                'Mercedes',
                'Toyota',
                'Honda'
            ].filter(item => item.toLowerCase().includes(query.toLowerCase()));
            
            if (suggestions.length > 0) {
                suggestionsContainer.innerHTML = suggestions
                    .map(suggestion => `<div class="search-suggestion-item">${suggestion}</div>`)
                    .join('');
                suggestionsContainer.style.display = 'block';
                
                // Add click handlers to suggestions
                suggestionsContainer.querySelectorAll('.search-suggestion-item').forEach(item => {
                    item.addEventListener('click', () => {
                        input.value = item.textContent;
                        suggestionsContainer.style.display = 'none';
                        input.closest('form').submit();
                    });
                });
            } else {
                suggestionsContainer.style.display = 'none';
            }
        }, 300);
        
        input.addEventListener('input', (e) => {
            handleSearch(e.target.value);
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchContainer.contains(e.target)) {
                suggestionsContainer.style.display = 'none';
            }
        });
    });
};

// Performance monitoring
const monitorPerformance = () => {
    if ('performance' in window) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
                
                console.log('Page Load Performance:', {
                    loadTime: `${loadTime}ms`,
                    domContentLoaded: `${perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart}ms`,
                    totalPageLoad: `${perfData.loadEventEnd - perfData.navigationStart}ms`
                });
            }, 0);
        });
    }
};

// Initialize all functionality when DOM is ready
const init = () => {
    initAOS();
    lazyLoadImages();
    initScrollToTop();
    initNavbarScroll();
    initEnhancedSearch();
    monitorPerformance();
};

// Use DOMContentLoaded for faster initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Export functions for potential use in other scripts
window.BrownieCarRental = {
    debounce,
    throttle,
    initAOS,
    lazyLoadImages,
    initScrollToTop,
    initNavbarScroll,
    initEnhancedSearch
};

// Enhanced Car Rental System JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS (Animate On Scroll)
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true,
            offset: 100
        });
    }

    // Hide loading spinner
    const loadingOverlay = document.getElementById('loading');
    if (loadingOverlay) {
        setTimeout(() => {
            loadingOverlay.style.display = 'none';
        }, 1000);
    }

    // Enhanced Navbar Scroll Effect
    const navbar = document.getElementById('mainNavbar');
    if (navbar) {
        let lastScrollTop = 0;
        let scrollTimeout;

        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            // Add scrolled class for styling
            if (scrollTop > 50) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }

            // Auto-hide/show navbar on scroll
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // Scrolling down
                navbar.style.transform = 'translateY(-100%)';
            } else {
                // Scrolling up
                navbar.style.transform = 'translateY(0)';
            }

            lastScrollTop = scrollTop;

            // Clear timeout and reset navbar visibility after scroll stops
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                navbar.style.transform = 'translateY(0)';
            }, 150);
        });
    }

    // Enhanced Search Functionality
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const searchTerm = this.value.trim();
            
            if (searchTerm.length >= 2) {
                searchTimeout = setTimeout(() => {
                    // Add search suggestions or live search here
                    showSearchSuggestions(searchTerm);
                }, 300);
            } else {
                hideSearchSuggestions();
            }
        });

        // Clear search on escape
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                hideSearchSuggestions();
            }
        });
    });

    // Car Card Animations
    const carCards = document.querySelectorAll('.car-card, .modern-car-card');
    carCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-12px) scale(1.02)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Enhanced Form Validation
    const forms = document.querySelectorAll('form[novalidate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });

        // Real-time validation
        const inputs = form.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });

            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });

    // Enhanced Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover focus',
            delay: { show: 300, hide: 100 }
        });
    });

    // Image Lazy Loading Enhancement
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // Enhanced Button Interactions
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Local Storage for User Preferences
    initializeUserPreferences();

    // Initialize notification system
    initializeNotifications();

    // Car comparison functionality
    initializeCarComparison();
});

// Search Suggestions
function showSearchSuggestions(term) {
    // This would connect to your search API
    console.log('Searching for:', term);
    // Implementation for search suggestions
}

function hideSearchSuggestions() {
    const suggestions = document.querySelector('.search-suggestions');
    if (suggestions) {
        suggestions.style.display = 'none';
    }
}

// Enhanced Form Validation
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('.form-control[required]');
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    let isValid = true;
    let errorMessage = '';

    // Remove existing validation classes
    field.classList.remove('is-valid', 'is-invalid');

    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }

    // Email validation
    if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }

    // Phone validation
    if (field.name === 'cell_no' && value) {
        const phoneRegex = /^[\+]?[1-9]?[\d\s\-\(\)]{8,15}$/;
        if (!phoneRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid phone number';
        }
    }

    // Date validation
    if (type === 'date' && value) {
        const selectedDate = new Date(value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (selectedDate < today) {
            isValid = false;
            errorMessage = 'Date cannot be in the past';
        }
    }

    // Apply validation classes and messages
    if (isValid) {
        field.classList.add('is-valid');
        hideFieldError(field);
    } else {
        field.classList.add('is-invalid');
        showFieldError(field, errorMessage);
    }

    return isValid;
}

function showFieldError(field, message) {
    let errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        field.parentNode.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
}

function hideFieldError(field) {
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// User Preferences
function initializeUserPreferences() {
    // Load saved preferences
    const preferences = JSON.parse(localStorage.getItem('carRentalPreferences')) || {};
    
    // Apply saved theme, language, etc.
    if (preferences.theme) {
        document.body.classList.add(`theme-${preferences.theme}`);
    }
}

function saveUserPreference(key, value) {
    const preferences = JSON.parse(localStorage.getItem('carRentalPreferences')) || {};
    preferences[key] = value;
    localStorage.setItem('carRentalPreferences', JSON.stringify(preferences));
}

// Notification System
function initializeNotifications() {
    // Check for saved notifications
    const notifications = JSON.parse(localStorage.getItem('carRentalNotifications')) || [];
    notifications.forEach(notification => {
        if (!notification.read) {
            showNotification(notification.message, notification.type);
        }
    });
}

function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Position notifications
    let container = document.querySelector('.notification-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Car Comparison Feature
function initializeCarComparison() {
    const compareButtons = document.querySelectorAll('.compare-car-btn');
    compareButtons.forEach(button => {
        button.addEventListener('click', function() {
            const carId = this.dataset.carId;
            toggleCarComparison(carId);
        });
    });
}

function toggleCarComparison(carId) {
    let compareList = JSON.parse(localStorage.getItem('carComparison')) || [];
    
    if (compareList.includes(carId)) {
        compareList = compareList.filter(id => id !== carId);
        showNotification('Car removed from comparison', 'info');
    } else {
        if (compareList.length >= 3) {
            showNotification('You can compare maximum 3 cars', 'warning');
            return;
        }
        compareList.push(carId);
        showNotification('Car added to comparison', 'success');
    }
    
    localStorage.setItem('carComparison', JSON.stringify(compareList));
    updateComparisonUI(compareList);
}

function updateComparisonUI(compareList) {
    // Update comparison badge
    const badge = document.querySelector('.comparison-badge');
    if (badge) {
        badge.textContent = compareList.length;
        badge.style.display = compareList.length > 0 ? 'inline' : 'none';
    }
    
    // Update compare buttons state
    const compareButtons = document.querySelectorAll('.compare-car-btn');
    compareButtons.forEach(button => {
        const carId = button.dataset.carId;
        if (compareList.includes(carId)) {
            button.classList.add('active');
            button.innerHTML = '<i class="fas fa-check"></i> Added';
        } else {
            button.classList.remove('active');
            button.innerHTML = '<i class="fas fa-balance-scale"></i> Compare';
        }
    });
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Add CSS for ripple effect and notifications
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.4);
        pointer-events: none;
        animation: ripple-animation 0.6s linear;
        z-index: 1;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    .notification-container {
        position: fixed;
        top: 100px;
        right: 20px;
        z-index: 1050;
        max-width: 350px;
    }
    
    .notification-toast {
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border: none;
        border-radius: 12px;
    }
    
    .comparison-badge {
        position: absolute;
        top: -8px;
        right: -8px;
        background: #dc3545;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        font-size: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .compare-car-btn.active {
        background: #28a745 !important;
        border-color: #28a745 !important;
    }
    
    .lazy {
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .lazy.loaded {
        opacity: 1;
    }
`;
document.head.appendChild(style);
