// CSCL Teacher Dashboard JavaScript - S2.15 stage-status & wizard-progress fix
(function() {
    'use strict';
    try {
        if (typeof console !== 'undefined' && console.log) console.log('[teacher] script loaded');
    } catch (e) {
        if (typeof console !== 'undefined' && console.error) console.error('[teacher] init log failed', e);
    }
})();
// S2.17: global fatal logger for runtime errors (low-noise)
(function() {
    try {
        var prevOnError = window.onerror;
        window.onerror = function(msg, file, line, col, err) {
            try { console.error('[teacher][fatal]', msg, file || '', line || '', col || '', err && err.stack || ''); } catch (e) {}
            if (typeof prevOnError === 'function') return prevOnError.apply(window, arguments);
            return false;
        };
        window.addEventListener('unhandledrejection', function(ev) {
            try { console.error('[teacher][fatal] unhandledrejection', ev.reason, (ev.reason && ev.reason.stack) || ''); } catch (e) {}
        });
    } catch (e) {}
})();
const API_BASE = '/api/cscl';
const API_BASE_GENERAL = '/api';
// B1: Single course bucket for docs + script so RAG retrieves uploaded documents
const DEFAULT_COURSE_ID = 'default-course';

// S2.13: do not render text that looks like PDF binary
function looksLikePdfBinary(text) {
    if (!text || typeof text !== 'string') return false;
    if (text.indexOf('%PDF-') !== -1) return true;
    var re = /\b(obj|endobj|stream|endstream|xref|trailer|startxref)\b/i;
    if (re.test(text)) return true;
    var nonPrint = 0;
    for (var i = 0; i < text.length; i++) {
        var c = text[i];
        if (c !== '\n' && c !== '\t' && (c < ' ' || c > '\u007f')) nonPrint++;
    }
    if (text.length > 0 && nonPrint / text.length > 0.10) return true;
    return false;
}

// State
let currentScriptId = null;
let currentPipelineRunId = null;
let _pipelinePollingActive = false;
let wizardStep = 1;
let currentSpec = null;
let scripts = [];
let pipelineRuns = [];

// Initialize - S2.14.2: phased init, full stack on error, event delegation
document.addEventListener('DOMContentLoaded', function() {
    try {
        if (typeof showLoading === 'function') showLoading(false);
    } catch (e) { /* ignore */ }
    try {
        if (typeof console !== 'undefined' && console.log) console.log('[teacher] dom ready');
    } catch (e) { /* ignore */ }
    try {
        loadDashboardData();
    } catch (err) {
        console.error('[teacher] loadDashboardData error', err);
        if (err && err.stack) console.error(err.stack);
        if (typeof showLoading === 'function') showLoading(false);
    }
    try {
        setupNavigation();
    } catch (err) {
        console.error('[teacher] setupNavigation error', err);
        if (err && err.stack) console.error(err.stack);
        if (typeof showLoading === 'function') showLoading(false);
    }
    try {
        if (typeof console !== 'undefined' && console.log) console.log('[teacher] bind start');
    } catch (e) { /* ignore */ }
    try {
        setupEventDelegation();
    } catch (err) {
        console.error('[teacher] setupEventDelegation error', err);
        if (err && err.stack) console.error(err.stack);
        if (typeof showLoading === 'function') showLoading(false);
    }
    try {
        checkHealth();
    } catch (err) {
        console.error('[teacher] checkHealth error', err);
        if (typeof showLoading === 'function') showLoading(false);
    }
    try {
        loadTaskTypes();
    } catch (err) {
        console.error('[teacher] loadTaskTypes error', err);
    }
    try {
        var sid = sessionStorage.getItem('cscl_current_script_id');
        if (sid && !currentScriptId) currentScriptId = sid;
        var rid = sessionStorage.getItem('cscl_current_run_id');
        if (rid && !currentPipelineRunId) currentPipelineRunId = rid;
    } catch (e) { /* ignore */ }
    try {
        restorePipelineState();
    } catch (e) { console.error('[teacher] restorePipelineState error', e); }
    try {
        var demoSpec = sessionStorage.getItem('demoSpec');
        if (demoSpec) {
            var spec = JSON.parse(demoSpec);
            if (typeof fillSpecForm === 'function') fillSpecForm(spec);
            sessionStorage.removeItem('demoSpec');
        }
    } catch (e) {
        console.error('[teacher] demo spec parse error', e);
        if (e && e.stack) console.error(e.stack);
        if (typeof showLoading === 'function') showLoading(false);
    }
    try {
        var tutorialEl = document.getElementById('teacherTutorial');
        var dismissBtn = document.getElementById('teacherTutorialDismiss');
        if (localStorage.getItem('teacher_tutorial_dismissed') === '1' && tutorialEl) {
            tutorialEl.classList.add('hidden');
        }
        if (dismissBtn && tutorialEl) {
            dismissBtn.addEventListener('click', function() {
                try { localStorage.setItem('teacher_tutorial_dismissed', '1'); } catch (e) {}
                tutorialEl.classList.add('hidden');
            });
        }
    } catch (e) { /* ignore */ }
    try {
        if (typeof console !== 'undefined' && console.log) console.log('[teacher] bind end');
    } catch (e) { /* ignore */ }
    setTimeout(function() {
        try {
            if (typeof showLoading === 'function') showLoading(false);
        } catch (e) { /* ignore */ }
    }, 3000);
});
document.addEventListener('localeChange', function() {
    try { if (typeof updateCurrentStep === 'function') updateCurrentStep(); } catch (e) {}
});

// S2.14.2/S2.17: document-level event delegation - id/class/data-action/data-view/data-step
function setupEventDelegation() {
    try {
        if (typeof console !== 'undefined' && console.log) console.log('[teacher] delegation bind start');
    } catch (e) {}
    document.addEventListener('click', function(e) {
        var target = e.target;
        var btn = target.closest ? target.closest('button, a[href="#"], .step-action-btn, .process-card, .nav-item') : null;
        if (!btn) return;
        var action = (btn.getAttribute && btn.getAttribute('data-action')) || btn.id || (btn.className && typeof btn.className === 'string' && btn.className.split(/\s+/)[0]) || '';
        try {
            if (typeof console !== 'undefined' && console.log) console.log('[teacher] click captured action=' + (action || '') + ' id=' + (btn.id || '') + ' class=' + (typeof btn.className === 'string' ? btn.className : ''));
        } catch (e) {}
        var view = btn.getAttribute && btn.getAttribute('data-view');
        var card = btn.closest && btn.closest('.process-card');
        var step = (card && card.getAttribute && card.getAttribute('data-step')) || (btn.getAttribute && btn.getAttribute('data-step'));
        var isStepBtn = btn.classList && btn.classList.contains('step-action-btn');
        var isProcessCard = btn.classList && btn.classList.contains('process-card');

        if (view !== null && view !== undefined && view !== '') {
            try {
                console.log('[teacher] action:', 'nav-' + view);
                if (typeof switchView === 'function') { e.preventDefault(); switchView(view); }
            } catch (err) {
                console.error('[teacher] handler error nav', err);
                if (err && err.stack) console.error(err.stack);
            }
            return;
        }
        if (step !== null && step !== undefined && (isProcessCard || isStepBtn)) {
            var num = parseInt(step, 10);
            if (num >= 1 && num <= 4) {
                try {
                    console.log('[teacher] action: go-step-' + num);
                    e.preventDefault();
                    if (e.stopPropagation) e.stopPropagation();
                    if (typeof goToStep === 'function') goToStep(num);
                } catch (err) {
                    console.error('[teacher] handler error goToStep', err);
                    if (err && err.stack) console.error(err.stack);
                }
            }
            return;
        }
        if (action === 'import-outline' || action === 'btnImport' || (btn.classList && btn.classList.contains('btn-import'))) {
            try {
                console.log('[teacher] action: import-outline');
                e.preventDefault();
                if (typeof goToStep === 'function') goToStep(1);
            } catch (err) {
                console.error('[teacher] handler error import-outline', err);
                if (err && err.stack) console.error(err.stack);
            }
            return;
        }
        if (action === 'validate-goals' || action === 'btnValidate' || (btn.classList && btn.classList.contains('btn-validate'))) {
            try {
                console.log('[teacher] action: validate-goals');
                e.preventDefault();
                if (typeof goToStep === 'function') goToStep(2);
            } catch (err) {
                console.error('[teacher] handler error validate-goals', err);
                if (err && err.stack) console.error(err.stack);
            }
            return;
        }
        if (action === 'run-pipeline' || action === 'btnGenerate' || (btn.classList && btn.classList.contains('btn-generate'))) {
            try {
                console.log('[teacher] action: run-pipeline');
                e.preventDefault();
                if (typeof goToStep === 'function') goToStep(3);
            } catch (err) {
                console.error('[teacher] handler error run-pipeline', err);
                if (err && err.stack) console.error(err.stack);
            }
            return;
        }
        if (action === 'review-publish' || action === 'btnPublish' || (btn.classList && btn.classList.contains('btn-publish'))) {
            try {
                console.log('[teacher] action: review-publish');
                e.preventDefault();
                if (typeof goToStep === 'function') goToStep(4);
            } catch (err) {
                console.error('[teacher] handler error review-publish', err);
                if (err && err.stack) console.error(err.stack);
            }
            return;
        }
        if (btn.getAttribute && btn.getAttribute('onclick') && (btn.getAttribute('onclick').indexOf('startNewActivity') !== -1 || btn.getAttribute('onclick').indexOf('goToStep') !== -1)) {
            var stepMatch = btn.getAttribute('onclick').match(/goToStep\s*\(\s*(\d+)\s*\)/);
            if (stepMatch) {
                try {
                    var n = parseInt(stepMatch[1], 10);
                    console.log('[teacher] action: go-step-' + n + ' (onclick fallback)');
                    e.preventDefault();
                    if (e.stopPropagation) e.stopPropagation();
                    if (typeof goToStep === 'function') goToStep(n);
                } catch (err) {
                    console.error('[teacher] handler error goToStep fallback', err);
                    if (err && err.stack) console.error(err.stack);
                }
                return;
            }
            if (btn.getAttribute('onclick').indexOf('startNewActivity') !== -1) {
                try {
                    console.log('[teacher] action: startNewActivity (onclick fallback)');
                    e.preventDefault();
                    if (typeof startNewActivity === 'function') startNewActivity();
                } catch (err) {
                    console.error('[teacher] handler error startNewActivity', err);
                    if (err && err.stack) console.error(err.stack);
                }
                return;
            }
        }
    }, true);
    try {
        if (typeof console !== 'undefined' && console.log) console.log('[teacher] delegation bind end');
    } catch (e) {}
}

