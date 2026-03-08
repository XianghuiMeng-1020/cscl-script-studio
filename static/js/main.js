const API_BASE_URL = '/api'; // Use relative URL

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('feedbackForm');
    const messageTextarea = document.getElementById('message');
    const charCount = document.querySelector('.char-count');

    if (messageTextarea && charCount) {
        messageTextarea.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = `${length} / 1000 characters`;
            
            if (length > 1000) {
                charCount.style.color = 'var(--danger-color)';
            } else if (length > 800) {
                charCount.style.color = 'var(--warning-color)';
            } else {
                charCount.style.color = 'var(--text-secondary)';
            }
        });
    }

    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                name: document.getElementById('name').value.trim(),
                email: document.getElementById('email').value.trim(),
                category: document.getElementById('category').value,
                priority: document.getElementById('priority').value,
                message: document.getElementById('message').value.trim()
            };

            if (formData.message.length > 1000) {
                showNotification('Message is too long. Maximum 1000 characters allowed.', 'error');
                return;
            }

            const submitBtn = form.querySelector('.submit-btn');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
            submitBtn.disabled = true;

            try {
                const response = await fetch(`${API_BASE_URL}/feedback`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (response.ok) {
                    showNotification('Thank you! Your feedback has been submitted successfully.', 'success');
                    form.reset();
                    if (charCount) {
                        charCount.textContent = '0 / 1000 characters';
                        charCount.style.color = 'var(--text-secondary)';
                    }
                } else {
                    showNotification(data.error || 'Failed to submit feedback. Please try again.', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('Network error. Please check your connection and try again.', 'error');
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});

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

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

document.querySelectorAll('input[type="email"]').forEach(input => {
    input.addEventListener('blur', function() {
        if (this.value && !validateEmail(this.value)) {
            this.style.borderColor = 'var(--danger-color)';
            showNotification('Please enter a valid email address', 'error');
        } else {
            this.style.borderColor = 'var(--border-color)';
        }
    });
});
