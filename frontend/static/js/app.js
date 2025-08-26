/**
 * PolyVeda - Main JavaScript Application
 */

// Global configuration
window.PolyVeda = {
    config: {
        apiBaseUrl: '/api/',
        csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')?.value,
        debug: false
    },
    
    // Utility functions
    utils: {
        // Show notification
        showNotification: function(message, type = 'info', duration = 5000) {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} animate-slide-down fixed top-4 right-4 z-50 max-w-sm`;
            
            const icon = this.getNotificationIcon(type);
            const closeButton = `
                <button onclick="this.parentElement.remove()" class="ml-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            `;
            
            notification.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        ${icon}
                        <span>${message}</span>
                    </div>
                    ${closeButton}
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after duration
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, duration);
        },
        
        // Get notification icon based on type
        getNotificationIcon: function(type) {
            const icons = {
                success: '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>',
                error: '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>',
                warning: '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>',
                info: '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>'
            };
            return icons[type] || icons.info;
        },
        
        // Format date
        formatDate: function(date, format = 'YYYY-MM-DD') {
            const d = new Date(date);
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const hours = String(d.getHours()).padStart(2, '0');
            const minutes = String(d.getMinutes()).padStart(2, '0');
            
            return format
                .replace('YYYY', year)
                .replace('MM', month)
                .replace('DD', day)
                .replace('HH', hours)
                .replace('mm', minutes);
        },
        
        // Format file size
        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        
        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Throttle function
        throttle: function(func, limit) {
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
        }
    },
    
    // API functions
    api: {
        // Make API request
        request: async function(endpoint, options = {}) {
            const url = this.config.apiBaseUrl + endpoint;
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                }
            };
            
            const finalOptions = { ...defaultOptions, ...options };
            
            try {
                const response = await fetch(url, finalOptions);
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.message || 'API request failed');
                }
                
                return data;
            } catch (error) {
                console.error('API Error:', error);
                throw error;
            }
        },
        
        // GET request
        get: function(endpoint) {
            return this.request(endpoint, { method: 'GET' });
        },
        
        // POST request
        post: function(endpoint, data) {
            return this.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },
        
        // PUT request
        put: function(endpoint, data) {
            return this.request(endpoint, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },
        
        // DELETE request
        delete: function(endpoint) {
            return this.request(endpoint, { method: 'DELETE' });
        }
    },
    
    // UI components
    ui: {
        // Show loading overlay
        showLoading: function() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.classList.remove('hidden');
            }
        },
        
        // Hide loading overlay
        hideLoading: function() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.classList.add('hidden');
            }
        },
        
        // Toggle sidebar
        toggleSidebar: function() {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                sidebar.classList.toggle('sidebar-closed');
                sidebar.classList.toggle('sidebar-open');
            }
        },
        
        // Show modal
        showModal: function(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('hidden');
                document.body.classList.add('overflow-hidden');
            }
        },
        
        // Hide modal
        hideModal: function(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('hidden');
                document.body.classList.remove('overflow-hidden');
            }
        },
        
        // Initialize tooltips
        initTooltips: function() {
            const tooltips = document.querySelectorAll('[data-tooltip]');
            tooltips.forEach(element => {
                element.addEventListener('mouseenter', function() {
                    const tooltip = document.createElement('div');
                    tooltip.className = 'absolute z-50 px-2 py-1 text-xs text-white bg-gray-900 rounded shadow-lg';
                    tooltip.textContent = this.getAttribute('data-tooltip');
                    tooltip.style.top = this.offsetTop - 30 + 'px';
                    tooltip.style.left = this.offsetLeft + 'px';
                    document.body.appendChild(tooltip);
                    this._tooltip = tooltip;
                });
                
                element.addEventListener('mouseleave', function() {
                    if (this._tooltip) {
                        this._tooltip.remove();
                        this._tooltip = null;
                    }
                });
            });
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    PolyVeda.ui.initTooltips();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize file uploads
    initFileUploads();
    
    // Initialize search functionality
    initSearch();
    
    // Initialize dark mode toggle
    initDarkMode();
});

// Form validation
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showFieldError(input, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(input);
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-sm text-danger-600 mt-1';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
    field.classList.add('border-danger-500');
}

function clearFieldError(field) {
    const errorDiv = field.parentNode.querySelector('.text-sm.text-danger-600');
    if (errorDiv) {
        errorDiv.remove();
    }
    field.classList.remove('border-danger-500');
}

// File upload functionality
function initFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const files = Array.from(this.files);
            const maxSize = 10 * 1024 * 1024; // 10MB
            const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
            
            files.forEach(file => {
                if (file.size > maxSize) {
                    PolyVeda.utils.showNotification(`File ${file.name} is too large. Maximum size is 10MB.`, 'error');
                    this.value = '';
                    return;
                }
                
                if (!allowedTypes.includes(file.type)) {
                    PolyVeda.utils.showNotification(`File type ${file.type} is not allowed.`, 'error');
                    this.value = '';
                    return;
                }
            });
        });
    });
}

// Search functionality
function initSearch() {
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(input => {
        const debouncedSearch = PolyVeda.utils.debounce(function(query) {
            performSearch(query, input.getAttribute('data-search'));
        }, 300);
        
        input.addEventListener('input', function() {
            debouncedSearch(this.value);
        });
    });
}

function performSearch(query, target) {
    const targetElement = document.querySelector(target);
    if (!targetElement) return;
    
    const items = targetElement.querySelectorAll('[data-search-item]');
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        const matches = text.includes(query.toLowerCase());
        item.style.display = matches ? 'block' : 'none';
    });
}

// Dark mode functionality
function initDarkMode() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.documentElement.classList.toggle('dark');
            const isDark = document.documentElement.classList.contains('dark');
            localStorage.setItem('darkMode', isDark);
        });
    }
    
    // Check for saved dark mode preference
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
        document.documentElement.classList.add('dark');
    }
}

// Export for use in other modules
window.PolyVeda = PolyVeda;