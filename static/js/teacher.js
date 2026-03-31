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

// B1/B2: AI Enhancement Settings
let aiEnhancementSettings = {
    image_generation: false,
    web_retrieval: false
};
let pipelineRuns = [];
let wizardFolderId = null;  // Track current folder context when creating activities from within a folder

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
        // Folder navigation tab switching
        if (btn.classList && btn.classList.contains('folder-nav-item')) {
            var folderTab = btn.getAttribute('data-folder-tab');
            if (folderTab) {
                try {
                    console.log('[teacher] action: folder-tab-' + folderTab);
                    e.preventDefault();
                    if (typeof switchFolderTab === 'function') switchFolderTab(folderTab);
                } catch (err) {
                    console.error('[teacher] handler error folder tab', err);
                }
                return;
            }
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
        showNotification(t('teacher.notify.service_unavailable'), 'warning');
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
            case 'folders':
                loadFolders();
                break;
            case 'folder-detail':
                // loaded by openFolder()
                break;
            case 'scripts':
                loadScripts();
                break;
            case 'spec-validation':
                break;
            case 'pipeline-runs':
                loadPipelineRuns();
                break;
            case 'documents':
                loadDocuments();
                break;
            case 'decisions':
                // Decision Records view is no longer in sidebar; kept for compatibility
                // loadDecisionTimeline() is called when needed internally
                break;
            case 'quality-reports':
                loadQualityReports();
                break;
            case 'publish':
                loadPublishView();
                break;
            case 'settings':
                initSettingsPage();
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
// ── Course Folder functions ──────────────────────────────────────────
var currentFolderId = null;

async function loadFolders() {
    var container = document.getElementById('foldersList');
    if (!container) return;
    container.innerHTML = '<div class="loading-placeholder"><i class="fas fa-spinner fa-spin"></i><p>' + t('common.loading') + '</p></div>';
    try {
        var res = await fetch(API_BASE + '/folders', { credentials: 'include' });
        var data = await res.json();
        var folders = data.folders || [];
        if (folders.length === 0) {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-folder"></i><h4>' + t('teacher.quality.no_scripts', '暂无课程文件夹') + '</h4><p>' + t('teacher.home.title', '创建你的第一个课程文件夹') + '</p><button class="btn-primary" onclick="createNewFolder()"><i class="fas fa-plus"></i> ' + t('teacher.folders.create') + '</button></div>';
            return;
        }
        var html = '';
        folders.forEach(function(f) {
            html += '<div class="script-card folder-card">';
            html += '<div class="script-card-header" onclick="openFolder(\'' + f.id + '\')" style="cursor: pointer;"><i class="fas fa-folder" style="color: var(--primary-color); margin-right: 0.5rem;"></i><h4>' + _esc(f.name) + '</h4></div>';
            if (f.description) html += '<p class="script-card-meta" onclick="openFolder(\'' + f.id + '\')" style="cursor: pointer;">' + _esc(f.description) + '</p>';
            var activityCountText = (typeof t === 'function')
                ? (f.activity_count === 0 ? t('teacher.folder.activity_count_zero') : t('teacher.folder.activity_count').replace('{n}', f.activity_count || 0))
                : (f.activity_count || 0) + ' ' + t('teacher.folder.activity_count', '个活动');
            html += '<div class="script-card-footer" onclick="openFolder(\'' + f.id + '\')" style="cursor: pointer;"><span>' + activityCountText + '</span>';
            html += '<span>' + (f.created_at ? new Date(f.created_at).toLocaleDateString() : '') + '</span></div>';
            html += '<div class="folder-card-actions" style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color);">';
            html += '<button class="btn-secondary btn-sm" onclick="event.stopPropagation(); deleteFolder(\'' + f.id + '\', \'' + _esc(f.name).replace(/\\/g, '\\\\').replace(/\'/g, "\\'") + '\', ' + (f.activity_count || 0) + ')" title="' + t('common.delete') + '" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">';
            html += '<i class="fas fa-trash"></i> ' + t('common.delete') + '';
            html += '</button>';
            html += '</div>';
            html += '</div>';
        });
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.load_failed') + ': ' + e.message + '</p></div>';
    }
}

async function createNewFolder() {
    var promptText = (typeof t === 'function') ? t('teacher.folder.prompt_name') : '请输入课程文件夹名称：';
    var name = prompt(promptText);
    if (!name || !name.trim()) return;
    try {
        var res = await fetch(API_BASE + '/folders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name.trim() }),
            credentials: 'include'
        });
        var data = await res.json();
        if (data.success) {
            showNotification((typeof t === 'function') ? t('teacher.folder.create_success') : '课程文件夹已创建', 'success');
            loadFolders();
            // Auto-set as current folder and course_id for wizard
            currentFolderId = data.folder.id;
        } else {
            showNotification(data.error || ((typeof t === 'function') ? t('teacher.folder.create_error') : '创建失败'), 'error');
        }
    } catch (e) {
        showNotification(((typeof t === 'function') ? t('teacher.folder.create_error') : '创建失败') + ': ' + e.message, 'error');
    }
}

async function deleteFolder(folderId, folderName, activityCount) {
    // Check if folder has activities
    if (activityCount > 0) {
        var hasActivitiesMsg = (typeof t === 'function') 
            ? t('teacher.folder.delete_has_activities').replace('{n}', activityCount)
            : '该文件夹下还有 ' + activityCount + ' 个活动，无法删除。请先删除所有活动后再删除文件夹。';
        showNotification(hasActivitiesMsg, 'error');
        return;
    }
    
    // Confirm deletion
    var confirmMsg = (typeof t === 'function')
        ? t('teacher.folder.delete_confirm').replace('{name}', folderName)
        : '确定要删除课程文件夹"' + folderName + '"吗？此操作不可撤销。';
    if (!confirm(confirmMsg)) {
        return;
    }
    
    try {
        showLoading(true);
        var res = await fetch(API_BASE + '/folders/' + folderId, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (res.ok) {
            showNotification((typeof t === 'function') ? t('teacher.folder.delete_success') : '课程文件夹已删除', 'success');
            loadFolders();
        } else {
            var data = await res.json();
            if (res.status === 400 && data.error && data.error.includes('activities')) {
                showNotification((typeof t === 'function') ? t('teacher.folder.delete_has_activities').replace('{n}', activityCount || '若干') : '该文件夹下还有活动，无法删除。请先删除所有活动。', 'error');
            } else {
                showNotification(data.error || ((typeof t === 'function') ? t('teacher.folder.delete_error') : '删除失败'), 'error');
            }
        }
    } catch (e) {
        showNotification(((typeof t === 'function') ? t('teacher.folder.delete_error') : '删除失败') + ': ' + e.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function openFolder(folderId) {
    currentFolderId = folderId;
    switchView('folder-detail');
    var nameEl = document.getElementById('folderDetailName');
    var descEl = document.getElementById('folderDetailDesc');

    // Initialize folder navigation to Overview tab
    switchFolderTab('overview');

    // Get all content containers
    var overviewDocsEl = document.getElementById('folderOverviewDocsList');
    var overviewActsEl = document.getElementById('folderOverviewActivitiesList');
    var actsEl = document.getElementById('folderActivitiesList');
    var matsEl = document.getElementById('folderMaterialsList');

    // Show loading state
    var loadingHtml = '<div class="loading-placeholder"><i class="fas fa-spinner fa-spin"></i><p>' + t('common.loading') + '</p></div>';
    if (overviewDocsEl) overviewDocsEl.innerHTML = loadingHtml;
    if (overviewActsEl) overviewActsEl.innerHTML = loadingHtml;
    if (actsEl) actsEl.innerHTML = loadingHtml;
    if (matsEl) matsEl.innerHTML = loadingHtml;

    try {
        var res = await fetch(API_BASE + '/folders/' + folderId, { credentials: 'include' });
        var data = await res.json();
        if (!data.success) { showNotification(data.error || t('teacher.notify.load_failed'), 'error'); return; }
        var folder = data.folder;
        if (nameEl) nameEl.textContent = folder.name;
        if (descEl) descEl.textContent = folder.description || (typeof t === 'function' ? t('teacher.folder.default_desc') : 'Manage activities and materials for this course');

        // Store folder data for later use
        window.currentFolderData = data;

        // Render all content areas
        renderFolderDocuments(data.documents || []);
        renderFolderActivities(data.activities || []);
    } catch (e) {
        showNotification(t('teacher.notify.load_failed') + ': ' + e.message, 'error');
    }
}

function renderFolderDocuments(docs) {
    var overviewDocsEl = document.getElementById('folderOverviewDocsList');
    var matsEl = document.getElementById('folderMaterialsList');

    // Use documents_by_activity from global data if available
    var docsByActivity = (window.currentFolderData && window.currentFolderData.documents_by_activity) || null;

    var dhtml = '';
    if (docs.length === 0) {
        var emptyMsg = typeof t === 'function' ? t('teacher.folder.no_docs') : '暂无课程材料，请先上传文件';
        dhtml = '<div class="empty-state"><i class="fas fa-folder-open"></i><p>' + emptyMsg + '</p></div>';
    } else if (docsByActivity) {
        // Grouped by activity view
        dhtml = '<div class="documents-grouped-list">';

        // First show course-level materials
        var courseGroup = docsByActivity['course'];
        if (courseGroup && courseGroup.documents && courseGroup.documents.length > 0) {
            dhtml += '<div class="document-group">';
            dhtml += '<div class="document-group-header"><i class="fas fa-graduation-cap"></i> ' + _esc(courseGroup.group_name) + '</div>';
            dhtml += '<div class="documents-list">';
            courseGroup.documents.forEach(function(d) {
                dhtml += renderDocumentItem(d);
            });
            dhtml += '</div></div>';
        }

        // Show unassigned activity materials (if any)
        var unassignedGroup = docsByActivity['unassigned'];
        if (unassignedGroup && unassignedGroup.documents && unassignedGroup.documents.length > 0) {
            dhtml += '<div class="document-group">';
            dhtml += '<div class="document-group-header"><i class="fas fa-tasks"></i> ' + _esc(unassignedGroup.group_name) + '</div>';
            dhtml += '<div class="documents-list">';
            unassignedGroup.documents.forEach(function(d) {
                dhtml += renderDocumentItem(d);
            });
            dhtml += '</div></div>';
        }

        // Show activity-specific materials
        Object.keys(docsByActivity).forEach(function(key) {
            if (key === 'course' || key === 'unassigned') return;
            var group = docsByActivity[key];
            if (group.documents && group.documents.length > 0) {
                dhtml += '<div class="document-group">';
                dhtml += '<div class="document-group-header"><i class="fas fa-folder-open"></i> ' + _esc(group.group_name) + '</div>';
                dhtml += '<div class="documents-list">';
                group.documents.forEach(function(d) {
                    dhtml += renderDocumentItem(d);
                });
                dhtml += '</div></div>';
            }
        });

        dhtml += '</div>';
    } else {
        // Fallback to simple list view
        dhtml = '<div class="documents-list">';
        docs.forEach(function(d) {
            dhtml += renderDocumentItem(d);
        });
        dhtml += '</div>';
    }

    if (overviewDocsEl) overviewDocsEl.innerHTML = dhtml;
    if (matsEl) matsEl.innerHTML = dhtml;
}

function renderDocumentItem(d) {
    var iconClass = getDocumentIconClass(d.mime_type);
    var filename = d.filename || d.original_filename || d.title || 'document';
    var uploadDate = d.created_at ? new Date(d.created_at).toLocaleDateString() : '';
    var docId = d.id || '';
    var fileSize = d.file_size || d.size || 0;
    var mimeType = d.mime_type || '';

    var html = '<div class="document-item" id="doc-item-' + docId + '">';
    html += '<div class="document-icon"><i class="' + iconClass + '"></i></div>';
    html += '<div class="document-info">';
    html += '<div class="document-name" title="' + _esc(filename) + '">' + _esc(filename) + '</div>';
    html += '<div class="document-meta">';
    var metaParts = [];
    if (fileSize > 0) {
        metaParts.push(formatFileSize(fileSize));
    }
    if (uploadDate) {
        metaParts.push(uploadDate);
    }
    if (mimeType) {
        metaParts.push(getFileTypeLabel(mimeType));
    }
    html += metaParts.join(' · ');
    html += '</div>';
    html += '</div>';
    // Add view content button
    html += '<button class="btn-secondary btn-sm document-view-btn" onclick="toggleDocumentContent(\'' + docId + '\', event)" title="' + (typeof t === 'function' ? t('teacher.doc.view_content') : '查看') + '">';
    html += '<i class="fas fa-eye"></i> <span class="btn-text">' + (typeof t === 'function' ? t('teacher.doc.view_content') : '查看') + '</span>';
    html += '</button>';
    html += '</div>';
    // Content container (collapsed by default)
    html += '<div class="document-content-panel" id="doc-content-' + docId + '" style="display: none;">';
    html += '<div class="document-content-loading">' + (typeof t === 'function' ? t('teacher.doc.loading') : '加载中...') + '</div>';
    html += '</div>';
    return html;
}

// Format file size to human readable format
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    var k = 1024;
    var sizes = ['B', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Get file type label from mime type
function getFileTypeLabel(mimeType) {
    if (!mimeType) return '';
    if (mimeType.includes('pdf')) return 'PDF';
    if (mimeType.includes('word') || mimeType.includes('document')) return 'DOC';
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return 'PPT';
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return 'XLS';
    if (mimeType.includes('text')) return 'TXT';
    if (mimeType.includes('image')) return 'IMG';
    return mimeType.split('/')[1] || '';
}

// Toggle document content expand/collapse
async function toggleDocumentContent(docId, event) {
    if (event) event.stopPropagation();

    var contentPanel = document.getElementById('doc-content-' + docId);
    var docItem = document.getElementById('doc-item-' + docId);
    var btn = docItem ? docItem.querySelector('.document-view-btn') : null;
    var btnText = btn ? btn.querySelector('.btn-text') : null;

    if (!contentPanel) return;

    var isExpanded = contentPanel.style.display !== 'none';

    if (isExpanded) {
        // Collapse
        contentPanel.style.display = 'none';
        if (btn) btn.classList.remove('active');
        if (btnText) btnText.textContent = typeof t === 'function' ? t('teacher.doc.view_content') : '查看';
    } else {
        // Expand and load content
        contentPanel.style.display = 'block';
        if (btn) btn.classList.add('active');
        if (btnText) btnText.textContent = typeof t === 'function' ? t('teacher.doc.hide_content') : '隐藏';

        // Load content if not already loaded
        var loadingDiv = contentPanel.querySelector('.document-content-loading');
        if (loadingDiv) {
            try {
                var courseId = DEFAULT_COURSE_ID;
                var res = await fetch(API_BASE + '/courses/' + courseId + '/docs/' + docId + '/content', { credentials: 'include' });
                var data = await res.json();

                if (data.success && data.has_content && data.content_preview) {
                    contentPanel.innerHTML = '<div class="document-content-text">' + escapeHtml(data.content_preview) + '</div>';
                } else {
                    contentPanel.innerHTML = '<div class="document-content-empty">' + (typeof t === 'function' ? t('teacher.doc.no_content') : '暂无提取内容') + '</div>';
                }
            } catch (e) {
                contentPanel.innerHTML = '<div class="document-content-error">' + (typeof t === 'function' ? t('teacher.doc.load_error') : '加载失败') + '</div>';
            }
        }
    }
}

function getDocumentIconClass(mimeType) {
    if (!mimeType) return 'fas fa-file';
    if (mimeType.includes('pdf')) return 'fas fa-file-pdf';
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return 'fas fa-file-powerpoint';
    if (mimeType.includes('word') || mimeType.includes('document')) return 'fas fa-file-word';
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet') || mimeType.includes('csv')) return 'fas fa-file-excel';
    if (mimeType.includes('image')) return 'fas fa-file-image';
    if (mimeType.includes('text')) return 'fas fa-file-alt';
    return 'fas fa-file';
}

function renderFolderActivities(activities) {
    var overviewActsEl = document.getElementById('folderOverviewActivitiesList');
    var actsEl = document.getElementById('folderActivitiesList');

    var ahtml = '';
    if (activities.length === 0) {
        var emptyMsg = typeof t === 'function' ? t('teacher.folder.no_activities') : 'No activities yet. Create your first activity.';
        ahtml = '<div class="empty-state"><i class="fas fa-tasks"></i><p>' + emptyMsg + '</p></div>';
    } else {
        ahtml = '';
        activities.forEach(function(a) {
            ahtml += '<div class="script-card" onclick="openScriptProject(\'' + a.id + '\')">';
            ahtml += '<div class="script-card-header"><h4>' + _esc(a.title) + '</h4>';
            ahtml += '<span class="status-badge status-' + (a.status || 'draft') + '">' + (a.status || 'draft') + '</span></div>';
            ahtml += '<p class="script-card-meta">' + _esc(a.topic || '') + '</p>';
            ahtml += '<div class="script-card-footer"><span>' + _esc(a.task_type || '') + '</span>';
            ahtml += '<span>' + (a.updated_at ? new Date(a.updated_at).toLocaleDateString() : '') + '</span></div>';
            ahtml += '</div>';
        });
    }

    if (overviewActsEl) overviewActsEl.innerHTML = ahtml;
    if (actsEl) actsEl.innerHTML = ahtml;
}

function switchFolderTab(tabName) {
    // Update nav items
    document.querySelectorAll('.folder-nav-item').forEach(function(item) {
        item.classList.remove('active');
        if (item.getAttribute('data-folder-tab') === tabName) {
            item.classList.add('active');
        }
    });

    // Update tab content visibility
    document.querySelectorAll('.folder-tab-content').forEach(function(content) {
        content.classList.remove('active');
    });

    var targetTab = document.getElementById('folder' + tabName.charAt(0).toUpperCase() + tabName.slice(1) + 'Tab');
    if (targetTab) targetTab.classList.add('active');
}

function openFolderUploadModal() {
    // Create a simple file input trigger
    var input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '.txt,.md,.pdf,.pptx,.docx,.xlsx,.csv,.png,.jpg,.jpeg';
    input.onchange = function(e) {
        if (e.target.files && e.target.files.length > 0) {
            uploadFilesToFolder(e.target.files);
        }
    };
    input.click();
}

async function uploadFilesToFolder(files) {
    if (!currentFolderId) {
        showNotification(t('teacher.notify.select_folder_first'), 'warning');
        return;
    }

    showNotification(t('teacher.notify.upload_in_progress'), 'info');

    try {
        var uploadedCount = 0;
        for (var i = 0; i < files.length; i++) {
            var formData = new FormData();
            formData.append('file', files[i]);
            formData.append('title', files[i].name);
            formData.append('folder_id', currentFolderId);

            var res = await fetch(API_BASE + '/courses/' + DEFAULT_COURSE_ID + '/docs/upload', {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });

            var data = await res.json();
            if (data.success || data.document_id) {
                uploadedCount++;
            }
        }

        showNotification(t('teacher.notify.upload_success').replace('{n}', uploadedCount), 'success');

        // Refresh folder data
        if (window.currentFolderData) {
            // Re-fetch folder data to update the list
            openFolder(currentFolderId);
        }
    } catch (e) {
        showNotification(t('teacher.notify.upload_failed') + ': ' + e.message, 'error');
    }
}

function createActivityInFolder() {
    if (!currentFolderId) { showNotification(t('teacher.notify.select_folder_first'), 'warning'); return; }
    wizardFolderId = currentFolderId;
    goToStep(2);
}

async function loadDashboardData() {
    // Home page initialization - simplified, no longer shows stats or progress
    // This function is called when entering the home dashboard view
    try {
        // Just ensure wizard step tracking is consistent
        updateCurrentStep();
    } catch (error) {
        console.error('[teacher] Error in loadDashboardData:', error);
    }
}

async function loadRecentPipelines() {
    var container = document.getElementById('recentPipelines');
    if (!container) return;
    try {
        if (scripts.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.pipeline.no_runs') + '</p></div>';
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
                container.innerHTML = '<div class="empty-state"><p>' + t('teacher.pipeline.no_runs') + '</p></div>';
            } else {
                container.innerHTML = recent.map(run => `
                    <div class="activity-item">
                        <div class="activity-icon"><i class="fas fa-project-diagram"></i></div>
                        <div class="activity-content">
                            <h5>${t('teacher.pipeline.run_prefix')} ${run.run_id.substring(0, 8)}</h5>
                            <p>${t('teacher.pipeline.status_label')} ${run.status}</p>
                        </div>
                        <div class="activity-time">${formatTime(run.created_at)}</div>
                    </div>
                `).join('');
            }
        } else {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.pipeline.load_runs_error') + '</p></div>';
        }
    } catch (error) {
        if (container) container.innerHTML = '<div class="empty-state"><p>' + t('teacher.pipeline.load_runs_error') + '</p></div>';
    }
}

async function loadRecentDecisions() {
    var container = document.getElementById('recentDecisions');
    if (container) container.innerHTML = '<div class="empty-state"><p>' + t('teacher.decisions.no_decisions') + '</p></div>';
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
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.login_first') + '</p></div>';
            return;
        }
        
        if (res.status === 403) {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.no_permission') + '</p></div>';
            return;
        }
        
        if (res.ok) {
            const data = await res.json();
            scripts = data.scripts || [];
            renderScripts(scripts);
        } else {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.load_script_failed') + '</p></div>';
        }
    } catch (error) {
        console.error('Error loading scripts:', error);
        container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.load_script_failed') + '</p></div>';
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
                <h4>${t('teacher.scripts.no_projects')}</h4>
                <p>${t('teacher.scripts.no_projects_desc')}</p>
                <button class="btn-primary" onclick="createNewScriptProject()">
                    <i class="fas fa-plus"></i>
                    ${t('teacher.scripts.create_new')}
                </button>
            </div>
        `;
        return;
    }
    
    var labelEdit = typeof t === 'function' ? t('common.edit') : 'Edit';
    var labelDuplicate = typeof t === 'function' ? t('teacher.scripts.duplicate') : 'Duplicate';
    var labelQuality = typeof t === 'function' ? t('teacher.scripts.quality_report') : 'Quality Report';
    container.innerHTML = scriptsList.map(script => {
        var folderInfo = script.folder_name ? `<span class="folder-badge"><i class="fas fa-folder"></i> ${escapeHtml(script.folder_name)}</span>` : '';
        return `
        <div class="script-card" onclick="openScript('${script.id}')">
            <div class="script-card-header">
                <h4>${escapeHtml(script.title || 'Untitled')}</h4>
                <span class="status-badge ${script.status}">${script.status}</span>
            </div>
            <div class="script-card-content">
                ${folderInfo}
                <p><strong>${t('teacher.scripts.topic')}</strong> ${escapeHtml(script.topic || 'N/A')}</p>
                <p><strong>${t('teacher.scripts.duration')}</strong> ${script.duration_minutes || 0}${t('teacher.scripts.minutes')}</p>
            </div>
            <div class="script-card-footer">
                <span class="script-time">${t('teacher.scripts.updated')} ${formatTime(script.updated_at)}</span>
                <button class="btn-secondary btn-sm" onclick="event.stopPropagation(); editScript('${script.id}')" title="${labelEdit}">
                    <i class="fas fa-edit"></i> ${labelEdit}
                </button>
                <button class="btn-secondary btn-sm" onclick="event.stopPropagation(); duplicateScript('${script.id}')" title="${labelDuplicate}">
                    <i class="fas fa-copy"></i> ${labelDuplicate}
                </button>
                <button class="btn-secondary btn-sm" onclick="event.stopPropagation(); viewScriptQuality('${script.id}')">
                    <i class="fas fa-chart-line"></i> ${labelQuality}
                </button>
            </div>
        </div>
    `}).join('');
}

// Four-Step Process Navigation
function startNewActivity() {
    wizardStep = 1;
    wizardFolderId = null;  // Clear folder context when starting from global entry point
    switchView('wizard');
    resetWizard();
    if (typeof loadUploadedFilesListForStep1 === 'function') loadUploadedFilesListForStep1();
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
    if (step === 1 && typeof loadUploadedFilesListForStep1 === 'function') loadUploadedFilesListForStep1();
}

function updateCurrentStep() {
    // Update process cards active state (used in wizard view)
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
            showNotification(t('teacher.notify.complete_validation_first'), 'warning');
            return;
        }
    }
    if (wizardStep === 3) {
        if (!currentPipelineRunId) {
            showNotification(t('teacher.notify.run_pipeline_first'), 'warning');
            return;
        }
    }
    if (wizardStep === 1) {
        var materialLevel = 'course';
        var syllabusEl = document.getElementById('syllabusText');
        var text = syllabusEl ? (syllabusEl.value || '').trim() : '';
        var uploadedDocId = null;
        if (text.length >= 80) {
            try {
                var uploadRes = await fetch(API_BASE + '/courses/' + DEFAULT_COURSE_ID + '/docs/upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: 'Teaching materials (Step 1)', text: text, material_level: materialLevel }),
                    credentials: 'include'
                });
                var uploadData = uploadRes.json ? await uploadRes.json().catch(function() { return {}; }) : {};
                if (uploadRes.ok) {
                    if (typeof loadDocuments === 'function') loadDocuments();
                    uploadedDocId = uploadData.doc_id || uploadData.document && uploadData.document.id;
                }
            } catch (e) {
                console.warn('[teacher] Step 1 materials upload failed', e);
            }
        }
        var lessonNotesEl = document.getElementById('lessonNotes');
        var lessonNotes = lessonNotesEl ? (lessonNotesEl.value || '').trim() : '';
        if (lessonNotes.length >= 20) {
            try {
                var notesRes = await fetch(API_BASE + '/courses/' + DEFAULT_COURSE_ID + '/docs/upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title: 'Lesson notes (Step 1)', text: lessonNotes, material_level: 'course' }),
                    credentials: 'include'
                });
                if (notesRes.ok && typeof loadDocuments === 'function') loadDocuments();
            } catch (e) {
                console.warn('[teacher] Step 1 lesson notes upload failed', e);
            }
        }
        // Bug 1 fix: after pasting syllabus, prefill Step 2 from uploaded document so form reflects pasted content
        if (uploadedDocId && typeof fillSpecForm === 'function') {
            try {
                var prefillRes = await fetch(API_BASE + '/courses/' + DEFAULT_COURSE_ID + '/docs/' + uploadedDocId + '/prefill', { credentials: 'include' });
                if (prefillRes.ok) {
                    var prefillData = await prefillRes.json();
                    var sug = prefillData.suggestions || {};
                    var v = function (key) { var s = sug[key]; return s && s.value !== undefined ? s.value : ''; };
                    var spec = {
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
                    fillSpecForm(spec);
                    if (prefillData.warnings && prefillData.warnings.length) showNotification(prefillData.warnings[0], 'warning');
                    else showNotification(typeof t === 'function' ? t('teacher.doc.prefill_success') : 'Suggestions filled. Please confirm or edit, then validate.', 'success');
                }
            } catch (e) {
                console.warn('[teacher] Step 1 prefill after upload failed', e);
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
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.preview.still_running') + '</p></div>';
            setTimeout(function() { loadScriptPreview(); }, 3000);
            return;
        }

        // Prefer final_output_json saved on the pipeline run (includes merged materials)
        var output = run.final_output_json || null;

        if (!output) {
            var stageOrder = ['refiner', 'critic', 'material_generator', 'planner'];
            for (var i = 0; i < stageOrder.length; i++) {
                var st = stages.find(function(s) { return s.stage_name === stageOrder[i] && s.status === 'success' && s.output_json; });
                if (st) { output = st.output_json; break; }
            }
        }

        if (!output) {
            var errMsg = run.error_message || 'No output was generated';
            container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Pipeline did not produce output: ' + errMsg + '</p></div>';
            return;
        }

        // Always merge classroom-ready materials from material_generator stage as fallback
        var matStage = stages.find(function(s) { return s.stage_name === 'material_generator' && s.status === 'success' && s.output_json; });
        if (matStage && matStage.output_json) {
            var mat = matStage.output_json;
            if (mat.student_worksheet && !output.student_worksheet) output.student_worksheet = mat.student_worksheet;
            if (mat.student_slides && !output.student_slides) output.student_slides = mat.student_slides;
            if (mat.teacher_guide && !output.teacher_guide) output.teacher_guide = mat.teacher_guide;
            if (mat.role_cards && !output.role_cards) output.role_cards = mat.role_cards;
        }

        var hasWorksheet = output.student_worksheet && (output.student_worksheet.title || output.student_worksheet.goal);
        var hasStudentSlides = output.student_slides && (output.student_slides.title || (output.student_slides.slides && output.student_slides.slides.length > 0));
        var hasTeacherGuide = output.teacher_guide && (output.teacher_guide.overview || output.teacher_guide.rationale);
        var hasAnyMaterials = hasWorksheet || hasStudentSlides || hasTeacherGuide;

        var html = '<div class="script-preview-content">';

        if (hasAnyMaterials) {
            html += '<div class="preview-tabs"><button type="button" class="preview-tab active" data-tab="student">' + (typeof t === 'function' ? t('teacher.preview.tab_worksheet') : 'Student Worksheet') + '</button>';
            html += '<button type="button" class="preview-tab" data-tab="slides">' + (typeof t === 'function' ? t('teacher.preview.tab_slides') : 'Student Slides') + '</button>';
            html += '<button type="button" class="preview-tab" data-tab="teacher">' + (typeof t === 'function' ? t('teacher.preview.tab_facilitation') : 'Teacher Facilitation Sheet') + '</button>';
            html += '<button type="button" class="preview-tab" data-tab="structure">' + (typeof t === 'function' ? t('teacher.preview.tab_structure') : 'Structure') + '</button></div>';
            html += '<div class="preview-tab-panels">';

            html += '<div class="preview-tab-panel active" id="preview-panel-student">';
            if (hasWorksheet) {
                var sw = output.student_worksheet;
                html += '<div class="worksheet-preview">';
                html += '<h2 class="worksheet-title">' + _esc(sw.title || 'Activity') + '</h2>';
                if (sw.goal) html += '<p class="worksheet-goal"><strong>' + (typeof t === 'function' ? t('teacher.preview.goal') : 'Goal') + ':</strong> ' + _esc(sw.goal) + '</p>';
                if (sw.roles_summary) html += '<div class="worksheet-roles"><h4>' + (typeof t === 'function' ? t('teacher.preview.roles') : 'Roles') + '</h4><p>' + _esc(sw.roles_summary) + '</p></div>';
                if (sw.steps && sw.steps.length) {
                    html += '<div class="worksheet-steps"><h4>' + (typeof t === 'function' ? t('teacher.preview.steps') : 'Steps') + '</h4>';
                    sw.steps.forEach(function(step, i) {
                        html += '<div class="worksheet-step"><strong>Step ' + (step.step_order || i + 1) + ': ' + _esc(step.title || '') + '</strong>';
                        if (step.duration_minutes) html += ' <span class="step-duration">(' + step.duration_minutes + ' min)</span>';
                        if (step.description) html += '<p>' + _esc(step.description) + '</p>';
                        if (step.prompts && step.prompts.length) {
                            html += '<ul class="step-prompts">';
                            step.prompts.forEach(function(p) { html += '<li>' + _esc(p) + '</li>'; });
                            html += '</ul>';
                        }
                        html += '</div>';
                    });
                    html += '</div>';
                }
                if (sw.timing_summary) html += '<p class="worksheet-timing">' + _esc(sw.timing_summary) + '</p>';
                if (sw.output_instructions) html += '<div class="worksheet-output"><h4>' + (typeof t === 'function' ? t('teacher.preview.output') : 'Expected output') + '</h4><p>' + _esc(sw.output_instructions) + '</p></div>';
                if (sw.reporting_instructions) html += '<p class="worksheet-reporting">' + _esc(sw.reporting_instructions) + '</p>';
                html += '</div>';
            } else {
                html += '<p class="empty-tab">' + (typeof t === 'function' ? t('teacher.preview.no_worksheet') : 'No student worksheet in this run.') + '</p>';
            }
            html += '</div>';

            html += '<div class="preview-tab-panel" id="preview-panel-slides">';
            if (hasStudentSlides) {
                var ss = output.student_slides;
                html += '<div class="student-slides-preview">';
                html += '<h2 class="slides-title">' + _esc(ss.title || 'Student Slides') + '</h2>';
                var slides = ss.slides || [];
                slides.forEach(function(slide, i) {
                    html += '<div class="slide-card">';
                    html += '<h4>' + (typeof t === 'function' ? t('teacher.preview.slide') : 'Slide') + ' ' + (slide.slide_number != null ? slide.slide_number : i + 1) + ': ' + _esc(slide.title || '') + '</h4>';
                    if (slide.content) html += '<div class="slide-content">' + _esc(slide.content) + '</div>';
                    html += '</div>';
                });
                html += '</div>';
            } else {
                html += '<p class="empty-tab">' + (typeof t === 'function' ? t('teacher.preview.no_slides') : 'No student slides in this run.') + '</p>';
            }
            html += '</div>';

            html += '<div class="preview-tab-panel" id="preview-panel-teacher">';
            if (hasTeacherGuide) {
                var tg = output.teacher_guide;
                html += '<div class="teacher-guide-preview">';
                if (tg.overview) html += '<h3>' + (typeof t === 'function' ? t('teacher.preview.overview') : 'Overview') + '</h3><p>' + _esc(tg.overview) + '</p>';
                if (tg.alignment_with_objectives) html += '<h3>' + (typeof t === 'function' ? t('teacher.preview.alignment') : 'Alignment with objectives') + '</h3><p>' + _esc(tg.alignment_with_objectives) + '</p>';
                if (tg.rationale) html += '<h3>' + (typeof t === 'function' ? t('teacher.preview.rationale') : 'Rationale') + '</h3><p>' + _esc(tg.rationale) + '</p>';
                if (tg.implementation_steps) html += '<h3>' + (typeof t === 'function' ? t('teacher.preview.implementation') : 'Implementation') + '</h3><p>' + _esc(tg.implementation_steps) + '</p>';
                if (tg.monitoring_points) html += '<h3>' + (typeof t === 'function' ? t('teacher.preview.monitoring') : 'Monitoring') + '</h3><p>' + _esc(tg.monitoring_points) + '</p>';
                if (tg.expected_difficulties) html += '<h3>' + (typeof t === 'function' ? t('teacher.preview.difficulties') : 'Expected difficulties') + '</h3><p>' + _esc(tg.expected_difficulties) + '</p>';
                if (tg.debrief_questions) html += '<h3>' + (typeof t === 'function' ? t('teacher.preview.debrief') : 'Debrief questions') + '</h3><p>' + _esc(tg.debrief_questions) + '</p>';
                if (tg.adaptation_suggestions) html += '<h3>' + (typeof t === 'function' ? t('teacher.preview.adaptations') : 'Adaptations') + '</h3><p>' + _esc(tg.adaptation_suggestions) + '</p>';
                html += '</div>';
            } else {
                html += '<p class="empty-tab">' + (typeof t === 'function' ? t('teacher.preview.no_teacher_guide') : 'No teacher guide in this run.') + '</p>';
            }
            html += '</div>';

            html += '<div class="preview-tab-panel" id="preview-panel-structure">';
        }

        var roles = output.roles || [];
        if (roles.length > 0) {
            html += '<div class="preview-section"><h3><i class="fas fa-users"></i> Roles</h3><div class="roles-grid">';
            roles.forEach(function(r) {
                html += '<div class="role-card"><strong>' + _esc(r.role_id || r.role_name || r.name || 'Role') + '</strong>';
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

        if (hasAnyMaterials) {
            html += '</div>';
        }

        /* Pipeline Summary removed per Issue #7 - not shown to end user */

        if (hasAnyMaterials) {
            html += '</div>';
        }
        html += '</div>';
        container.innerHTML = html;

        if (hasAnyMaterials) {
            container.querySelectorAll('.preview-tab').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    var tab = this.getAttribute('data-tab');
                    container.querySelectorAll('.preview-tab').forEach(function(b) { b.classList.remove('active'); });
                    container.querySelectorAll('.preview-tab-panel').forEach(function(p) { p.classList.remove('active'); });
                    this.classList.add('active');
                    var panel = document.getElementById('preview-panel-' + tab);
                    if (panel) panel.classList.add('active');
                });
            });
        }

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

/** Step 4: Edit & Regenerate — go back to Step 2 so teacher can modify spec and run pipeline again */
function editAndRegenerate() {
    if (currentSpec && typeof fillSpecForm === 'function') {
        var flat = currentSpec;
        if (currentSpec.course_context && !currentSpec.course) {
            var cc = currentSpec.course_context;
            flat = {
                course: cc.subject,
                topic: cc.topic,
                duration_minutes: cc.duration,
                mode: cc.mode,
                class_size: cc.class_size,
                course_context: cc.description,
                teaching_stage: currentSpec.teaching_stage,
                collaboration_purpose: currentSpec.collaboration_purpose,
                group_size: currentSpec.group_size,
                grouping_strategy: currentSpec.grouping_strategy,
                role_structure: currentSpec.role_structure,
                whole_class_reporting: currentSpec.whole_class_reporting,
                learning_objectives: (currentSpec.learning_objectives && (currentSpec.learning_objectives.knowledge || currentSpec.learning_objectives.skills))
                    ? [].concat(currentSpec.learning_objectives.knowledge || [], currentSpec.learning_objectives.skills || [])
                    : [],
                scaffolding_options: currentSpec.scaffolding_options || [],
                student_difficulties: currentSpec.student_difficulties || '',
                output_format: currentSpec.output_format,
                task_requirements: (currentSpec.task_requirements && currentSpec.task_requirements.requirements_text) || '',
                initial_idea: currentSpec.initial_idea || ''
            };
        }
        fillSpecForm(flat);
    }
    goToStep(2);
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
            if (!runBtn.querySelector('.fa-spinner')) runBtn.innerHTML = '<i class="fas fa-play"></i> <span>' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation') + '</span>';
        }
    }
}

function cancelWizard() {
    if (confirm(t('teacher.wizard.cancel_confirm'))) {
        switchView('dashboard');
        resetWizard();
    }
}

// Step 1: Load and display uploaded files list (for current course)
async function loadUploadedFilesListForStep1() {
    var container = document.getElementById('uploadedFilesList');
    if (!container) return;
    var courseId = typeof DEFAULT_COURSE_ID !== 'undefined' ? DEFAULT_COURSE_ID : 'default-course';
    try {
        var res = await fetch((typeof API_BASE !== 'undefined' ? API_BASE : '/api/cscl') + '/courses/' + courseId + '/docs', { credentials: 'include' });
        if (!res.ok) {
            container.innerHTML = '';
            return;
        }
        var data = await res.json();
        var documents = data.documents || [];
        if (documents.length === 0) {
            container.innerHTML = '<p class="uploaded-files-empty">' + (typeof t === 'function' ? t('teacher.wizard.step1.no_uploaded_yet') : 'No files uploaded yet') + '</p>';
            return;
        }
        var labelUploaded = typeof t === 'function' ? t('teacher.wizard.step1.uploaded_at') : 'Uploaded';
        var labelDelete = typeof t === 'function' ? t('common.delete') : 'Delete';
        container.innerHTML = documents.map(function(doc) {
            return '<div class="uploaded-file-item">' +
                '<span class="uploaded-file-name">' + escapeHtml(doc.title || 'Untitled') + '</span>' +
                ' <span class="uploaded-file-meta">' + (doc.mime_type || '') + ' · ' + (doc.created_at ? formatTime(doc.created_at) : '') + '</span>' +
                ' <button type="button" class="btn-secondary btn-sm" onclick="deleteDocumentFromStep1(\'' + doc.id + '\')" aria-label="' + labelDelete + '">' + labelDelete + '</button>' +
                '</div>';
        }).join('');
    } catch (e) {
        console.warn('[teacher] loadUploadedFilesListForStep1 error', e);
        container.innerHTML = '';
    }
}

function deleteDocumentFromStep1(docId) {
    if (!confirm(typeof t === 'function' ? t('teacher.doc.confirm_delete') : 'Delete this document?')) return;
    var courseId = typeof DEFAULT_COURSE_ID !== 'undefined' ? DEFAULT_COURSE_ID : 'default-course';
    fetch((typeof API_BASE !== 'undefined' ? API_BASE : '/api/cscl') + '/courses/' + courseId + '/docs/' + docId, {
        method: 'DELETE',
        credentials: 'include'
    }).then(function(res) {
        if (res.ok) {
            loadUploadedFilesListForStep1();
            if (typeof loadDocuments === 'function') loadDocuments();
        }
    }).catch(function() {});
}

// Step 1: Upload Teaching Materials (multiple files supported; optional skip text extraction)
// PDF/PPTX/DOCX/images: upload to backend. TXT/MD/CSV: read locally then upload as text or send file.
var MATERIAL_UPLOAD_EXTENSIONS = ['pdf', 'pptx', 'docx', 'png', 'jpg', 'jpeg', 'xlsx'];
document.getElementById('syllabusFile')?.addEventListener('change', async function(e) {
    var files = e.target.files;
    if (!files || !files.length) return;
    var materialLevel = 'course';
    var skipExtract = document.getElementById('step1SkipExtract') && document.getElementById('step1SkipExtract').checked;
    var courseId = typeof DEFAULT_COURSE_ID !== 'undefined' ? DEFAULT_COURSE_ID : 'default-course';
    var baseUrl = (typeof API_BASE !== 'undefined' ? API_BASE : '/api/cscl') + '/courses/' + courseId + '/docs/upload';
    var firstExtractedText = null;
    var okCount = 0;
    var errCount = 0;
    try {
        showLoading(true);
        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            var ext = (file.name || '').split('.').pop().toLowerCase();
            if (MATERIAL_UPLOAD_EXTENSIONS.indexOf(ext) === -1 && ext !== 'pdf') {
                if (ext === 'txt' || ext === 'md' || ext === 'csv') {
                    try {
                        var text = await new Promise(function(resolve, reject) {
                            var r = new FileReader();
                            r.onload = function() { resolve(r.result || ''); };
                            r.onerror = reject;
                            r.readAsText(file);
                        });
                        var ta = document.getElementById('syllabusText');
                        ta.value = (ta.value ? ta.value + '\n\n' : '') + text;
                    } catch (err) { console.warn('Read text file failed', file.name, err); }
                }
                continue;
            }
            var formData = new FormData();
            formData.append('file', file);
            formData.append('title', file.name);
            formData.append('material_level', materialLevel);
            formData.append('extract_text', skipExtract ? 'false' : 'true');
            var res = await fetch(baseUrl, { method: 'POST', body: formData, credentials: 'include' });
            var result = await res.json();
            if (res.ok) {
                okCount++;
                if (!skipExtract && (result.extracted_text || result.extracted_text_preview) && !firstExtractedText)
                    firstExtractedText = result.extracted_text || result.extracted_text_preview;
            } else {
                errCount++;
                var msg = (result.code === 'PDF_PARSE_FAILED')
                    ? t('teacher.pdf.parse_failed_generic')
                    : (result.error || result.message || t('teacher.notify.upload_failed'));
                showNotification((file.name || '') + ': ' + msg, 'error');
            }
        }
        if (firstExtractedText)
            document.getElementById('syllabusText').value = firstExtractedText;
        if (okCount > 0) {
            showNotification(t('teacher.notify.upload_success').replace('{n}', okCount), 'success');
            if (typeof loadDocuments === 'function') loadDocuments();
            if (typeof loadUploadedFilesListForStep1 === 'function') loadUploadedFilesListForStep1();
        }
    } catch (err) {
        console.error('Upload error:', err);
        showNotification(t('teacher.notify.upload_failed'), 'error');
    } finally {
        showLoading(false);
    }
    e.target.value = '';
});

// Step 2: Lesson-specific file upload handler
var LESSON_UPLOAD_EXTENSIONS = ['pdf', 'pptx', 'docx', 'png', 'jpg', 'jpeg', 'xlsx'];
document.getElementById('lessonFile')?.addEventListener('change', async function(e) {
    var files = e.target.files;
    if (!files || !files.length) return;
    var materialLevel = 'lesson';
    var courseId = typeof DEFAULT_COURSE_ID !== 'undefined' ? DEFAULT_COURSE_ID : 'default-course';
    var baseUrl = (typeof API_BASE !== 'undefined' ? API_BASE : '/api/cscl') + '/courses/' + courseId + '/docs/upload';
    var okCount = 0;
    var errCount = 0;
    try {
        showLoading(true);
        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            var ext = (file.name || '').split('.').pop().toLowerCase();
            if (LESSON_UPLOAD_EXTENSIONS.indexOf(ext) === -1) {
                if (ext === 'txt' || ext === 'md' || ext === 'csv') {
                    // Text files - read locally and add to initial idea field
                    try {
                        var text = await new Promise(function(resolve, reject) {
                            var r = new FileReader();
                            r.onload = function() { resolve(r.result || ''); };
                            r.onerror = reject;
                            r.readAsText(file);
                        });
                        var ta = document.getElementById('specInitialIdea');
                        if (ta) {
                            ta.value = (ta.value ? ta.value + '\n\n' : '') + '[From ' + file.name + ']:\n' + text.substring(0, 2000);
                        }
                        okCount++;
                    } catch (err) { console.warn('Read text file failed', file.name, err); }
                }
                continue;
            }
            var formData = new FormData();
            formData.append('file', file);
            formData.append('title', file.name);
            formData.append('material_level', materialLevel);
            formData.append('extract_text', 'false'); // Lesson files: don't extract, just store for RAG
            // Associate with current folder if available
            if (typeof currentFolderId !== 'undefined' && currentFolderId) {
                formData.append('folder_id', currentFolderId);
            }
            var res = await fetch(baseUrl, { method: 'POST', body: formData, credentials: 'include' });
            var result = await res.json();
            if (res.ok) {
                okCount++;
            } else {
                errCount++;
                var msg = (result.code === 'PDF_PARSE_FAILED')
                    ? t('teacher.pdf.parse_failed_generic')
                    : (result.error || result.message || t('teacher.notify.upload_failed'));
                showNotification((file.name || '') + ': ' + msg, 'error');
            }
        }
        if (okCount > 0) {
            showNotification(t('teacher.notify.upload_success').replace('{n}', okCount), 'success');
            loadLessonUploadedFiles();
        }
    } catch (err) {
        console.error('Lesson upload error:', err);
        showNotification(t('teacher.notify.upload_failed'), 'error');
    } finally {
        showLoading(false);
    }
    e.target.value = '';
});

// Step 2: Load and display lesson-specific uploaded files
async function loadLessonUploadedFiles() {
    var container = document.getElementById('lessonUploadedFilesList');
    if (!container) return;
    var courseId = typeof DEFAULT_COURSE_ID !== 'undefined' ? DEFAULT_COURSE_ID : 'default-course';
    try {
        // Build URL with folder filter if available
        var url = (typeof API_BASE !== 'undefined' ? API_BASE : '/api/cscl') + '/courses/' + courseId + '/docs';
        if (typeof currentFolderId !== 'undefined' && currentFolderId) {
            url += '?folder_id=' + encodeURIComponent(currentFolderId);
        }
        var res = await fetch(url, { credentials: 'include' });
        if (!res.ok) {
            container.innerHTML = '';
            return;
        }
        var data = await res.json();
        var documents = data.documents || [];
        // Filter only lesson-level documents
        var lessonDocs = documents.filter(function(doc) { return doc.material_level === 'lesson'; });
        if (lessonDocs.length === 0) {
            container.innerHTML = '';
            return;
        }
        var labelDelete = typeof t === 'function' ? t('common.delete') : 'Delete';
        container.innerHTML = lessonDocs.map(function(doc) {
            return '<div class="uploaded-file-item" style="padding: 0.5rem; background: #f8f9fa; border-radius: 4px; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">' +
                '<span class="uploaded-file-name"><i class="fas fa-file"></i> ' + escapeHtml(doc.title || 'Untitled') + '</span>' +
                ' <span class="uploaded-file-meta" style="color: #6c757d; font-size: 0.85rem;">' + (doc.mime_type || '') + '</span>' +
                ' <button type="button" class="btn-secondary btn-sm" onclick="deleteLessonDocument(\'' + doc.id + '\')" aria-label="' + labelDelete + '"><i class="fas fa-trash"></i></button>' +
                '</div>';
        }).join('');
    } catch (e) {
        console.warn('[teacher] loadLessonUploadedFiles error', e);
        container.innerHTML = '';
    }
}

function deleteLessonDocument(docId) {
    if (!confirm(typeof t === 'function' ? t('teacher.doc.confirm_delete') : 'Delete this document?')) return;
    var courseId = typeof DEFAULT_COURSE_ID !== 'undefined' ? DEFAULT_COURSE_ID : 'default-course';
    fetch((typeof API_BASE !== 'undefined' ? API_BASE : '/api/cscl') + '/courses/' + courseId + '/docs/' + docId, {
        method: 'DELETE',
        credentials: 'include'
    }).then(function(res) {
        if (res.ok) {
            loadLessonUploadedFiles();
        }
    }).catch(function() {});
}

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
    var tsEl = document.getElementById('specTeachingStage');
    if (tsEl) tsEl.value = spec.teaching_stage || 'concept_exploration';
    var cpEl = document.getElementById('specCollaborationPurpose');
    if (cpEl) cpEl.value = spec.collaboration_purpose || 'compare_ideas';
    var gsEl = document.getElementById('specGroupSize');
    if (gsEl) gsEl.value = spec.group_size != null ? spec.group_size : 4;
    var gstEl = document.getElementById('specGroupingStrategy');
    if (gstEl) gstEl.value = spec.grouping_strategy || 'random';
    var rsEl = document.getElementById('specRoleStructure');
    if (rsEl) rsEl.value = spec.role_structure || 'assigned_roles';
    var wcrEl = document.getElementById('specWholeClassReporting');
    if (wcrEl) wcrEl.checked = spec.whole_class_reporting !== false;
    var objEl = document.getElementById('specCourseContext');
    if (objEl) objEl.value = spec.course_context || spec.course_context_description || '';
    document.getElementById('specObjectives').value = Array.isArray(spec.learning_objectives)
        ? spec.learning_objectives.join('\n')
        : (spec.learning_objectives || '');
    var scaffoldEls = document.querySelectorAll('#specScaffoldingOptions input[name="scaffolding"]');
    if (scaffoldEls.length) {
        var opts = spec.scaffolding_options || [];
        scaffoldEls.forEach(function(cb) { cb.checked = opts.indexOf(cb.value) !== -1; });
    }
    var diffEl = document.getElementById('specStudentDifficulties');
    if (diffEl) diffEl.value = spec.student_difficulties || spec.teacher_concerns || '';
    var outEls = document.querySelectorAll('#specOutputFormat input[name="output_format"]');
    if (outEls.length) {
        var formats = spec.output_format || spec.output_formats || ['student_worksheet', 'student_slides', 'teacher_facilitation_sheet'];
        outEls.forEach(function(cb) { cb.checked = formats.indexOf(cb.value) !== -1; });
    }
    var trEl = document.getElementById('specTaskRequirements');
    if (trEl) trEl.value = spec.task_requirements || spec.requirements_text || '';
    var initialIdeaEl = document.getElementById('specInitialIdea');
    if (initialIdeaEl) initialIdeaEl.value = spec.initial_idea || '';
}

function buildCanonicalSpecFromForm() {
    var modeVal = document.getElementById('specMode').value;
    var mode = (modeVal && modeVal.toLowerCase() === 'async') ? 'async' : 'sync';
    var objectives = document.getElementById('specObjectives').value.split('\n').filter(function(s) { return s.trim(); });
    var knowledge = objectives.length ? objectives : ['Understand topic'];
    var skills = objectives.length > 1 ? objectives.slice(1) : (objectives.length ? [objectives[0]] : ['Apply concepts']);
    var scaffolding = [];
    document.querySelectorAll('#specScaffoldingOptions input[name="scaffolding"]:checked').forEach(function(cb) { scaffolding.push(cb.value); });
    var outputFormat = [];
    document.querySelectorAll('#specOutputFormat input[name="output_format"]:checked').forEach(function(cb) { outputFormat.push(cb.value); });
    if (outputFormat.length === 0) outputFormat = ['student_worksheet', 'student_slides', 'teacher_facilitation_sheet'];
    var topicVal = document.getElementById('specTopic').value.trim();
    var descVal = (document.getElementById('specCourseContext') && document.getElementById('specCourseContext').value) ? document.getElementById('specCourseContext').value.trim() : '';
    if (!descVal) descVal = topicVal || 'See learning objectives.';
    var spec = {
        course_context: {
            subject: document.getElementById('specCourse').value.trim(),
            topic: topicVal,
            class_size: parseInt(document.getElementById('specClassSize').value, 10) || 30,
            mode: mode,
            duration: parseInt(document.getElementById('specDuration').value, 10) || 90,
            description: descVal
        },
        learning_objectives: { knowledge: knowledge, skills: skills },
        task_requirements: {
            task_type: '',
            expected_output: '',
            collaboration_form: 'group',
            requirements_text: (document.getElementById('specTaskRequirements') && document.getElementById('specTaskRequirements').value) ? document.getElementById('specTaskRequirements').value.trim() : ''
        }
    };
    var tsEl = document.getElementById('specTeachingStage');
    if (tsEl) spec.teaching_stage = tsEl.value || 'concept_exploration';
    var cpEl = document.getElementById('specCollaborationPurpose');
    if (cpEl) spec.collaboration_purpose = cpEl.value || 'compare_discuss_ideas';
    var gsEl = document.getElementById('specGroupSize');
    if (gsEl) spec.group_size = parseInt(gsEl.value, 10) || 4;
    var gstEl = document.getElementById('specGroupingStrategy');
    if (gstEl) spec.grouping_strategy = gstEl.value || 'random';
    var rsEl = document.getElementById('specRoleStructure');
    if (rsEl) spec.role_structure = rsEl.value || 'no_roles';
    var wcrEl = document.getElementById('specWholeClassReporting');
    if (wcrEl) spec.whole_class_reporting = wcrEl.checked;
    spec.scaffolding_options = scaffolding;
    var diffEl = document.getElementById('specStudentDifficulties');
    if (diffEl) spec.student_difficulties = (diffEl.value || '').trim();
    spec.output_format = outputFormat;
    var initialIdeaEl = document.getElementById('specInitialIdea');
    if (initialIdeaEl) spec.initial_idea = (initialIdeaEl.value || '').trim() || undefined;
    return spec;
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
    'task_requirements': 'specTaskRequirements',
    'task_requirements.task_type': 'specCollaborationPurpose',
    'task_requirements.expected_output': 'specTaskRequirements',
    'task_requirements.collaboration_form': 'specCollaborationPurpose',
    'task_requirements.requirements_text': 'specTaskRequirements',
    'teaching_stage': 'specTeachingStage',
    'collaboration_purpose': 'specCollaborationPurpose',
    'group_size': 'specGroupSize',
    'grouping_strategy': 'specGroupingStrategy',
    'role_structure': 'specRoleStructure',
    'activity_design': 'specTeachingStage'
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
                resultDiv.innerHTML = '<h4><i class="fas fa-exclamation-circle"></i> ' + t('teacher.validation.failed_title') + '</h4><ul>' + (result.issues || []).map(function(issue) { return '<li>' + escapeHtml(issue) + '</li>'; }).join('') + '</ul><p><strong>' + t('teacher.validation.action_label') + '</strong> ' + t('teacher.validation.fix_issues') + '</p>';
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
            showNotification(t('teacher.notify.validation_failed'), 'error');
        } else if (res.status === 401) {
            if (resultDiv) resultDiv.className = 'validation-result error';
            if (resultDiv) resultDiv.innerHTML = '<p>' + t('teacher.notify.login_first') + '</p>';
            if (document.getElementById('wizardStep2Next')) document.getElementById('wizardStep2Next').disabled = true;
            showNotification(t('teacher.notify.login_first'), 'error');
        } else if (res.status === 403) {
            if (resultDiv) resultDiv.className = 'validation-result error';
            if (resultDiv) resultDiv.innerHTML = '<p>' + t('teacher.notify.no_permission') + '</p>';
            if (document.getElementById('wizardStep2Next')) document.getElementById('wizardStep2Next').disabled = true;
            showNotification(t('teacher.notify.no_permission'), 'error');
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
            resultDiv.innerHTML = '<p>' + t('teacher.validation.service_unavailable') + '</p>';
        }
        showNotification(t('teacher.notify.validation_failed'), 'error');
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
            status.textContent = t('teacher.pipeline.pending');
            status.className = 'stage-status';
        }
        var inputEl = stage.querySelector('.input-summary');
        if (inputEl) {
            var spans = inputEl.querySelectorAll('span');
            var target = spans.length > 1 ? spans[1] : spans[0];
            if (target) { target.removeAttribute('data-i18n'); target.textContent = t('teacher.pipeline.waiting'); }
        }
        var outputEl = stage.querySelector('.output-summary');
        if (outputEl) {
            var spans = outputEl.querySelectorAll('span');
            var target = spans.length > 1 ? spans[1] : spans[0];
            if (target) { target.removeAttribute('data-i18n'); target.textContent = t('teacher.pipeline.waiting'); }
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
                    statusEl.textContent = t('teacher.pipeline.skipped');
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
    if (titleEl) titleEl.textContent = message || t('teacher.pipeline.error_title');
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
            listEl.innerHTML = '<li>' + escapeHtml(message || t('teacher.pipeline.error_title')) + '</li>';
        }
    }
    if (actionEl) {
        if (showRetryButton) {
            actionEl.innerHTML = '<button class="btn-secondary" onclick="retryPipelineWithFallback()" style="margin-top: 10px;"><i class="fas fa-redo"></i> ' + t('teacher.pipeline.retry_fallback') + '</button>';
        } else {
            actionEl.textContent = t('teacher.pipeline.fix_and_retry');
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
    if (runBtn) { runBtn.disabled = true; runBtn.classList.add('btn-loading'); runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.generating') : 'Generating...'); }
    if (!currentSpec) {
        showNotification(t('teacher.notify.complete_validation_first'), 'warning');
        pipelineRunInProgress = false;
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
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
            showNotification(t('teacher.pipeline.plan_errors'), 'error');
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
        showNotification(t('teacher.notify.verify_failed'), 'error');
        pipelineRunInProgress = false;
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
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
                    course_id: wizardFolderId || DEFAULT_COURSE_ID,
                    folder_id: wizardFolderId,
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
                    showNotification(t('teacher.notify.session_expired'), 'error');
                    pipelineRunInProgress = false;
                    if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
                    return;
                }
                showNotification(t('teacher.notify.create_script_failed'), 'error');
                pipelineRunInProgress = false;
                if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
                return;
            }
        } catch (error) {
            console.error('Error creating script:', error);
            showNotification(t('teacher.notify.create_script_failed'), 'error');
            pipelineRunInProgress = false;
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            return;
        }
    }

    // Guard: GET script to avoid stale id / auth mismatch
    try {
        var getRes = await fetch(API_BASE + '/scripts/' + currentScriptId, { credentials: 'include' });
        if (getRes.status === 404) {
            currentScriptId = null;
            if (typeof sessionStorage !== 'undefined') sessionStorage.removeItem('cscl_current_script_id');
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            showNotification(t('teacher.notify.script_expired'), 'warning');
            goToStep(2);
            return;
        }
        if (getRes.status === 401) {
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            showNotification(t('teacher.notify.session_expired'), 'error');
            return;
        }
    } catch (e) {
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
        showNotification(t('teacher.notify.verify_failed'), 'error');
        return;
    }

    try {
        showLoading(true);
        resetPipelineStageCards();
        var idemKey = 'run-' + currentScriptId + '-' + (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now() + '-' + Math.random().toString(36).slice(2));

        // Include AI enhancement settings in pipeline run
        var pipelinePayload = {
            spec: currentSpec,
            idempotency_key: idemKey,
            ai_enhancement: {
                image_generation: aiEnhancementSettings.image_generation || false,
                web_retrieval: aiEnhancementSettings.web_retrieval || false
            }
        };

        var res = await fetch(API_BASE + '/scripts/' + currentScriptId + '/pipeline/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Idempotency-Key': idemKey
            },
            body: JSON.stringify(pipelinePayload),
            credentials: 'include'
        });
        var result = await res.json().catch(function() { return {}; });

        if (res.status === 401) {
            pipelineRunInProgress = false;
            showLoading(false);
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            showNotification(t('teacher.notify.session_expired'), 'error');
            return;
        }
        if (res.status === 403) {
            pipelineRunInProgress = false;
            showLoading(false);
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            showNotification(t('teacher.notify.no_permission'), 'error');
            return;
        }
        if (res.status === 400) {
            pipelineRunInProgress = false;
            showLoading(false);
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            var code = result.code || '';
            var errMsg = result.error || result.message || 'Request failed.';
            if (code === 'PREFLIGHT_NO_COURSE_DOCS') {
                errMsg = typeof t === 'function' ? t('teacher.pipeline.no_course_docs') : '当前课程下还没有上传文档。请先在 Step 1 中上传课程文档，再点击运行生成。';
                showPipelineErrorPanel(errMsg, typeof t === 'function' ? t('teacher.pipeline.no_docs_title') : '请先上传课程文档', false);
                showNotification(errMsg, 'error');
                goToStep(1);
            } else if (code === 'PREFLIGHT_MISSING_COURSE_ID') {
                showNotification(typeof t === 'function' ? t('teacher.pipeline.missing_course_id') : '请填写课程信息（Step 2 中的课程）后再运行。', 'error');
                goToStep(2);
            } else {
                showNotification(errMsg, 'error');
            }
            resetPipelineStageCards();
            return;
        }
        if (res.status === 503) {
            if (result.code === 'LLM_PROVIDER_NOT_READY') {
                var errorMsg = result.error || 'Configured LLM provider is not runnable';
                var details = result.details || {};
                var reason = details.reason || 'Provider not available';
                var hint = (typeof t === 'function' && t('teacher.pipeline.llm_hint')) ? t('teacher.pipeline.llm_hint') : 'If self-hosting, set OPENAI_API_KEY (or Qwen API key) in the environment.';
                showPipelineErrorPanel(
                    errorMsg + '. ' + reason + ' ' + hint,
                    'LLM Provider Not Ready',
                    true
                );
                if (typeof sessionStorage !== 'undefined' && currentSpec) {
                    sessionStorage.setItem('cscl_current_spec', JSON.stringify(currentSpec));
                }
                showNotification(errorMsg, 'error');
            } else {
                showNotification(t('teacher.notify.service_temp_unavailable'), 'warning');
                simulatePipelineRun();
            }
            pipelineRunInProgress = false;
            showLoading(false);
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            resetPipelineStageCards();
            return;
        }
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
                var errorMsg = result.error || 'Pipeline execution failed';
                showPipelineErrorPanel(
                    errorMsg,
                    'Pipeline Failed',
                    true
                );
                if (typeof sessionStorage !== 'undefined' && currentSpec) {
                    sessionStorage.setItem('cscl_current_spec', JSON.stringify(currentSpec));
                }
                showNotification(errorMsg, 'error');
            } else {
                showNotification(result.error || result.message || 'Pipeline failed', 'error');
            }
            pipelineRunInProgress = false;
            showLoading(false);
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            resetPipelineStageCards();
            return;
        }
        if (result.success && result.run_id) {
            currentPipelineRunId = result.run_id;
            try { sessionStorage.setItem('cscl_current_run_id', result.run_id); } catch (e) {}
            if (result.status === 'success' || result.status === 'completed') {
                showNotification(t('teacher.notify.generation_completed'), 'success');
                updateStageCardsFromResult(result);
                var nextBtn = document.getElementById('wizardStep3Next');
                if (nextBtn) nextBtn.disabled = false;
                pipelineRunInProgress = false;
                showLoading(false);
                if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            } else if (result.status === 'partial_failed') {
                showNotification(t('teacher.notify.generation_partial'), 'warning');
                updateStageCardsFromResult(result);
                pipelineRunInProgress = false;
                showLoading(false);
                if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            } else {
                showNotification(t('teacher.notify.pipeline_started'), 'success');
                _pipelinePollingActive = true;
                pollPipelineStatus(result.run_id);
            }
        } else {
            showNotification(t('teacher.notify.pipeline_failed_start'), 'error');
            resetPipelineStageCards();
            pipelineRunInProgress = false;
            showLoading(false);
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
        }
    } catch (error) {
        console.error('Error running pipeline:', error);
        showNotification(t('teacher.notify.pipeline_failed'), 'error');
        resetPipelineStageCards();
        pipelineRunInProgress = false;
        showLoading(false);
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
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
                _finishPolling(t('teacher.notify.pipeline_timeout'), 'error');
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
                _finishPolling(t('teacher.notify.pipeline_completed'), 'success');
            } else if (data.run.status === 'failed' || data.run.status === 'partial_failed') {
                _finishPolling(t('teacher.notify.pipeline_failed') + ': ' + (data.run.error_message || 'unknown'), 'warning');
            }
        } else {
            _pollRetryCount++;
            if (_pollRetryCount < _pollMaxRetries) {
                setTimeout(() => pollPipelineStatus(runId), 2000);
            } else {
                _finishPolling(t('teacher.notify.pipeline_poll_failed'), 'error');
            }
        }
    } catch (error) {
        console.error('Error polling pipeline:', error);
        _pollRetryCount++;
        if (_pollRetryCount < _pollMaxRetries) {
            setTimeout(() => pollPipelineStatus(runId), 3000);
        } else {
            _finishPolling(t('teacher.notify.pipeline_poll_failed'), 'error');
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
    if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
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
            if (runBtn) { runBtn.disabled = true; runBtn.classList.add('btn-loading'); runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.generating') : 'Generating...'); }
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
            if (stage.status === 'success') target.textContent = t('teacher.pipeline.done');
            else if (stage.status === 'running') target.textContent = t('teacher.pipeline.processing');
            else if (stage.status === 'failed') target.textContent = t('teacher.pipeline.error_label');
            else if (stage.status === 'skipped') target.textContent = t('teacher.pipeline.skipped');
        }
    }
    if (outputEl) {
        var outputSpans = outputEl.querySelectorAll('span');
        var target = outputSpans.length > 1 ? outputSpans[1] : outputSpans[0];
        if (target) {
            target.removeAttribute('data-i18n');
            if (stage.status === 'success') target.textContent = stage.output_json ? t('teacher.pipeline.generated') : t('teacher.pipeline.done');
            else if (stage.status === 'running') target.textContent = t('teacher.pipeline.waiting');
            else if (stage.status === 'failed') target.textContent = stage.error_message ? stage.error_message.substring(0, 60) : t('teacher.pipeline.failed_label');
            else if (stage.status === 'skipped') target.textContent = t('teacher.pipeline.skipped');
        }
    }
}

// S2.18: Retry pipeline with fallback provider
async function retryPipelineWithFallback() {
    if (!currentScriptId) {
        showNotification(t('teacher.notify.no_retry_script'), 'warning');
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
        showNotification(t('teacher.notify.no_retry_spec'), 'warning');
        return;
    }
    
    var runBtn = document.getElementById('runPipelineBtn');
    hidePipelineErrorPanel();
    
    try {
        showLoading(true);
        if (runBtn) { runBtn.disabled = true; runBtn.innerHTML = '<i class="fas fa-sync fa-spin"></i> ' + t('teacher.notify.retrying'); }
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
            showNotification(t('teacher.notify.session_expired'), 'error');
            return;
        }
        if (res.status === 403) {
            showNotification(t('teacher.notify.no_permission'), 'error');
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
                showNotification(t('teacher.notify.retry_success'), 'success');
                updateStageCardsFromResult(result);
                var nextBtn = document.getElementById('wizardStep3Next');
                if (nextBtn) nextBtn.disabled = false;
                showLoading(false);
                if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
            } else {
                showNotification(t('teacher.notify.pipeline_started'), 'success');
                _pipelinePollingActive = true;
                pollPipelineStatus(result.run_id);
            }
        } else {
            showNotification(t('teacher.notify.pipeline_failed_start'), 'error');
            resetPipelineStageCards();
            showLoading(false);
            if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
        }
    } catch (error) {
        console.error('Error retrying pipeline:', error);
        showNotification(t('teacher.notify.retry_failed'), 'error');
        resetPipelineStageCards();
        showLoading(false);
        if (runBtn) { runBtn.disabled = false; runBtn.classList.remove('btn-loading'); runBtn.innerHTML = '<i class="fas fa-play"></i> ' + (typeof t === 'function' ? t('teacher.pipeline.start') : 'Start Generation'); }
    }
}

function simulatePipelineRun() {
    const stages = ['planner', 'material', 'critic', 'refiner'];
    let currentStage = 0;
    
    const runStage = () => {
        if (currentStage >= stages.length) {
            document.getElementById('wizardStep3Next').disabled = false;
            showNotification(t('teacher.pipeline.simulation_completed'), 'success');
            return;
        }
        
        const stage = stages[currentStage];
        const stageElement = document.querySelector(`[data-stage="${stage}"]`);
        if (stageElement) {
            const statusEl = stageElement.querySelector('.stage-status');
            statusEl.textContent = t('teacher.pipeline.stage.running');
            statusEl.className = 'stage-status running';
            
            setTimeout(() => {
                statusEl.textContent = t('teacher.pipeline.stage.completed');
                statusEl.className = 'stage-status completed';
                stageElement.querySelector('.stage-duration').textContent = '2.5s';
                stageElement.querySelector('.input-summary span').textContent = t('teacher.pipeline.spec_validated') + '...';
                stageElement.querySelector('.output-summary span').textContent = t('teacher.pipeline.generated') + '...';
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
        showNotification(t('teacher.notify.finalize_failed'), 'error');
        return;
    }
    
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/scripts/${currentScriptId}/finalize`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (res.ok) {
            showNotification(t('teacher.notify.finalize_success'), 'success');
            document.getElementById('publishBtn').disabled = false;
        } else if (res.status === 401) {
            showNotification(t('teacher.notify.login_first'), 'error');
        } else if (res.status === 403) {
            showNotification(t('teacher.notify.no_permission'), 'error');
        } else if (res.status === 404) {
            showNotification(t('teacher.notify.script_not_found'), 'error');
        } else {
            showNotification(t('teacher.notify.finalize_failed'), 'error');
        }
    } catch (error) {
        console.error('Error finalizing script:', error);
        showNotification(t('teacher.notify.finalize_failed'), 'error');
    } finally {
        showLoading(false);
    }
}

async function publishScript() {
    if (!currentScriptId) {
        showNotification(t('teacher.notify.publish_failed'), 'error');
        return;
    }
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/scripts/${currentScriptId}/publish`, { method: 'POST', credentials: 'include' });
        const data = await res.json().catch(function() { return {}; });
        if (res.ok && (data.share_code || data.already_published)) {
            var studentUrl = data.student_url || (window.location.origin + '/student?code=' + (data.share_code || ''));
            showPublishShareModal(data.share_code || '', studentUrl);
            if (data.already_published) showNotification(t('teacher.notify.already_published'), 'info');
            else showNotification(t('teacher.notify.publish_success'), 'success');
        } else if (res.status === 401) {
            showNotification(t('teacher.notify.login_first'), 'error');
        } else if (res.status === 403) {
            showNotification(t('teacher.notify.no_permission'), 'error');
        } else if (res.status === 404) {
            showNotification(t('teacher.notify.script_not_found'), 'error');
        } else {
            showNotification(data.error || t('teacher.notify.publish_failed'), 'error');
        }
    } catch (e) {
        console.error('publishScript error', e);
        showNotification(t('teacher.notify.publish_failed'), 'error');
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
        navigator.clipboard.writeText(el.value).then(function() { showNotification(t('teacher.notify.code_copied'), 'success'); }).catch(function() { showNotification(t('teacher.notify.copy_failed'), 'error'); });
    }
}

function copyPublishShareUrl() {
    var el = document.getElementById('publishShareUrlInput');
    if (el && el.value) {
        navigator.clipboard.writeText(el.value).then(function() { showNotification(t('teacher.notify.link_copied'), 'success'); }).catch(function() { showNotification(t('teacher.notify.copy_failed'), 'error'); });
    }
}

async function viewQualityReport() {
    if (!currentScriptId) {
        showNotification(t('teacher.notify.no_script_selected'), 'error');
        return;
    }
    
    switchView('quality-report-detail');
    await loadQualityReportDetail(currentScriptId);
}

async function exportScript(format) {
    if (!currentScriptId) {
        showNotification(t('teacher.notify.no_script_to_export'), 'error');
        return;
    }
    format = (format || 'json').toLowerCase();
    var urlExport = API_BASE + '/scripts/' + currentScriptId + '/export';
    if (format !== 'json') urlExport += '?format=' + encodeURIComponent(format);
    try {
        var res = await fetch(urlExport, { credentials: 'include' });
        if (res.ok) {
            if (format === 'html' || format === 'markdown' || format === 'docx') {
                var blob = await res.blob();
                var disp = res.headers.get('Content-Disposition');
                var filename = 'activity.' + (format === 'html' ? 'html' : format === 'docx' ? 'docx' : 'md');
                if (disp) {
                    var m = disp.match(/filename="?([^";\n]+)"?/);
                    if (m && m[1]) filename = m[1].trim();
                }
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.click();
                URL.revokeObjectURL(url);
            } else {
                var data = await res.json();
                var blob = new Blob([JSON.stringify(data.script, null, 2)], { type: 'application/json' });
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = 'script_' + currentScriptId + '.json';
                a.click();
                URL.revokeObjectURL(url);
            }
            showNotification(t('teacher.notify.export_success'), 'success');
        } else if (res.status === 401) {
            showNotification(t('teacher.notify.login_first'), 'error');
        } else if (res.status === 403) {
            showNotification(t('teacher.notify.no_permission'), 'error');
        } else if (res.status === 404) {
            var errBody = await res.json().catch(function() { return {}; });
            showNotification(errBody.error || t('teacher.notify.export_not_found'), 'error');
        } else {
            showNotification(t('teacher.notify.export_failed'), 'error');
        }
    } catch (error) {
        console.error('Error exporting script:', error);
        showNotification(t('teacher.notify.export_failed'), 'error');
    }
}

// Toggle advanced actions panel visibility in Step 4
function toggleAdvancedActions() {
    var panel = document.getElementById('advancedActionsPanel');
    var icon = document.getElementById('advancedToggleIcon');
    if (!panel) return;
    var isHidden = panel.style.display === 'none';
    panel.style.display = isHidden ? 'flex' : 'none';
    if (icon) {
        icon.className = isHidden ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
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
                    <h4>${t('teacher.quality.no_scripts')}</h4>
                    <p>${t('teacher.quality.no_scripts_desc')}</p>
                    <button class="btn-primary" onclick="switchView('folders')">
                        <i class="fas fa-folder"></i>
                        ${t('teacher.quality.go_to_folders')}
                    </button>
                </div>
            `;
            return;
        }
        
        // Show list of scripts with quality report links
        container.innerHTML = `
            <div class="quality-reports-list">
                <h3>${t('teacher.quality.select_script')}</h3>
                <div class="scripts-grid">
                    ${scripts.map(script => `
                        <div class="script-card" onclick="viewScriptQuality('${script.id}')">
                            <div class="script-card-header">
                                <h4>${escapeHtml(script.title || t('teacher.scripts.untitled'))}</h4>
                                <span class="status-badge ${script.status}">${script.status}</span>
                            </div>
                            <div class="script-card-content">
                                <p><strong>${t('teacher.scripts.topic')}</strong> ${escapeHtml(script.topic || 'N/A')}</p>
                            </div>
                            <div class="script-card-footer">
                                <button class="btn-primary" onclick="event.stopPropagation(); viewScriptQuality('${script.id}')">
                                    <i class="fas fa-chart-line"></i>
                                    ${t('teacher.quality.view_report')}
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading quality reports:', error);
        container.innerHTML = '<div class="empty-state"><p>' + t('teacher.quality.error_loading') + '</p></div>';
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
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.login_first') + '</p></div>';
            return;
        }
        
        if (res.status === 403) {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.no_permission') + '</p></div>';
            return;
        }
        
        if (res.status === 404) {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.quality.not_found') + '</p></div>';
            return;
        }
        
        if (res.ok) {
            const data = await res.json();
            renderQualityReport(data.report);
        } else {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.quality.load_failed') + '</p></div>';
        }
    } catch (error) {
        console.error('Error loading quality report:', error);
        container.innerHTML = '<div class="empty-state"><p>' + t('teacher.quality.error_loading') + '</p></div>';
    } finally {
        showLoading(false);
    }
}