// Health Check
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE_GENERAL}/health`);
        const data = await res.json();
        console.log('Health check:', data);
    } catch (error) {
        console.error('Health check failed:', error);
        showNotification('Service unavailable. Some features may not work.', 'warning');
    }
}

// Navigation - S2.14.2: guard against missing elements
function setupNavigation() {
    var items = document.querySelectorAll('.nav-item');
    if (!items || !items.length) return;
    items.forEach(function(item) {
        if (!item || !item.addEventListener) return;
        item.addEventListener('click', function(e) {
            e.preventDefault();
            var view = this.dataset && this.dataset.view;
            if (view && typeof switchView === 'function') switchView(view);
        });
    });
}

// Map data-view (kebab-case) to DOM id (camelCase + View)
function viewNameToId(viewName) {
    const camel = viewName.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    return camel + 'View';
}

function switchView(viewName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });
    
    // Update views - hide all first
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    
    // Show target view (spec-validation -> specValidationView, etc.)
    const viewId = viewNameToId(viewName);
    const viewElement = document.getElementById(viewId);
    if (viewElement) {
        viewElement.classList.add('active');
        // Scroll to top of main content
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.scrollTop = 0;
        }
    } else {
        console.warn(`View element not found: ${viewId}`);
        // Fallback: show dashboard
        const dashboardView = document.getElementById('dashboardView');
        if (dashboardView) {
            dashboardView.classList.add('active');
            showNotification(`View "${viewName}" not found, showing dashboard`, 'warning');
        }
    }
    
    // Load data for view
    try {
        switch(viewName) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'scripts':
                loadScripts();
                break;
            case 'spec-validation':
                // Standalone spec validation view - already visible
                break;
            case 'pipeline-runs':
                loadPipelineRuns();
                break;
            case 'documents':
                loadDocuments();
                break;
            case 'decisions':
                loadDecisionTimeline();
                break;
            case 'quality-reports':
                loadQualityReports();
                break;
            case 'publish':
                loadPublishView();
                break;
            case 'settings':
                // Settings view - placeholder page is fine
                break;
            case 'wizard':
                resetWizard();
                break;
            default:
                console.warn(`Unknown view: ${viewName}`);
        }
    } catch (error) {
        console.error(`Error loading view ${viewName}:`, error);
        showNotification(`Failed to load ${viewName} view`, 'error');
    }
}

// Task types from config (no hardcoded list in JS)
async function loadTaskTypes() {
    var sel = document.getElementById('specTaskType');
    if (!sel) return;
    try {
        var res = await fetch(API_BASE + '/task-types', { credentials: 'include' });
        if (!res.ok) {
            sel.innerHTML = '<option value="structured_debate">Structured Debate</option><option value="evidence_comparison">Evidence Comparison</option><option value="perspective_synthesis">Perspective Synthesis</option><option value="claim_counterclaim_roleplay">Claim–Counterclaim Role Play</option>';
            return;
        }
        var data = await res.json();
        var types = data.task_types || [];
        sel.innerHTML = types.map(function(t) {
            var id = t.id || '';
            var name = t.display_name || t.label || id;
            var desc = t.description || t.pedagogical_goal || '';
            return '<option value="' + escapeHtml(id) + '" title="' + escapeHtml(desc) + '">' + escapeHtml(name) + '</option>';
        }).join('');
        if (sel.options.length && !sel.value) sel.selectedIndex = 0;
    } catch (e) {
        sel.innerHTML = '<option value="structured_debate">Structured Debate</option><option value="evidence_comparison">Evidence Comparison</option><option value="perspective_synthesis">Perspective Synthesis</option><option value="claim_counterclaim_roleplay">Claim–Counterclaim Role Play</option>';
    }
}

// Dashboard
async function loadDashboardData() {
    try {
        showLoading(true);
        
        // Load scripts
        const scriptsRes = await fetch(`${API_BASE}/scripts`, {
            credentials: 'include'
        });
        
        if (scriptsRes.status === 401) {
            showNotification('请先登录', 'error');
            showLoading(false);
            return;
        }
        
        if (scriptsRes.status === 403) {
            showNotification('当前角色无权限', 'error');
            showLoading(false);
            return;
        }
        
        if (scriptsRes.ok) {
            const data = await scriptsRes.json();
            scripts = data.scripts || [];
        }
        
        // Update stats
        const activeProjects = scripts.filter(s => s.status === 'draft' || s.status === 'final').length;
        const readyToPublish = scripts.filter(s => s.status === 'final').length;
        
        const statActiveProjectsEl = document.getElementById('statActiveProjects');
        const statRunningPipelinesEl = document.getElementById('statRunningPipelines');
        const statReadyToPublishEl = document.getElementById('statReadyToPublish');
        const statAvgQualityEl = document.getElementById('statAvgQuality');
        
        if (statActiveProjectsEl) statActiveProjectsEl.textContent = activeProjects;
        if (statRunningPipelinesEl) statRunningPipelinesEl.textContent = '0';
        if (statReadyToPublishEl) statReadyToPublishEl.textContent = readyToPublish;
        if (statAvgQualityEl) statAvgQualityEl.textContent = '--';
        
        // Update current step indicator
        updateCurrentStep();
        
        // Load recent pipelines
        await loadRecentPipelines();
        
        // Load recent decisions
        await loadRecentDecisions();
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard data', 'error');
        showLoading(false);
    } finally {
        showLoading(false);
    }
}

async function loadRecentPipelines() {
    var container = document.getElementById('recentPipelines');
    if (!container) return;
    try {
        if (scripts.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No pipeline runs yet</p></div>';
            return;
        }
        
        // Get runs for first script
        const scriptId = scripts[0].id;
        const res = await fetch(`${API_BASE}/scripts/${scriptId}/pipeline/runs`, {
            credentials: 'include'
        });
        
        if (res.ok) {
            const data = await res.json();
            const runs = data.runs || [];
            const recent = runs.slice(0, 3);
            
            if (recent.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>No pipeline runs yet</p></div>';
            } else {
                container.innerHTML = recent.map(run => `
                    <div class="activity-item">
                        <div class="activity-icon"><i class="fas fa-project-diagram"></i></div>
                        <div class="activity-content">
                            <h5>Pipeline Run ${run.run_id.substring(0, 8)}</h5>
                            <p>Status: ${run.status}</p>
                        </div>
                        <div class="activity-time">${formatTime(run.created_at)}</div>
                    </div>
                `).join('');
            }
        } else {
            container.innerHTML = '<div class="empty-state"><p>Unable to load pipeline runs</p></div>';
        }
    } catch (error) {
        if (container) container.innerHTML = '<div class="empty-state"><p>Error loading pipeline runs</p></div>';
    }
}

async function loadRecentDecisions() {
    var container = document.getElementById('recentDecisions');
    if (container) container.innerHTML = '<div class="empty-state"><p>No decisions yet</p></div>';
}

// Script Management
async function loadScripts() {
    const container = document.getElementById('scriptsList');
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/scripts`, {
            credentials: 'include'
        });
        
        if (res.status === 401) {
            container.innerHTML = '<div class="empty-state"><p>Please login first</p></div>';
            return;
        }
        
        if (res.status === 403) {
            container.innerHTML = '<div class="empty-state"><p>Current role has no permission</p></div>';
            return;
        }
        
        if (res.ok) {
            const data = await res.json();
            scripts = data.scripts || [];
            renderScripts(scripts);
        } else {
            container.innerHTML = '<div class="empty-state"><p>Failed to load scripts</p></div>';
        }
    } catch (error) {
        console.error('Error loading scripts:', error);
        container.innerHTML = '<div class="empty-state"><p>Error loading scripts</p></div>';
    } finally {
        showLoading(false);
    }
}

function renderScripts(scriptsList) {
    const container = document.getElementById('scriptsList');
    
    if (scriptsList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h4>No Script Projects</h4>
                <p>You haven't created any script projects yet.</p>
                <button class="btn-primary" onclick="createNewScriptProject()">
                    <i class="fas fa-plus"></i>
                    Create New Script Project
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = scriptsList.map(script => `
        <div class="script-card" onclick="openScript('${script.id}')">
            <div class="script-card-header">
                <h4>${escapeHtml(script.title || 'Untitled')}</h4>
                <span class="status-badge ${script.status}">${script.status}</span>
            </div>
            <div class="script-card-content">
                <p><strong>Topic:</strong> ${escapeHtml(script.topic || 'N/A')}</p>
                <p><strong>Duration:</strong> ${script.duration_minutes || 0} minutes</p>
                <p><strong>Task Type:</strong> ${script.task_type || 'N/A'}</p>
            </div>
            <div class="script-card-footer">
                <span class="script-time">Updated: ${formatTime(script.updated_at)}</span>
                <button class="btn-secondary btn-sm" onclick="event.stopPropagation(); viewScriptQuality('${script.id}')">
                    <i class="fas fa-chart-line"></i>
                    Quality Report
                </button>
            </div>
        </div>
    `).join('');
}

// Four-Step Process Navigation
function startNewActivity() {
    wizardStep = 1;
    switchView('wizard');
    resetWizard();
}

function goToStep(step) {
    wizardStep = step;
    switchView('wizard');
    resetWizard();
    // Navigate to specific step
    for (let i = 1; i < step; i++) {
        const stepEl = document.querySelector(`.wizard-step[data-step="${i}"]`);
        if (stepEl) {
            stepEl.classList.add('completed');
        }
    }
    const currentStepEl = document.querySelector(`.wizard-step[data-step="${step}"]`);
    if (currentStepEl) {
        currentStepEl.classList.add('active');
    }
    // Show corresponding wizard step content
    document.querySelectorAll('.wizard-step-content').forEach((content, index) => {
        content.classList.toggle('active', index === step - 1);
    });
    updateCurrentStep();
}

function updateCurrentStep() {
    const indicator = document.getElementById('currentStepIndicator');
    if (indicator) {
        indicator.textContent = wizardStep || 1;
    }
    const statusEl = document.getElementById('currentStatus');
    if (statusEl) {
        const statusMap = {
            1: typeof t === 'function' ? t('teacher.step1.title') : '导入课程大纲',
            2: typeof t === 'function' ? t('teacher.step2.title') : '确认教学目标',
            3: typeof t === 'function' ? t('teacher.step3.title') : '生成活动流程',
            4: typeof t === 'function' ? t('teacher.step4.title') : '审阅并发布'
        };
        statusEl.textContent = statusMap[wizardStep] || (typeof t === 'function' ? t('teacher.dashboard.ready') : '准备开始');
    }
    // Update process cards active state
    document.querySelectorAll('.process-card').forEach(card => {
        const cardStep = parseInt(card.dataset.step);
        card.classList.toggle('active', cardStep === wizardStep);
        card.classList.toggle('completed', cardStep < wizardStep);
    });
}

function toggleTechDrawer() {
    const drawer = document.getElementById('techDrawerContent');
    const btn = document.querySelector('.drawer-toggle');
    if (drawer && btn) {
        drawer.classList.toggle('hidden');
        const icon = btn.querySelector('i');
        if (icon) {
            icon.classList.toggle('fa-chevron-down');
            icon.classList.toggle('fa-chevron-up');
        }
    }
}

// Wizard Functions
function createNewScriptProject() {
    startNewActivity();
}

function resetWizard() {
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        step.classList.toggle('active', index === wizardStep - 1);
        step.classList.toggle('completed', index < wizardStep - 1);
    });
    document.querySelectorAll('.wizard-step-content').forEach((content, index) => {
        content.classList.toggle('active', index === wizardStep - 1);
    });
    updateCurrentStep();
}

async function wizardNext() {
    if (wizardStep === 2) {
        if (!currentSpec) {
            showNotification('请先完成教学目标检查', 'warning');
            return;
        }
    }
    if (wizardStep === 3) {
        if (!currentPipelineRunId) {
            showNotification('Please run pipeline first', 'warning');
            return;
        }
    }
    if (wizardStep === 1) {
        var syllabusEl = document.getElementById('syllabusText');
        var text = syllabusEl ? (syllabusEl.value || '').trim() : '';
        if (text.length >= 80) {
            try {
                var uploadRes = await fetch(API_BASE + '/courses/' + DEFAULT_COURSE_ID + '/docs/upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: 'Syllabus (Step 1)', text: text }),
                    credentials: 'include'
                });
                if (uploadRes.ok && typeof loadDocuments === 'function') loadDocuments();
            } catch (e) {
                console.warn('[teacher] Step 1 syllabus upload as course doc failed', e);
            }
        }
    }
    
    if (wizardStep < 4) {
        wizardStep++;
        updateWizardProgress();
        if (wizardStep === 4) {
            loadScriptPreview();
        }
    }
}

function wizardBack() {
    if (wizardStep > 1) {
        wizardStep--;
        updateWizardProgress();
    }
}

