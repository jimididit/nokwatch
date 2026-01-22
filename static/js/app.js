// Website Monitor Application JavaScript

// State management
let jobs = [];
let currentJobId = null;
let refreshInterval = null;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// Initialize application
function initializeApp() {
    setupEventListeners();
    loadJobs();
    startAutoRefresh();
    
    // Keyboard shortcuts (desktop only)
    if (window.innerWidth >= 768) {
        document.addEventListener('keydown', handleKeyboardShortcuts);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Add job button
    const addBtn = document.getElementById('add-job-btn');
    if (addBtn) {
        addBtn.addEventListener('click', () => openJobModal());
    }
    
    // Test email button
    const testEmailBtn = document.getElementById('test-email-btn');
    if (testEmailBtn) {
        testEmailBtn.addEventListener('click', () => testEmail());
    }
    
    // Job form submission
    const jobForm = document.getElementById('job-form');
    if (jobForm) {
        jobForm.addEventListener('submit', handleJobSubmit);
    }
    
    // Close modal on overlay click
    const modal = document.getElementById('job-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeJobModal();
            }
        });
    }
    
    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeJobModal();
        }
    });
}

// Load all jobs from API
async function loadJobs() {
    try {
        showLoading(true);
        const response = await fetch('/api/jobs');
        
        if (!response.ok) {
            throw new Error('Failed to load jobs');
        }
        
        const data = await response.json();
        jobs = data.jobs || [];
        
        renderJobs();
        updateEmptyState();
    } catch (error) {
        console.error('Error loading jobs:', error);
        showToast('Failed to load monitors', 'error');
    } finally {
        showLoading(false);
    }
}

// Render jobs to the page
function renderJobs() {
    const container = document.getElementById('jobs-container');
    if (!container) return;
    
    if (jobs.length === 0) {
        container.classList.add('hidden');
        return;
    }
    
    container.classList.remove('hidden');
    container.innerHTML = jobs.map(job => createJobCard(job)).join('');
    
    // Attach event listeners to cards
    attachCardEventListeners();
}

// Create job card HTML
function createJobCard(job) {
    const lastChecked = job.last_checked 
        ? formatRelativeTime(job.last_checked) 
        : 'Never';
    
    const lastMatch = job.last_match 
        ? formatRelativeTime(job.last_match) 
        : 'Never';
    
    const statusBadge = job.is_active 
        ? '<span class="badge badge-active">Active</span>' 
        : '<span class="badge badge-inactive">Inactive</span>';
    
    const intervalText = formatInterval(job.check_interval);
    const matchTypeText = job.match_type === 'regex' ? 'Regex' : 'String';
    const conditionText = job.match_condition === 'contains' ? 'contains' : 'does not contain';
    
    return `
        <div class="card" data-job-id="${job.id}">
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(job.name)}</h3>
                <div class="card-actions">
                    <button class="btn btn-icon" onclick="runCheckNow(${job.id})" aria-label="Run Check Now" title="Run check now">
                        ▶️
                    </button>
                    <button class="btn btn-icon" onclick="editJob(${job.id})" aria-label="Edit">
                        ✏️
                    </button>
                    <button class="btn btn-icon" onclick="toggleJob(${job.id})" aria-label="Toggle">
                        ${job.is_active ? '⏸️' : '▶️'}
                    </button>
                    <button class="btn btn-icon btn-danger" onclick="deleteJob(${job.id})" aria-label="Delete">
                        🗑️
                    </button>
                </div>
            </div>
            <div class="card-body">
                <p>
                    <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer" class="url-link">
                        ${escapeHtml(job.url)}
                    </a>
                </p>
                <p class="text-secondary">
                    Checks every ${intervalText} for "${escapeHtml(job.match_pattern)}" 
                    (${matchTypeText}, ${conditionText})
                </p>
            </div>
            <div class="card-footer">
                <div>
                    <strong>Status:</strong> ${statusBadge}
                </div>
                <div>
                    <strong>Last Check:</strong> ${lastChecked}
                </div>
                <div>
                    <strong>Last Match:</strong> ${lastMatch}
                </div>
                <div>
                    <strong>Email:</strong> ${escapeHtml(job.email_recipient)}
                </div>
            </div>
            <div class="accordion">
                <div class="accordion-header" onclick="toggleHistory(${job.id})">
                    <span>Check History</span>
                    <span id="history-toggle-${job.id}">▼</span>
                </div>
                <div class="accordion-content" id="history-${job.id}">
                    <div class="loading" style="margin: 1rem auto;"></div>
                </div>
            </div>
        </div>
    `;
}

