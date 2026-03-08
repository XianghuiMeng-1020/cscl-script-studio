const API_BASE_URL = '/api'; // Use relative URL

let allFeedbacks = [];
let currentFeedback = null;

document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadFeedbacks();

    document.getElementById('refreshBtn').addEventListener('click', function() {
        this.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
        loadStats();
        loadFeedbacks();
        setTimeout(() => {
            this.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
        }, 1000);
    });

    document.getElementById('statusFilter').addEventListener('change', filterFeedbacks);
    document.getElementById('categoryFilter').addEventListener('change', filterFeedbacks);
    document.getElementById('searchInput').addEventListener('input', filterFeedbacks);

    document.getElementById('deleteBtn').addEventListener('click', deleteFeedback);
});

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const stats = await response.json();

        document.getElementById('totalCount').textContent = stats.total;
        document.getElementById('pendingCount').textContent = stats.pending;
        document.getElementById('progressCount').textContent = stats.in_progress;
        document.getElementById('resolvedCount').textContent = stats.resolved;
    } catch (error) {
        console.error('Error loading stats:', error);
        showNotification('Failed to load statistics', 'error');
    }
}

async function loadFeedbacks() {
    const feedbacksList = document.getElementById('feedbacksList');
    feedbacksList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading feedbacks...</p></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/feedbacks`);
        allFeedbacks = await response.json();
        
        displayFeedbacks(allFeedbacks);
    } catch (error) {
        console.error('Error loading feedbacks:', error);
        feedbacksList.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h4>Failed to load feedbacks</h4><p>Please try again later</p></div>';
    }
}

function displayFeedbacks(feedbacks) {
    const feedbacksList = document.getElementById('feedbacksList');

    if (feedbacks.length === 0) {
        feedbacksList.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><h4>No feedbacks found</h4><p>No feedback submissions match your criteria</p></div>';
        return;
    }

    feedbacksList.innerHTML = feedbacks.map(feedback => `
        <div class="feedback-item" onclick="viewFeedback(${feedback.id})">
            <div class="feedback-header">
                <div class="feedback-user">
                    <div class="user-avatar">${getInitials(feedback.name)}</div>
                    <div class="user-info">
                        <h4>${escapeHtml(feedback.name)}</h4>
                        <p>${escapeHtml(feedback.email)}</p>
                    </div>
                </div>
                <div class="feedback-meta">
                    <span class="badge status-${feedback.status.toLowerCase().replace(' ', '-')}">
                        <i class="fas fa-circle"></i>
                        ${feedback.status}
                    </span>
                    <span class="badge priority-${feedback.priority.toLowerCase()}">
                        <i class="fas fa-flag"></i>
                        ${feedback.priority}
                    </span>
                    <span class="badge category">
                        <i class="fas fa-tag"></i>
                        ${feedback.category}
                    </span>
                </div>
            </div>
            <div class="feedback-content">
                <p class="feedback-message">${escapeHtml(truncateText(feedback.message, 150))}</p>
            </div>
            <div class="feedback-footer">
                <span class="feedback-time">
                    <i class="fas fa-clock"></i>
                    ${formatDate(feedback.timestamp)}
                </span>
                <div class="feedback-actions">
                    <button class="action-btn btn-view" onclick="event.stopPropagation(); viewFeedback(${feedback.id})">
                        <i class="fas fa-eye"></i>
                        View Details
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function filterFeedbacks() {
    const statusFilter = document.getElementById('statusFilter').value;
    const categoryFilter = document.getElementById('categoryFilter').value;
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();

    let filtered = allFeedbacks;

    if (statusFilter) {
        filtered = filtered.filter(f => f.status === statusFilter);
    }

    if (categoryFilter) {
        filtered = filtered.filter(f => f.category === categoryFilter);
    }

    if (searchTerm) {
        filtered = filtered.filter(f => 
            f.name.toLowerCase().includes(searchTerm) ||
            f.email.toLowerCase().includes(searchTerm) ||
            f.message.toLowerCase().includes(searchTerm)
        );
    }

    displayFeedbacks(filtered);
}

async function viewFeedback(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/feedback/${id}`);
        currentFeedback = await response.json();

        const modalBody = document.getElementById('modalBody');
        
        // Build sentiment display
        let sentimentHTML = '';
        if (currentFeedback.sentiment) {
            const sentiment = currentFeedback.sentiment;
            sentimentHTML = `
                <div class="detail-group">
                    <label><i class="fas fa-brain"></i> AI Analysis</label>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">
                        <span class="badge" style="background: #e0e7ff; color: #3730a3;">
                            Sentiment: ${sentiment.sentiment || 'N/A'}
                        </span>
                        <span class="badge" style="background: #fef3c7; color: #92400e;">
                            Emotion: ${sentiment.emotion || 'N/A'}
                        </span>
                        <span class="badge" style="background: #fee2e2; color: #991b1b;">
                            Urgency: ${sentiment.urgency || 'N/A'}
                        </span>
                    </div>
                </div>
            `;
        }
        
        // Build summary display
        let summaryHTML = '';
        if (currentFeedback.summary && currentFeedback.summary !== currentFeedback.message) {
            summaryHTML = `
                <div class="detail-group">
                    <label><i class="fas fa-file-alt"></i> AI Summary</label>
                    <p style="font-style: italic; color: #6b7280;">${escapeHtml(currentFeedback.summary)}</p>
                </div>
            `;
        }
        
        modalBody.innerHTML = `
            <div class="detail-group">
                <label><i class="fas fa-user"></i> Name</label>
                <p>${escapeHtml(currentFeedback.name)}</p>
            </div>
            <div class="detail-group">
                <label><i class="fas fa-envelope"></i> Email</label>
                <p>${escapeHtml(currentFeedback.email)}</p>
            </div>
            <div class="detail-group">
                <label><i class="fas fa-tag"></i> Category</label>
                <p>${escapeHtml(currentFeedback.category)}${currentFeedback.ai_enhanced ? ' <span class="badge" style="background: #10b981; color: white;"><i class="fas fa-robot"></i> AI</span>' : ''}</p>
            </div>
            <div class="detail-group">
                <label><i class="fas fa-flag"></i> Priority</label>
                <p>${escapeHtml(currentFeedback.priority)}${currentFeedback.ai_enhanced ? ' <span class="badge" style="background: #10b981; color: white;"><i class="fas fa-robot"></i> AI</span>' : ''}</p>
            </div>
            ${sentimentHTML}
            <div class="detail-group">
                <label><i class="fas fa-circle"></i> Status</label>
                <select id="statusSelect" class="form-control">
                    <option value="Pending" ${currentFeedback.status === 'Pending' ? 'selected' : ''}>Pending</option>
                    <option value="In Progress" ${currentFeedback.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                    <option value="Resolved" ${currentFeedback.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                    <option value="Closed" ${currentFeedback.status === 'Closed' ? 'selected' : ''}>Closed</option>
                </select>
            </div>
            <div class="detail-group">
                <label><i class="fas fa-clock"></i> Submitted</label>
                <p>${formatDate(currentFeedback.timestamp)}</p>
            </div>
            ${summaryHTML}
            <div class="detail-group">
                <label><i class="fas fa-comment-dots"></i> Message</label>
                <p>${escapeHtml(currentFeedback.message)}</p>
            </div>
            <div class="detail-group">
                <label><i class="fas fa-reply"></i> Admin Response</label>
                <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <button class="btn-primary" onclick="generateAIResponse()" style="font-size: 0.9rem; padding: 0.5rem 1rem;">
                        <i class="fas fa-magic"></i> Generate AI Response
                    </button>
                </div>
                <textarea id="responseText" rows="4" placeholder="Enter your response here...">${currentFeedback.response || ''}</textarea>
            </div>
            <div style="margin-top: 1rem;">
                <button class="btn-primary" onclick="updateFeedback()">
                    <i class="fas fa-save"></i> Save Changes
                </button>
            </div>
        `;

        document.getElementById('feedbackModal').classList.add('show');
    } catch (error) {
        console.error('Error loading feedback:', error);
        showNotification('Failed to load feedback details', 'error');
    }
}

async function generateAIResponse() {
    if (!currentFeedback) return;
    
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    btn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/feedback/${currentFeedback.id}/ai-response`);
        const data = await response.json();
        
        if (response.ok && data.suggested_response) {
            document.getElementById('responseText').value = data.suggested_response;
            showNotification('AI response generated successfully!', 'success');
        } else {
            showNotification('Failed to generate AI response', 'error');
        }
    } catch (error) {
        console.error('Error generating AI response:', error);
        showNotification('Network error. Please try again.', 'error');
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

async function updateFeedback() {
    const status = document.getElementById('statusSelect').value;
    const response = document.getElementById('responseText').value;

    try {
        const res = await fetch(`${API_BASE_URL}/feedback/${currentFeedback.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status, response })
        });

        if (res.ok) {
            showNotification('Feedback updated successfully', 'success');
            closeModal();
            loadStats();
            loadFeedbacks();
        } else {
            showNotification('Failed to update feedback', 'error');
        }
    } catch (error) {
        console.error('Error updating feedback:', error);
        showNotification('Network error. Please try again.', 'error');
    }
}

async function deleteFeedback() {
    if (!currentFeedback) return;

    if (!confirm('Are you sure you want to delete this feedback? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/feedback/${currentFeedback.id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Feedback deleted successfully', 'success');
            closeModal();
            loadStats();
            loadFeedbacks();
        } else {
            showNotification('Failed to delete feedback', 'error');
        }
    } catch (error) {
        console.error('Error deleting feedback:', error);
        showNotification('Network error. Please try again.', 'error');
    }
}

function closeModal() {
    document.getElementById('feedbackModal').classList.remove('show');
    currentFeedback = null;
}

function getInitials(name) {
    return name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2);
}

function formatDate(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        if (hours === 0) {
            const minutes = Math.floor(diff / (1000 * 60));
            return minutes === 0 ? 'Just now' : `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        }
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (days === 1) {
        return 'Yesterday';
    } else if (days < 7) {
        return `${days} days ago`;
    } else {
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function escapeHtml(text) {
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
    }, 4000);
}

document.getElementById('feedbackModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});