async function loadScriptPreview() {
    var container = document.getElementById('scriptPreview');
    if (!container) return;

    container.innerHTML = '<div class="loading-placeholder"><i class="fas fa-spinner fa-spin"></i><p>Loading script preview...</p></div>';

    var runId = currentPipelineRunId;
    if (!runId && currentScriptId) {
        try {
            var runsRes = await fetch(API_BASE + '/scripts/' + currentScriptId + '/pipeline/runs', { credentials: 'include' });
            if (runsRes.ok) {
                var runsData = await runsRes.json();
                var runs = runsData.runs || [];
                if (runs.length > 0) runId = runs[0].run_id;
            }
        } catch (e) { console.warn('[teacher] loadScriptPreview runs fetch error', e); }
    }

    if (!runId) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>No pipeline run found. Please go back and run the pipeline first.</p></div>';
        return;
    }

    try {
        var res = await fetch(API_BASE + '/pipeline/runs/' + runId, { credentials: 'include' });
        if (!res.ok) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load pipeline results (HTTP ' + res.status + ')</p></div>';
            return;
        }
        var data = await res.json();
        var stages = data.stages || [];
        var run = data.run || {};

        if (run.status === 'running') {
            container.innerHTML = '<div class="loading-placeholder"><i class="fas fa-spinner fa-spin"></i><p>Pipeline is still running... Please wait.</p></div>';
            setTimeout(function() { loadScriptPreview(); }, 3000);
            return;
        }

        var output = null;
        var stageOrder = ['refiner', 'critic', 'material_generator', 'planner'];
        for (var i = 0; i < stageOrder.length; i++) {
            var st = stages.find(function(s) { return s.stage_name === stageOrder[i] && s.status === 'success' && s.output_json; });
            if (st) { output = st.output_json; break; }
        }

        if (!output) {
            var errMsg = run.error_message || 'No output was generated';
            container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Pipeline did not produce output: ' + errMsg + '</p></div>';
            return;
        }

        var html = '<div class="script-preview-content">';
        var roles = output.roles || [];
        if (roles.length > 0) {
            html += '<div class="preview-section"><h3><i class="fas fa-users"></i> Roles</h3><div class="roles-grid">';
            roles.forEach(function(r) {
                html += '<div class="role-card"><strong>' + _esc(r.role_id || r.name || 'Role') + '</strong>';
                if (r.description) html += '<p>' + _esc(r.description) + '</p>';
                html += '</div>';
            });
            html += '</div></div>';
        }

        var scenes = output.scenes || [];
        if (scenes.length > 0) {
            html += '<div class="preview-section"><h3><i class="fas fa-film"></i> Scenes (' + scenes.length + ')</h3>';
            scenes.forEach(function(scene, idx) {
                html += '<div class="scene-card">';
                html += '<div class="scene-header"><span class="scene-number">Scene ' + (scene.order_index || idx + 1) + '</span>';
                if (scene.scene_type) html += '<span class="scene-type badge">' + _esc(scene.scene_type) + '</span>';
                html += '</div>';
                if (scene.purpose) html += '<p class="scene-purpose">' + _esc(scene.purpose) + '</p>';
                var scriptlets = scene.scriptlets || [];
                if (scriptlets.length > 0) {
                    html += '<div class="scriptlets-list">';
                    scriptlets.forEach(function(sl) {
                        html += '<div class="scriptlet-item">';
                        if (sl.role_id) html += '<span class="scriptlet-role">' + _esc(sl.role_id) + ':</span> ';
                        html += '<span class="scriptlet-text">' + _esc(sl.prompt_text || '') + '</span>';
                        if (sl.prompt_type) html += ' <span class="scriptlet-type badge-sm">' + _esc(sl.prompt_type) + '</span>';
                        html += '</div>';
                    });
                    html += '</div>';
                }
                if (scene.transition_rule) html += '<p class="scene-transition"><em>Transition: ' + _esc(scene.transition_rule) + '</em></p>';
                html += '</div>';
            });
            html += '</div>';
        }

        if (output.refinements_applied) {
            var ref = output.refinements_applied;
            html += '<div class="preview-section"><h3><i class="fas fa-magic"></i> Refinements Applied</h3><ul>';
            if (ref.scenes_added) html += '<li>Scenes added: ' + ref.scenes_added + '</li>';
            if (ref.roles_added) html += '<li>Roles added: ' + ref.roles_added + '</li>';
            if (ref.scriptlets_fixed) html += '<li>Scriptlets fixed: ' + ref.scriptlets_fixed + '</li>';
            html += '</ul></div>';
        }

        var stagesSummary = '<div class="preview-section"><h3><i class="fas fa-info-circle"></i> Pipeline Summary</h3>';
        stagesSummary += '<div class="pipeline-summary-grid">';
        stages.forEach(function(s) {
            var cls = s.status === 'success' ? 'stage-ok' : (s.status === 'failed' ? 'stage-fail' : 'stage-skip');
            stagesSummary += '<div class="pipeline-summary-item ' + cls + '">';
            stagesSummary += '<strong>' + _esc(s.stage_name) + '</strong>';
            stagesSummary += '<span class="summary-status">' + _esc(s.status) + '</span>';
            if (s.latency_ms) stagesSummary += '<span class="summary-time">' + (s.latency_ms / 1000).toFixed(1) + 's</span>';
            stagesSummary += '</div>';
        });
        stagesSummary += '</div></div>';
        html += stagesSummary;

        html += '</div>';
        container.innerHTML = html;

        var finalizeBtn = document.getElementById('finalizeBtn');
        if (finalizeBtn && (run.status === 'completed' || run.status === 'success')) {
            finalizeBtn.disabled = false;
        }

    } catch (e) {
        console.error('[teacher] loadScriptPreview error:', e);
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Error loading preview: ' + e.message + '</p></div>';
    }
}

function _esc(str) {
    if (!str) return '';
    var d = document.createElement('div');
    d.textContent = String(str);
    return d.innerHTML;
}

function updateWizardProgress() {
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        const stepNum = index + 1;
        step.classList.toggle('active', stepNum === wizardStep);
        step.classList.toggle('completed', stepNum < wizardStep);
    });
    
    document.querySelectorAll('.wizard-step-content').forEach((content, index) => {
        content.classList.toggle('active', index === wizardStep - 1);
    });
    updateCurrentStep();
    // Ensure Run Pipeline button is enabled when showing Step 3 and not currently running
    if (wizardStep === 3 && !pipelineRunInProgress) {
        var runBtn = document.getElementById('runPipelineBtn');
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.classList.remove('btn-loading');
            if (!runBtn.querySelector('.fa-spinner')) runBtn.innerHTML = '<i class="fas fa-play"></i> <span data-i18n="teacher.pipeline.start">开始生成</span>';
        }
    }
}

function cancelWizard() {
    if (confirm('Are you sure you want to cancel? All progress will be lost.')) {
        switchView('dashboard');
        resetWizard();
    }
}

// Step 1: Upload Syllabus
// PDF files are uploaded to the backend for extraction (pypdf); only .txt/.md are read locally.
document.getElementById('syllabusFile')?.addEventListener('change', async function(e) {
    const file = e.target.files[0];
    if (!file) return;
    const ext = (file.name || '').split('.').pop().toLowerCase();
    if (ext === 'pdf') {
        // PDF: upload to backend, show extracted text (never read raw bytes locally)
        try {
            showLoading(true);
            const courseId = typeof DEFAULT_COURSE_ID !== 'undefined' ? DEFAULT_COURSE_ID : 'default-course';
            const formData = new FormData();
            formData.append('file', file);
            formData.append('title', file.name);
            const res = await fetch((typeof API_BASE !== 'undefined' ? API_BASE : '/api/cscl') + '/courses/' + courseId + '/docs/upload', {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });
            const result = await res.json();
            if (res.ok && (result.extracted_text || result.extracted_text_preview)) {
                document.getElementById('syllabusText').value = result.extracted_text || result.extracted_text_preview;
                showNotification('PDF uploaded and text extracted successfully', 'success');
                if (typeof loadDocuments === 'function') loadDocuments();
            } else {
                var code = result.code || '';
                var msg = code === 'PDF_PARSE_FAILED'
                    ? 'Unable to extract text from this PDF. Please try a text-based PDF or paste text manually.'
                    : (result.error || result.message || 'PDF extraction failed. Please paste text manually.');
                showNotification(msg, 'error');
            }
        } catch (err) {
            console.error('PDF upload error:', err);
            showNotification('Failed to upload PDF. Please paste text manually.', 'error');
        } finally {
            showLoading(false);
        }
    } else {
        // TXT/MD: safe to read as text locally
        const reader = new FileReader();
        reader.onload = function(ev) {
            document.getElementById('syllabusText').value = ev.target.result;
        };
        reader.readAsText(file);
    }
});

// Step 2: Validate Spec — canonical payload matches backend (course_context, learning_objectives, task_requirements)
function fillDemoSpec() {
    const demoSpec = {
        course: "Introduction to Data Science",
        topic: "Algorithmic Fairness in Education",
        duration_minutes: 90,
        mode: "sync",
        class_size: 30,
        course_context: "Undergraduate data science course; learners have basic statistics. Instructional context: 90-min synchronous session for collaborative argumentation on algorithmic fairness.",
        learning_objectives: [
            "Explain basic fairness metrics",
            "Compare trade-offs between accuracy and fairness",
            "Construct evidence-based group arguments"
        ],
        task_type: "structured_debate",
        collaboration_form: "group",
        expected_output: [
            "Group argument map",
            "300-word joint reflection"
        ],
        task_requirements: "Minimum 2 evidence sources per position; each group must respond to at least one counterargument; group artifact: shared argument map and 300-word reflection."
    };
    fillSpecForm(demoSpec);
}

function fillSpecForm(spec) {
    document.getElementById('specCourse').value = spec.course || '';
    document.getElementById('specTopic').value = spec.topic || '';
    document.getElementById('specDuration').value = spec.duration_minutes != null ? spec.duration_minutes : 90;
    var mode = (spec.mode || 'sync').toLowerCase();
    document.getElementById('specMode').value = mode === 'async' ? 'async' : 'sync';
    document.getElementById('specClassSize').value = spec.class_size != null ? spec.class_size : 30;
    var objEl = document.getElementById('specCourseContext');
    if (objEl) objEl.value = spec.course_context || spec.course_context_description || '';
    document.getElementById('specObjectives').value = Array.isArray(spec.learning_objectives)
        ? spec.learning_objectives.join('\n')
        : (spec.learning_objectives || '');
    document.getElementById('specTaskType').value = spec.task_type || 'structured_debate';
    document.getElementById('specExpectedOutput').value = Array.isArray(spec.expected_output)
        ? spec.expected_output.join('\n')
        : (spec.expected_output || '');
    var cfEl = document.getElementById('specCollaborationForm');
    if (cfEl) cfEl.value = spec.collaboration_form || 'group';
    var trEl = document.getElementById('specTaskRequirements');
    if (trEl) trEl.value = spec.task_requirements || spec.requirements_text || '';
}

function buildCanonicalSpecFromForm() {
    var modeVal = document.getElementById('specMode').value;
    var mode = (modeVal && modeVal.toLowerCase() === 'async') ? 'async' : 'sync';
    var objectives = document.getElementById('specObjectives').value.split('\n').filter(function(s) { return s.trim(); });
    var knowledge = objectives.length ? objectives : ['Understand topic'];
    var skills = objectives.length > 1 ? objectives.slice(1) : (objectives.length ? [objectives[0]] : ['Apply concepts']);
    var cfEl = document.getElementById('specCollaborationForm');
    var collaborationForm = (cfEl && cfEl.value) ? cfEl.value : 'group';
    return {
        course_context: {
            subject: document.getElementById('specCourse').value.trim(),
            topic: document.getElementById('specTopic').value.trim(),
            class_size: parseInt(document.getElementById('specClassSize').value, 10) || 30,
            mode: mode,
            duration: parseInt(document.getElementById('specDuration').value, 10) || 90,
            description: (document.getElementById('specCourseContext') && document.getElementById('specCourseContext').value) ? document.getElementById('specCourseContext').value.trim() : ''
        },
        learning_objectives: { knowledge: knowledge, skills: skills },
        task_requirements: {
            task_type: document.getElementById('specTaskType').value || 'structured_debate',
            expected_output: (document.getElementById('specExpectedOutput').value.split('\n').filter(function(s) { return s.trim(); }).join('; ')) || 'Group artifact',
            collaboration_form: collaborationForm,
            requirements_text: (document.getElementById('specTaskRequirements') && document.getElementById('specTaskRequirements').value) ? document.getElementById('specTaskRequirements').value.trim() : ''
        }
    };
}

