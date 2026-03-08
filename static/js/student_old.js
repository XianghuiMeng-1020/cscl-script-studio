// Student Portal JavaScript
const API_BASE = '/api';

// State
let currentStudentId = 'S001';
let studentSubmissions = [];
let currentFeedback = null;
let scoreChart = null;
let feedbackViewStartTime = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadStudentData();
    loadAssignments();
    setupSubmissionForm();
});

// ==================== Engagement Tracking ====================
async function trackEngagement(action, details = {}) {
    if (!currentFeedback) return;
    
    try {
        await fetch(`${API_BASE}/engagement/track`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_id: currentStudentId,
                submission_id: currentFeedback.id,
                action: action,
                details: details
            })
        });
    } catch (error) {
        console.error('Error tracking engagement:', error);
    }
}

// Load Student Data
async function loadStudentData() {
    currentStudentId = document.getElementById('studentSelect').value;
    
    try {
        // Get users to find student name
        const usersRes = await fetch(`${API_BASE}/users`);
        const users = await usersRes.json();
        const student = users.students?.find(s => s.id === currentStudentId);
        
        if (student) {
            document.getElementById('studentName').textContent = student.name;
        }
        
        // Get student submissions
        const statsRes = await fetch(`${API_BASE}/stats/student/${currentStudentId}`);
        const stats = await statsRes.json();
        
        studentSubmissions = stats.submissions || [];
        
        // Update stats
        document.getElementById('totalSubmissions').textContent = stats.total_submissions;
        document.getElementById('gradedCount').textContent = stats.graded;
        document.getElementById('pendingCount').textContent = stats.pending;
        
        // Render feedback cards
        renderFeedbackCards();
        
    } catch (error) {
        console.error('Error loading student data:', error);
        showNotification('Failed to load data', 'error');
    }
}