function renderQualityReport(report) {
    const container = document.getElementById('qualityReportDetailContent');
    const dims = report.dimensions || report;
    const summary = report.summary || {};
    const overallScore = summary.overall_score || 0;
    const overallStatus = summary.status || (overallScore >= 70 ? 'good' : overallScore >= 50 ? 'needs_attention' : 'insufficient_data');

    const primaryDims = [
        { key: 'coverage', label: t('teacher.quality.dim_coverage'), icon: 'fas fa-check-circle', desc: t('teacher.quality.dim_coverage_desc') },
        { key: 'pedagogical_alignment', label: t('teacher.quality.dim_pedagogical'), icon: 'fas fa-graduation-cap', desc: t('teacher.quality.dim_pedagogical_desc') },
        { key: 'grounding', label: t('teacher.quality.dim_grounding'), icon: 'fas fa-anchor', desc: t('teacher.quality.dim_grounding_desc') }
    ];
    const advancedDims = [
        { key: 'argumentation_support', label: t('teacher.quality.dim_argumentation'), icon: 'fas fa-comments', desc: t('teacher.quality.dim_argumentation_desc'), how: t('teacher.quality.dim_argumentation_how') },
        { key: 'safety_checks', label: t('teacher.quality.dim_safety'), icon: 'fas fa-shield-alt', desc: t('teacher.quality.dim_safety_desc'), how: t('teacher.quality.dim_safety_how') },
        { key: 'teacher_in_loop', label: t('teacher.quality.dim_teacher'), icon: 'fas fa-user-check', desc: t('teacher.quality.dim_teacher_desc'), how: t('teacher.quality.dim_teacher_how') }
    ];

    function getDimMetric(key) {
        var m = dims[key] || {};
        var rawEv = m.evidence || [];
        var ev = Array.isArray(rawEv) ? rawEv : (typeof rawEv === 'object' ? Object.values(rawEv).flat() : [String(rawEv)]);
        return { score: m.score || 0, status: getStatusFromScore(m.score || 0), evidence: ev, action_tip: m.action_tip || '' };
    }

    var publishLabel, publishClass;
    if (overallScore >= 70) { publishLabel = t('teacher.quality.ready_to_publish'); publishClass = 'review-ready'; }
    else if (overallScore >= 50) { publishLabel = t('teacher.quality.needs_revision'); publishClass = 'review-needs-revision'; }
    else { publishLabel = t('teacher.quality.not_ready'); publishClass = 'review-not-ready'; }

    var summaryText = summary.summary_text || '';
    if (!summaryText) {
        var issues = [];
        primaryDims.forEach(function(d) { var m = getDimMetric(d.key); if (m.score < 70 && m.action_tip) issues.push(m.action_tip); });
        summaryText = issues.length > 0 ? issues.join(' ') : t('teacher.quality.no_action');
    }

    var warnings = report.warnings || [];

    container.innerHTML = `
        <div class="review-page">
            <div class="review-summary-card ${publishClass}">
                <div class="review-summary-header">
                    <div class="review-status-badge ${publishClass}">
                        <i class="fas ${overallScore >= 70 ? 'fa-check-circle' : overallScore >= 50 ? 'fa-exclamation-triangle' : 'fa-times-circle'}"></i>
                        ${publishLabel}
                    </div>
                </div>
                <div class="review-summary-text">
                    <h4>${t('teacher.quality.review_summary_label')}</h4>
                    <p>${escapeHtml(summaryText)}</p>
                </div>
            </div>

            <div class="review-section">
                <h3>${t('teacher.quality.key_checks')}</h3>
                <div class="review-checks-grid">
                    ${primaryDims.map(function(dim) {
                        var m = getDimMetric(dim.key);
                        return '<div class="review-check-card ' + m.status + '">' +
                            '<div class="review-check-header">' +
                                '<i class="' + dim.icon + '"></i>' +
                                '<span class="review-check-label">' + dim.label + '</span>' +
                                '<span class="review-check-score ' + m.status + '">' + m.score + '/100</span>' +
                            '</div>' +
                            '<p class="review-check-desc">' + escapeHtml(dim.desc) + '</p>' +
                            (m.action_tip ? '<p class="review-check-tip"><i class="fas fa-lightbulb"></i> ' + escapeHtml(m.action_tip) + '</p>' : '') +
                        '</div>';
                    }).join('')}
                </div>
            </div>

            ${warnings.length > 0 ? '<div class="review-section review-warnings"><h3><i class="fas fa-exclamation-triangle"></i> ' + t('teacher.quality.suggested_revisions') + '</h3><ul>' + warnings.map(function(w) { return '<li>' + escapeHtml(typeof w === 'string' ? w : w.message || '') + '</li>'; }).join('') + '</ul></div>' : ''}

            <div class="review-section review-advanced">
                <button class="btn-secondary review-advanced-toggle" onclick="toggleAdvancedReview()">
                    <i class="fas fa-chevron-down"></i> ${t('teacher.quality.show_advanced')}
                </button>
                <div class="review-advanced-content" style="display:none;">
                    <div class="quality-report-grid">
                        ${[...primaryDims, ...advancedDims].map(function(dim) {
                            var m = getDimMetric(dim.key);
                            var howText = dim.how || '';
                            return '<div class="quality-dimension-card ' + m.status + '">' +
                                '<div class="dimension-header">' +
                                    '<div class="dimension-icon"><i class="' + dim.icon + '"></i></div>' +
                                    '<div class="dimension-info">' +
                                        '<h4>' + dim.label + '</h4>' +
                                        '<p class="dimension-desc">' + escapeHtml(dim.desc) + '</p>' +
                                        '<div class="dimension-score"><span class="score-value">' + m.score + '/100</span><span class="score-status ' + m.status + '">' + (m.score === 0 ? t('teacher.quality.not_assessed') : m.status) + '</span></div>' +
                                        (howText ? '<div class="dimension-how-assessed"><span class="how-assessed-label"><i class="fas fa-info-circle"></i> ' + t('teacher.quality.how_assessed') + ':</span><span class="how-assessed-text">' + escapeHtml(howText) + '</span></div>' : '') +
                                    '</div>' +
                                '</div>' +
                                '<div class="dimension-body">' +
                                    '<div class="dimension-evidence"><h5>' + t('teacher.quality.evidence') + ':</h5>' +
                                        (m.evidence.length > 0 ? '<ul>' + m.evidence.map(function(e) { return '<li>' + escapeHtml(typeof e === 'string' ? e : JSON.stringify(e)) + '</li>'; }).join('') + '</ul>' : '<p>' + t('teacher.quality.no_evidence') + '</p>') +
                                    '</div>' +
                                    (m.action_tip ? '<div class="dimension-action"><h5>' + t('teacher.quality.action_tip') + ':</h5><p>' + escapeHtml(m.action_tip) + '</p></div>' : '') +
                                '</div>' +
                            '</div>';
                        }).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function toggleAdvancedReview() {
    var content = document.querySelector('.review-advanced-content');
    var btn = document.querySelector('.review-advanced-toggle');
    if (!content || !btn) return;
    var isHidden = content.style.display === 'none';
    content.style.display = isHidden ? 'block' : 'none';
    btn.innerHTML = '<i class="fas fa-chevron-' + (isHidden ? 'up' : 'down') + '"></i> ' + (isHidden ? t('teacher.quality.hide_advanced') : t('teacher.quality.show_advanced'));
}

function getStatusFromScore(score) {
    if (score === 0) return 'unassessed';
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
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.pipeline.no_runs') + '</p></div>';
        } else {
            container.innerHTML = allRuns.map(run => `
                <div class="pipeline-run-card" onclick="viewPipelineRun('${run.run_id}')">
                    <div class="run-header">
                        <h4>Run ${run.run_id.substring(0, 8)}...</h4>
                        <span class="status-badge ${run.status}">${run.status}</span>
                    </div>
                    <div class="run-content">
                        <p><strong>ID:</strong> ${run.script_id.substring(0, 8)}...</p>
                        <p><strong>${t('teacher.scripts.updated')}</strong> ${formatTime(run.created_at)}</p>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading pipeline runs:', error);
        container.innerHTML = '<div class="empty-state"><p>' + t('teacher.pipeline.load_runs_error') + '</p></div>';
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
    if (!timeString) return '-';
    const date = new Date(timeString);
    return date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function openScript(scriptId) {
    currentScriptId = scriptId;
    switchView('scripts');
}

/** Open script in wizard at Step 2 to edit and re-run pipeline */
async function editScript(scriptId) {
    try {
        showLoading(true);
        var res = await fetch(API_BASE + '/scripts/' + scriptId, { credentials: 'include' });
        if (!res.ok) {
            showNotification(res.status === 404 ? 'Script not found' : 'Failed to load script', 'error');
            return;
        }
        var data = await res.json();
        var script = data.script || data;
        var flat = {
            course: script.course_id || script.title || '',
            topic: script.topic || '',
            duration_minutes: script.duration_minutes != null ? script.duration_minutes : 90,
            mode: 'sync',
            class_size: 30,
            course_context: script.topic ? 'Activity: ' + script.topic : '',
            learning_objectives: Array.isArray(script.learning_objectives) ? script.learning_objectives : (script.learning_objectives ? [script.learning_objectives] : []),
            task_type: script.task_type || 'structured_debate',
            teaching_stage: 'concept_exploration',
            collaboration_purpose: 'compare_ideas',
            group_size: 4,
            grouping_strategy: 'random',
            role_structure: 'no_roles',
            whole_class_reporting: true,
            scaffolding_options: [],
            student_difficulties: '',
            output_format: ['student_worksheet', 'student_slides', 'teacher_facilitation_sheet'],
            task_requirements: '',
            initial_idea: ''
        };
        currentScriptId = scriptId;
        if (typeof fillSpecForm === 'function') fillSpecForm(flat);
        goToStep(2);
        showNotification(typeof t === 'function' ? t('teacher.scripts.edit_ready') : 'Edit the form and run generation again.', 'success');
    } catch (e) {
        console.error('editScript error', e);
        showNotification(t('teacher.notify.load_script_failed'), 'error');
    } finally {
        showLoading(false);
    }
}

/** Create a copy of the script */
async function duplicateScript(scriptId) {
    try {
        showLoading(true);
        var res = await fetch(API_BASE + '/scripts/' + scriptId, { credentials: 'include' });
        if (!res.ok) {
            showNotification(t('teacher.notify.load_script_failed'), 'error');
            return;
        }
        var data = await res.json();
        var script = data.script || data;
        var copyTitle = (script.title || 'Untitled') + (typeof t === 'function' ? t('teacher.scripts.copy_suffix') : ' (Copy)');
        var createRes = await fetch(API_BASE + '/scripts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: copyTitle,
                topic: script.topic || '',
                course_id: script.course_id || null,
                task_type: script.task_type || 'structured_debate',
                duration_minutes: script.duration_minutes != null ? script.duration_minutes : 60,
                learning_objectives: script.learning_objectives || []
            }),
            credentials: 'include'
        });
        if (!createRes.ok) {
            var errData = await createRes.json().catch(function() { return {}; });
            showNotification(errData.error || errData.message || 'Failed to duplicate', 'error');
            return;
        }
        var createData = await createRes.json();
        var newScript = createData.script;
        showNotification(typeof t === 'function' ? t('teacher.scripts.duplicate_success') : 'Script duplicated. You can edit it from the list.', 'success');
        loadScripts();
    } catch (e) {
        console.error('duplicateScript error', e);
        showNotification(t('teacher.notify.duplicate_failed'), 'error');
    } finally {
        showLoading(false);
    }
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
        task_type: '',
        expected_output: ''
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
                <h4><i class="fas fa-exclamation-circle"></i> ${t('teacher.validation.failed_title')}</h4>
                <ul>
                    ${result.issues.map(issue => `<li>${escapeHtml(issue)}</li>`).join('')}
                </ul>
                <p><strong>${t('teacher.validation.action_label')}</strong> ${t('teacher.validation.fix_issues')}</p>
            `;
        } else if (res.status === 401) {
            resultDiv.className = 'validation-result error';
            resultDiv.innerHTML = '<p>' + t('teacher.notify.login_first') + '</p>';
        } else if (res.status === 403) {
            resultDiv.className = 'validation-result error';
            resultDiv.innerHTML = '<p>' + t('teacher.notify.no_permission') + '</p>';
        } else {
            resultDiv.className = 'validation-result success';
            resultDiv.innerHTML = `
                <h4><i class="fas fa-check-circle"></i> ${t('teacher.validation.success_title')}</h4>
                <p>${t('teacher.spec.ready')}</p>
                <button class="btn-primary" onclick="createNewScriptProject()" style="margin-top: 1rem;">
                    <i class="fas fa-arrow-right"></i>
                    ${t('teacher.validation.create_script')}
                </button>
            `;
            showNotification(typeof t === 'function' ? t('teacher.spec.validated') : 'Teaching plan validated successfully', 'success');
        }
    } catch (error) {
        console.error('Error validating spec:', error);
        const resultDiv = document.getElementById('standaloneValidationResult');
        resultDiv.classList.remove('hidden');
        resultDiv.className = 'validation-result error';
        resultDiv.innerHTML = '<p>' + t('teacher.validation.service_unavailable') + '</p>';
    } finally {
        showLoading(false);
    }
}

// Document Management - Organized by Activity/Folder
async function loadDocuments() {
    const container = document.getElementById('documentsList');
    try {
        showLoading(true);
        const courseId = DEFAULT_COURSE_ID;
        
        // Load both folders and documents in parallel
        const [foldersRes, docsRes] = await Promise.all([
            fetch(`${API_BASE}/folders`, { credentials: 'include' }),
            fetch(`${API_BASE}/courses/${courseId}/docs`, { credentials: 'include' })
        ]);
        
        if (docsRes.status === 401) {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.login_first') + '</p></div>';
            return;
        }
        
        if (docsRes.status === 403) {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.no_permission') + '</p></div>';
            return;
        }
        
        // Get folders data
        let folders = [];
        let folderMap = {};
        if (foldersRes.ok) {
            const foldersData = await foldersRes.json();
            folders = foldersData.folders || [];
            folderMap = folders.reduce(function(acc, f) {
                acc[f.id] = f;
                return acc;
            }, {});
        }
        
        if (docsRes.ok) {
            const data = await docsRes.json();
            const documents = data.documents || [];
            
            if (documents.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-book"></i>
                        <h4>${t('teacher.doc.no_docs')}</h4>
                        <p>${t('teacher.doc.no_docs_desc')}</p>
                        <button class="btn-primary" onclick="uploadDocument()">
                            <i class="fas fa-upload"></i>
                            ${t('teacher.doc.upload_first')}
                        </button>
                    </div>
                `;
            } else {
                // Group documents by folder_id
                var courseDocs = documents.filter(function(d) { return !d.folder_id; });
                var groupedDocs = {};
                documents.forEach(function(doc) {
                    if (doc.folder_id) {
                        if (!groupedDocs[doc.folder_id]) {
                            groupedDocs[doc.folder_id] = [];
                        }
                        groupedDocs[doc.folder_id].push(doc);
                    }
                });
                
                var uploadedLabel = typeof t === 'function' ? t('teacher.wizard.step1.uploaded_at') : '上传时间';
                var html = '';
                
                // Helper function to render a document card
                function renderDocCard(doc) {
                    return '<div class="document-card" style="margin-bottom: 0.75rem; border: 1px solid #e9ecef; border-radius: 6px; padding: 0.75rem;">' +
                        '<div class="document-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">' +
                            '<h4 style="margin: 0; font-size: 0.95rem;">' + escapeHtml(doc.title || t('teacher.doc.untitled')) + '</h4>' +
                            '<span class="document-type" style="font-size: 0.75rem; color: #6c757d; background: #f8f9fa; padding: 0.25rem 0.5rem; border-radius: 4px;">' + (doc.mime_type || 'text/plain') + '</span>' +
                        '</div>' +
                        '<div class="document-content" style="font-size: 0.85rem; color: #6c757d; margin-bottom: 0.5rem;">' +
                            '<span><i class="fas fa-clock"></i> ' + uploadedLabel + ': ' + formatTime(doc.created_at) + '</span>' +
                        '</div>' +
                        '<div class="document-actions" style="display: flex; gap: 0.5rem;">' +
                            '<button class="btn-primary btn-sm" onclick="applyPrefillFromDoc(\'' + doc.id + '\')" title="' + t('teacher.doc.prefill_title') + '" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">' +
                                '<i class="fas fa-magic"></i> ' + t('teacher.doc.prefill_btn') +
                            '</button>' +
                            '<button class="btn-secondary btn-sm" onclick="deleteDocument(\'' + doc.id + '\')" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">' +
                                '<i class="fas fa-trash"></i>' +
                            '</button>' +
                        '</div>' +
                    '</div>';
                }
                
                // 1. Course-level documents section
                if (courseDocs.length > 0) {
                    html += '<div class="docs-section" style="margin-bottom: 1.5rem;">';
                    html += '<h3 style="font-size: 1.1rem; color: #495057; margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 2px solid #dee2e6;">' +
                        '<i class="fas fa-graduation-cap"></i> ' + t('teacher.doc.course_materials') + '</h3>';
                    html += '<div class="docs-list">';
                    courseDocs.forEach(function(doc) {
                        html += renderDocCard(doc);
                    });
                    html += '</div></div>';
                }
                
                // 2. Activity/Folder documents sections
                Object.keys(groupedDocs).forEach(function(folderId) {
                    var folder = folderMap[folderId];
                    var folderName = folder ? folder.name : t('teacher.doc.activity_prefix') + ' ' + folderId.substring(0, 8);
                    var folderDocs = groupedDocs[folderId];
                    
                    html += '<div class="docs-section" style="margin-bottom: 1.5rem;">';
                    html += '<h3 style="font-size: 1.1rem; color: #495057; margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 2px solid #007bff;">' +
                        '<i class="fas fa-folder-open"></i> ' + escapeHtml(folderName) + '</h3>';
                    html += '<div class="docs-list">';
                    folderDocs.forEach(function(doc) {
                        html += renderDocCard(doc);
                    });
                    html += '</div></div>';
                });
                
                container.innerHTML = html || '<div class="empty-state"><p>' + t('teacher.doc.no_docs') + '</p></div>';
            }
        } else {
            container.innerHTML = '<div class="empty-state"><p>' + t('teacher.notify.load_failed') + '</p></div>';
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        container.innerHTML = '<div class="empty-state"><p>' + t('teacher.quality.error_loading') + '</p></div>';
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
            showNotification(data.message || t('teacher.notify.prefill_failed'), 'error');
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
        else showNotification(typeof t === 'function' ? t('teacher.doc.prefill_success') : '建议已填充。请确认或编辑，然后验证。', 'success');
        if (typeof goToStep === 'function') goToStep(2);
    } catch (e) {
        console.error('Prefill error:', e);
        showNotification(t('teacher.notify.prefill_load_error'), 'error');
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
                    showNotification(typeof t === 'function' ? t('teacher.pdf.parse_failed_binary') : '解析失败：检测到二进制PDF内容。请重新上传或使用其他文件。', 'error');
                    return;
                }
                showNotification(t('teacher.notify.doc_upload_success'), 'success');
                loadDocuments(); // Will display extracted_text_preview or empty state
            } else {
                var code = result.code || '';
                var msg = typeof t === 'function'
                    ? (code === 'PDF_PARSE_FAILED' ? t('teacher.pdf.parse_failed_binary')
                        : code === 'EMPTY_EXTRACTED_TEXT' ? t('teacher.pdf.parse_failed_empty')
                        : code === 'TEXT_TOO_SHORT' ? t('teacher.pdf.parse_failed_short')
                        : t('teacher.pdf.parse_failed_generic'))
                    : '提取失败。请重试或使用其他文件。';
                showNotification(msg, 'error');
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            showNotification(typeof t === 'function' ? t('teacher.pdf.parse_failed_generic') : '提取失败。请重试或使用其他文件。', 'error');
        } finally {
            showLoading(false);
        }
    };
    input.click();
}