// Backend field_path (machine-readable) -> frontend element id for scroll/highlight on 422
var pathToFieldId = {
    'course_context': 'specCourse',
    'course_context.subject': 'specCourse',
    'course_context.topic': 'specTopic',
    'course_context.class_size': 'specClassSize',
    'course_context.mode': 'specMode',
    'course_context.duration': 'specDuration',
    'course_context.description': 'specCourseContext',
    'learning_objectives': 'specObjectives',
    'learning_objectives.knowledge': 'specObjectives',
    'learning_objectives.skills': 'specObjectives',
    'task_requirements': 'specTaskType',
    'task_requirements.task_type': 'specTaskType',
    'task_requirements.expected_output': 'specExpectedOutput',
    'task_requirements.collaboration_form': 'specCollaborationForm',
    'task_requirements.requirements_text': 'specTaskRequirements'
};

function firstErrorFieldIdFromPaths(fieldPaths) {
    if (fieldPaths && fieldPaths.length > 0) {
        var id = pathToFieldId[fieldPaths[0]];
        if (id) return id;
    }
    return null;
}

function firstErrorFieldIdFromIssues(issues) {
    if (!issues || !issues.length) return null;
    for (var i = 0; i < issues.length; i++) {
        var issue = issues[i];
        var path = (issue.indexOf('course_context.description') !== -1) ? 'course_context.description' : (issue.indexOf('task_requirements.requirements_text') !== -1) ? 'task_requirements.requirements_text' : (issue.indexOf('task_requirements.collaboration_form') !== -1) ? 'task_requirements.collaboration_form' : (issue.indexOf('course_context') !== -1) ? 'course_context' : (issue.indexOf('task_requirements') !== -1) ? 'task_requirements' : (issue.indexOf('learning_objectives') !== -1) ? 'specObjectives' : null;
        if (path && path !== 'specObjectives' && pathToFieldId[path]) return pathToFieldId[path];
        if (path === 'specObjectives' || (issue.indexOf('learning_objectives') !== -1)) return 'specObjectives';
    }
    return 'specCourse';
}

async function validateSpec() {
    var form = document.getElementById('specForm');
    if (!form || !form.checkValidity()) {
        if (form) form.reportValidity();
        return;
    }
    var spec = buildCanonicalSpecFromForm();
    try {
        showLoading(true);
        var res = await fetch(API_BASE + '/spec/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(spec),
            credentials: 'include'
        });
        var result = await res.json();
        var resultDiv = document.getElementById('specValidationResult');
        if (resultDiv) resultDiv.classList.remove('hidden');
        document.querySelectorAll('.spec-form .form-group input, .spec-form .form-group select, .spec-form .form-group textarea').forEach(function(el) { el.classList.remove('validation-error'); });
        if (res.status === 422 || !result.valid) {
            if (resultDiv) {
                resultDiv.className = 'validation-result error';
                resultDiv.innerHTML = '<h4><i class="fas fa-exclamation-circle"></i> Validation Failed</h4><ul>' + (result.issues || []).map(function(issue) { return '<li>' + escapeHtml(issue) + '</li>'; }).join('') + '</ul><p><strong>Action:</strong> Fix the issues above and try again.</p>';
            }
            var firstId = firstErrorFieldIdFromPaths(result.field_paths) || firstErrorFieldIdFromIssues(result.issues);
            if (firstId) {
                var el = document.getElementById(firstId);
                if (el) {
                    el.classList.add('validation-error');
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            if (document.getElementById('wizardStep2Next')) document.getElementById('wizardStep2Next').disabled = true;
            showNotification('Validation failed. Fix the highlighted fields and try again.', 'error');
        } else if (res.status === 401) {
            if (resultDiv) resultDiv.className = 'validation-result error';
            if (resultDiv) resultDiv.innerHTML = '<p>Please login first</p>';
            if (document.getElementById('wizardStep2Next')) document.getElementById('wizardStep2Next').disabled = true;
            showNotification('Please login first', 'error');
        } else if (res.status === 403) {
            if (resultDiv) resultDiv.className = 'validation-result error';
            if (resultDiv) resultDiv.innerHTML = '<p>Current role has no permission</p>';
            if (document.getElementById('wizardStep2Next')) document.getElementById('wizardStep2Next').disabled = true;
            showNotification('Current role has no permission', 'error');
        } else {
            resultDiv.className = 'validation-result success';
            resultDiv.innerHTML = '<h4><i class="fas fa-check-circle"></i> Validation Successful</h4><p>' + (typeof t === 'function' ? t('teacher.spec.ready') : 'Teaching plan is complete and ready for pipeline generation.') + '</p>';
            currentSpec = result.normalized_spec || spec;
            if (document.getElementById('wizardStep2Next')) document.getElementById('wizardStep2Next').disabled = false;
            showNotification(typeof t === 'function' ? t('teacher.spec.validated') : 'Teaching plan validated successfully', 'success');
        }
    } catch (error) {
        console.error('Error validating spec:', error);
        var resultDiv = document.getElementById('specValidationResult');
        if (resultDiv) {
            resultDiv.classList.remove('hidden');
            resultDiv.className = 'validation-result error';
            resultDiv.innerHTML = '<p>Service temporarily unavailable. Please check your connection and try again.</p>';
        }
        showNotification('Validation request failed. Please try again.', 'error');
        if (document.getElementById('wizardStep2Next')) document.getElementById('wizardStep2Next').disabled = true;
    } finally {
        showLoading(false);
    }
}

function specForScript(s) {
    if (!s) return null;
    if (s.course_context) {
        var lo = s.learning_objectives || {};
        var knowledge = lo.knowledge || [];
        var skills = lo.skills || [];
        return {
            topic: s.course_context.topic,
            course: s.course_context.subject,
            duration_minutes: s.course_context.duration,
            learning_objectives: knowledge.concat(skills),
            task_type: (s.task_requirements && s.task_requirements.task_type) || 'structured_debate'
        };
    }
    return s;
}

function resetPipelineStageCards() {
    document.querySelectorAll('.pipeline-stage').forEach(function(stage) {
        var status = stage.querySelector('.stage-status');
        if (status) {
            status.removeAttribute('data-i18n');
            status.textContent = 'Pending';
            status.className = 'stage-status';
        }
        var inputEl = stage.querySelector('.input-summary');
        if (inputEl) {
            var spans = inputEl.querySelectorAll('span');
            var target = spans.length > 1 ? spans[1] : spans[0];
            if (target) { target.removeAttribute('data-i18n'); target.textContent = 'Waiting...'; }
        }
        var outputEl = stage.querySelector('.output-summary');
        if (outputEl) {
            var spans = outputEl.querySelectorAll('span');
            var target = spans.length > 1 ? spans[1] : spans[0];
            if (target) { target.removeAttribute('data-i18n'); target.textContent = 'Waiting...'; }
        }
        var dur = stage.querySelector('.stage-duration');
        if (dur) dur.textContent = '--';
    });
}

// Map backend stage_name to HTML data-stage attribute
var _stageNameToDataStage = {
    'planner': 'planner',
    'material_generator': 'material',
    'critic': 'critic',
    'refiner': 'refiner'
};
var _allDataStages = ['planner', 'material', 'critic', 'refiner'];
var _allStageNames = ['planner', 'material_generator', 'critic', 'refiner'];

function updateStageCardsFromResult(result) {
    var stages = result.stages || [];
    var seenDataStages = {};

    // Update provider/model/spec info from first stage or result
    if (stages.length > 0) {
        var first = stages[0];
        var provEl = document.getElementById('pipelineProvider');
        var modelEl = document.getElementById('pipelineModel');
        if (provEl) provEl.textContent = first.provider || '--';
        if (modelEl) modelEl.textContent = first.model || '--';
    }
    var specHashEl = document.getElementById('pipelineSpecHash');
    var cfgEl = document.getElementById('pipelineConfigFingerprint');
    if (specHashEl && result.spec_hash) specHashEl.textContent = result.spec_hash.substring(0, 16) + '...';
    if (cfgEl && result.config_fingerprint) cfgEl.textContent = result.config_fingerprint.substring(0, 16) + '...';

    stages.forEach(function(stage, idx) {
        var backendName = stage.stage_name || _allStageNames[idx];
        var dataStage = _stageNameToDataStage[backendName] || backendName;
        seenDataStages[dataStage] = true;

        var card = document.querySelector('[data-stage="' + dataStage + '"]');
        if (!card) return;

        _setStageStatus(card, stage.status);
        var durationEl = card.querySelector('.stage-duration');
        if (durationEl && stage.latency_ms) {
            durationEl.textContent = (stage.latency_ms / 1000).toFixed(1) + 's';
        }
        _setStageIO(card, stage);
    });

    // Mark stages that were not executed (e.g. refiner skipped) as "Skipped"
    _allDataStages.forEach(function(ds) {
        if (!seenDataStages[ds]) {
            var card = document.querySelector('[data-stage="' + ds + '"]');
            if (card) {
                var statusEl = card.querySelector('.stage-status');
                if (statusEl && statusEl.textContent === 'Pending') {
                    statusEl.textContent = 'Skipped';
                    statusEl.className = 'stage-status skipped';
                }
                var durationEl = card.querySelector('.stage-duration');
                if (durationEl) durationEl.textContent = '--';
            }
        }
    });
}

function showPipelineErrorPanel(issues, message, showRetryButton) {
    var panel = document.getElementById('pipelineErrorPanel');
    var listEl = document.getElementById('pipelineErrorList');
    var titleEl = document.getElementById('pipelineErrorTitle');
    var actionEl = document.getElementById('pipelineErrorAction');
    if (!panel) return;
    panel.classList.remove('hidden');
    if (titleEl) titleEl.textContent = message || 'Pipeline error';
    if (listEl) {
        if (Array.isArray(issues)) {
            listEl.innerHTML = issues.map(function(i) {
                var f = (i && i.field) ? i.field : 'spec';
                var r = (i && i.reason) ? i.reason : 'invalid';
                return '<li>' + escapeHtml(f + ' (' + r + ')') + '</li>';
            }).join('');
        } else if (typeof issues === 'string') {
            listEl.innerHTML = '<li>' + escapeHtml(issues) + '</li>';
        } else {
            listEl.innerHTML = '<li>' + escapeHtml(message || 'Pipeline error') + '</li>';
        }
    }
    if (actionEl) {
        if (showRetryButton) {
            actionEl.innerHTML = '<button class="btn-secondary" onclick="retryPipelineWithFallback()" style="margin-top: 10px;"><i class="fas fa-redo"></i> Retry with fallback provider</button>';
        } else {
            actionEl.textContent = 'Fix the fields in Step 2 and run again.';
        }
    }
}

function hidePipelineErrorPanel() {
    var panel = document.getElementById('pipelineErrorPanel');
    if (panel) panel.classList.add('hidden');
}

// M5: Guard against double-click / duplicate pipeline run
var pipelineRunInProgress = false;

// Step 3: Run Pipeline — preflight validate, script 404/401 handling, 422 issues in panel, no endless pending
async function runPipeline() {
    var runBtn = document.getElementById('runPipelineBtn');
    if (pipelineRunInProgress && runBtn) {
        runBtn.disabled = true;
        return;
    }
    pipelineRunInProgress = true;
    if (runBtn) { runBtn.disabled = true; runBtn.classList.add('btn-loading'); runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...'; }
    if (!currentSpec) {
        showNotification('Please complete teaching plan validation first', 'warning');
        pipelineRunInProgress = false;
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
        return;
    }
    hidePipelineErrorPanel();

    // Preflight: validate spec first; block run if 422
    try {
        var vRes = await fetch(API_BASE + '/spec/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentSpec),
            credentials: 'include'
        });
        var vData = await vRes.json().catch(function() { return {}; });
        if (vRes.status === 422 || !vData.valid) {
            showNotification('Teaching plan has errors. Fix them before running.', 'error');
            if (vData.issues && vData.issues.length) {
                goToStep(2);
                var firstId = firstErrorFieldIdFromPaths(vData.field_paths) || firstErrorFieldIdFromIssues(vData.issues);
                if (firstId) {
                    var el = document.getElementById(firstId);
                    if (el) { el.classList.add('validation-error'); el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
                }
            }
            return;
        }
    } catch (e) {
        showNotification('Could not validate teaching plan. Try again.', 'error');
        pipelineRunInProgress = false;
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
        return;
    }

    if (!currentScriptId) {
        var flat = specForScript(currentSpec);
        try {
            var res = await fetch(API_BASE + '/scripts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: (flat && flat.topic) ? flat.topic : 'New Script',
                    topic: (flat && flat.topic) ? flat.topic : '',
                    course_id: DEFAULT_COURSE_ID,
                    learning_objectives: (flat && flat.learning_objectives) ? flat.learning_objectives : [],
                    task_type: (flat && flat.task_type) ? flat.task_type : 'structured_debate',
                    duration_minutes: (flat && flat.duration_minutes) ? flat.duration_minutes : 90
                }),
                credentials: 'include'
            });
            if (res.ok) {
                var data = await res.json();
                currentScriptId = data.script && data.script.id;
                if (currentScriptId && typeof sessionStorage !== 'undefined') sessionStorage.setItem('cscl_current_script_id', currentScriptId);
            } else {
                if (res.status === 401) {
                    showNotification('Session expired, please login again', 'error');
                    pipelineRunInProgress = false;
                    if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
                    return;
                }
                showNotification('Failed to create script project', 'error');
                pipelineRunInProgress = false;
                if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
                return;
            }
        } catch (error) {
            console.error('Error creating script:', error);
            showNotification('Failed to create script project', 'error');
            pipelineRunInProgress = false;
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
            return;
        }
    }

    // Guard: GET script to avoid stale id / auth mismatch
    try {
        var getRes = await fetch(API_BASE + '/scripts/' + currentScriptId, { credentials: 'include' });
        if (getRes.status === 404) {
            currentScriptId = null;
            if (typeof sessionStorage !== 'undefined') sessionStorage.removeItem('cscl_current_script_id');
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
            showNotification('Script expired, please complete Step 2 again', 'warning');
            goToStep(2);
            return;
        }
        if (getRes.status === 401) {
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
            showNotification('Session expired, please login again', 'error');
            return;
        }
    } catch (e) {
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
        showNotification('Could not verify script. Try again.', 'error');
        return;
    }

    try {
        showLoading(true);
        resetPipelineStageCards();
        var idemKey = 'run-' + currentScriptId + '-' + (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now() + '-' + Math.random().toString(36).slice(2));
        var res = await fetch(API_BASE + '/scripts/' + currentScriptId + '/pipeline/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Idempotency-Key': idemKey
            },
            body: JSON.stringify({ spec: currentSpec, idempotency_key: idemKey }),
            credentials: 'include'
        });
        var result = await res.json().catch(function() { return {}; });

        if (res.status === 401) {
            pipelineRunInProgress = false;
            showNotification('Session expired, please login again', 'error');
            return;
        }
        if (res.status === 403) {
            pipelineRunInProgress = false;
            showNotification('Current role has no permission', 'error');
            return;
        }
        // 400: 未上传课程文档 / 缺少 course_id
        if (res.status === 400) {
            pipelineRunInProgress = false;
            var code = result.code || '';
            var errMsg = result.error || result.message || 'Request failed.';
            if (code === 'PREFLIGHT_NO_COURSE_DOCS') {
                errMsg = typeof t === 'function' ? t('teacher.pipeline.no_course_docs') : '当前课程下还没有上传文档。请先在左侧「课程文档」中上传 PDF 或文本，再点击运行生成。';
                showPipelineErrorPanel(errMsg, typeof t === 'function' ? t('teacher.pipeline.no_docs_title') : '请先上传课程文档', false);
                showNotification(errMsg, 'error');
                // Optionally open or highlight the course documents sidebar
                var docsSection = document.querySelector('[data-docs-section]') || document.getElementById('documentsView');
                if (docsSection) { docsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); var navItem = document.querySelector('[data-view="documents"]'); if (navItem) navItem.click(); }
            } else if (code === 'PREFLIGHT_MISSING_COURSE_ID') {
                showNotification(typeof t === 'function' ? t('teacher.pipeline.missing_course_id') : '请填写课程信息（Step 2 中的课程）后再运行。', 'error');
                goToStep(2);
            } else {
                showNotification(errMsg, 'error');
            }
            resetPipelineStageCards();
            return;
        }
        // S2.18: Handle 503 LLM_PROVIDER_NOT_READY
        if (res.status === 503) {
            if (result.code === 'LLM_PROVIDER_NOT_READY') {
                var errorMsg = result.error || 'Configured LLM provider is not runnable';
                var details = result.details || {};
                var reason = details.reason || 'Provider not available';
                showPipelineErrorPanel(
                    errorMsg + '. ' + reason,
                    'LLM Provider Not Ready',
                    true  // Show retry button
                );
                // Preserve spec in sessionStorage
                if (typeof sessionStorage !== 'undefined' && currentSpec) {
                    sessionStorage.setItem('cscl_current_spec', JSON.stringify(currentSpec));
                }
                showNotification(errorMsg, 'error');
            } else {
                showNotification('Service temporarily unavailable. You can use mock mode for testing.', 'warning');
                simulatePipelineRun();
            }
            pipelineRunInProgress = false;
            resetPipelineStageCards();
            return;
        }
        // S2.18: Handle 422 PIPELINE_FAILED with retry option
        if (!res.ok || res.status === 422) {
            if (res.status === 422 && result.issues && result.issues.length > 0) {
                showPipelineErrorPanel(result.issues, result.message || 'Spec validation failed.', false);
                goToStep(2);
                var firstField = result.issues[0] && result.issues[0].field;
                var firstId = firstField && pathToFieldId[firstField] ? pathToFieldId[firstField] : null;
                if (firstId) {
                    var el = document.getElementById(firstId);
                    if (el) { el.classList.add('validation-error'); el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
                }
                showNotification(result.message || 'Fix the fields above and run again.', 'error');
            } else if (result.code === 'PIPELINE_FAILED') {
                // Pipeline failed - show error with retry option
                var errorMsg = result.error || 'Pipeline execution failed';
                showPipelineErrorPanel(
                    errorMsg,
                    'Pipeline Failed',
                    true  // Show retry button
                );
                // Preserve spec in sessionStorage
                if (typeof sessionStorage !== 'undefined' && currentSpec) {
                    sessionStorage.setItem('cscl_current_spec', JSON.stringify(currentSpec));
                }
                showNotification(errorMsg, 'error');
            } else {
                showNotification(result.error || result.message || 'Pipeline failed', 'error');
            }
            pipelineRunInProgress = false;
            resetPipelineStageCards();
            return;
        }
        if (result.success && result.run_id) {
            currentPipelineRunId = result.run_id;
            try { sessionStorage.setItem('cscl_current_run_id', result.run_id); } catch (e) {}
            if (result.status === 'success' || result.status === 'completed') {
                showNotification('Generation completed!', 'success');
                updateStageCardsFromResult(result);
                var nextBtn = document.getElementById('wizardStep3Next');
                if (nextBtn) nextBtn.disabled = false;
                pipelineRunInProgress = false;
                showLoading(false);
                if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
            } else if (result.status === 'partial_failed') {
                showNotification('Generation partially completed. Some stages had errors.', 'warning');
                updateStageCardsFromResult(result);
                pipelineRunInProgress = false;
                showLoading(false);
                if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
            } else {
                showNotification('Pipeline started, please wait...', 'success');
                _pipelinePollingActive = true;
                pollPipelineStatus(result.run_id);
            }
        } else {
            showNotification('Pipeline failed to start', 'error');
            resetPipelineStageCards();
            pipelineRunInProgress = false;
            showLoading(false);
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
        }
    } catch (error) {
        console.error('Error running pipeline:', error);
        showNotification('Failed to run pipeline. Service may be unavailable.', 'error');
        resetPipelineStageCards();
        pipelineRunInProgress = false;
        showLoading(false);
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
    }
}

