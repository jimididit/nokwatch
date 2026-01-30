// Website Monitor Application JavaScript

// Lightweight inline SVG icons (24x24 viewBox, stroke-based)
const Icons = {
    play: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
    pause: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>',
    pencil: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>',
    trash: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>',
    check: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    x: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    chevronDown: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
    chevronUp: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>',
    mail: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>',
    search: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    export: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>',
    import: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>'
};

// State management
let jobs = [];
let currentJobId = null;
let refreshInterval = null;
let monitorTemplates = [];
let wizardSuggestions = null;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// Initialize application
function initializeApp() {
    setupEventListeners();
    injectHeaderIcons();
    loadJobs();
    loadStatistics();
    loadTemplates();
    startAutoRefresh();
    
    // Keyboard shortcuts (desktop only)
    if (window.innerWidth >= 768) {
        document.addEventListener('keydown', handleKeyboardShortcuts);
    }
}

// Replace header/empty-state emojis with SVG icons; add icons to mobile nav items
function injectHeaderIcons() {
    const testEmailBtn = document.getElementById('test-email-btn');
    if (testEmailBtn) {
        testEmailBtn.innerHTML = '<span class="btn-icon-inline">' + Icons.mail + '</span> Test Email';
    }
    const emptyIcon = document.querySelector('.empty-state-icon');
    if (emptyIcon) {
        emptyIcon.innerHTML = Icons.search;
        emptyIcon.classList.add('empty-state-icon-svg');
    }
    // Mobile nav: Export, Import, Test Email with icons
    const mobileExport = document.getElementById('mobile-export-btn');
    const mobileImport = document.getElementById('mobile-import-btn');
    const mobileTestEmail = document.getElementById('mobile-test-email-btn');
    if (mobileExport) mobileExport.innerHTML = '<span class="mobile-nav-item-icon">' + Icons.export + '</span> Export';
    if (mobileImport) mobileImport.innerHTML = '<span class="mobile-nav-item-icon">' + Icons.import + '</span> Import';
    if (mobileTestEmail) mobileTestEmail.innerHTML = '<span class="mobile-nav-item-icon">' + Icons.mail + '</span> Test Email';
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
    
    // Close modals on overlay click
    const jobModal = document.getElementById('job-modal');
    if (jobModal) {
        jobModal.addEventListener('click', (e) => {
            if (e.target === jobModal) closeJobModal();
        });
    }
    const wizardModal = document.getElementById('wizard-modal');
    if (wizardModal) {
        wizardModal.addEventListener('click', (e) => {
            if (e.target === wizardModal) closeWizardModal();
        });
    }
    const historyModal = document.getElementById('history-modal');
    if (historyModal) {
        historyModal.addEventListener('click', (e) => {
            if (e.target === historyModal) closeHistoryModal();
        });
    }
    
    // Close modal / lightbox / mobile nav on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (document.getElementById('lightbox')?.classList.contains('active')) {
                closeLightbox();
            } else if (document.getElementById('history-modal')?.classList.contains('active')) {
                closeHistoryModal();
            } else if (document.getElementById('mobile-nav')?.classList.contains('open')) {
                closeMobileNav();
            } else if (document.getElementById('wizard-modal')?.classList.contains('active')) {
                closeWizardModal();
            } else {
                closeJobModal();
            }
        }
    });
    
    // Stats period change
    const statsPeriod = document.getElementById('stats-period');
    if (statsPeriod) {
        statsPeriod.addEventListener('change', () => loadStatistics());
    }
    
    // Tag filter change
    const tagFilter = document.getElementById('tag-filter');
    if (tagFilter) {
        tagFilter.addEventListener('change', onTagFilterChange);
    }
    
    // Lightbox: View larger for diff / screenshot (delegated; works in history modal or elsewhere)
    document.addEventListener('click', (e) => {
        if (e.target.closest('.view-large-diff')) {
            const btn = e.target.closest('.view-large-diff');
            const block = btn.closest('.history-modal-block') || btn.closest('details');
            const pre = block ? block.querySelector('.history-diff-content pre, .history-modal-diff pre') : null;
            const content = pre ? pre.innerHTML : '';
            openLightbox('diff', content);
        } else if (e.target.closest('.view-large-screenshot')) {
            const btn = e.target.closest('.view-large-screenshot');
            const src = btn.getAttribute('data-screenshot-src') || '';
            if (src) openLightbox('screenshot', src);
        }
    });
    
    // Export / Import
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) exportBtn.addEventListener('click', exportConfig);
    const importBtn = document.getElementById('import-btn');
    if (importBtn) importBtn.addEventListener('click', () => document.getElementById('import-file-input')?.click());
    const importInput = document.getElementById('import-file-input');
    if (importInput) importInput.addEventListener('change', handleImportFile);
    
    // Mobile nav
    const menuBtn = document.getElementById('header-menu-btn');
    if (menuBtn) menuBtn.addEventListener('click', openMobileNav);

    // Template selector: prefill form when a template is selected
    const templateSelect = document.getElementById('template-select');
    if (templateSelect) {
        templateSelect.addEventListener('change', () => applyTemplateToForm(templateSelect.value));
    }
}

