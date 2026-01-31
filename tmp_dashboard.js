/**
 * AI API Gateway - Dashboard JavaScript
 * Handles dynamic functionality, interactions, and API calls
 */

// ========== Utility Functions ==========

/**
 * Show a notification message
 * @param {string} message - Notification text
 * @param {string} type - 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (0 = no auto-close)
 */
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.display = 'block';
    
    document.body.appendChild(notification);
    
    if (duration > 0) {
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out forwards';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @param {string} message - Success message
 */
async function copyToClipboard(text, message = 'Copied to clipboard!') {
    try {
        await navigator.clipboard.writeText(text);
        showNotification(message, 'success', 2000);
        return true;
    } catch (err) {
        showNotification('Failed to copy to clipboard', 'error', 2000);
        return false;
    }
}

/**
 * Format date to readable string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Format bytes to human-readable size
 * @param {number} bytes - Number of bytes
 * @returns {string} Formatted size
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Mask API key for display (show only first and last 4 chars)
 * @param {string} key - API key to mask
 * @returns {string} Masked key
 */
function maskKey(key) {
    if (!key || key.length < 8) return '***';
    return key.substring(0, 4) + '***' + key.substring(key.length - 4);
}

// ========== Tunnel URL Management ==========

/**
 * Fetch and display the tunnel URL
 */
async function fetchTunnelUrl() {
    try {
        const response = await fetch('/api/tunnel-url');
        const data = await response.json();
        
        const tunnelInfo = document.getElementById('tunnel-info');
        const tunnelUrl = document.getElementById('tunnel-url');
        
        if (data.tunnel_url) {
            tunnelUrl.href = data.tunnel_url;
            tunnelUrl.textContent = data.tunnel_url;
            tunnelInfo.style.display = 'block';
        } else {
            tunnelInfo.style.display = 'none';
        }
    } catch (error) {
        console.error('Error fetching tunnel URL:', error);
    }
}

// ========== API Key Management ==========

/**
 * Create a new API key
 */
async function createApiKey() {
    const expirationInput = document.getElementById('key-expiration');
    const expiration = expirationInput.value;
    
    if (!expiration) {
        showNotification('Please select an expiration date', 'warning', 3000);
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Creating...';
    
    try {
        const response = await fetch('/api/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                expires_at: expiration
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.api_key) {
            showNotification('API key created! Copy it now (you won\'t see it again)', 'success', 5000);
            
            // Show key in modal or alert
            const keyDisplay = prompt(
                'Your API Key:\n\n' + data.api_key + '\n\nClick Copy to copy to clipboard, or save it securely.',
                data.api_key
            );
            
            if (keyDisplay) {
                await copyToClipboard(data.api_key, 'API key copied!');
            }
            
            // Refresh the key list
            location.reload();
        } else {
            showNotification(data.detail || 'Failed to create API key', 'error', 3000);
        }
    } catch (error) {
        showNotification('Error creating API key: ' + error.message, 'error', 3000);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>✓</span> Create Key';
    }
}

/**
 * Delete (revoke) an API key
 * @param {string} keyId - The key ID to revoke
 */
async function deleteApiKey(keyId) {
    if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>';
    
    try {
        const response = await fetch(`/api/delete/${keyId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('API key revoked', 'success', 2000);
            // Remove the row after a short delay
            setTimeout(() => {
                const row = btn.closest('tr');
                row.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => row.remove(), 300);
            }, 300);
        } else {
            const data = await response.json();
            showNotification(data.detail || 'Failed to revoke API key', 'error', 3000);
            btn.disabled = false;
            btn.innerHTML = '✕ Revoke';
        }
    } catch (error) {
        showNotification('Error revoking API key: ' + error.message, 'error', 3000);
        btn.disabled = false;
        btn.innerHTML = '✕ Revoke';
    }
}

/**
 * Copy an API key ID to clipboard
 * @param {string} keyId - The key ID to copy
 */
async function copyKeyId(keyId) {
    await copyToClipboard(keyId, 'Key ID copied!');
}

// ========== Status Helper ==========

/**
 * Get status badge HTML
 * @param {string} status - The status (active, expired, revoked)
 * @returns {string} HTML badge
 */
function getStatusBadge(status) {
    const badges = {
        'active': '<span class="status-badge status-active">Active</span>',
        'expired': '<span class="status-badge status-expired">Expired</span>',
        'revoked': '<span class="status-badge status-revoked">Revoked</span>',
        'pending': '<span class="status-badge status-pending">Pending</span>'
    };
    return badges[status] || '<span class="status-badge status-pending">Unknown</span>';
}

// ========== Page Initialization ==========

/**
 * Initialize the dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Fetch and display tunnel URL on page load
    fetchTunnelUrl();
    
    // Refresh tunnel URL every 10 seconds
    setInterval(fetchTunnelUrl, 10000);
    
    // Set minimum date for expiration input (today)
    const expirationInput = document.getElementById('key-expiration');
    if (expirationInput) {
        const today = new Date().toISOString().split('T')[0];
        expirationInput.min = today;
        // Set default to 30 days from now
        const thirtyDaysFromNow = new Date();
        thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
        expirationInput.value = thirtyDaysFromNow.toISOString().split('T')[0];
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) searchInput.focus();
        }
    });
});

// ========== Export Functions for Testing ==========

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showNotification,
        copyToClipboard,
        formatDate,
        formatBytes,
        maskKey,
        fetchTunnelUrl,
        createApiKey,
        deleteApiKey,
        copyKeyId,
        getStatusBadge
    };
}