var _pollRetryCount = 0;
var _pollMaxRetries = 90;
async function pollPipelineStatus(runId) {
    _pipelinePollingActive = true;
    try {
        const res = await fetch(`${API_BASE}/pipeline/runs/${runId}`, {
            credentials: 'include'
        });

        if (res.status === 404) {
            _pollRetryCount++;
            if (_pollRetryCount < _pollMaxRetries) {
                setTimeout(() => pollPipelineStatus(runId), 2000);
            } else {
                _finishPolling('Pipeline run not found after timeout', 'error');
            }
            return;
        }

        if (res.ok) {
            _pollRetryCount = 0;
            const data = await res.json();
            updatePipelineVisualization(data);

            if (data.run.status === 'running') {
                setTimeout(() => pollPipelineStatus(runId), 2000);
            } else if (data.run.status === 'completed' || data.run.status === 'success') {
                var nextBtn = document.getElementById('wizardStep3Next');
                if (nextBtn) nextBtn.disabled = false;
                _finishPolling('Pipeline completed successfully', 'success');
            } else if (data.run.status === 'failed' || data.run.status === 'partial_failed') {
                _finishPolling('Pipeline finished with errors: ' + (data.run.error_message || 'unknown'), 'warning');
            }
        } else {
            _pollRetryCount++;
            if (_pollRetryCount < _pollMaxRetries) {
                setTimeout(() => pollPipelineStatus(runId), 2000);
            } else {
                _finishPolling('Pipeline polling failed', 'error');
            }
        }
    } catch (error) {
        console.error('Error polling pipeline:', error);
        _pollRetryCount++;
        if (_pollRetryCount < _pollMaxRetries) {
            setTimeout(() => pollPipelineStatus(runId), 3000);
        } else {
            _finishPolling('Pipeline polling failed', 'error');
        }
    }
}

function _finishPolling(message, level) {
    _pipelinePollingActive = false;
    pipelineRunInProgress = false;
    _pollRetryCount = 0;
    if (message) showNotification(message, level || 'success');
    showLoading(false);
    var runBtn = document.getElementById('runPipelineBtn');
    if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
}

