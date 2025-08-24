/**
 * MCP Admin Suite JavaScript
 * Common functionality for all admin interfaces
 */

// Global configuration
const MCP_CONFIG = {
    websocket: {
        reconnectDelay: 3000,
        heartbeatInterval: 30000
    },
    ui: {
        toastDuration: 5000,
        refreshInterval: 30000
    }
};

// Utility functions
const Utils = {
    /**
     * Format timestamp to local time string
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        return new Date(timestamp).toLocaleString();
    },

    /**
     * Format duration in seconds to human readable string
     */
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    },

    /**
     * Format file size in bytes to human readable string
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Debounce function execution
     */
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = MCP_CONFIG.ui.toastDuration) {
        // Create toast container if it doesn't exist
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(container);
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast"></button>
            </div>
        `;

        container.appendChild(toast);

        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();

        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            container.removeChild(toast);
        });
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard', 'success');
        } catch (err) {
            this.showToast('Failed to copy to clipboard', 'error');
        }
    },

    /**
     * Validate JSON string
     */
    isValidJSON(str) {
        try {
            JSON.parse(str);
            return true;
        } catch (e) {
            return false;
        }
    },

    /**
     * Pretty print JSON
     */
    prettyPrintJSON(obj) {
        return JSON.stringify(obj, null, 2);
    }
};

// WebSocket manager
class WebSocketManager {
    constructor(url, options = {}) {
        this.url = url;
        this.options = {
            reconnectDelay: options.reconnectDelay || MCP_CONFIG.websocket.reconnectDelay,
            heartbeatInterval: options.heartbeatInterval || MCP_CONFIG.websocket.heartbeatInterval,
            onOpen: options.onOpen || (() => {}),
            onMessage: options.onMessage || (() => {}),
            onClose: options.onClose || (() => {}),
            onError: options.onError || (() => {})
        };
        
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.heartbeatTimer = null;
    }

    connect() {
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = (event) => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                this.options.onOpen(event);
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.options.onMessage(data);
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket disconnected');
                this.stopHeartbeat();
                this.options.onClose(event);
                
                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    setTimeout(() => this.connect(), this.options.reconnectDelay);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.options.onError(error);
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.options.onError(error);
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    startHeartbeat() {
        this.heartbeatTimer = setInterval(() => {
            this.send({ type: 'ping', timestamp: Date.now() });
        }, this.options.heartbeatInterval);
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close();
        }
    }
}

// API client
class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    async get(endpoint, params = {}) {
        const query = new URLSearchParams(params).toString();
        const url = query ? `${endpoint}?${query}` : endpoint;
        return this.request(url);
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: data
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: data
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// Form validation helper
class FormValidator {
    constructor(formElement) {
        this.form = formElement;
        this.validators = {};
    }

    addValidator(fieldName, validator) {
        this.validators[fieldName] = validator;
    }

    validate() {
        let isValid = true;
        const errors = {};

        for (const [fieldName, validator] of Object.entries(this.validators)) {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const result = validator(field.value, field);
                if (result !== true) {
                    isValid = false;
                    errors[fieldName] = result;
                    this.showFieldError(field, result);
                } else {
                    this.clearFieldError(field);
                }
            }
        }

        return { isValid, errors };
    }

    showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    clearAllErrors() {
        this.form.querySelectorAll('.is-invalid').forEach(field => {
            this.clearFieldError(field);
        });
    }
}

// Data table helper
class DataTable {
    constructor(tableElement, options = {}) {
        this.table = tableElement;
        this.tbody = tableElement.querySelector('tbody');
        this.options = {
            emptyMessage: 'No data available',
            loadingMessage: 'Loading...',
            ...options
        };
    }

    showLoading() {
        const colCount = this.table.querySelectorAll('thead th').length;
        this.tbody.innerHTML = `
            <tr>
                <td colspan="${colCount}" class="text-center py-4">
                    <div class="spinner-border spinner-border-sm me-2"></div>
                    ${this.options.loadingMessage}
                </td>
            </tr>
        `;
    }

    showEmpty(message = null) {
        const colCount = this.table.querySelectorAll('thead th').length;
        this.tbody.innerHTML = `
            <tr>
                <td colspan="${colCount}" class="text-center text-muted py-4">
                    ${message || this.options.emptyMessage}
                </td>
            </tr>
        `;
    }

    updateData(rows) {
        if (!rows || rows.length === 0) {
            this.showEmpty();
            return;
        }

        this.tbody.innerHTML = rows.join('');
    }

    addRow(rowHTML) {
        if (this.tbody.innerHTML.includes('No data available') || 
            this.tbody.innerHTML.includes('Loading...')) {
            this.tbody.innerHTML = rowHTML;
        } else {
            this.tbody.insertAdjacentHTML('beforeend', rowHTML);
        }
    }
}

// Auto-refresh manager
class AutoRefresh {
    constructor(callback, interval = MCP_CONFIG.ui.refreshInterval) {
        this.callback = callback;
        this.interval = interval;
        this.timerId = null;
        this.isRunning = false;
    }

    start() {
        if (!this.isRunning) {
            this.isRunning = true;
            this.timerId = setInterval(this.callback, this.interval);
        }
    }

    stop() {
        if (this.isRunning) {
            this.isRunning = false;
            if (this.timerId) {
                clearInterval(this.timerId);
                this.timerId = null;
            }
        }
    }

    restart() {
        this.stop();
        this.start();
    }

    setInterval(newInterval) {
        this.interval = newInterval;
        if (this.isRunning) {
            this.restart();
        }
    }
}

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    // Update current time every second
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        setInterval(() => {
            timeElement.textContent = new Date().toLocaleString();
        }, 1000);
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Add copy-to-clipboard functionality to code blocks
    document.querySelectorAll('pre code').forEach(block => {
        const button = document.createElement('button');
        button.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-1';
        button.innerHTML = '<i class="bi bi-clipboard"></i>';
        button.style.fontSize = '0.75rem';
        
        button.addEventListener('click', () => {
            Utils.copyToClipboard(block.textContent);
        });
        
        block.parentNode.style.position = 'relative';
        block.parentNode.appendChild(button);
    });
});

// Export global objects
window.Utils = Utils;
window.WebSocketManager = WebSocketManager;
window.APIClient = APIClient;
window.FormValidator = FormValidator;
window.DataTable = DataTable;
window.AutoRefresh = AutoRefresh;