async function deleteDocument(docId) {
    if (!confirm(t('teacher.notify.doc_delete_confirm'))) {
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
            showNotification(t('teacher.notify.doc_deleted'), 'success');
            loadDocuments();
        } else {
            const result = await res.json();
            showNotification(result.error || t('teacher.notify.doc_delete_failed'), 'error');
        }
    } catch (error) {
        console.error('Error deleting document:', error);
        showNotification(t('teacher.notify.doc_delete_failed'), 'error');
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
                    <h4>${t('teacher.decisions.no_decisions')}</h4>
                    <p>${t('teacher.decisions.no_decisions_desc')}</p>
                    <button class="btn-primary" onclick="switchView('folders')">
                        <i class="fas fa-folder"></i>
                        ${t('teacher.decisions.go_to_folders')}
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
                        <h4>${t('teacher.decisions.no_decisions')}</h4>
                        <p>${t('teacher.decisions.no_decisions_desc')}</p>
                    </div>
                `;
            } else {
                container.innerHTML = decisions.map(decision => `
                    <div class="decision-item">
                        <div class="decision-header">
                            <h4>${escapeHtml(decision.decision_type || t('teacher.decisions.unknown'))}</h4>
                            <span class="decision-time">${formatTime(decision.created_at)}</span>
                        </div>
                        <div class="decision-content">
                            <p><strong>${t('teacher.decisions.target')}</strong> ${escapeHtml(decision.target_type || 'N/A')}</p>
                            ${decision.reason ? `<p><strong>${t('teacher.decisions.reason')}</strong> ${escapeHtml(decision.reason)}</p>` : ''}
                        </div>
                    </div>
                `).join('');
            }
        } else if (res.status === 404) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <h4>${t('teacher.decisions.no_decisions')}</h4>
                    <p>${t('teacher.decisions.no_decisions_desc')}</p>
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
                    <h4>${t('teacher.publish.no_scripts')}</h4>
                    <p>${t('teacher.publish.no_scripts_desc')}</p>
                    <button class="btn-primary" onclick="switchView('folders')">
                        <i class="fas fa-folder"></i>
                        ${t('teacher.quality.go_to_folders')}
                    </button>
                </div>
            `;
        } else {
            container.innerHTML = readyScripts.map(script => `
                <div class="script-card">
                    <div class="script-card-header">
                        <h4>${escapeHtml(script.title || 'Untitled')}</h4>
                        <span class="status-badge final">${t('teacher.publish.ready')}</span>
                    </div>
                    <div class="script-card-content">
                        <p><strong>${t('teacher.publish.topic')}</strong> ${escapeHtml(script.topic || 'N/A')}</p>
                    </div>
                    <div class="script-card-footer">
                        <button class="btn-primary" onclick="publishScriptById('${script.id}')">
                            <i class="fas fa-rocket"></i>
                            ${t('teacher.publish.publish_btn')}
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state"><p>' + t('teacher.publish.error_loading') + '</p></div>';
    }
}

async function publishScriptById(scriptId) {
    if (!scriptId) {
        showNotification(t('teacher.notify.publish_failed'), 'error');
        return;
    }
    try {
        showLoading(true);
        const res = await fetch(`${API_BASE}/scripts/${scriptId}/publish`, { method: 'POST', credentials: 'include' });
        const data = await res.json().catch(function() { return {}; });
        if (res.ok && (data.share_code || data.already_published)) {
            const studentUrl = data.student_url || (window.location.origin + '/student?code=' + (data.share_code || ''));
            showPublishShareModal(data.share_code || '', studentUrl);
            if (data.already_published) showNotification(t('teacher.notify.already_published'), 'info');
            else showNotification(t('teacher.notify.publish_success'), 'success');
        } else if (res.status === 401) {
            showNotification(t('teacher.notify.login_first'), 'error');
        } else if (res.status === 403) {
            showNotification(t('teacher.notify.no_permission'), 'error');
        } else if (res.status === 404) {
            showNotification(t('teacher.notify.script_not_found'), 'error');
        } else {
            showNotification(data.error || t('teacher.notify.publish_failed'), 'error');
        }
    } catch (e) {
        console.error('publishScriptById error', e);
        showNotification(t('teacher.notify.publish_failed'), 'error');
    } finally {
        showLoading(false);
    }
}

// B1/B2: AI Enhancement Settings Functions
function loadAIEnhancementSettings() {
    // Load settings from localStorage
    try {
        const saved = localStorage.getItem('ai_enhancement_settings');
        if (saved) {
            aiEnhancementSettings = JSON.parse(saved);
        }
    } catch (e) {
        console.warn('[teacher] Failed to load AI enhancement settings:', e);
    }
    
    // Update UI toggles
    const imageToggle = document.getElementById('imageGenerationToggle');
    const webToggle = document.getElementById('webRetrievalToggle');
    
    if (imageToggle) {
        imageToggle.checked = aiEnhancementSettings.image_generation;
        // Add change listener
        imageToggle.addEventListener('change', function() {
            aiEnhancementSettings.image_generation = this.checked;
            saveAIEnhancementSettings();
            showNotification(this.checked ? t('teacher.notify.image_gen_enabled') : t('teacher.notify.image_gen_disabled'), 'info');
        });
    }
    
    if (webToggle) {
        webToggle.checked = aiEnhancementSettings.web_retrieval;
        // Add change listener
        webToggle.addEventListener('change', function() {
            aiEnhancementSettings.web_retrieval = this.checked;
            saveAIEnhancementSettings();
            showNotification(this.checked ? t('teacher.notify.web_retrieval_enabled') : t('teacher.notify.web_retrieval_disabled'), 'info');
        });
    }
}

function saveAIEnhancementSettings() {
    try {
        localStorage.setItem('ai_enhancement_settings', JSON.stringify(aiEnhancementSettings));
    } catch (e) {
        console.warn('[teacher] Failed to save AI enhancement settings:', e);
    }
}

function getAIEnhancementSettings() {
    return aiEnhancementSettings;
}

// Initialize settings when settings view is loaded
function initSettingsPage() {
    loadAIEnhancementSettings();
}

// S2.16/S2.17: global compatibility fallback for any remaining inline handlers / old cache
if (typeof goToStep !== 'undefined') { window.goToStep = goToStep; }
if (typeof switchView !== 'undefined') { window.switchView = switchView; }
if (typeof startNewActivity !== 'undefined') { window.startNewActivity = startNewActivity; }
if (typeof uploadDocument !== 'undefined') { window.importCourseDocument = uploadDocument; }
if (typeof validateStandaloneSpec !== 'undefined') { window.validateObjectives = validateStandaloneSpec; }
if (typeof validateSpec !== 'undefined' && !window.validateObjectives) { window.validateObjectives = validateSpec; }
if (typeof runPipeline !== 'undefined') { window.generateScript = runPipeline; }
if (typeof loadAIEnhancementSettings !== 'undefined') { window.loadAIEnhancementSettings = loadAIEnhancementSettings; }
if (typeof saveAIEnhancementSettings !== 'undefined') { window.saveAIEnhancementSettings = saveAIEnhancementSettings; }
if (typeof getAIEnhancementSettings !== 'undefined') { window.getAIEnhancementSettings = getAIEnhancementSettings; }