async function restorePipelineState() {
    if (!currentScriptId) return;
    try {
        var res = await fetch(API_BASE + '/scripts/' + currentScriptId + '/pipeline/runs', { credentials: 'include' });
        if (!res.ok) return;
        var data = await res.json();
        var runs = data.runs || [];
        if (runs.length === 0) return;
        var latest = runs[0];
        currentPipelineRunId = latest.run_id;
        try { sessionStorage.setItem('cscl_current_run_id', latest.run_id); } catch (e) {}
        if (latest.status === 'running') {
            _pipelinePollingActive = true;
            var runBtn = document.getElementById('runPipelineBtn');
            if (runBtn) { runBtn.disabled = true; runBtn.classList.add('btn-loading'); runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...'; }
            showLoading(true);
            pollPipelineStatus(latest.run_id);
        } else if (latest.status === 'success' || latest.status === 'completed') {
            var detailRes = await fetch(API_BASE + '/pipeline/runs/' + latest.run_id, { credentials: 'include' });
            if (detailRes.ok) {
                var detailData = await detailRes.json();
                updatePipelineVisualization(detailData);
                var nextBtn = document.getElementById('wizardStep3Next');
                if (nextBtn) nextBtn.disabled = false;
            }
        } else if (latest.status === 'partial_failed' || latest.status === 'failed') {
            var detailRes2 = await fetch(API_BASE + '/pipeline/runs/' + latest.run_id, { credentials: 'include' });
            if (detailRes2.ok) {
                var detailData2 = await detailRes2.json();
                updatePipelineVisualization(detailData2);
            }
        }
    } catch (e) {
        console.warn('[teacher] restorePipelineState failed:', e);
    }
}

function updatePipelineVisualization(data) {
    var stages = data.stages || [];
    var run = data.run || {};
    
    // Update tech info
    if (stages.length > 0) {
        var firstStage = stages[0];
        var provEl = document.getElementById('pipelineProvider');
        var modelEl = document.getElementById('pipelineModel');
        if (provEl) provEl.textContent = firstStage.provider || '--';
        if (modelEl) modelEl.textContent = firstStage.model || '--';
    }
    var specHashEl = document.getElementById('pipelineSpecHash');
    var cfgEl = document.getElementById('pipelineConfigFingerprint');
    if (specHashEl) specHashEl.textContent = run.spec_hash ? run.spec_hash.substring(0, 16) + '...' : '--';
    if (cfgEl) cfgEl.textContent = run.config_fingerprint ? run.config_fingerprint.substring(0, 16) + '...' : '--';
    
    // Update stages using the same name mapping
    stages.forEach(function(stage, idx) {
        var backendName = stage.stage_name || stage.stage || _allStageNames[idx];
        var dataStage = _stageNameToDataStage[backendName] || backendName;
        var stageElement = document.querySelector('[data-stage="' + dataStage + '"]');
        if (stageElement) {
            _setStageStatus(stageElement, stage.status);
            var durationEl = stageElement.querySelector('.stage-duration');
            if (durationEl) {
                durationEl.textContent = stage.latency_ms ? (stage.latency_ms / 1000).toFixed(1) + 's'
                    : stage.duration_seconds ? stage.duration_seconds.toFixed(1) + 's' : '--';
            }
            _setStageIO(stageElement, stage);
        }
    });
}

function _setStageStatus(stageElement, status) {
    var statusEl = stageElement.querySelector('.stage-status');
    if (!statusEl) return;
    statusEl.removeAttribute('data-i18n');
    var label = status ? status.charAt(0).toUpperCase() + status.slice(1) : '--';
    statusEl.textContent = label;
    statusEl.className = 'stage-status ' + (status || '');
}

function _setStageIO(stageElement, stage) {
    var inputEl = stageElement.querySelector('.input-summary');
    var outputEl = stageElement.querySelector('.output-summary');
    if (inputEl) {
        var inputSpans = inputEl.querySelectorAll('span');
        var target = inputSpans.length > 1 ? inputSpans[1] : inputSpans[0];
        if (target) {
            target.removeAttribute('data-i18n');
            if (stage.status === 'success') target.textContent = 'Done';
            else if (stage.status === 'running') target.textContent = 'Processing...';
            else if (stage.status === 'failed') target.textContent = 'Error';
            else if (stage.status === 'skipped') target.textContent = 'Skipped';
        }
    }
    if (outputEl) {
        var outputSpans = outputEl.querySelectorAll('span');
        var target = outputSpans.length > 1 ? outputSpans[1] : outputSpans[0];
        if (target) {
            target.removeAttribute('data-i18n');
            if (stage.status === 'success') target.textContent = stage.output_json ? 'Generated' : 'Done';
            else if (stage.status === 'running') target.textContent = 'Waiting...';
            else if (stage.status === 'failed') target.textContent = stage.error_message ? stage.error_message.substring(0, 60) : 'Failed';
            else if (stage.status === 'skipped') target.textContent = 'Skipped';
        }
    }
}

// S2.18: Retry pipeline with fallback provider
async function retryPipelineWithFallback() {
    if (!currentScriptId) {
        showNotification('No script to retry', 'error');
        return;
    }
    
    // Restore spec from sessionStorage if available
    if (typeof sessionStorage !== 'undefined') {
        var savedSpec = sessionStorage.getItem('cscl_current_spec');
        if (savedSpec) {
            try {
                currentSpec = JSON.parse(savedSpec);
            } catch (e) {
                console.warn('Could not restore spec from sessionStorage:', e);
            }
        }
    }
    
    if (!currentSpec) {
        showNotification('No spec available to retry', 'error');
        return;
    }
    
    var runBtn = document.getElementById('runPipelineBtn');
    hidePipelineErrorPanel();
    
    try {
        showLoading(true);
        if (runBtn) { runBtn.disabled = true; runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Retrying...'; }
        resetPipelineStageCards();
        
        var res = await fetch(API_BASE + '/scripts/' + currentScriptId + '/pipeline/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                spec: currentSpec,
                generation_options: {
                    force_provider: 'openai'
                }
            }),
            credentials: 'include'
        });
        var result = await res.json().catch(function() { return {}; });
        
        if (res.status === 401) {
            showNotification('Session expired, please login again', 'error');
            return;
        }
        if (res.status === 403) {
            showNotification('Current role has no permission', 'error');
            return;
        }
        if (!res.ok) {
            showNotification(result.error || result.message || 'Retry failed', 'error');
            resetPipelineStageCards();
            return;
        }
        if (result.success && result.run_id) {
            currentPipelineRunId = result.run_id;
            try { sessionStorage.setItem('cscl_current_run_id', result.run_id); } catch (e) {}
            if (result.status === 'success' || result.status === 'completed') {
                showNotification('Pipeline retry completed!', 'success');
                updateStageCardsFromResult(result);
                var nextBtn = document.getElementById('wizardStep3Next');
                if (nextBtn) nextBtn.disabled = false;
                showLoading(false);
                if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
            } else {
                showNotification('Pipeline retry started', 'success');
                _pipelinePollingActive = true;
                pollPipelineStatus(result.run_id);
            }
        } else {
            showNotification('Pipeline retry failed to start', 'error');
            resetPipelineStageCards();
            showLoading(false);
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
        }
    } catch (error) {
        console.error('Error retrying pipeline:', error);
        showNotification('Failed to retry pipeline. Service may be unavailable.', 'error');
        resetPipelineStageCards();
        showLoading(false);
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> Run Pipeline'; }
    }
}

function simulatePipelineRun() {
    const stages = ['planner', 'material', 'critic', 'refiner'];
    let currentStage = 0;
    
    const runStage = () => {
        if (currentStage >= stages.length) {
            document.getElementById('wizardStep3Next').disabled = false;
            showNotification('Pipeline simulation completed', 'success');
            return;
        }
        
        const stage = stages[currentStage];
        const stageElement = document.querySelector(`[data-stage="${stage}"]`);
        if (stageElement) {
            const statusEl = stageElement.querySelector('.stage-status');
            statusEl.textContent = 'Running';
            statusEl.className = 'stage-status running';
            
            setTimeout(() => {
                statusEl.textContent = 'Completed';
                statusEl.className = 'stage-status completed';
                stageElement.querySelector('.stage-duration').textContent = '2.5s';
                stageElement.querySelector('.input-summary span').textContent = (typeof t === 'function' ? t('teacher.pipeline.spec_validated') : 'Teaching plan validated') + '...';
                stageElement.querySelector('.output-summary span').textContent = 'Stage output generated...';
                currentStage++;
                runStage();
            }, 1500);
        }
    };
    
    runStage();
}

// Step 4: Finalize & Publish
async function finalizeScript() {
    if (!currentScriptId) {
        showNotification('No script to finalize', 'error');
        return;
    }
    
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/scripts/${currentScriptId}/finalize`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (res.ok) {
            showNotification('Script finalized successfully', 'success');
            document.getElementById('publishBtn').disabled = false;
        } else if (res.status === 401) {
            showNotification('Please login first', 'error');
        } else if (res.status === 403) {
            showNotification('Current role has no permission', 'error');
        } else if (res.status === 404) {
            showNotification('Script not found or not yet created', 'error');
        } else {
            showNotification('Failed to finalize script', 'error');
        }
    } catch (error) {
        console.error('Error finalizing script:', error);
        showNotification('Failed to finalize script', 'error');
    } finally {
        showLoading(false);
    }
}

async function publishScript() {
    if (!currentScriptId) {
        showNotification('No script to publish', 'error');
        return;
    }
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/scripts/${currentScriptId}/publish`, { method: 'POST', credentials: 'include' });
        const data = await res.json().catch(function() { return {}; });
        if (res.ok && (data.share_code || data.already_published)) {
            var studentUrl = data.student_url || (window.location.origin + '/student?code=' + (data.share_code || ''));
            showPublishShareModal(data.share_code || '', studentUrl);
            if (data.already_published) showNotification('Activity already published; share link shown.', 'info');
            else showNotification('Published successfully', 'success');
        } else if (res.status === 401) {
            showNotification('Please login first', 'error');
        } else if (res.status === 403) {
            showNotification('Current role has no permission', 'error');
        } else if (res.status === 404) {
            showNotification('Script not found', 'error');
        } else {
            showNotification(data.error || 'Failed to publish', 'error');
        }
    } catch (e) {
        console.error('publishScript error', e);
        showNotification('Failed to publish', 'error');
    } finally {
        showLoading(false);
    }
}

function showPublishShareModal(shareCode, studentUrl) {
    var modal = document.getElementById('publishShareModal');
    var codeIn = document.getElementById('publishShareCodeInput');
    var urlIn = document.getElementById('publishShareUrlInput');
    if (modal && codeIn && urlIn) {
        codeIn.value = shareCode || '';
        urlIn.value = studentUrl || (window.location.origin + '/student?code=' + (shareCode || ''));
        modal.classList.remove('hidden');
    }
}

function closePublishShareModal() {
    var modal = document.getElementById('publishShareModal');
    if (modal) modal.classList.add('hidden');
}

function copyPublishShareCode() {
    var el = document.getElementById('publishShareCodeInput');
    if (el && el.value) {
        navigator.clipboard.writeText(el.value).then(function() { showNotification('Invite code copied', 'success'); }).catch(function() { showNotification('Copy failed', 'error'); });
    }
}

function copyPublishShareUrl() {
    var el = document.getElementById('publishShareUrlInput');
    if (el && el.value) {
        navigator.clipboard.writeText(el.value).then(function() { showNotification('Link copied', 'success'); }).catch(function() { showNotification('Copy failed', 'error'); });
    }
}

async function viewQualityReport() {
    if (!currentScriptId) {
        showNotification('No script selected', 'error');
        return;
    }
    
    switchView('quality-report-detail');
    await loadQualityReportDetail(currentScriptId);
}

