// Teacher Dashboard JavaScript
const API_BASE = '/api';

// State
let currentSubmission = null;
let currentRubric = null;
let allSubmissions = [];
let allRubrics = [];
let gradingStartTime = null;
let systemConfig = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    setupNavigation();
    loadSystemConfig();
});

// Load system configuration
async function loadSystemConfig() {
    try {
        const res = await fetch(`${API_BASE}/config`);
        systemConfig = await res.json();
    } catch (error) {
        console.error('Error loading config:', error);
        systemConfig = { features: {}, thresholds: {}, limits: {} };
    }
}

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const view = this.dataset.view;
            switchView(view);
        });
    });
}

function switchView(viewName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });
    
    // Update views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(viewName + 'View').classList.add('active');
    
    // Load data for view
    switch(viewName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'submissions':
            loadPendingSubmissions();
            break;
        case 'graded':
            loadGradedSubmissions();
            break;
        case 'rubrics':
            loadRubrics();
            break;
    }
}

// Dashboard
async function loadDashboardData() {
    try {
        const [statsRes, submissionsRes] = await Promise.all([
            fetch(`${API_BASE}/stats/teacher`),
            fetch(`${API_BASE}/submissions`)
        ]);
        
        const stats = await statsRes.json();
        const submissions = await submissionsRes.json();
        allSubmissions = submissions;
        
        // Update stats
        document.getElementById('statAssignments').textContent = stats.total_assignments;
        document.getElementById('statPending').textContent = stats.pending_grading;
        document.getElementById('statGraded').textContent = stats.graded;
        document.getElementById('statAvgScore').textContent = stats.average_score || '--';
        document.getElementById('pendingBadge').textContent = stats.pending_grading;
        
        // Recent submissions
        const recent = submissions.slice(0, 5);
        renderRecentSubmissions(recent);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load data', 'error');
    }
}

