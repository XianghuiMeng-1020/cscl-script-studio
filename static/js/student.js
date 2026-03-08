// CSCL Student Dashboard JavaScript - S2.14 dead-UI hotfix
(function() {
    'use strict';
    try {
        if (typeof console !== 'undefined' && console.log) console.log('[student.js] loading');
    } catch (e) {
        if (typeof console !== 'undefined' && console.error) console.error('[student.js] init log failed', e);
    }
})();
const API_BASE = '/api/cscl';
const API_BASE_GENERAL = '/api';

// State
let currentActivity = null;
let currentTask = null;
let currentScriptId = null;

// Initialize - S2.14: catch errors so one failure does not leave UI dead
document.addEventListener('DOMContentLoaded', function() {
    try {
        if (typeof console !== 'undefined' && console.log) console.log('[student.js] DOMContentLoaded');
        var urlParams = new URLSearchParams(window.location.search);
        currentScriptId = urlParams.get('script_id');
        if (currentScriptId) {
            var banner = document.getElementById('contextBanner');
            var scriptIdSpan = document.getElementById('contextScriptId');
            if (banner && scriptIdSpan) {
                banner.classList.remove('hidden');
                scriptIdSpan.textContent = currentScriptId.substring(0, 16) + '...';
            }
        }
        checkHealth();
        if (currentScriptId) {
            loadCurrentActivity();
            loadCurrentTask();
            loadProgress();
        } else {
            showEmptyState();
        }
        loadActivityHistory();
    } catch (err) {
        console.error('[student.js] init error', err);
        if (typeof showNotification === 'function') {
            showNotification('Student UI init failed: ' + (err && err.message ? err.message : 'unknown'), 'error');
        }
    }
});

// Health Check
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE_GENERAL}/health`);
        const data = await res.json();
        console.log('Health check:', data);
    } catch (error) {
        console.error('Health check failed:', error);
        showNotification('服务不可用，部分功能可能无法使用。', 'warning');
    }
}

// Toggle Collapsible Sections
function toggleCollapsible(button) {
    const content = button.nextElementSibling;
    if (content) {
        content.classList.toggle('hidden');
        button.classList.toggle('active');
    }
}

// Submit Task
function submitTask() {
    if (!currentTask) {
        showNotification('没有可提交的任务', 'warning');
        return;
    }
    // TODO: Implement task submission
    showNotification('任务提交功能开发中', 'info');
}

// Continue Task
function continueTask() {
    if (!currentTask) {
        showNotification('没有可继续的任务', 'warning');
        return;
    }
    // TODO: Implement continue task
    showNotification('继续任务功能开发中', 'info');
}

// Load Current Activity
async function loadCurrentActivity() {
    const container = document.getElementById('currentActivityCard');
    
    if (!currentScriptId) {
        showEmptyState();
        return;
    }
    
    try {
        showLoading(true);
        
        // Try to get script export for activity info
        const res = await fetch(`${API_BASE}/scripts/${currentScriptId}/export`, {
            credentials: 'include'
        });
        
        const tr = (typeof t === 'function' ? t : (k, d) => d || k);
        if (res.status === 401) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-lock"></i>
                    <h4>${tr('student.error.login')}</h4>
                    <p>${tr('student.error.login_desc')}</p>
                </div>
            `;
            return;
        }
        if (res.status === 403) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-ban"></i>
                    <h4>${tr('student.error.forbidden')}</h4>
                    <p>${tr('student.error.forbidden_desc')}</p>
                </div>
            `;
            return;
        }
        if (res.status === 404) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <h4>${tr('student.error.not_found')}</h4>
                    <p>${tr('student.error.not_found_desc')}</p>
                    <p><strong>${tr('student.empty.next_step')}</strong></p>
                    <a href="/" class="btn-primary" style="margin-top: 1rem; display: inline-block;">
                        <i class="fas fa-arrow-left"></i>
                        ${tr('home.teacher.action')}
                    </a>
                </div>
            `;
            return;
        }
        
        if (res.ok) {
            const data = await res.json();
            const script = data.script;
            
            // Extract activity info from script
            const activity = {
                id: script.id,
                title: script.title || 'Untitled Activity',
                stage: 'Active',
                deadline: script.updated_at ? new Date(new Date(script.updated_at).getTime() + 7 * 24 * 60 * 60 * 1000).toISOString() : null,
                role: 'Participant',
                nextAction: 'Continue Activity'
            };
            
            currentActivity = activity;
            renderCurrentActivity(activity);
        } else {
            throw new Error(`HTTP ${res.status}`);
        }
    } catch (error) {
        console.error('Error loading current activity:', error);
        const tr = (typeof t === 'function' ? t : (k, d) => d || k);
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h4>${tr('student.error.load_failed')}</h4>
                <p>${tr('common.error.network')}</p>
                <p><strong>${tr('student.empty.next_step')}</strong></p>
                <button class="btn-secondary" onclick="location.reload()" style="margin-top: 1rem;">
                    <i class="fas fa-sync"></i>
                    ${tr('student.error.retry')}
                </button>
            </div>
        `;
    } finally {
        showLoading(false);
    }
}

function showEmptyState() {
    const tr = (typeof t === 'function' ? t : (k, d) => d || k);
    const container = document.getElementById('currentActivityCard');
    container.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-calendar-times"></i>
            <h4>${tr('student.empty.title')}</h4>
            <p><strong>${tr('student.empty.reason')}</strong></p>
            <p><strong>${tr('student.empty.next_step')}</strong></p>
        </div>
    `;
    const taskContainer = document.getElementById('currentTaskCard');
    if (taskContainer) {
        taskContainer.innerHTML = `<div class="empty-state"><p>${tr('student.empty.no_task')}</p></div>`;
    }
}