async function exportScript() {
    if (!currentScriptId) {
        showNotification('No script to export', 'error');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/scripts/${currentScriptId}/export`, {
            credentials: 'include'
        });
        
        if (res.ok) {
            const data = await res.json();
            const blob = new Blob([JSON.stringify(data.script, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `script_${currentScriptId}.json`;
            a.click();
            URL.revokeObjectURL(url);
            showNotification('Script exported successfully', 'success');
        } else if (res.status === 401) {
            showNotification('Please login first', 'error');
        } else if (res.status === 403) {
            showNotification('Current role has no permission', 'error');
        } else if (res.status === 404) {
            showNotification('Script not found or not yet created', 'error');
        } else {
            showNotification('Failed to export script', 'error');
        }
    } catch (error) {
        console.error('Error exporting script:', error);
        showNotification('Failed to export script', 'error');
    }
}

// Quality Report
async function loadQualityReports() {
    const container = document.getElementById('qualityReportContent');
    try {
        showLoading(true);
        
        // Load scripts if not loaded
        if (scripts.length === 0) {
            await loadScripts();
        }
        
        if (scripts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-chart-line"></i>
                    <h4>No Script Projects</h4>
                    <p>Create a script project first to view quality reports.</p>
                    <button class="btn-primary" onclick="switchView('scripts')">
                        <i class="fas fa-plus"></i>
                        Create Script Project
                    </button>
                </div>
            `;
            return;
        }
        
        // Show list of scripts with quality report links
        container.innerHTML = `
            <div class="quality-reports-list">
                <h3>Select a script to view quality report:</h3>
                <div class="scripts-grid">
                    ${scripts.map(script => `
                        <div class="script-card" onclick="viewScriptQuality('${script.id}')">
                            <div class="script-card-header">
                                <h4>${escapeHtml(script.title || 'Untitled')}</h4>
                                <span class="status-badge ${script.status}">${script.status}</span>
                            </div>
                            <div class="script-card-content">
                                <p><strong>Topic:</strong> ${escapeHtml(script.topic || 'N/A')}</p>
                            </div>
                            <div class="script-card-footer">
                                <button class="btn-primary" onclick="event.stopPropagation(); viewScriptQuality('${script.id}')">
                                    <i class="fas fa-chart-line"></i>
                                    View Quality Report
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading quality reports:', error);
        container.innerHTML = '<div class="empty-state"><p>Error loading quality reports</p></div>';
    } finally {
        showLoading(false);
    }
}

async function loadQualityReportDetail(scriptId) {
    const container = document.getElementById('qualityReportDetailContent');
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/scripts/${scriptId}/quality-report`, {
            credentials: 'include'
        });
        
        if (res.status === 401) {
            container.innerHTML = '<div class="empty-state"><p>Please login first</p></div>';
            return;
        }
        
        if (res.status === 403) {
            container.innerHTML = '<div class="empty-state"><p>Current role has no permission</p></div>';
            return;
        }
        
        if (res.status === 404) {
            container.innerHTML = '<div class="empty-state"><p>Resource not found or not yet created</p></div>';
            return;
        }
        
        if (res.ok) {
            const data = await res.json();
            renderQualityReport(data.report);
        } else {
            container.innerHTML = '<div class="empty-state"><p>Failed to load quality report</p></div>';
        }
    } catch (error) {
        console.error('Error loading quality report:', error);
        container.innerHTML = '<div class="empty-state"><p>Error loading quality report</p></div>';
    } finally {
        showLoading(false);
    }
}

function renderQualityReport(report) {
    const container = document.getElementById('qualityReportDetailContent');
    
    const dimensions = [
        { key: 'coverage', label: 'Coverage', icon: 'fas fa-check-circle' },
        { key: 'pedagogical_alignment', label: 'Pedagogical Alignment', icon: 'fas fa-graduation-cap' },
        { key: 'argumentation_support', label: 'Argumentation Support', icon: 'fas fa-comments' },
        { key: 'grounding', label: 'Grounding', icon: 'fas fa-anchor' },
        { key: 'safety_checks', label: 'Safety Checks', icon: 'fas fa-shield-alt' },
        { key: 'teacher_in_loop', label: 'Teacher in Loop', icon: 'fas fa-user-check' }
    ];
    
    container.innerHTML = `
        <div class="quality-report-grid">
            ${dimensions.map(dim => {
                const metric = report[dim.key] || {};
                const score = metric.score || 0;
                const status = getStatusFromScore(score);
                const evidence = metric.evidence || [];
                const actionTip = metric.action_tip || 'No specific action needed';
                
                return `
                    <div class="quality-dimension-card ${status}">
                        <div class="dimension-header">
                            <div class="dimension-icon">
                                <i class="${dim.icon}"></i>
                            </div>
                            <div class="dimension-info">
                                <h4>${dim.label}</h4>
                                <div class="dimension-score">
                                    <span class="score-value">${score}/100</span>
                                    <span class="score-status ${status}">${status.toUpperCase()}</span>
                                </div>
                            </div>
                        </div>
                        <div class="dimension-body">
                            <div class="dimension-evidence">
                                <h5>Evidence:</h5>
                                ${evidence.length > 0 
                                    ? `<ul>${evidence.map(e => `<li>${escapeHtml(e)}</li>`).join('')}</ul>`
                                    : '<p>No evidence available</p>'
                                }
                            </div>
                            <div class="dimension-action">
                                <h5>Action Tip:</h5>
                                <p>${escapeHtml(actionTip)}</p>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function getStatusFromScore(score) {
    if (score >= 80) return 'good';
    if (score >= 60) return 'warning';
    return 'poor';
}

// Pipeline Runs
async function loadPipelineRuns() {
    const container = document.getElementById('pipelineRunsList');
    try {
        showLoading(true);
        
        if (scripts.length === 0) {
            await loadScripts();
        }
        
        if (scripts.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No scripts available. Create a script project first.</p></div>';
            return;
        }
        
        // Load runs for all scripts
        const allRuns = [];
        for (const script of scripts.slice(0, 5)) {
            try {
                const res = await fetch(`${API_BASE}/scripts/${script.id}/pipeline/runs`, {
                    credentials: 'include'
                });
                if (res.ok) {
                    const data = await res.json();
                    allRuns.push(...(data.runs || []));
                }
            } catch (e) {
                console.error('Error loading runs for script:', e);
            }
        }
        
        if (allRuns.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No pipeline runs found</p></div>';
        } else {
            container.innerHTML = allRuns.map(run => `
                <div class="pipeline-run-card" onclick="viewPipelineRun('${run.run_id}')">
                    <div class="run-header">
                        <h4>Run ${run.run_id.substring(0, 8)}...</h4>
                        <span class="status-badge ${run.status}">${run.status}</span>
                    </div>
                    <div class="run-content">
                        <p><strong>Script:</strong> ${run.script_id.substring(0, 8)}...</p>
                        <p><strong>Created:</strong> ${formatTime(run.created_at)}</p>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading pipeline runs:', error);
        container.innerHTML = '<div class="empty-state"><p>Error loading pipeline runs</p></div>';
    } finally {
        showLoading(false);
    }
}

async function viewPipelineRun(runId) {
    switchView('pipeline-run-detail');
    const container = document.getElementById('pipelineRunDetailContent');
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/pipeline/runs/${runId}`, {
            credentials: 'include'
        });
        
        if (res.ok) {
            const data = await res.json();
            updatePipelineVisualization(data);
            container.innerHTML = '<div class="pipeline-visualization">' + document.getElementById('pipelineVisualization').innerHTML + '</div>';
        } else {
            container.innerHTML = '<div class="empty-state"><p>Failed to load pipeline run details</p></div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state"><p>Error loading pipeline run details</p></div>';
    } finally {
        showLoading(false);
    }
}

// Utility Functions
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.toggle('hidden', !show);
    }
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    if (notification) {
        notification.textContent = message;
        notification.className = `notification show ${type}`;
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(timeString) {
    if (!timeString) return 'N/A';
    const date = new Date(timeString);
    return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function openScript(scriptId) {
    currentScriptId = scriptId;
    switchView('scripts');
}

function viewScriptQuality(scriptId) {
    currentScriptId = scriptId;
    switchView('quality-report-detail');
    loadQualityReportDetail(scriptId);
}

function uploadSyllabus() {
    createNewScriptProject();
    // Auto-advance to step 2 after a moment
    setTimeout(() => {
        wizardStep = 2;
        updateWizardProgress();
    }, 100);
}

function openLastPipeline() {
    switchView('pipeline-runs');
    loadPipelineRuns();
}

// Standalone Spec Validation
function fillStandaloneDemoSpec() {
    const demoSpec = {
        course: "Introduction to Data Science",
        topic: "Algorithmic Fairness in Education",
        duration_minutes: 90,
        mode: "Sync",
        class_size: 30,
        learning_objectives: [
            "Explain basic fairness metrics",
            "Compare trade-offs between accuracy and fairness",
            "Construct evidence-based group arguments"
        ],
        task_type: "structured_debate",
        expected_output: [
            "Group argument map",
            "300-word joint reflection"
        ]
    };
    
    document.getElementById('standaloneSpecCourse').value = demoSpec.course;
    document.getElementById('standaloneSpecTopic').value = demoSpec.topic;
    document.getElementById('standaloneSpecDuration').value = demoSpec.duration_minutes;
    document.getElementById('standaloneSpecMode').value = demoSpec.mode;
    document.getElementById('standaloneSpecClassSize').value = demoSpec.class_size;
    document.getElementById('standaloneSpecObjectives').value = demoSpec.learning_objectives.join('\n');
    document.getElementById('standaloneSpecTaskType').value = demoSpec.task_type;
    document.getElementById('standaloneSpecExpectedOutput').value = demoSpec.expected_output.join('\n');
}

async function validateStandaloneSpec() {
    const form = document.getElementById('standaloneSpecForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const spec = {
        course: document.getElementById('standaloneSpecCourse').value,
        topic: document.getElementById('standaloneSpecTopic').value,
        duration_minutes: parseInt(document.getElementById('standaloneSpecDuration').value),
        mode: document.getElementById('standaloneSpecMode').value,
        class_size: parseInt(document.getElementById('standaloneSpecClassSize').value),
        learning_objectives: document.getElementById('standaloneSpecObjectives').value.split('\n').filter(s => s.trim()),
        task_type: document.getElementById('standaloneSpecTaskType').value,
        expected_output: document.getElementById('standaloneSpecExpectedOutput').value.split('\n').filter(s => s.trim())
    };
    
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/spec/validate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(spec),
            credentials: 'include'
        });
        
        const result = await res.json();
        const resultDiv = document.getElementById('standaloneValidationResult');
        resultDiv.classList.remove('hidden');
        
        if (res.status === 422 || !result.valid) {
            resultDiv.className = 'validation-result error';
            resultDiv.innerHTML = `
                <h4><i class="fas fa-exclamation-circle"></i> Validation Failed</h4>
                <ul>
                    ${result.issues.map(issue => `<li>${escapeHtml(issue)}</li>`).join('')}
                </ul>
                <p><strong>Action:</strong> Please fix the issues above and try again.</p>
            `;
        } else if (res.status === 401) {
            resultDiv.className = 'validation-result error';
            resultDiv.innerHTML = '<p>Please login first</p>';
        } else if (res.status === 403) {
            resultDiv.className = 'validation-result error';
            resultDiv.innerHTML = '<p>Current role has no permission</p>';
        } else {
            resultDiv.className = 'validation-result success';
            resultDiv.innerHTML = `
                <h4><i class="fas fa-check-circle"></i> Validation Successful</h4>
                <p>${typeof t === 'function' ? t('teacher.spec.ready') : 'Teaching plan is complete and ready for pipeline generation.'}</p>
                <button class="btn-primary" onclick="createNewScriptProject()" style="margin-top: 1rem;">
                    <i class="fas fa-arrow-right"></i>
                    Create Script Project
                </button>
            `;
            showNotification(typeof t === 'function' ? t('teacher.spec.validated') : 'Teaching plan validated successfully', 'success');
        }
    } catch (error) {
        console.error('Error validating spec:', error);
        const resultDiv = document.getElementById('standaloneValidationResult');
        resultDiv.classList.remove('hidden');
        resultDiv.className = 'validation-result error';
        resultDiv.innerHTML = '<p>Service temporarily unavailable. You can continue with mock mode.</p>';
    } finally {
        showLoading(false);
    }
}

// Document Management
async function loadDocuments() {
    const container = document.getElementById('documentsList');
    try {
        showLoading(true);
        const courseId = DEFAULT_COURSE_ID;
        const res = await fetch(`${API_BASE}/courses/${courseId}/docs`, {
            credentials: 'include'
        });
        
        if (res.status === 401) {
            container.innerHTML = '<div class="empty-state"><p>Please login first</p></div>';
            return;
        }
        
        if (res.status === 403) {
            container.innerHTML = '<div class="empty-state"><p>Current role has no permission</p></div>';
            return;
        }
        
        if (res.ok) {
            const data = await res.json();
            const documents = data.documents || [];
            
            if (documents.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-book"></i>
                        <h4>No Course Documents</h4>
                        <p>Upload course documents to enable RAG retrieval for script generation.</p>
                        <button class="btn-primary" onclick="uploadDocument()">
                            <i class="fas fa-upload"></i>
                            Upload First Document
                        </button>
                    </div>
                `;
            } else {
                container.innerHTML = documents.map(doc => {
                    // Only show extracted_text_preview, never raw file bytes; hide if looks like PDF binary
                    var preview = doc.extracted_text_preview;
                    if (preview && typeof preview === 'string' && looksLikePdfBinary(preview)) preview = null;
                    const previewHtml = preview
                        ? `<div class="document-preview"><pre>${escapeHtml(preview)}</pre></div>`
                        : `<div class="document-preview empty"><p><i class="fas fa-info-circle"></i> 未提取到文本</p></div>`;
                    
                    return `
                    <div class="document-card">
                        <div class="document-header">
                            <h4>${escapeHtml(doc.title || 'Untitled')}</h4>
                            <span class="document-type">${doc.mime_type || 'text/plain'}</span>
                        </div>
                        <div class="document-content">
                            <p><strong>Uploaded:</strong> ${formatTime(doc.created_at)}</p>
                            <p><strong>Chunks:</strong> ${doc.chunks_count || 0}</p>
                            ${previewHtml}
                        </div>
                        <div class="document-actions">
                            <button class="btn-primary btn-sm" onclick="applyPrefillFromDoc('${doc.id}')" title="Use this document to suggest form fields">
                                <i class="fas fa-magic"></i>
                                \u586b\u5145\u5efa\u8bae
                            </button>
                            <button class="btn-secondary btn-sm" onclick="deleteDocument('${doc.id}')">
                                <i class="fas fa-trash"></i>
                                Delete
                            </button>
                        </div>
                    </div>
                `;
                }).join('');
            }
        } else {
            container.innerHTML = '<div class="empty-state"><p>Failed to load documents</p></div>';
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        container.innerHTML = '<div class="empty-state"><p>Error loading documents</p></div>';
    } finally {
        showLoading(false);
    }
}