// Attach event listeners to job cards
function attachCardEventListeners() {
    // History accordion toggles are handled inline
}

// Open job modal for creating/editing
function openJobModal(jobId = null) {
    const modal = document.getElementById('job-modal');
    const modalTitle = document.getElementById('modal-title');
    const form = document.getElementById('job-form');
    
    currentJobId = jobId;
    
    if (jobId) {
        modalTitle.textContent = 'Edit Monitor';
        const job = jobs.find(j => j.id === jobId);
        if (job) {
            populateForm(job);
        }
    } else {
        modalTitle.textContent = 'Add Monitor';
        form.reset();
        resetFormToggles();
    }
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Focus first input
    setTimeout(() => {
        document.getElementById('job-name').focus();
    }, 100);
}

// Close job modal
function closeJobModal() {
    const modal = document.getElementById('job-modal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
    currentJobId = null;
    
    // Clear form errors
    clearFormErrors();
}

// Populate form with job data
function populateForm(job) {
    document.getElementById('job-id').value = job.id || '';
    document.getElementById('job-name').value = job.name || '';
    document.getElementById('job-url').value = job.url || '';
    document.getElementById('check-interval').value = job.check_interval || 300;
    document.getElementById('match-pattern').value = job.match_pattern || '';
    document.getElementById('email-recipient').value = job.email_recipient || '';
    
    // Set match type toggle
    setToggleActive('match-type', job.match_type || 'string');
    document.getElementById('match-type').value = job.match_type || 'string';
    
    // Set condition toggle
    setToggleActive('match-condition', job.match_condition || 'contains');
    document.getElementById('match-condition').value = job.match_condition || 'contains';
}

// Reset form toggles
function resetFormToggles() {
    setToggleActive('match-type', 'string');
    setToggleActive('match-condition', 'contains');
    document.getElementById('match-type').value = 'string';
    document.getElementById('match-condition').value = 'contains';
}

// Set toggle button active state
function setToggleActive(inputId, value) {
    const input = document.getElementById(inputId);
    const toggles = input.closest('.form-group').querySelectorAll('.toggle-option');
    toggles.forEach(toggle => {
        if (toggle.dataset.value === value) {
            toggle.classList.add('active');
        } else {
            toggle.classList.remove('active');
        }
    });
}

// Toggle match type
function toggleMatchType(button) {
    const toggles = button.parentElement.querySelectorAll('.toggle-option');
    toggles.forEach(t => t.classList.remove('active'));
    button.classList.add('active');
    document.getElementById('match-type').value = button.dataset.value;
    
    // Update help text
    const helpText = document.getElementById('match-type-help');
    if (button.dataset.value === 'regex') {
        helpText.textContent = 'Use regular expressions for advanced pattern matching';
    } else {
        helpText.textContent = 'Search for exact text (case-insensitive)';
    }
}

// Toggle match condition
function toggleCondition(button) {
    const toggles = button.parentElement.querySelectorAll('.toggle-option');
    toggles.forEach(t => t.classList.remove('active'));
    button.classList.add('active');
    document.getElementById('match-condition').value = button.dataset.value;
}

// Handle job form submission
async function handleJobSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Convert check_interval to integer
    data.check_interval = parseInt(data.check_interval);
    
    // Get toggle values
    data.match_type = document.getElementById('match-type').value;
    data.match_condition = document.getElementById('match-condition').value;
    
    // Clear previous errors
    clearFormErrors();
    
    // Validate form
    if (!validateForm(data)) {
        return;
    }
    
    const saveBtn = document.getElementById('save-job-btn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    try {
        const url = currentJobId 
            ? `/api/jobs/${currentJobId}` 
            : '/api/jobs';
        
        const method = currentJobId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to save job');
        }
        
        showToast(
            currentJobId ? 'Monitor updated successfully' : 'Monitor created successfully',
            'success'
        );
        
        closeJobModal();
        loadJobs();
        
    } catch (error) {
        console.error('Error saving job:', error);
        showToast(error.message || 'Failed to save monitor', 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save';
    }
}