function renderRecentSubmissions(submissions) {
    const container = document.getElementById('recentSubmissions');
    
    if (submissions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h4>No Submissions</h4>
                <p>No student submissions yet</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = submissions.map(sub => `
        <div class="submission-item" onclick="openGrading('${sub.id}')">
            <div class="submission-info">
                <div class="submission-avatar">${getInitials(sub.student_name)}</div>
                <div class="submission-details">
                    <h4>${escapeHtml(sub.student_name)}</h4>
                    <p>${escapeHtml(sub.content.substring(0, 50))}...</p>
                </div>
            </div>
            <div class="submission-status">
                <span class="status-badge ${sub.status}">${sub.status === 'pending' ? 'Pending' : 'Graded'}</span>
            </div>
        </div>
    `).join('');
}

// Pending Submissions
async function loadPendingSubmissions() {
    const container = document.getElementById('pendingSubmissions');
    container.innerHTML = '<div class="loading-placeholder"><i class="fas fa-spinner fa-spin"></i><p>Loading...</p></div>';
    
    try {
        const res = await fetch(`${API_BASE}/submissions?status=pending`);
        const submissions = await res.json();
        
        if (submissions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-check-circle"></i>
                    <h4>Great job!</h4>
                    <p>All submissions have been graded</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = submissions.map(sub => renderSubmissionCard(sub)).join('');
        
    } catch (error) {
        console.error('Error loading submissions:', error);
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h4>Failed to load submissions</h4></div>';
    }
}

// Graded Submissions
async function loadGradedSubmissions() {
    const container = document.getElementById('gradedSubmissions');
    container.innerHTML = '<div class="loading-placeholder"><i class="fas fa-spinner fa-spin"></i><p>Loading...</p></div>';
    
    try {
        const res = await fetch(`${API_BASE}/submissions?status=graded`);
        const submissions = await res.json();
        
        if (submissions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <h4>No Graded Submissions</h4>
                    <p>Graded submissions will appear here</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = submissions.map(sub => renderSubmissionCard(sub, true)).join('');
        
    } catch (error) {
        console.error('Error loading submissions:', error);
    }
}

function renderSubmissionCard(sub, isGraded = false) {
    const date = new Date(sub.submitted_at);
    const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    
    return `
        <div class="submission-card" onclick="openGrading('${sub.id}')">
            <div class="submission-card-header">
                <div class="student-badge">
                    <div class="avatar">${getInitials(sub.student_name)}</div>
                    <div class="info">
                        <h4>${escapeHtml(sub.student_name)}</h4>
                        <p>Student ID: ${sub.student_id}</p>
                    </div>
                </div>
                <span class="status-badge ${sub.status}">${sub.status === 'pending' ? 'Pending' : 'Graded'}</span>
            </div>
            <div class="submission-card-content">
                <h5>Submission Content</h5>
                <p class="submission-preview">${escapeHtml(sub.content.substring(0, 150))}...</p>
            </div>
            <div class="submission-card-footer">
                <span class="submission-time"><i class="fas fa-clock"></i> ${dateStr}</span>
                <button class="grade-btn" onclick="event.stopPropagation(); openGrading('${sub.id}')">
                    ${isGraded ? 'View Details' : 'Start Grading'}
                </button>
            </div>
        </div>
    `;
}

// Rubrics
async function loadRubrics() {
    const container = document.getElementById('rubricsList');
    container.innerHTML = '<div class="loading-placeholder"><i class="fas fa-spinner fa-spin"></i><p>Loading...</p></div>';
    
    try {
        const res = await fetch(`${API_BASE}/rubrics`);
        allRubrics = await res.json();
        
        if (allRubrics.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-list-check"></i>
                    <h4>No Rubrics</h4>
                    <p>Please create a rubric first</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = allRubrics.map(rubric => `
            <div class="rubric-card">
                <h4>${escapeHtml(rubric.name)}</h4>
                <p>${escapeHtml(rubric.description)}</p>
                <div class="criteria-list">
                    ${rubric.criteria.map(c => `
                        <div class="criteria-item">
                            <i class="fas fa-check-circle"></i>
                            <span>${escapeHtml(c.name)}</span>
                            <span class="criteria-weight">${c.weight}%</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading rubrics:', error);
    }
}

// Grading
async function openGrading(submissionId) {
    try {
        // Start timing for grading
        gradingStartTime = Date.now();
        
        // Load submission
        const subRes = await fetch(`${API_BASE}/submissions/${submissionId}`);
        currentSubmission = await subRes.json();
        
        // Load rubrics
        const rubRes = await fetch(`${API_BASE}/rubrics`);
        allRubrics = await rubRes.json();
        currentRubric = allRubrics[0]; // Use first rubric
        
        // Switch to grading view
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById('gradingView').classList.add('active');
        
        // Render student work
        document.getElementById('gradingStudentInfo').textContent = currentSubmission.student_name;
        document.getElementById('studentWorkContent').textContent = currentSubmission.content;
        
        // Render rubric scoring
        renderRubricScoring();
        
        // Load existing feedback if graded
        if (currentSubmission.feedback) {
            document.getElementById('feedbackText').value = currentSubmission.feedback;
        } else {
            document.getElementById('feedbackText').value = '';
        }
        
        // Hide AI results and work analysis
        hideAIResults();
        hideWorkAnalysis();
        
    } catch (error) {
        console.error('Error opening grading:', error);
        showNotification('Failed to load submission', 'error');
    }
}

// Hide work analysis panel
function hideWorkAnalysis() {
    const panel = document.getElementById('workAnalysisPanel');
    if (panel) {
        panel.classList.add('hidden');
    }
}

function renderRubricScoring() {
    const container = document.getElementById('rubricScoring');
    
    if (!currentRubric || !currentRubric.criteria) {
        container.innerHTML = '<p>No rubric available</p>';
        return;
    }
    
    const existingScores = currentSubmission.rubric_scores || {};
    
    container.innerHTML = currentRubric.criteria.map(criterion => {
        const selectedLevel = existingScores[criterion.id] || '';
        
        return `
            <div class="score-item" data-criterion-id="${criterion.id}">
                <div class="score-item-header">
                    <h5>${escapeHtml(criterion.name)}</h5>
                    <span class="score-weight">${criterion.weight}%</span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                    ${escapeHtml(criterion.description)}
                </p>
                <div class="score-levels">
                    ${criterion.levels.map(level => `
                        <div class="score-level ${selectedLevel === level ? 'selected' : ''}" 
                             onclick="selectScoreLevel('${criterion.id}', '${level}', this)">
                            ${level}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');
}

function selectScoreLevel(criterionId, level, element) {
    // Update UI
    const parent = element.closest('.score-item');
    parent.querySelectorAll('.score-level').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
}

function getSelectedScores() {
    const scores = {};
    document.querySelectorAll('.score-item').forEach(item => {
        const criterionId = item.dataset.criterionId;
        const selected = item.querySelector('.score-level.selected');
        if (selected) {
            scores[criterionId] = selected.textContent.trim();
        }
    });
    
    // Calculate total score
    let totalScore = 0;
    let totalWeight = 0;
    
    if (currentRubric && currentRubric.criteria) {
        currentRubric.criteria.forEach(c => {
            const level = scores[c.id];
            if (level) {
                const levelIndex = c.levels.indexOf(level);
                const levelScore = ((c.levels.length - levelIndex) / c.levels.length) * 100;
                totalScore += levelScore * (c.weight / 100);
                totalWeight += c.weight;
            }
        });
    }
    
    scores.total = totalWeight > 0 ? Math.round(totalScore) : 0;
    return scores;
}

// AI Functions
async function checkFeedbackAlignment() {
    const feedback = document.getElementById('feedbackText').value;
    if (!feedback.trim()) {
        showNotification('Please enter feedback content first', 'error');
        return;
    }
    
    if (!currentRubric || !currentRubric.criteria) {
        showNotification('No rubric available', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const res = await fetch(`${API_BASE}/ai/check-alignment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                feedback: feedback,
                rubric_criteria: currentRubric.criteria
            })
        });
        
        const result = await res.json();
        
        // Display results
        const content = document.getElementById('aiResultsContent');
        content.innerHTML = `
            <div class="ai-analysis-card">
                <h5>Rubric Coverage</h5>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: ${result.coverage_score}%"></div>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary);">${result.coverage_score}% of rubric criteria mentioned in feedback</p>
            </div>
            <div class="ai-analysis-card">
                <h5>Covered Criteria</h5>
                <div class="criteria-tags">
                    ${result.covered_criteria.map(c => `<span class="criteria-tag covered">${c}</span>`).join('')}
                    ${result.covered_criteria.length === 0 ? '<span style="color: var(--text-muted);">None</span>' : ''}
                </div>
            </div>
            <div class="ai-analysis-card">
                <h5>Missing Criteria</h5>
                <div class="criteria-tags">
                    ${result.missing_criteria.map(c => `<span class="criteria-tag missing">${c}</span>`).join('')}
                    ${result.missing_criteria.length === 0 ? '<span style="color: var(--success-color);">All covered!</span>' : ''}
                </div>
            </div>
            ${result.suggestions.length > 0 ? `
                <div class="ai-analysis-card">
                    <h5>Suggestions</h5>
                    <ul class="suggestions-list">
                        ${result.suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
        
        showAIResults();
        
    } catch (error) {
        console.error('Error checking alignment:', error);
        showNotification('AI analysis failed', 'error');
    } finally {
        hideLoading();
    }
}

async function analyzeFeedbackQuality() {
    const feedback = document.getElementById('feedbackText').value;
    if (!feedback.trim()) {
        showNotification('Please enter feedback content first', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const res = await fetch(`${API_BASE}/ai/analyze-quality`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ feedback: feedback })
        });
        
        const result = await res.json();
        
        const content = document.getElementById('aiResultsContent');
        content.innerHTML = `
            <div class="ai-analysis-card">
                <h5>Feedback Quality Score</h5>
                <div class="quality-scores">
                    <div class="quality-score">
                        <div class="score">${result.specificity?.score || '-'}/5</div>
                        <div class="label">Specificity</div>
                    </div>
                    <div class="quality-score">
                        <div class="score">${result.feedforward?.score || '-'}/5</div>
                        <div class="label">Feedforward</div>
                    </div>
                    <div class="quality-score">
                        <div class="score">${result.tone?.score || '-'}/5</div>
                        <div class="label">Tone</div>
                    </div>
                </div>
            </div>
            <div class="ai-analysis-card">
                <h5>Detailed Analysis</h5>
                <p style="font-size: 0.85rem; margin-bottom: 0.5rem;"><strong>Specificity:</strong> ${result.specificity?.analysis || 'N/A'}</p>
                <p style="font-size: 0.85rem; margin-bottom: 0.5rem;"><strong>Feedforward:</strong> ${result.feedforward?.analysis || 'N/A'}</p>
                <p style="font-size: 0.85rem;"><strong>Tone:</strong> ${result.tone?.analysis || 'N/A'}</p>
            </div>
            ${result.improvement_suggestions?.length > 0 ? `
                <div class="ai-analysis-card">
                    <h5>Improvement Suggestions</h5>
                    <ul class="suggestions-list">
                        ${result.improvement_suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
        
        showAIResults();
        
    } catch (error) {
        console.error('Error analyzing quality:', error);
        showNotification('AI analysis failed', 'error');
    } finally {
        hideLoading();
    }
}

async function improveFeedback() {
    const feedback = document.getElementById('feedbackText').value;
    if (!feedback.trim()) {
        showNotification('Please enter feedback content first', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const res = await fetch(`${API_BASE}/ai/improve-feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                feedback: feedback,
                type: 'comprehensive',
                rubric_criteria: currentRubric?.criteria,
                student_work: currentSubmission?.content
            })
        });
        
        const result = await res.json();
        
        const content = document.getElementById('aiResultsContent');
        content.innerHTML = `
            <div class="ai-analysis-card">
                <h5>AI Optimized Feedback</h5>
                <div class="improved-feedback">${escapeHtml(result.improved_feedback || 'Unable to generate optimization')}</div>
                <button class="apply-btn" onclick="applyImprovedFeedback('${escapeHtml(result.improved_feedback || '').replace(/'/g, "\\'")}')">
                    <i class="fas fa-check"></i> Apply This Feedback
                </button>
            </div>
        `;
        
        showAIResults();
        
    } catch (error) {
        console.error('Error improving feedback:', error);
        showNotification('AI optimization failed', 'error');
    } finally {
        hideLoading();
    }
}

function applyImprovedFeedback(feedback) {
    document.getElementById('feedbackText').value = feedback;
    hideAIResults();
    showNotification('Applied AI optimized feedback', 'success');
    
    // Log suggestion accepted
    logActivity('suggestion_accepted', { type: 'improved_feedback' });
}

function showAIResults() {
    document.getElementById('aiAnalysisResults').classList.remove('hidden');
}

function hideAIResults() {
    document.getElementById('aiAnalysisResults').classList.add('hidden');
}

// ==================== New AI Features ====================

// Analyze student work structure and content
async function analyzeStudentWork() {
    if (!currentSubmission || !currentSubmission.content) {
        showNotification('No student work to analyze', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const res = await fetch(`${API_BASE}/ai/analyze-work`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: currentSubmission.content,
                submission_id: currentSubmission.id,
                teacher_id: 'T001'
            })
        });
        
        const analysis = await res.json();
        
        const content = document.getElementById('aiResultsContent');
        content.innerHTML = `
            <div class="ai-analysis-card">
                <h5><i class="fas fa-file-alt"></i> Document Structure</h5>
                <div class="structure-grid">
                    <div class="structure-item">
                        <span class="label">Words</span>
                        <span class="value">${analysis.word_count}</span>
                    </div>
                    <div class="structure-item">
                        <span class="label">Sentences</span>
                        <span class="value">${analysis.sentence_count}</span>
                    </div>
                    <div class="structure-item">
                        <span class="label">Paragraphs</span>
                        <span class="value">${analysis.paragraph_count}</span>
                    </div>
                    <div class="structure-item">
                        <span class="label">Lexical Diversity</span>
                        <span class="value">${(analysis.lexical_diversity * 100).toFixed(1)}%</span>
                    </div>
                </div>
            </div>
            <div class="ai-analysis-card">
                <h5><i class="fas fa-sitemap"></i> Structure Analysis</h5>
                <div class="structure-checks">
                    <div class="check-item ${analysis.structure.has_title ? 'pass' : 'fail'}">
                        <i class="fas ${analysis.structure.has_title ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                        Has Title
                    </div>
                    <div class="check-item ${analysis.structure.has_introduction ? 'pass' : 'fail'}">
                        <i class="fas ${analysis.structure.has_introduction ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                        Has Introduction
                    </div>
                    <div class="check-item ${analysis.structure.has_conclusion ? 'pass' : 'fail'}">
                        <i class="fas ${analysis.structure.has_conclusion ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                        Has Conclusion
                    </div>
                </div>
            </div>
            <div class="ai-analysis-card">
                <h5><i class="fas fa-chart-bar"></i> Quality Indicators</h5>
                <div class="quality-indicators">
                    <div class="indicator ${analysis.quality_indicators.length_adequate ? 'good' : 'warning'}">
                        <i class="fas ${analysis.quality_indicators.length_adequate ? 'fa-check' : 'fa-exclamation-triangle'}"></i>
                        ${analysis.quality_indicators.length_adequate ? 'Adequate Length' : 'Too Short'}
                    </div>
                    <div class="indicator ${analysis.quality_indicators.well_structured ? 'good' : 'warning'}">
                        <i class="fas ${analysis.quality_indicators.well_structured ? 'fa-check' : 'fa-exclamation-triangle'}"></i>
                        ${analysis.quality_indicators.well_structured ? 'Well Structured' : 'Needs Better Structure'}
                    </div>
                    <div class="indicator ${analysis.quality_indicators.diverse_vocabulary ? 'good' : 'warning'}">
                        <i class="fas ${analysis.quality_indicators.diverse_vocabulary ? 'fa-check' : 'fa-exclamation-triangle'}"></i>
                        ${analysis.quality_indicators.diverse_vocabulary ? 'Diverse Vocabulary' : 'Limited Vocabulary'}
                    </div>
                </div>
            </div>
            ${analysis.segments && analysis.segments.length > 0 ? `
                <div class="ai-analysis-card">
                    <h5><i class="fas fa-list"></i> Content Segments</h5>
                    <div class="segments-list">
                        ${analysis.segments.slice(0, 5).map(seg => `
                            <div class="segment-item">
                                <span class="segment-type">${seg.type}</span>
                                <span class="segment-words">${seg.word_count} words</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
        
        showAIResults();
        
    } catch (error) {
        console.error('Error analyzing work:', error);
        showNotification('Work analysis failed', 'error');
    } finally {
        hideLoading();
    }
}

// AI suggests rubric scores
async function suggestScores() {
    if (!currentSubmission || !currentRubric) {
        showNotification('Missing submission or rubric', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const res = await fetch(`${API_BASE}/ai/suggest-scores`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_work: currentSubmission.content,
                rubric_criteria: currentRubric.criteria,
                submission_id: currentSubmission.id,
                teacher_id: 'T001'
            })
        });
        
        const result = await res.json();
        
        const content = document.getElementById('aiResultsContent');
        content.innerHTML = `
            <div class="ai-analysis-card">
                <h5><i class="fas fa-star"></i> AI Score Suggestions</h5>
                <p class="disclaimer">These are suggestions only. Please review and adjust based on your professional judgment.</p>
                <div class="score-suggestions">
                    ${result.suggestions ? result.suggestions.map(s => `
                        <div class="suggestion-item">
                            <div class="suggestion-header">
                                <span class="criterion-name">${escapeHtml(s.criterion_name)}</span>
                                <span class="suggested-level">${escapeHtml(s.suggested_level)}</span>
                            </div>
                            <div class="suggestion-rationale">${escapeHtml(s.rationale)}</div>
                            <div class="suggestion-confidence">
                                Confidence: ${(s.confidence * 100).toFixed(0)}%
                            </div>
                            <button class="apply-score-btn" onclick="applyScoreSuggestion('${s.criterion_id}', '${escapeHtml(s.suggested_level)}')">
                                <i class="fas fa-check"></i> Apply
                            </button>
                        </div>
                    `).join('') : '<p>No suggestions available</p>'}
                </div>
            </div>
            ${result.overall_assessment ? `
                <div class="ai-analysis-card">
                    <h5><i class="fas fa-clipboard-check"></i> Overall Assessment</h5>
                    <p>${escapeHtml(result.overall_assessment)}</p>
                </div>
            ` : ''}
            <div class="ai-analysis-card">
                <button class="apply-all-btn" onclick="applyAllScoreSuggestions()">
                    <i class="fas fa-check-double"></i> Apply All Suggestions
                </button>
            </div>
        `;
        
        // Store suggestions for later use
        window.currentScoreSuggestions = result.suggestions;
        
        showAIResults();
        
    } catch (error) {
        console.error('Error getting score suggestions:', error);
        showNotification('Score suggestion failed', 'error');
    } finally {
        hideLoading();
    }
}

// Apply a single score suggestion
function applyScoreSuggestion(criterionId, level) {
    const scoreItem = document.querySelector(`.score-item[data-criterion-id="${criterionId}"]`);
    if (scoreItem) {
        const levelBtn = Array.from(scoreItem.querySelectorAll('.score-level'))
            .find(el => el.textContent.trim() === level);
        if (levelBtn) {
            scoreItem.querySelectorAll('.score-level').forEach(el => el.classList.remove('selected'));
            levelBtn.classList.add('selected');
            showNotification(`Applied ${level} for ${criterionId}`, 'success');
            logActivity('score_suggestion_applied', { criterion: criterionId, level: level });
        }
    }
}

// Apply all score suggestions
function applyAllScoreSuggestions() {
    if (window.currentScoreSuggestions) {
        window.currentScoreSuggestions.forEach(s => {
            applyScoreSuggestion(s.criterion_id, s.suggested_level);
        });
        showNotification('Applied all score suggestions', 'success');
    }
}

// Detailed feedback analysis with coverage details
async function detailedFeedbackAnalysis() {
    const feedback = document.getElementById('feedbackText').value;
    if (!feedback.trim()) {
        showNotification('Please enter feedback content first', 'error');
        return;
    }
    
    if (!currentRubric || !currentSubmission) {
        showNotification('Missing rubric or submission', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const res = await fetch(`${API_BASE}/ai/detailed-analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                feedback: feedback,
                student_work: currentSubmission.content,
                rubric_criteria: currentRubric.criteria,
                submission_id: currentSubmission.id,
                teacher_id: 'T001'
            })
        });
        
        const analysis = await res.json();
        
        const content = document.getElementById('aiResultsContent');
        content.innerHTML = `
            <div class="ai-analysis-card">
                <h5><i class="fas fa-chart-pie"></i> Overall Coverage: ${analysis.overall_coverage}%</h5>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: ${analysis.overall_coverage}%"></div>
                </div>
            </div>
            <div class="ai-analysis-card">
                <h5><i class="fas fa-list-check"></i> Criterion Coverage Details</h5>
                <div class="coverage-details">
                    ${analysis.coverage_details ? analysis.coverage_details.map(c => `
                        <div class="coverage-item ${c.status}">
                            <div class="coverage-header">
                                <span class="criterion-name">${escapeHtml(c.criterion_name)}</span>
                                <span class="coverage-score ${c.coverage_score > 30 ? 'good' : 'low'}">${c.coverage_score}%</span>
                            </div>
                            <div class="matched-keywords">
                                ${c.matched_keywords.length > 0 
                                    ? c.matched_keywords.map(k => `<span class="keyword">${k}</span>`).join('') 
                                    : '<span class="no-match">No keywords matched</span>'}
                            </div>
                            <div class="status-badge ${c.status}">${c.status === 'covered' ? 'Covered' : 'Potentially Missing'}</div>
                        </div>
                    `).join('') : '<p>No coverage data</p>'}
                </div>
            </div>
            <div class="ai-analysis-card">
                <h5><i class="fas fa-microscope"></i> Quality Markers</h5>
                <div class="quality-markers">
                    <div class="marker">
                        <span class="label">Specificity Indicators</span>
                        <span class="value ${analysis.quality_markers.specificity_indicators >= 2 ? 'good' : 'warning'}">${analysis.quality_markers.specificity_indicators}</span>
                    </div>
                    <div class="marker">
                        <span class="label">Feedforward Indicators</span>
                        <span class="value ${analysis.quality_markers.feedforward_indicators >= 1 ? 'good' : 'warning'}">${analysis.quality_markers.feedforward_indicators}</span>
                    </div>
                    <div class="marker">
                        <span class="label">Positive Tone Words</span>
                        <span class="value">${analysis.quality_markers.positive_tone_words}</span>
                    </div>
                    <div class="marker">
                        <span class="label">Balance Ratio</span>
                        <span class="value ${analysis.quality_markers.balance_ratio >= 0.5 ? 'good' : 'warning'}">${(analysis.quality_markers.balance_ratio * 100).toFixed(0)}%</span>
                    </div>
                </div>
            </div>
            ${Object.values(analysis.flags).some(v => v) ? `
                <div class="ai-analysis-card warning">
                    <h5><i class="fas fa-exclamation-triangle"></i> Improvement Flags</h5>
                    <ul class="flags-list">
                        ${analysis.flags.needs_more_specificity ? '<li>Consider adding more specific references to student work</li>' : ''}
                        ${analysis.flags.needs_feedforward ? '<li>Consider adding forward-looking guidance for improvement</li>' : ''}
                        ${analysis.flags.tone_too_negative ? '<li>Consider balancing criticism with positive observations</li>' : ''}
                    </ul>
                </div>
            ` : `
                <div class="ai-analysis-card success">
                    <h5><i class="fas fa-check-circle"></i> Feedback Quality</h5>
                    <p>Your feedback meets quality standards!</p>
                </div>
            `}
        `;
        
        showAIResults();
        
    } catch (error) {
        console.error('Error in detailed analysis:', error);
        showNotification('Detailed analysis failed', 'error');
    } finally {
        hideLoading();
    }
}

// Log activity helper
async function logActivity(type, details) {
    try {
        await fetch(`${API_BASE}/logs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: type,
                user_id: 'T001',
                details: details
            })
        });
    } catch (error) {
        console.error('Error logging activity:', error);
    }
}

// Submit Feedback
async function submitFeedback() {
    const feedback = document.getElementById('feedbackText').value;
    if (!feedback.trim()) {
        showNotification('Please enter feedback content', 'error');
        return;
    }
    
    const scores = getSelectedScores();
    
    // Calculate grading time
    const gradingTime = gradingStartTime ? Math.round((Date.now() - gradingStartTime) / 1000) : 0;
    
    showLoading();
    
    try {
        const res = await fetch(`${API_BASE}/submissions/${currentSubmission.id}/feedback`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                feedback: feedback,
                rubric_scores: scores
            })
        });
        
        if (res.ok) {
            // Log grading completion with time
            logActivity('grading_completed', {
                submission_id: currentSubmission.id,
                student_id: currentSubmission.student_id,
                grading_time: gradingTime
            });
            
            showNotification('Feedback submitted successfully!', 'success');
            gradingStartTime = null;
            setTimeout(() => {
                switchView('submissions');
            }, 1000);
        } else {
            throw new Error('Submit failed');
        }
        
    } catch (error) {
        console.error('Error submitting feedback:', error);
        showNotification('Submission failed, please try again', 'error');
    } finally {
        hideLoading();
    }
}

// Utilities
function getInitials(name) {
    return name ? name.charAt(0).toUpperCase() : '?';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.className = `notification ${type} show`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                 type === 'error' ? 'fa-exclamation-circle' : 
                 'fa-info-circle';
    
    notification.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
    `;

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.classList.remove('show');
            notification.style.animation = '';
        }, 300);
    }, 3000);
}