// Render Feedback Cards
function renderFeedbackCards() {
    const container = document.getElementById('feedbackCards');
    
    if (studentSubmissions.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <i class="fas fa-inbox"></i>
                <h4>No Submissions</h4>
                <p>You have not submitted any assignments yet</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = studentSubmissions.map(sub => {
        const date = new Date(sub.submitted_at);
        const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const isGraded = sub.status === 'graded';
        const totalScore = sub.rubric_scores?.total || 0;
        
        return `
            <div class="feedback-card ${isGraded ? '' : 'pending'}" onclick="${isGraded ? `openFeedbackModal('${sub.id}')` : ''}">
                <div class="feedback-card-header">
                    <div class="assignment-info">
                        <h4>Assignment Submission</h4>
                        <p>Submitted on ${dateStr}</p>
                    </div>
                    <span class="status-badge ${sub.status}">${isGraded ? 'Graded' : 'Pending'}</span>
                </div>
                <div class="feedback-card-content">
                    ${isGraded ? `
                        <div class="score-preview">
                            <div class="score-circle">${totalScore}</div>
                            <div class="score-details">
                                <h5>Overall Score</h5>
                                <p>${getScoreDescription(totalScore)}</p>
                            </div>
                        </div>
                    ` : `
                        <div class="pending-message">
                            <i class="fas fa-hourglass-half"></i>
                            <p>Your instructor is reviewing your work...</p>
                        </div>
                    `}
                </div>
                <div class="feedback-card-footer">
                    <span class="submission-date"><i class="fas fa-calendar"></i> ${dateStr}</span>
                    <button class="view-feedback-btn" ${isGraded ? `onclick="event.stopPropagation(); openFeedbackModal('${sub.id}')"` : 'disabled'}>
                        ${isGraded ? '<i class="fas fa-eye"></i> View Feedback' : '<i class="fas fa-clock"></i> Waiting'}
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function getScoreDescription(score) {
    if (score >= 90) return 'Excellent! Keep it up';
    if (score >= 80) return 'Good, room for improvement';
    if (score >= 70) return 'Fair, needs strengthening';
    if (score >= 60) return 'Passing, needs more effort';
    return 'Needs improvement';
}

// Open Feedback Modal
async function openFeedbackModal(submissionId) {
    try {
        const res = await fetch(`${API_BASE}/submissions/${submissionId}`);
        currentFeedback = await res.json();
        
        if (!currentFeedback.feedback) {
            showNotification('This assignment has not been graded yet', 'error');
            return;
        }
        
        // Start tracking view time
        feedbackViewStartTime = Date.now();
        
        // Track feedback view
        trackEngagement('view_feedback');
        
        // Update modal title
        document.getElementById('modalTitle').textContent = 'Assignment Feedback Details';
        
        // Render visual summary
        renderVisualSummary();
        
        // Track visual summary view
        trackEngagement('view_visual_summary');
        
        // Render rubric scores
        renderRubricScores();
        
        // Render written feedback
        document.getElementById('writtenFeedback').textContent = currentFeedback.feedback;
        
        // Render video script
        document.getElementById('videoScript').textContent = currentFeedback.video_script || 'No video script available';
        
        // Render encouragement
        const encouragement = currentFeedback.visual_summary?.encouragement || 'Keep up the great work!';
        document.getElementById('encouragementText').textContent = encouragement;
        
        // Show modal
        document.getElementById('feedbackModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading feedback:', error);
        showNotification('Failed to load feedback', 'error');
    }
}

// Render Visual Summary
function renderVisualSummary() {
    const summary = currentFeedback.visual_summary || {};
    
    // Strengths
    const strengthsList = document.getElementById('strengthsList');
    const strengths = summary.strengths || ['Good performance'];
    strengthsList.innerHTML = strengths.map(s => `<li>${escapeHtml(s)}</li>`).join('');
    
    // Improvements
    const improvementsList = document.getElementById('improvementsList');
    const improvements = summary.improvements || ['Keep improving'];
    improvementsList.innerHTML = improvements.map(i => `<li>${escapeHtml(i)}</li>`).join('');
    
    // Overall comment
    const overallComment = summary.overall_comment || 'Overall good performance, keep it up!';
    document.getElementById('overallComment').textContent = overallComment;
    
    // Render chart
    renderScoreChart();
}

// Render Score Chart
function renderScoreChart() {
    const ctx = document.getElementById('scoreChart').getContext('2d');
    const scores = currentFeedback.rubric_scores || {};
    
    // Destroy existing chart
    if (scoreChart) {
        scoreChart.destroy();
    }
    
    // Prepare data
    const labels = [];
    const data = [];
    const backgroundColors = [];
    
    // Map score levels to numeric values
    const levelMap = {
        '优秀': 100,
        '良好': 75,
        '一般': 50,
        '需改进': 25
    };
    
    const colorMap = {
        '优秀': '#22c55e',
        '良好': '#0d9488',
        '一般': '#eab308',
        '需改进': '#ef4444'
    };
    
    Object.entries(scores).forEach(([key, value]) => {
        if (key !== 'total' && typeof value === 'string') {
            labels.push(key);
            data.push(levelMap[value] || 50);
            backgroundColors.push(colorMap[value] || '#64748b');
        }
    });
    
    // If no detailed scores, show total
    if (labels.length === 0) {
        labels.push('综合评分');
        data.push(scores.total || 0);
        backgroundColors.push('#0d9488');
    }
    
    scoreChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: '评分',
                data: data,
                backgroundColor: 'rgba(13, 148, 136, 0.2)',
                borderColor: '#0d9488',
                borderWidth: 2,
                pointBackgroundColor: '#0d9488',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#0d9488'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 25,
                        display: false
                    },
                    grid: {
                        color: '#e2e8f0'
                    },
                    angleLines: {
                        color: '#e2e8f0'
                    },
                    pointLabels: {
                        font: {
                            size: 11
                        },
                        color: '#64748b'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Render Rubric Scores
function renderRubricScores() {
    const container = document.getElementById('rubricScoresDisplay');
    const scores = currentFeedback.rubric_scores || {};
    
    const levelMap = {
        'Excellent': { width: 100, class: 'excellent' },
        'Good': { width: 75, class: 'good' },
        'Fair': { width: 50, class: 'fair' },
        'Needs Improvement': { width: 25, class: 'poor' }
    };
    
    const criteriaNames = {
        'C1': 'Argument Clarity',
        'C2': 'Evidence Support',
        'C3': 'Organization',
        'C4': 'Language Expression'
    };
    
    let html = '';
    
    Object.entries(scores).forEach(([key, value]) => {
        if (key !== 'total' && typeof value === 'string') {
            const levelInfo = levelMap[value] || { width: 50, class: 'fair' };
            const displayName = criteriaNames[key] || key;
            
            html += `
                <div class="rubric-score-item">
                    <h5>${escapeHtml(displayName)}</h5>
                    <div class="score-bar">
                        <div class="score-bar-fill ${levelInfo.class}" style="width: ${levelInfo.width}%"></div>
                    </div>
                    <span class="level ${levelInfo.class}">${escapeHtml(value)}</span>
                </div>
            `;
        }
    });
    
    // Add total score
    if (scores.total !== undefined) {
        const totalClass = scores.total >= 80 ? 'excellent' : scores.total >= 60 ? 'good' : scores.total >= 40 ? 'fair' : 'poor';
        html += `
            <div class="rubric-score-item" style="background: linear-gradient(135deg, #f0fdfa 0%, #ecfeff 100%);">
                <h5>Overall Score</h5>
                <div class="score-bar">
                    <div class="score-bar-fill ${totalClass}" style="width: ${scores.total}%"></div>
                </div>
                <span class="level ${totalClass}" style="font-size: 1.25rem;">${scores.total} pts</span>
            </div>
        `;
    }
    
    container.innerHTML = html || '<p style="color: var(--text-secondary);">No detailed scores available</p>';
}

// Close Modal
function closeModal() {
    // Track time spent viewing feedback
    if (feedbackViewStartTime && currentFeedback) {
        const timeSpent = Math.round((Date.now() - feedbackViewStartTime) / 1000);
        trackEngagement('time_spent', { seconds: timeSpent });
        feedbackViewStartTime = null;
    }
    
    document.getElementById('feedbackModal').classList.remove('show');
    currentFeedback = null;
}

// Copy Script
function copyScript() {
    const script = document.getElementById('videoScript').textContent;
    
    // Track video script view
    trackEngagement('view_video_script');
    
    navigator.clipboard.writeText(script).then(() => {
        showNotification('Script copied to clipboard', 'success');
    }).catch(() => {
        showNotification('Copy failed', 'error');
    });
}

// Utilities
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Load Assignments for submission dropdown
async function loadAssignments() {
    try {
        const res = await fetch(`${API_BASE}/assignments`);
        const assignments = await res.json();
        
        const select = document.getElementById('assignmentSelect');
        select.innerHTML = '<option value="">-- Select an assignment --</option>';
        
        assignments.forEach(assignment => {
            const option = document.createElement('option');
            option.value = assignment.id;
            option.textContent = assignment.title;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading assignments:', error);
    }
}

// Setup Submission Form
function setupSubmissionForm() {
    const form = document.getElementById('submissionForm');
    const textarea = document.getElementById('submissionContent');
    const charCount = document.getElementById('charCount');
    
    // Character count
    textarea.addEventListener('input', function() {
        charCount.textContent = this.value.length;
    });
    
    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const assignmentId = document.getElementById('assignmentSelect').value;
        const content = textarea.value.trim();
        
        if (!assignmentId) {
            showNotification('Please select an assignment', 'error');
            return;
        }
        
        if (!content) {
            showNotification('Please enter your work content', 'error');
            return;
        }
        
        // Get current student info
        const usersRes = await fetch(`${API_BASE}/users`);
        const users = await usersRes.json();
        const student = users.students?.find(s => s.id === currentStudentId);
        
        try {
            const res = await fetch(`${API_BASE}/submissions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    assignment_id: assignmentId,
                    student_id: currentStudentId,
                    student_name: student?.name || 'Student',
                    content: content
                })
            });
            
            if (res.ok) {
                showNotification('Assignment submitted successfully!', 'success');
                form.reset();
                charCount.textContent = '0';
                loadStudentData(); // Refresh the submissions list
            } else {
                throw new Error('Submission failed');
            }
        } catch (error) {
            console.error('Error submitting:', error);
            showNotification('Submission failed, please try again', 'error');
        }
    });
}