function openMobileNav() {
    const nav = document.getElementById('mobile-nav');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    const menuBtn = document.getElementById('header-menu-btn');
    if (nav && backdrop) {
        nav.classList.add('open');
        nav.setAttribute('aria-hidden', 'false');
        backdrop.classList.add('open');
        backdrop.setAttribute('aria-hidden', 'false');
        if (menuBtn) menuBtn.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
    }
}

function closeMobileNav() {
    const nav = document.getElementById('mobile-nav');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    const menuBtn = document.getElementById('header-menu-btn');
    if (nav && backdrop) {
        nav.classList.remove('open');
        nav.setAttribute('aria-hidden', 'true');
        backdrop.classList.remove('open');
        backdrop.setAttribute('aria-hidden', 'true');
        if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }
}

// Smart Setup wizard
function openWizardModal() {
    wizardSuggestions = null;
    const modal = document.getElementById('wizard-modal');
    const urlInput = document.getElementById('wizard-url');
    const errorEl = document.getElementById('wizard-error');
    const resultsEl = document.getElementById('wizard-results');
    const useBtn = document.getElementById('wizard-use-btn');
    const analyzeBtn = document.getElementById('wizard-analyze-btn');
    if (modal) modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    if (urlInput) urlInput.value = '';
    if (errorEl) { errorEl.classList.add('hidden'); errorEl.textContent = ''; }
    if (resultsEl) resultsEl.classList.add('hidden');
    if (useBtn) useBtn.classList.add('hidden');
    if (analyzeBtn) analyzeBtn.classList.remove('hidden');
    setTimeout(() => urlInput?.focus(), 100);
}

function closeWizardModal() {
    const modal = document.getElementById('wizard-modal');
    if (modal) modal.classList.remove('active');
    document.body.style.overflow = '';
    wizardSuggestions = null;
}