function renderCurrentActivity(activity) {
    const container = document.getElementById('currentActivityCard');
    const deadline = activity.deadline ? new Date(activity.deadline) : null;
    const now = new Date();
    const timeLeft = deadline ? deadline - now : null;
    const daysLeft = timeLeft ? Math.ceil(timeLeft / (1000 * 60 * 60 * 24)) : null;
    
    container.innerHTML = `
        <div class="activity-card-content">
            <h3 class="activity-title-main">${escapeHtml(activity.title || '未命名活动')}</h3>
            ${deadline ? `
            <div id="deadlineInfo" class="deadline-info">
                <i class="fas fa-clock"></i>
                <span>截止时间：<strong id="deadlineText">${formatDate(activity.deadline)} (剩余 ${daysLeft} 天)</strong></span>
            </div>
            ` : ''}
        </div>
    `;
    
    // Show deadline info if exists
    if (deadline) {
        const deadlineEl = document.getElementById('deadlineInfo');
        if (deadlineEl) {
            deadlineEl.classList.remove('hidden');
        }
    }
}

// Load Current Task
async function loadCurrentTask() {
    const container = document.getElementById('currentTaskCard');
    
    if (!currentScriptId) {
        const tr = (typeof t === 'function' ? t : (k, d) => d || k);
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-info-circle"></i>
                <h4>${tr('student.empty.title')}</h4>
                <p><strong>${tr('student.empty.reason')}</strong></p>
                <p><strong>${tr('student.empty.next_step')}</strong></p>
            </div>
        `;
        return;
    }
    
    try {
        showLoading(true);
        
        // Get script export for task info
        const res = await fetch(`${API_BASE}/scripts/${currentScriptId}/export`, {
            credentials: 'include'
        });
        
        if (res.ok) {
            const data = await res.json();
            const script = data.script;
            
            // Extract task from script scenes
            const scenes = script.scenes || [];
            const firstScene = scenes[0];
            
            if (firstScene) {
                const task = {
                    description: firstScene.purpose || 'Participate in the collaborative learning activity.',
                    instructions: [
                        'Follow the scene instructions',
                        'Collaborate with your peers',
                        'Complete the assigned tasks'
                    ]
                };
                
                // Extract instructions from scriptlets if available
                if (firstScene.scriptlets && firstScene.scriptlets.length > 0) {
                    task.instructions = firstScene.scriptlets.slice(0, 3).map(s => s.prompt_text || 'Follow instructions').slice(0, 50) + '...';
                }
                
                currentTask = task;
                renderCurrentTask(task);
            } else {
                container.innerHTML = `
                    <div class="empty-state">
                        <p><strong>Why empty:</strong> Script has no scenes defined yet.</p>
                        <p><strong>Next step:</strong> Wait for your instructor to complete script generation.</p>
                    </div>
                `;
            }
        } else if (res.status === 404) {
            container.innerHTML = `
                <div class="empty-state">
                    <p><strong>Why empty:</strong> Script not found or not yet created.</p>
                    <p><strong>Next step:</strong> Ask your instructor to create an activity.</p>
                </div>
            `;
        } else {
            throw new Error(`HTTP ${res.status}`);
        }
    } catch (error) {
        console.error('Error loading current task:', error);
        container.innerHTML = `
            <div class="empty-state">
                <p><strong>Why empty:</strong> Unable to load task data.</p>
                <p><strong>Next step:</strong> Check your connection and try again.</p>
            </div>
        `;
    } finally {
        showLoading(false);
    }
}

function renderCurrentTask(task) {
    const container = document.getElementById('currentTaskCard');
    container.innerHTML = `
        <div class="task-content">
            <h4>Current Scene Task</h4>
            <p class="task-description">${escapeHtml(task.description)}</p>
            <div class="task-instructions">
                <h5>Instructions:</h5>
                <ol>
                    ${task.instructions.map(inst => `<li>${escapeHtml(inst)}</li>`).join('')}
                </ol>
            </div>
        </div>
    `;
}

// Load Progress
async function loadProgress() {
    if (!currentScriptId) {
        return;
    }
    
    try {
        // Get quality report for progress summary
        const res = await fetch(`${API_BASE}/scripts/${currentScriptId}/quality-report`, {
            credentials: 'include'
        });
        
        if (res.ok) {
            const data = await res.json();
            const report = data.report || {};
            
            // Calculate average quality score as progress indicator
            const dimensions = ['coverage', 'pedagogical_alignment', 'argumentation_support', 
                              'grounding', 'safety_checks', 'teacher_in_loop'];
            const scores = dimensions.map(d => report[d]?.score || 0).filter(s => s > 0);
            const avgScore = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 50;
            
            // Update progress circle
            const progressCircle = document.querySelector('.progress-circle svg circle:last-child');
            if (progressCircle) {
                const circumference = 2 * Math.PI * 50;
                const offset = circumference - (avgScore / 100) * circumference;
                progressCircle.style.strokeDashoffset = offset;
            }
            
            const percentEl = document.querySelector('.progress-percent');
            if (percentEl) {
                percentEl.textContent = `${avgScore}%`;
            }
        } else {
            // Fallback to default progress
            const progress = 50;
            const progressCircle = document.querySelector('.progress-circle svg circle:last-child');
            if (progressCircle) {
                const circumference = 2 * Math.PI * 50;
                const offset = circumference - (progress / 100) * circumference;
                progressCircle.style.strokeDashoffset = offset;
            }
            
            const percentEl = document.querySelector('.progress-percent');
            if (percentEl) {
                percentEl.textContent = `${progress}%`;
            }
        }
    } catch (error) {
        console.error('Error loading progress:', error);
        // Graceful fallback
        const progress = 50;
        const percentEl = document.querySelector('.progress-percent');
        if (percentEl) {
            percentEl.textContent = `${progress}%`;
        }
    }
}

// Load Activity History
async function loadActivityHistory() {
    const container = document.getElementById('activityHistory');
    try {
        // For now, show empty state
        // In production, this would call an API endpoint for student activity history
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history"></i>
                <h4>No Past Activities</h4>
                <p><strong>Why:</strong> You haven't completed any activities yet.</p>
                <p><strong>Next step:</strong> Complete your current activity to see it in history.</p>
            </div>
        `;
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <p><strong>Why empty:</strong> Error loading activity history.</p>
                <p><strong>Next step:</strong> Try refreshing the page.</p>
            </div>
        `;
    }
}

// Actions
function continueActivity() {
    showNotification('Continuing activity...', 'info');
    // TODO: Navigate to activity detail page
}

function joinDemoActivity() {
    showNotification('Please ask your instructor to create an activity', 'info');
}

// Utility Functions
function showLoading(show) {
    // Simple loading indicator
    if (show) {
        const containers = document.querySelectorAll('#currentActivityCard, #currentTaskCard');
        containers.forEach(container => {
            if (container && !container.querySelector('.loading-placeholder')) {
                const placeholder = document.createElement('div');
                placeholder.className = 'loading-placeholder';
                placeholder.innerHTML = '<i class="fas fa-spinner fa-spin"></i><p>Loading...</p>';
                container.appendChild(placeholder);
            }
        });
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
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