// Validate form data
function validateForm(data) {
    let isValid = true;
    
    // Validate URL
    try {
        new URL(data.url);
    } catch {
        showFieldError('url', 'Please enter a valid URL');
        isValid = false;
    }
    
    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email_recipient)) {
        showFieldError('email', 'Please enter a valid email address');
        isValid = false;
    }
    
    // Validate regex pattern if match_type is regex
    if (data.match_type === 'regex') {
        try {
            new RegExp(data.match_pattern);
        } catch {
            showFieldError('pattern', 'Invalid regular expression pattern');
            isValid = false;
        }
    }
    
    return isValid;
}

// Show field error
function showFieldError(fieldName, message) {
    const errorElement = document.getElementById(`${fieldName}-error`);
    if (errorElement) {
        errorElement.textContent = message;
    }
}

// Clear all form errors
function clearFormErrors() {
    const errorElements = document.querySelectorAll('.form-error');
    errorElements.forEach(el => el.textContent = '');
}

// Edit job
function editJob(jobId) {
    openJobModal(jobId);
}

// Delete job
async function deleteJob(jobId) {
    const job = jobs.find(j => j.id === jobId);
    const jobName = job ? job.name : 'this monitor';
    
    if (!confirm(`Are you sure you want to delete "${jobName}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${jobId}`, {
            method: 'DELETE',
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to delete job');
        }
        
        showToast('Monitor deleted successfully', 'success');
        loadJobs();
        
    } catch (error) {
        console.error('Error deleting job:', error);
        showToast(error.message || 'Failed to delete monitor', 'error');
    }
}

// Toggle job active/inactive
async function toggleJob(jobId) {
    try {
        const response = await fetch(`/api/jobs/${jobId}/toggle`, {
            method: 'POST',
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to toggle job');
        }
        
        showToast(
            result.is_active ? 'Monitor activated' : 'Monitor deactivated',
            'success'
        );
        loadJobs();
        
    } catch (error) {
        console.error('Error toggling job:', error);
        showToast(error.message || 'Failed to toggle monitor', 'error');
    }
}

// Run check now for a specific job
async function runCheckNow(jobId) {
    const job = jobs.find(j => j.id === jobId);
    const jobName = job ? job.name : 'this monitor';
    
    if (!confirm(`Run check now for "${jobName}"? This will immediately check the website and send an email if a match is found.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${jobId}/run-check`, {
            method: 'POST',
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to run check');
        }
        
        showToast(result.message || 'Check started successfully', 'success');
        
        // Refresh jobs after a short delay to show updated last_checked time
        setTimeout(() => {
            loadJobs();
        }, 2000);
        
    } catch (error) {
        console.error('Error running check:', error);
        showToast(error.message || 'Failed to run check', 'error');
    }
}

// Toggle history accordion
async function toggleHistory(jobId) {
    const content = document.getElementById(`history-${jobId}`);
    const toggle = document.getElementById(`history-toggle-${jobId}`);
    
    if (content.classList.contains('active')) {
        content.classList.remove('active');
        toggle.textContent = '▼';
    } else {
        content.classList.add('active');
        toggle.textContent = '▲';
        
        // Load history if not already loaded
        if (content.querySelector('.loading')) {
            await loadJobHistory(jobId);
        }
    }
}

// Load job history
async function loadJobHistory(jobId) {
    const content = document.getElementById(`history-${jobId}`);
    
    try {
        const response = await fetch(`/api/jobs/${jobId}/history?limit=20`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load history');
        }
        
        const history = data.history || [];
        
        if (history.length === 0) {
            content.innerHTML = '<p class="text-muted" style="padding: 1rem;">No check history yet</p>';
        } else {
            content.innerHTML = history.map(item => createHistoryItem(item)).join('');
        }
        
    } catch (error) {
        console.error('Error loading history:', error);
        content.innerHTML = '<p class="text-muted" style="padding: 1rem;">Failed to load history</p>';
    }
}

// Create history item HTML
function createHistoryItem(item) {
    const time = formatRelativeTime(item.timestamp);
    const iconClass = item.status === 'success' ? 'success' : 'error';
    const icon = item.status === 'success' ? '✓' : '✗';
    
    return `
        <div class="history-item">
            <div class="history-icon ${iconClass}">${icon}</div>
            <div class="history-content">
                <div class="history-time">${time}</div>
                <div class="history-details">
                    Status: ${item.status} | 
                    Match: ${item.match_found ? 'Found' : 'Not Found'} | 
                    Response Time: ${item.response_time ? item.response_time.toFixed(2) + 's' : 'N/A'}
                    ${item.error_message ? `<br>Error: ${escapeHtml(item.error_message)}` : ''}
                </div>
            </div>
        </div>
    `;
}

// Show/hide loading state
function showLoading(show) {
    const loadingState = document.getElementById('loading-state');
    const jobsContainer = document.getElementById('jobs-container');
    const emptyState = document.getElementById('empty-state');
    
    if (show) {
        loadingState.classList.remove('hidden');
        jobsContainer.classList.add('hidden');
        emptyState.classList.add('hidden');
    } else {
        loadingState.classList.add('hidden');
    }
}

// Update empty state visibility
function updateEmptyState() {
    const emptyState = document.getElementById('empty-state');
    const jobsContainer = document.getElementById('jobs-container');
    
    if (jobs.length === 0) {
        emptyState.classList.remove('hidden');
        jobsContainer.classList.add('hidden');
    } else {
        emptyState.classList.add('hidden');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'toast-slide-in 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format relative time
function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Never';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
}

// Format interval
function formatInterval(seconds) {
    if (seconds < 60) return `${seconds} seconds`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes`;
    return `${Math.floor(seconds / 3600)} hour${Math.floor(seconds / 3600) > 1 ? 's' : ''}`;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start auto-refresh
function startAutoRefresh() {
    // Refresh every 30 seconds
    refreshInterval = setInterval(() => {
        loadJobs();
    }, 30000);
}

// Handle keyboard shortcuts
function handleKeyboardShortcuts(e) {
    // 'N' key to create new monitor (when not in input)
    if (e.key === 'n' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        openJobModal();
    }
}

// Test email functionality
async function testEmail() {
    const testEmailBtn = document.getElementById('test-email-btn');
    const originalText = testEmailBtn.textContent;
    
    // Prompt for email address
    const email = prompt('Enter email address to send test email to (or leave blank to use configured SMTP_USERNAME):');
    
    if (email === null) {
        return; // User cancelled
    }
    
    testEmailBtn.disabled = true;
    testEmailBtn.textContent = 'Sending...';
    
    try {
        const response = await fetch('/api/test-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: email || undefined }),
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast(result.message || 'Test email sent successfully!', 'success');
        } else {
            showToast(result.error || 'Failed to send test email', 'error');
        }
        
    } catch (error) {
        console.error('Error sending test email:', error);
        showToast('Error sending test email: ' + error.message, 'error');
    } finally {
        testEmailBtn.disabled = false;
        testEmailBtn.textContent = originalText;
    }
}

// Make functions globally available
window.openJobModal = openJobModal;
window.closeJobModal = closeJobModal;
window.editJob = editJob;
window.deleteJob = deleteJob;
window.toggleJob = toggleJob;
window.runCheckNow = runCheckNow;
window.toggleHistory = toggleHistory;
window.toggleMatchType = toggleMatchType;
window.toggleCondition = toggleCondition;
window.testEmail = testEmail;