async function runWizardAnalyze() {
    const urlInput = document.getElementById('wizard-url');
    const errorEl = document.getElementById('wizard-error');
    const resultsEl = document.getElementById('wizard-results');
    const suggestionsText = document.getElementById('wizard-suggestions-text');
    const useBtn = document.getElementById('wizard-use-btn');
    const analyzeBtn = document.getElementById('wizard-analyze-btn');
    const url = urlInput?.value?.trim();
    if (!url) {
        if (errorEl) { errorEl.textContent = 'Please enter a URL'; errorEl.classList.remove('hidden'); }
        return;
    }
    if (errorEl) { errorEl.classList.add('hidden'); errorEl.textContent = ''; }
    if (analyzeBtn) { analyzeBtn.disabled = true; analyzeBtn.textContent = 'Analyzing...'; }
    try {
        const response = await fetch('/api/wizard/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }
        wizardSuggestions = data.suggestions || {};
        if (suggestionsText) {
            const s = wizardSuggestions;
            const interval = s.check_interval === 3600 ? '1 hour' : s.check_interval === 300 ? '5 min' : (s.check_interval / 60) + ' min';
            suggestionsText.innerHTML = `
                <p><strong>Name:</strong> ${escapeHtml(s.name || '—')}</p>
                <p><strong>URL:</strong> ${escapeHtml(s.url || url)}</p>
                <p><strong>Pattern:</strong> ${escapeHtml(s.match_pattern || '—')} (${s.match_condition || 'contains'})</p>
                <p><strong>Check interval:</strong> ${interval}</p>
            `;
        }
        if (resultsEl) resultsEl.classList.remove('hidden');
        if (useBtn) useBtn.classList.remove('hidden');
        if (analyzeBtn) analyzeBtn.classList.add('hidden');
    } catch (e) {
        if (errorEl) { errorEl.textContent = e.message || 'Analysis failed'; errorEl.classList.remove('hidden'); }
    } finally {
        if (analyzeBtn) { analyzeBtn.disabled = false; analyzeBtn.textContent = 'Analyze'; }
    }
}

function applyWizardAndOpenForm() {
    if (!wizardSuggestions) return;
    closeWizardModal();
    currentJobId = null;
    openJobModal();
    document.getElementById('job-name').value = wizardSuggestions.name || '';
    document.getElementById('job-url').value = wizardSuggestions.url || '';
    document.getElementById('check-interval').value = String(wizardSuggestions.check_interval || 3600);
    document.getElementById('match-pattern').value = wizardSuggestions.match_pattern || '';
    setToggleActive('match-condition', wizardSuggestions.match_condition || 'contains');
    document.getElementById('match-condition').value = wizardSuggestions.match_condition || 'contains';
    document.getElementById('template-select').value = '';
    document.getElementById('template-description').textContent = '';
}

// Load monitor templates and populate dropdown
async function loadTemplates() {
    const select = document.getElementById('template-select');
    if (!select) return;
    try {
        const response = await fetch('/api/templates');
        if (!response.ok) return;
        const data = await response.json();
        monitorTemplates = data.templates || [];
        const currentValue = select.value;
        select.innerHTML = '<option value="">None — configure from scratch</option>' +
            monitorTemplates.map(t => `<option value="${escapeHtml(t.id)}">${escapeHtml(t.name)}</option>`).join('');
        if (monitorTemplates.some(t => t.id === currentValue)) select.value = currentValue;
    } catch (e) {
        console.error('Failed to load templates', e);
    }
}

// Apply selected template defaults to the job form (only when adding, not editing)
function applyTemplateToForm(templateId) {
    const descEl = document.getElementById('template-description');
    if (descEl) descEl.textContent = '';
    const patternInput = document.getElementById('match-pattern');
    if (!templateId || currentJobId !== null) {
        if (patternInput) patternInput.placeholder = 'e.g., Waitlist Open';
        return;
    }
    const t = monitorTemplates.find(tpl => tpl.id === templateId);
    if (!t) return;
    if (descEl) descEl.textContent = t.description || '';
    if (t.check_interval != null) {
        const el = document.getElementById('check-interval');
        if (el) el.value = String(t.check_interval);
    }
    if (t.match_type) {
        setToggleActive('match-type', t.match_type);
        const input = document.getElementById('match-type');
        if (input) input.value = t.match_type;
    }
    if (t.match_condition) {
        setToggleActive('match-condition', t.match_condition);
        const input = document.getElementById('match-condition');
        if (input) input.value = t.match_condition;
    }
    if (t.match_pattern != null) {
        const el = document.getElementById('match-pattern');
        if (el) el.value = t.match_pattern;
    }
    if (t.match_pattern_placeholder != null) {
        const el = document.getElementById('match-pattern');
        if (el) el.placeholder = t.match_pattern_placeholder;
    }
    if (t.notification_throttle_seconds != null) {
        const el = document.getElementById('notification-throttle');
        if (el) el.value = String(t.notification_throttle_seconds);
    }
}

// Export configuration as JSON file
async function exportConfig() {
    try {
        const response = await fetch('/api/export');
        if (!response.ok) throw new Error('Export failed');
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `nokwatch-export-${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        URL.revokeObjectURL(a.href);
        showToast('Configuration exported', 'success');
    } catch (e) {
        console.error('Export error:', e);
        showToast('Export failed', 'error');
    }
}

// Import configuration from JSON file
function handleImportFile(e) {
    const input = e.target;
    const file = input.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (ev) => {
        try {
            const data = JSON.parse(ev.target?.result || '{}');
            const response = await fetch('/api/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            if (response.ok) {
                showToast(result.message || `Imported ${result.created} job(s)`, result.errors?.length ? 'info' : 'success');
                loadJobs();
                loadStatistics();
            } else {
                showToast(result.error || 'Import failed', 'error');
            }
        } catch (err) {
            console.error('Import error:', err);
            showToast('Invalid file or import failed', 'error');
        }
        input.value = '';
    };
    reader.readAsText(file);
}

// Load and render statistics
async function loadStatistics() {
    const periodEl = document.getElementById('stats-period');
    const hours = periodEl ? parseInt(periodEl.value, 10) || 24 : 24;
    try {
        const response = await fetch(`/api/statistics?hours=${hours}`);
        if (!response.ok) return;
        const data = await response.json();
        const g = data.global || {};
        document.getElementById('stat-total-checks').textContent = g.total_checks ?? '—';
        document.getElementById('stat-success-rate').textContent = g.success_rate_pct != null ? g.success_rate_pct + '%' : '—';
        document.getElementById('stat-matches').textContent = g.match_count ?? '—';
        document.getElementById('stat-avg-response').textContent =
            g.avg_response_time_seconds != null ? g.avg_response_time_seconds + 's' : '—';
        const overTime = data.checks_over_time || [];
        renderStatsChart(overTime);
    } catch (e) {
        console.error('Error loading statistics:', e);
    }
}

// Populate tag filter dropdown and show/hide row
async function updateTagFilter(selectedTag) {
    const row = document.getElementById('tag-filter-row');
    const select = document.getElementById('tag-filter');
    if (!row || !select) return;
    try {
        const response = await fetch('/api/tags');
        if (!response.ok) return;
        const data = await response.json();
        const tags = data.tags || [];
        const currentValue = select.value;
        select.innerHTML = '<option value="">All monitors</option>' +
            tags.map(t => `<option value="${escapeHtml(t.name)}">${escapeHtml(t.name)}</option>`).join('');
        if (selectedTag !== undefined) {
            select.value = selectedTag || '';
        } else if (tags.some(t => t.name === currentValue)) {
            select.value = currentValue;
        }
        row.classList.toggle('hidden', tags.length === 0);
    } catch (e) {
        row.classList.add('hidden');
    }
}

function onTagFilterChange() {
    const value = document.getElementById('tag-filter')?.value?.trim() || '';
    loadJobs(value || undefined);
}

function renderStatsChart(overTime) {
    const container = document.getElementById('stats-chart');
    if (!container) return;
    if (!overTime.length) {
        container.innerHTML = '<p class="text-muted" style="margin:0;font-size:0.875rem;">No data for this period</p>';
        return;
    }
    const maxTotal = Math.max(...overTime.map(d => d.total || 0), 1);
    container.innerHTML = overTime.map(d => {
        const pct = Math.round((100 * (d.total || 0)) / maxTotal);
        const label = d.period_start ? d.period_start.replace('T', ' ').slice(0, 16) : '';
        return `<div class="stats-chart-bar" style="height:${Math.max(pct, 4)}%" title="${escapeHtml(label)}: ${d.total} checks" role="img" aria-label="${d.total} checks"></div>`;
    }).join('');
}

// Load all jobs from API (optional tag filter)
async function loadJobs(tagFilterOrUndefined) {
    const tagFilter = tagFilterOrUndefined !== undefined
        ? tagFilterOrUndefined
        : (document.getElementById('tag-filter')?.value || '').trim() || undefined;
    try {
        showLoading(true);
        const url = tagFilter ? `/api/jobs?tag=${encodeURIComponent(tagFilter)}` : '/api/jobs';
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Failed to load jobs');
        }
        
        const data = await response.json();
        jobs = data.jobs || [];
        
        renderJobs();
        updateEmptyState();
        updateTagFilter(tagFilter);
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
    const modeText = job.json_path ? 'JSON' : 'HTML';
    
    return `
        <div class="card" data-job-id="${job.id}">
            <div class="card-header">
                <h3 class="card-title">${escapeHtml(job.name)}</h3>
                <div class="card-actions">
                    <button class="btn btn-icon" onclick="runCheckNow(${job.id})" aria-label="Run Check Now" title="Run check now">
                        ${Icons.play}
                    </button>
                    <button class="btn btn-icon" onclick="editJob(${job.id})" aria-label="Edit">
                        ${Icons.pencil}
                    </button>
                    <button class="btn btn-icon" onclick="toggleJob(${job.id})" aria-label="Toggle">
                        ${job.is_active ? Icons.pause : Icons.play}
                    </button>
                    <button class="btn btn-icon btn-danger" onclick="deleteJob(${job.id})" aria-label="Delete">
                        ${Icons.trash}
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
                    (${matchTypeText}, ${conditionText}) · ${modeText}
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
                ${(job.tags || []).length ? `
                <div class="card-tags">
                    ${(job.tags || []).map(t => `<span class="card-tag">${escapeHtml(t)}</span>`).join('')}
                </div>
                ` : ''}
                <div class="card-footer-history">
                    <button type="button" class="btn btn-secondary btn-sm" onclick="openHistoryModal(${job.id})">Check History</button>
                </div>
            </div>
        </div>
    `;
}

// Attach event listeners to job cards
function attachCardEventListeners() {
    // Check History opens modal via openHistoryModal(jobId)
}

// Open job modal for creating/editing
function openJobModal(jobId = null) {
    const modal = document.getElementById('job-modal');
    const modalTitle = document.getElementById('modal-title');
    const form = document.getElementById('job-form');
    
    currentJobId = jobId;
    
    const templateSelect = document.getElementById('template-select');
    const templateDesc = document.getElementById('template-description');
    if (templateSelect) templateSelect.value = '';
    if (templateDesc) templateDesc.textContent = '';

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
        if (templateSelect) templateSelect.value = '';
        if (templateDesc) templateDesc.textContent = '';
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
    
    // Set advanced fields
    document.getElementById('notification-throttle').value = job.notification_throttle_seconds || 1800;
    document.getElementById('status-code-monitor').value = job.status_code_monitor || '';
    document.getElementById('response-time-threshold').value = job.response_time_threshold || '';
    document.getElementById('json-path').value = job.json_path || '';
    document.getElementById('job-tags').value = (job.tags || []).join(', ');
    document.getElementById('proxy-url').value = job.proxy_url || '';
    document.getElementById('custom-user-agent').value = job.custom_user_agent || '';
    document.getElementById('capture-screenshot').checked = !!job.capture_screenshot;
    
    // Auth config
    loadAuthConfig(job.auth_config || null);
    
    // Set match type toggle
    setToggleActive('match-type', job.match_type || 'string');
    document.getElementById('match-type').value = job.match_type || 'string';
    
    // Set condition toggle
    setToggleActive('match-condition', job.match_condition || 'contains');
    document.getElementById('match-condition').value = job.match_condition || 'contains';
    
    // Load notification channels
    loadNotificationChannels(job.notification_channels || []);
}

// Reset form toggles
function resetFormToggles() {
    setToggleActive('match-type', 'string');
    setToggleActive('match-condition', 'contains');
    document.getElementById('match-type').value = 'string';
    document.getElementById('match-condition').value = 'contains';
    
    // Reset advanced fields
    document.getElementById('notification-throttle').value = 1800;
    document.getElementById('status-code-monitor').value = '';
    document.getElementById('response-time-threshold').value = '';
    document.getElementById('json-path').value = '';
    document.getElementById('job-tags').value = '';
    document.getElementById('proxy-url').value = '';
    document.getElementById('custom-user-agent').value = '';
    document.getElementById('capture-screenshot').checked = false;
    document.getElementById('ai-enabled').checked = false;
    document.getElementById('ai-prompt').value = '';

    // Clear auth
    document.getElementById('auth-basic-username').value = '';
    document.getElementById('auth-basic-password').value = '';
    document.getElementById('auth-headers-container').innerHTML = '';
    document.getElementById('auth-cookies-container').innerHTML = '';
    
    // Clear notification channels
    document.getElementById('notification-channels-container').innerHTML = '';
}

// Auth config helpers
function loadAuthConfig(authConfig) {
    document.getElementById('auth-basic-username').value = '';
    document.getElementById('auth-basic-password').value = '';
    document.getElementById('auth-headers-container').innerHTML = '';
    document.getElementById('auth-cookies-container').innerHTML = '';
    if (!authConfig) return;
    if (authConfig.basic) {
        document.getElementById('auth-basic-username').value = authConfig.basic.username || '';
        document.getElementById('auth-basic-password').value = authConfig.basic.password || '';
    }
    if (authConfig.headers && typeof authConfig.headers === 'object') {
        const entries = Array.isArray(authConfig.headers)
            ? authConfig.headers.map(h => [h.name, h.value])
            : Object.entries(authConfig.headers);
        entries.forEach(([name, value]) => addAuthHeaderRow(name, value));
    }
    if (authConfig.cookies && typeof authConfig.cookies === 'object') {
        const entries = Object.entries(authConfig.cookies);
        entries.forEach(([name, value]) => addAuthCookieRow(name, value));
    }
}

function addAuthHeader() {
    addAuthHeaderRow('', '');
}

function addAuthHeaderRow(name, value) {
    const container = document.getElementById('auth-headers-container');
    const id = 'auth-header-' + Date.now();
    const row = document.createElement('div');
    row.className = 'auth-header-row';
    row.innerHTML = `
        <input type="text" class="form-input" placeholder="Header name" value="${escapeHtml(name)}" data-auth-name>
        <input type="text" class="form-input" placeholder="Value" value="${escapeHtml(value)}" data-auth-value>
        <button type="button" class="btn btn-icon btn-sm" onclick="this.closest('.auth-header-row').remove()" aria-label="Remove">${Icons.x}</button>
    `;
    container.appendChild(row);
}

function addAuthCookie() {
    addAuthCookieRow('', '');
}

function addAuthCookieRow(name, value) {
    const container = document.getElementById('auth-cookies-container');
    const row = document.createElement('div');
    row.className = 'auth-cookie-row';
    row.innerHTML = `
        <input type="text" class="form-input" placeholder="Name" value="${escapeHtml(name)}" data-cookie-name>
        <input type="text" class="form-input" placeholder="Value" value="${escapeHtml(value)}" data-cookie-value>
        <button type="button" class="btn btn-icon btn-sm" onclick="this.closest('.auth-cookie-row').remove()" aria-label="Remove">${Icons.x}</button>
    `;
    container.appendChild(row);
}

function getAuthConfigFromForm() {
    const username = document.getElementById('auth-basic-username').value.trim();
    const password = document.getElementById('auth-basic-password').value;
    const authConfig = {};
    if (username) {
        authConfig.basic = { username, password: password || '' };
    }
    const headerRows = document.querySelectorAll('#auth-headers-container .auth-header-row');
    const headers = {};
    headerRows.forEach(row => {
        const name = (row.querySelector('[data-auth-name]') || {}).value?.trim();
        const value = (row.querySelector('[data-auth-value]') || {}).value;
        if (name) headers[name] = value || '';
    });
    if (Object.keys(headers).length) authConfig.headers = headers;
    const cookieRows = document.querySelectorAll('#auth-cookies-container .auth-cookie-row');
    const cookies = {};
    cookieRows.forEach(row => {
        const name = (row.querySelector('[data-cookie-name]') || {}).value?.trim();
        const value = (row.querySelector('[data-cookie-value]') || {}).value;
        if (name) cookies[name] = value || '';
    });
    if (Object.keys(cookies).length) authConfig.cookies = cookies;
    if (!authConfig.basic && !authConfig.headers && !authConfig.cookies) return null;
    return authConfig;
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
    
    // Get advanced fields (always send throttle so "No cooldown" = 0 is saved)
    const throttleEl = document.getElementById('notification-throttle');
    if (throttleEl) {
        data.notification_throttle_seconds = parseInt(throttleEl.value, 10);
    }
    
    const statusCodeMonitor = document.getElementById('status-code-monitor').value;
    if (statusCodeMonitor) {
        data.status_code_monitor = parseInt(statusCodeMonitor);
    } else {
        data.status_code_monitor = null;
    }
    
    const responseTimeThreshold = document.getElementById('response-time-threshold').value;
    if (responseTimeThreshold) {
        data.response_time_threshold = parseFloat(responseTimeThreshold);
    } else {
        data.response_time_threshold = null;
    }
    
    const jsonPath = document.getElementById('json-path').value;
    if (jsonPath && jsonPath.trim()) {
        data.json_path = jsonPath.trim();
    } else {
        data.json_path = null;
    }
    
    const tagsInput = document.getElementById('job-tags').value;
    const tags = tagsInput ? tagsInput.split(',').map(s => s.trim()).filter(Boolean) : [];
    if (tags.length) data.tags = tags;
    
    const proxyUrl = document.getElementById('proxy-url').value?.trim();
    if (proxyUrl) data.proxy_url = proxyUrl;
    const customUserAgent = document.getElementById('custom-user-agent').value?.trim();
    if (customUserAgent) data.custom_user_agent = customUserAgent;
    data.capture_screenshot = document.getElementById('capture-screenshot').checked;
    data.ai_enabled = document.getElementById('ai-enabled').checked;
    const aiPrompt = document.getElementById('ai-prompt').value?.trim();
    data.ai_prompt = aiPrompt || null;

    const authConfig = getAuthConfigFromForm();
    if (authConfig) {
        data.auth_config = authConfig;
    }
    
    // Get notification channels
    const channels = getNotificationChannelsFromForm();
    if (channels.length > 0) {
        data.notification_channels = channels;
    }
    
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

// Open history modal for a job
async function openHistoryModal(jobId) {
    const job = jobs.find(j => j.id === jobId);
    const modal = document.getElementById('history-modal');
    const titleEl = document.getElementById('history-modal-title');
    const bodyEl = document.getElementById('history-modal-body');
    if (!modal || !titleEl || !bodyEl) return;
    titleEl.textContent = job ? `Check History — ${escapeHtml(job.name)}` : 'Check History';
    bodyEl.innerHTML = '<div class="loading" style="margin: 2rem auto;"></div>';
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    try {
        const response = await fetch(`/api/jobs/${jobId}/history?limit=50`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Failed to load history');
        const history = data.history || [];
        if (history.length === 0) {
            bodyEl.innerHTML = '<p class="text-muted history-modal-empty">No check history yet</p>';
        } else {
            bodyEl.innerHTML = history.map(item => createHistoryItemForModal(item)).join('');
        }
    } catch (error) {
        console.error('Error loading history:', error);
        bodyEl.innerHTML = '<p class="text-muted history-modal-empty">Failed to load history</p>';
    }
}

function closeHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Create history item HTML for modal (richer details, larger thumbnails)
function createHistoryItemForModal(item) {
    const timeRel = formatRelativeTime(item.timestamp);
    const timeFull = formatFullTimestamp(item.timestamp);
    const iconClass = item.status === 'success' ? 'success' : 'error';
    const iconSvg = item.status === 'success' ? Icons.check : Icons.x;
    const hasDiff = item.has_diff && item.diff_data;
    const diffId = hasDiff ? `diff-${item.id}` : '';
    const diffHtml = hasDiff ? renderDiffPreview(item.diff_data) : '';
    const matchBadge = item.match_found ? 'badge-match' : 'badge-no-match';
    const statusBadge = item.status === 'success' ? 'badge-active' : 'badge-error';

    return `
        <div class="history-modal-item" data-history-id="${item.id}">
            <div class="history-modal-item-header">
                <div class="history-icon ${iconClass}">${iconSvg}</div>
                <div class="history-modal-meta">
                    <div class="history-modal-time" title="${escapeHtml(timeFull)}">${timeRel}</div>
                    <div class="history-modal-time-full">${escapeHtml(timeFull)}</div>
                    <div class="history-modal-badges">
                        <span class="badge ${statusBadge}">${item.status}</span>
                        <span class="badge ${matchBadge}">${item.match_found ? 'Match' : 'No match'}</span>
                        ${item.http_status_code != null ? `<span class="badge">HTTP ${item.http_status_code}</span>` : ''}
                        ${item.response_time != null ? `<span class="badge">${item.response_time.toFixed(2)}s</span>` : ''}
                    </div>
                    ${item.error_message ? `<div class="history-modal-error">${escapeHtml(item.error_message)}</div>` : ''}
                </div>
            </div>
            <div class="history-modal-item-body">
                ${hasDiff ? `
                <div class="history-modal-block">
                    <div class="history-modal-block-label">Content diff</div>
                    <div class="history-diff-content history-modal-diff" id="${diffId}">${diffHtml}</div>
                    <button type="button" class="btn btn-secondary btn-sm view-large-diff">View larger</button>
                </div>
                ` : ''}
                ${item.screenshot_path ? `
                <div class="history-modal-block">
                    <div class="history-modal-block-label">Screenshot</div>
                    <div class="history-screenshot">
                        <img src="/static/${escapeHtml(item.screenshot_path)}" alt="Screenshot" class="history-modal-screenshot-img" loading="lazy">
                        <button type="button" class="btn btn-secondary btn-sm view-large-screenshot mt-sm" data-screenshot-src="/static/${escapeHtml(item.screenshot_path)}">View larger</button>
                    </div>
                </div>
                ` : ''}
                ${!hasDiff && !item.screenshot_path ? '<div class="history-modal-no-attachments text-muted">No diff or screenshot for this check.</div>' : ''}
            </div>
        </div>
    `;
}

function formatFullTimestamp(timestamp) {
    if (!timestamp) return '—';
    let normalized = timestamp;
    if (typeof timestamp === 'string' && /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(timestamp) && !timestamp.includes('T')) {
        normalized = timestamp.replace(' ', 'T');
    }
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return timestamp;
    return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'medium' });
}

// Lightbox: show diff or screenshot in larger view
function openLightbox(type, content) {
    const lb = document.getElementById('lightbox');
    const lbContent = document.getElementById('lightbox-content');
    if (!lb || !lbContent) return;
    lbContent.innerHTML = '';
    if (type === 'diff') {
        lbContent.className = 'lightbox-content lightbox-content-diff';
        const pre = document.createElement('pre');
        pre.className = 'diff-preview';
        pre.innerHTML = content;
        lbContent.appendChild(pre);
    } else if (type === 'screenshot') {
        lbContent.className = 'lightbox-content lightbox-content-image';
        const img = document.createElement('img');
        img.src = content;
        img.alt = 'Screenshot';
        img.className = 'lightbox-image';
        lbContent.appendChild(img);
    }
    lb.classList.add('active');
    lb.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
}

function closeLightbox() {
    const lb = document.getElementById('lightbox');
    if (!lb) return;
    lb.classList.remove('active');
    lb.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
}

// Render unified diff as HTML with line coloring
function renderDiffPreview(diffData) {
    if (!diffData || !diffData.trim()) return '';
    const lines = diffData.split('\n');
    const escaped = lines.map(line => {
        const safe = escapeHtml(line);
        if (safe.startsWith('+') && !safe.startsWith('+++')) return '<span class="diff-add">' + safe + '</span>';
        if (safe.startsWith('-') && !safe.startsWith('---')) return '<span class="diff-remove">' + safe + '</span>';
        return '<span class="diff-context">' + safe + '</span>';
    }).join('\n');
    return '<pre class="diff-preview">' + escaped + '</pre>';
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
    
    // Normalize SQLite "YYYY-MM-DD HH:MM:SS" to ISO-like "YYYY-MM-DDTHH:MM:SS" for consistent parsing
    let normalized = timestamp;
    if (typeof timestamp === 'string' && /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(timestamp) && !timestamp.includes('T')) {
        normalized = timestamp.replace(' ', 'T');
    }
    
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return timestamp;
    
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    // Date in future or invalid diff: show absolute date/time
    if (diffMs < 0) return date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });
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

// Start auto-refresh (polls /api/jobs so "Last Check" and status stay updated)
function startAutoRefresh() {
    // Refresh every 2 minutes; increase 120000 for less frequent, or set to 0 to disable
    const intervalMs = 120000;
    if (intervalMs > 0) {
        refreshInterval = setInterval(() => {
            loadJobs();
            loadStatistics();
        }, intervalMs);
    }
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

// Notification channel management
let notificationChannelCounter = 0;

function loadNotificationChannels(channels) {
    const container = document.getElementById('notification-channels-container');
    if (!container) return;
    
    container.innerHTML = '';
    notificationChannelCounter = 0;
    
    channels.forEach(channel => {
        addNotificationChannelUI(channel.channel_type, channel.config, channel.id);
    });
}

function addNotificationChannel() {
    // Show channel type selector
    const channelType = prompt('Select channel type:\n1. email\n2. discord\n3. slack\n\nEnter 1, 2, or 3:');
    
    if (!channelType) return;
    
    let type;
    if (channelType === '1' || channelType.toLowerCase() === 'email') {
        type = 'email';
    } else if (channelType === '2' || channelType.toLowerCase() === 'discord') {
        type = 'discord';
    } else if (channelType === '3' || channelType.toLowerCase() === 'slack') {
        type = 'slack';
    } else {
        showToast('Invalid channel type', 'error');
        return;
    }
    
    addNotificationChannelUI(type);
}

function addNotificationChannelUI(channelType, config = null, channelId = null) {
    const container = document.getElementById('notification-channels-container');
    if (!container) return;
    
    const channelIdAttr = channelId || `new_${notificationChannelCounter++}`;
    const channelDiv = document.createElement('div');
    channelDiv.className = 'notification-channel-item';
    channelDiv.dataset.channelId = channelIdAttr;
    channelDiv.dataset.channelType = channelType;
    
    let configHtml = '';
    if (channelType === 'email') {
        const emails = config?.email_addresses || (config?.email_addresses ? [config.email_addresses] : []);
        const emailList = Array.isArray(emails) ? emails.join(', ') : emails;
        configHtml = `
            <label class="form-label">Email Addresses (comma-separated)</label>
            <input type="text" class="form-input channel-config" 
                   data-config-key="email_addresses" 
                   value="${escapeHtml(emailList)}" 
                   placeholder="email1@example.com, email2@example.com">
        `;
    } else if (channelType === 'discord') {
        configHtml = `
            <label class="form-label">Discord Webhook URL</label>
            <input type="url" class="form-input channel-config" 
                   data-config-key="webhook_url" 
                   value="${config?.webhook_url || ''}" 
                   placeholder="https://discord.com/api/webhooks/...">
        `;
    } else if (channelType === 'slack') {
        configHtml = `
            <label class="form-label">Slack Webhook URL</label>
            <input type="url" class="form-input channel-config" 
                   data-config-key="webhook_url" 
                   value="${config?.webhook_url || ''}" 
                   placeholder="https://hooks.slack.com/services/...">
        `;
    }
    
    channelDiv.innerHTML = `
        <div class="notification-channel-header">
            <span class="channel-type-badge">${channelType.toUpperCase()}</span>
            <button type="button" class="btn btn-sm btn-danger" onclick="removeNotificationChannelUI(this)">
                Remove
            </button>
        </div>
        ${configHtml}
    `;
    
    container.appendChild(channelDiv);
}

function removeNotificationChannelUI(button) {
    const channelDiv = button.closest('.notification-channel-item');
    if (channelDiv) {
        channelDiv.remove();
    }
}

function getNotificationChannelsFromForm() {
    const container = document.getElementById('notification-channels-container');
    if (!container) return [];
    
    const channels = [];
    const channelItems = container.querySelectorAll('.notification-channel-item');
    
    channelItems.forEach(item => {
        const channelType = item.dataset.channelType;
        const config = {};
        
        const configInputs = item.querySelectorAll('.channel-config');
        configInputs.forEach(input => {
            const key = input.dataset.configKey;
            const value = input.value.trim();
            
            if (key === 'email_addresses') {
                // Split comma-separated emails and clean them
                config[key] = value.split(',').map(e => e.trim()).filter(e => e);
            } else {
                config[key] = value;
            }
        });
        
        // Only add if config has required values
        if (channelType === 'email' && config.email_addresses && config.email_addresses.length > 0) {
            channels.push({ channel_type: channelType, config });
        } else if ((channelType === 'discord' || channelType === 'slack') && config.webhook_url) {
            channels.push({ channel_type: channelType, config });
        }
    });
    
    return channels;
}

// Make functions globally available
window.openJobModal = openJobModal;
window.closeJobModal = closeJobModal;
window.editJob = editJob;
window.deleteJob = deleteJob;
window.toggleJob = toggleJob;
window.runCheckNow = runCheckNow;
window.openHistoryModal = openHistoryModal;
window.closeHistoryModal = closeHistoryModal;
window.openWizardModal = openWizardModal;
window.closeWizardModal = closeWizardModal;
window.runWizardAnalyze = runWizardAnalyze;
window.applyWizardAndOpenForm = applyWizardAndOpenForm;
window.toggleMatchType = toggleMatchType;
window.toggleCondition = toggleCondition;
window.testEmail = testEmail;
window.addNotificationChannel = addNotificationChannel;
window.removeNotificationChannelUI = removeNotificationChannelUI;