async function applyPrefillFromDoc(docId) {
    try {
        showLoading(true);
        const courseId = DEFAULT_COURSE_ID;
        const res = await fetch(`${API_BASE}/courses/${courseId}/docs/${docId}/prefill`, { credentials: 'include' });
        const data = await res.json();
        if (!res.ok) {
            showNotification(data.message || 'Failed to get suggestions', 'error');
            return;
        }
        const sug = data.suggestions || {};
        const v = function (key) { var s = sug[key]; return s && s.value !== undefined ? s.value : ''; };
        const spec = {
            course: v('course_title') || v('subject'),
            topic: v('topic'),
            duration_minutes: typeof v('duration') === 'number' ? v('duration') : (parseInt(v('duration'), 10) || 90),
            class_size: typeof v('class_size') === 'number' ? v('class_size') : (parseInt(v('class_size'), 10) || 30),
            mode: 'sync',
            course_context: v('description'),
            learning_objectives: Array.isArray(v('learning_outcomes')) ? v('learning_outcomes') : (v('learning_outcomes') ? [v('learning_outcomes')] : []),
            task_type: v('task_type') || 'structured_debate',
            expected_output: v('expected_output'),
            requirements_text: v('requirements_text')
        };
        if (typeof fillSpecForm === 'function') fillSpecForm(spec);
        if (data.warnings && data.warnings.length) showNotification(data.warnings[0], 'warning');
        else showNotification('\u5df2\u586b\u5165\u5efa\u8bae\uff0c\u8bf7\u786e\u8ba4\u6216\u4fee\u6539\u540e\u518d\u9a8c\u8bc1', 'success');
        if (typeof goToStep === 'function') goToStep(2);
    } catch (e) {
        console.error('Prefill error:', e);
        showNotification('Could not load suggestions. Try again.', 'error');
    } finally {
        showLoading(false);
    }
}

function uploadDocument() {
    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt,.md,.pdf';
    input.onchange = async function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', file.name);
        
        try {
            showLoading(true);
            const courseId = DEFAULT_COURSE_ID;
            const res = await fetch(`${API_BASE}/courses/${courseId}/docs/upload`, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });
            
            const result = await res.json();
            
            if (res.ok) {
                // Only use extracted_text_preview, never raw file bytes
                var preview = result.extracted_text_preview;
                // Backend already filters binary content via safe_preview_or_none
                // Double-check on frontend for safety
                if (preview && typeof preview === 'string' && looksLikePdfBinary(preview)) {
                    showNotification(typeof t === 'function' ? t('teacher.pdf.parse_failed_binary') : 'Parsing failed: binary PDF content detected. Please re-upload or use another file.', 'error');
                    return;
                }
                showNotification('Document uploaded successfully', 'success');
                loadDocuments(); // Will display extracted_text_preview or empty state
            } else {
                var code = result.code || '';
                var msg = typeof t === 'function'
                    ? (code === 'PDF_PARSE_FAILED' ? t('teacher.pdf.parse_failed_binary')
                        : code === 'EMPTY_EXTRACTED_TEXT' ? t('teacher.pdf.parse_failed_empty')
                        : code === 'TEXT_TOO_SHORT' ? t('teacher.pdf.parse_failed_short')
                        : t('teacher.pdf.parse_failed_generic'))
                    : 'Extraction failed. Please try again or use another file.';
                showNotification(msg, 'error');
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            showNotification(typeof t === 'function' ? t('teacher.pdf.parse_failed_generic') : 'Extraction failed. Please try again or use another file.', 'error');
        } finally {
            showLoading(false);
        }
    };
    input.click();
}

async function deleteDocument(docId) {
    if (!confirm('Are you sure you want to delete this document?')) {
        return;
    }
    
    try {
        showLoading(true);
        const courseId = DEFAULT_COURSE_ID;
        const res = await fetch(`${API_BASE}/courses/${courseId}/docs/${docId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (res.ok) {
            showNotification('Document deleted successfully', 'success');
            loadDocuments();
        } else {
            const result = await res.json();
            showNotification(result.error || 'Delete failed', 'error');
        }
    } catch (error) {
        console.error('Error deleting document:', error);
        showNotification('Delete failed', 'error');
    } finally {
        showLoading(false);
    }
}

// Decision Timeline
async function loadDecisionTimeline() {
    const container = document.getElementById('decisionTimelineContent');
    try {
        showLoading(true);
        
        // Try to load decisions for all scripts
        if (scripts.length === 0) {
            await loadScripts();
        }
        
        if (scripts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h4>No Decisions Yet</h4>
                    <p>Decision timeline will appear here after you create and modify script projects.</p>
                    <button class="btn-primary" onclick="switchView('scripts')">
                        <i class="fas fa-folder-open"></i>
                        Create Script Project
                    </button>
                </div>
            `;
            return;
        }
        
        // Load decisions for first script as example
        const scriptId = scripts[0].id;
        const res = await fetch(`${API_BASE}/scripts/${scriptId}/decisions`, {
            credentials: 'include'
        });
        
        if (res.ok) {
            const data = await res.json();
            const decisions = data.decisions || [];
            
            if (decisions.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-history"></i>
                        <h4>No Decisions Yet</h4>
                        <p>Decision timeline will appear here after you create and modify script projects.</p>
                    </div>
                `;
            } else {
                container.innerHTML = decisions.map(decision => `
                    <div class="decision-item">
                        <div class="decision-header">
                            <h4>${escapeHtml(decision.decision_type || 'Unknown')}</h4>
                            <span class="decision-time">${formatTime(decision.created_at)}</span>
                        </div>
                        <div class="decision-content">
                            <p><strong>Target:</strong> ${escapeHtml(decision.target_type || 'N/A')}</p>
                            ${decision.reason ? `<p><strong>Reason:</strong> ${escapeHtml(decision.reason)}</p>` : ''}
                        </div>
                    </div>
                `).join('');
            }
        } else if (res.status === 404) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h4>No Decisions Yet</h4>
                    <p>Decision timeline will appear here after you create and modify script projects.</p>
                </div>
            `;
        } else {
            container.innerHTML = '<div class="empty-state"><p>Failed to load decision timeline</p></div>';
        }
    } catch (error) {
        console.error('Error loading decision timeline:', error);
        container.innerHTML = '<div class="empty-state"><p>Error loading decision timeline</p></div>';
    } finally {
        showLoading(false);
    }
}

// Publish View
async function loadPublishView() {
    const container = document.getElementById('publishContent');
    try {
        await loadScripts();
        const readyScripts = scripts.filter(s => s.status === 'final');
        
        if (readyScripts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-rocket"></i>
                    <h4>No Scripts Ready to Publish</h4>
                    <p>Finalize a script project to make it available for publishing.</p>
                    <button class="btn-primary" onclick="switchView('scripts')">
                        <i class="fas fa-folder-open"></i>
                        View Script Projects
                    </button>
                </div>
            `;
        } else {
            container.innerHTML = readyScripts.map(script => `
                <div class="script-card">
                    <div class="script-card-header">
                        <h4>${escapeHtml(script.title || 'Untitled')}</h4>
                        <span class="status-badge final">Ready</span>
                    </div>
                    <div class="script-card-content">
                        <p><strong>Topic:</strong> ${escapeHtml(script.topic || 'N/A')}</p>
                    </div>
                    <div class="script-card-footer">
                        <button class="btn-primary" onclick="publishScriptById('${script.id}')">
                            <i class="fas fa-rocket"></i>
                            Publish Activity
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state"><p>Error loading publish view</p></div>';
    }
}

async function publishScriptById(scriptId) {
    if (!scriptId) {
        showNotification('No script to publish', 'error');
        return;
    }
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/scripts/${scriptId}/publish`, { method: 'POST', credentials: 'include' });
        const data = await res.json().catch(function() { return {}; });
        if (res.ok && (data.share_code || data.already_published)) {
            const studentUrl = data.student_url || (window.location.origin + '/student?code=' + (data.share_code || ''));
            showPublishShareModal(data.share_code || '', studentUrl);
            if (data.already_published) showNotification('Activity already published; share link shown.', 'info');
            else showNotification('Published successfully', 'success');
        } else if (res.status === 401) {
            showNotification('Please login first', 'error');
        } else if (res.status === 403) {
            showNotification('Current role has no permission', 'error');
        } else if (res.status === 404) {
            showNotification('Script not found', 'error');
        } else {
            showNotification(data.error || 'Failed to publish', 'error');
        }
    } catch (e) {
        console.error('publishScriptById error', e);
        showNotification('Failed to publish', 'error');
    } finally {
        showLoading(false);
    }
}

// S2.16/S2.17: global compatibility fallback for any remaining inline handlers / old cache
if (typeof goToStep !== 'undefined') { window.goToStep = goToStep; }
if (typeof switchView !== 'undefined') { window.switchView = switchView; }
if (typeof startNewActivity !== 'undefined') { window.startNewActivity = startNewActivity; }
if (typeof uploadDocument !== 'undefined') { window.importCourseDocument = uploadDocument; }
if (typeof validateStandaloneSpec !== 'undefined') { window.validateObjectives = validateStandaloneSpec; }
if (typeof validateSpec !== 'undefined' && !window.validateObjectives) { window.validateObjectives = validateSpec; }
if (typeof runPipeline !== 'undefined') { window.generateScript = runPipeline; }
