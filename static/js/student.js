// CSCL Student - join by share code, scenes, chat, submit
(function() {
    'use strict';
})();

const STUDENT_API = '/api/student';

let shareCode = '';
let activityData = null;
let myRoleLabel = '';
let currentSceneIndex = 0;
let progressSubmissions = [];
let chatPollTimer = null;
let currentUserId = null;

function tr(key, fallback) {
    return (typeof t === 'function' ? t(key) : null) || fallback || key;
}

document.addEventListener('DOMContentLoaded', function() {
    var params = new URLSearchParams(window.location.search);
    shareCode = (params.get('code') || '').trim().toUpperCase();
    var joinBlock = document.getElementById('studentJoinBlock');
    var activityBlock = document.getElementById('studentActivityBlock');
    var codeInput = document.getElementById('shareCodeInput');
    if (codeInput) codeInput.value = shareCode;

    var joinBtn = document.getElementById('joinActivityBtn');
    if (joinBtn) joinBtn.addEventListener('click', onJoinClick);

    var saveDraftBtn = document.getElementById('saveDraftBtn');
    var submitSceneBtn = document.getElementById('submitSceneBtn');
    if (saveDraftBtn) saveDraftBtn.addEventListener('click', onSaveDraft);
    if (submitSceneBtn) submitSceneBtn.addEventListener('click', onSubmitScene);

    var scenePrev = document.getElementById('scenePrevBtn');
    var sceneNext = document.getElementById('sceneNextBtn');
    if (scenePrev) scenePrev.addEventListener('click', function() { setSceneIndex(Math.max(0, currentSceneIndex - 1)); });
    if (sceneNext) sceneNext.addEventListener('click', function() {
        var scenes = activityData && activityData.scenes ? activityData.scenes : [];
        setSceneIndex(Math.min(currentSceneIndex + 1, Math.max(0, scenes.length - 1)));
    });

    var chatSend = document.getElementById('chatSendBtn');
    var chatInput = document.getElementById('chatInput');
    if (chatSend) chatSend.addEventListener('click', onChatSend);
    if (chatInput) chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onChatSend(); }
    });

    fetch('/api/auth/me', { credentials: 'include' })
        .then(function(r) { return r.ok ? r.json() : null; })
        .then(function(d) { if (d && d.id) currentUserId = d.id; })
        .catch(function() {});

    if (shareCode) {
        tryJoinAndLoad();
    } else {
        if (joinBlock) joinBlock.classList.remove('hidden');
        if (activityBlock) activityBlock.classList.add('hidden');
    }

    document.addEventListener('localeChange', function() {
        if (activityData) renderActivity();
        var chatIn = document.getElementById('chatInput');
        if (chatIn) chatIn.placeholder = tr('student.chat.placeholder', 'Type a message...');
    });
    var chatIn = document.getElementById('chatInput');
    if (chatIn) chatIn.placeholder = tr('student.chat.placeholder', 'Type a message...');
});

function showJoinError(msg) {
    var el = document.getElementById('joinError');
    if (el) { el.textContent = msg || ''; el.classList.toggle('hidden', !msg); }
}

async function tryJoinAndLoad() {
    if (!shareCode) return;
    showJoinError('');
    try {
        var joinRes = await fetch(STUDENT_API + '/activity/' + encodeURIComponent(shareCode) + '/join', {
            method: 'POST',
            credentials: 'include'
        });
        if (joinRes.status === 401) {
            showJoinError(tr('student.error.login', 'Please log in first.'));
            return;
        }
        if (!joinRes.ok) {
            var d = await joinRes.json().catch(function() { return {}; });
            showJoinError(d.error || tr('student.error.join_failed', 'Join failed.'));
            return;
        }
        var joinData = await joinRes.json();
        myRoleLabel = (joinData.role_label || '').trim();
        await loadActivity();
    } catch (e) {
        console.error('tryJoinAndLoad', e);
        showJoinError(tr('common.error.network', 'Network error.'));
    }
}

async function onJoinClick() {
    var codeInput = document.getElementById('shareCodeInput');
    shareCode = (codeInput && codeInput.value || '').trim().toUpperCase();
    if (!shareCode) {
        showJoinError(tr('student.activity.enter_code', 'Enter invite code.'));
        return;
    }
    if (window.history && window.history.replaceState) {
        var url = new URL(window.location.href);
        url.searchParams.set('code', shareCode);
        window.history.replaceState({}, '', url.toString());
    }
    await tryJoinAndLoad();
}

async function loadActivity() {
    if (!shareCode) return;
    try {
        var res = await fetch(STUDENT_API + '/activity/' + encodeURIComponent(shareCode), { credentials: 'include' });
        if (res.status === 401) {
            showJoinError(tr('student.error.login', 'Please log in first.'));
            return;
        }
        if (res.status === 404) {
            showJoinError(tr('student.error.not_found', 'Activity not found or not published.'));
            return;
        }
        if (!res.ok) throw new Error('HTTP ' + res.status);
        activityData = await res.json();
        var progressRes = await fetch(STUDENT_API + '/activity/' + encodeURIComponent(shareCode) + '/progress', { credentials: 'include' });
        if (progressRes.ok) {
            var prog = await progressRes.json();
            progressSubmissions = prog.submissions || [];
        } else {
            progressSubmissions = [];
        }
        currentSceneIndex = 0;
        showActivityPanel();
        renderActivity();
        startChatPolling();
    } catch (e) {
        console.error('loadActivity', e);
        showJoinError(tr('common.error.network', 'Network error.'));
    }
}

function showActivityPanel() {
    var joinBlock = document.getElementById('studentJoinBlock');
    var activityBlock = document.getElementById('studentActivityBlock');
    var chatInputArea = document.getElementById('chatInputArea');
    var chatEmpty = document.getElementById('chatEmpty');
    if (joinBlock) joinBlock.classList.add('hidden');
    if (activityBlock) activityBlock.classList.remove('hidden');
    if (chatInputArea) chatInputArea.classList.remove('hidden');
    if (chatEmpty) chatEmpty.classList.add('hidden');
}

function setSceneIndex(idx) {
    var scenes = activityData && activityData.scenes ? activityData.scenes : [];
    if (idx < 0 || idx >= scenes.length) return;
    currentSceneIndex = idx;
    renderActivity();
}

function renderActivity() {
    if (!activityData) return;
    var scenes = activityData.scenes || [];
    var scene = scenes[currentSceneIndex] || null;
    var prevBtn = document.getElementById('scenePrevBtn');
    var nextBtn = document.getElementById('sceneNextBtn');
    if (prevBtn) prevBtn.disabled = currentSceneIndex <= 0;
    if (nextBtn) nextBtn.disabled = currentSceneIndex >= scenes.length - 1;

    var titleEl = document.getElementById('activityTitle');
    var metaEl = document.getElementById('activityMeta');
    var progressEl = document.getElementById('sceneProgressText');
    if (titleEl) titleEl.textContent = activityData.title || tr('student.activity.untitled', 'Untitled');
    if (metaEl) metaEl.textContent = (activityData.topic || '') + (activityData.duration_minutes ? ' · ' + activityData.duration_minutes + ' min' : '');
    if (progressEl) progressEl.textContent = scenes.length ? (currentSceneIndex + 1) + '/' + scenes.length : '1/1';

    var purposeEl = document.getElementById('scenePurpose');
    var roleEl = document.getElementById('myRoleText');
    var taskEl = document.getElementById('sceneTaskContent');
    var textarea = document.getElementById('submissionTextarea');
    if (!scene) {
        if (purposeEl) purposeEl.textContent = '--';
        if (roleEl) roleEl.textContent = '--';
        if (taskEl) taskEl.textContent = '--';
        if (textarea) textarea.value = '';
        return;
    }
    if (purposeEl) purposeEl.textContent = scene.purpose || '--';
    var myRole = (activityData.myRoleLabel || '').trim() || (typeof activityData.role_label !== 'undefined' ? activityData.role_label : '');
    if (roleEl) roleEl.textContent = myRoleLabel || myRole || '--';
    var scriptlets = scene.scriptlets || [];
    var taskHtml = scriptlets.length
        ? scriptlets.map(function(s) { return '<p>' + escapeHtml(s.prompt_text || '') + '</p>'; }).join('')
        : '<p>' + escapeHtml(scene.purpose || '') + '</p>';
    if (taskEl) taskEl.innerHTML = taskHtml;

    var sub = progressSubmissions.find(function(s) { return s.scene_id === scene.id; });
    if (textarea) textarea.value = (sub && sub.content) || '';
}

function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function onSaveDraft() {
    saveSubmission('pending');
}

function onSubmitScene() {
    saveSubmission('submitted');
}

function saveSubmission(status) {
    if (!shareCode || !activityData) return;
    var scenes = activityData.scenes || [];
    var scene = scenes[currentSceneIndex];
    if (!scene) return;
    var textarea = document.getElementById('submissionTextarea');
    var content = textarea ? textarea.value : '';
    fetch(STUDENT_API + '/activity/' + encodeURIComponent(shareCode) + '/scenes/' + encodeURIComponent(scene.id) + '/submit', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content, status: status })
    })
        .then(function(r) { return r.json().then(function(d) { return { ok: r.ok, data: d }; }); })
        .then(function(result) {
            if (result.ok) {
                var idx = progressSubmissions.findIndex(function(s) { return s.scene_id === scene.id; });
                var sub = result.data;
                if (idx >= 0) progressSubmissions[idx] = sub;
                else progressSubmissions.push(sub);
                showNotification(status === 'submitted' ? tr('student.submission.submitted', 'Submitted.') : tr('student.submission.saved', 'Draft saved.'), 'success');
            } else {
                showNotification(result.data.error || tr('common.error.unknown', 'Error.'), 'error');
            }
        })
        .catch(function(e) {
            console.error('saveSubmission', e);
            showNotification(tr('common.error.network', 'Network error.'), 'error');
        });
}

function startChatPolling() {
    if (chatPollTimer) clearInterval(chatPollTimer);
    chatPollTimer = setInterval(pollChat, 3000);
    pollChat();
}

function pollChat() {
    if (!shareCode) return;
    fetch(STUDENT_API + '/activity/' + encodeURIComponent(shareCode) + '/messages?limit=50', { credentials: 'include' })
        .then(function(r) { return r.ok ? r.json() : Promise.reject(); })
        .then(function(d) {
            var list = d.messages || [];
            renderChat(list);
        })
        .catch(function() {});
}

function renderChat(messages) {
    var container = document.getElementById('chatMessages');
    if (!container) return;
    var empty = document.getElementById('chatEmpty');
    if (empty) empty.classList.toggle('hidden', (messages && messages.length) > 0);
    var existing = container.querySelectorAll('.chat-message');
    for (var i = 0; i < existing.length; i++) existing[i].remove();
    var me = currentUserId || '';
    messages.forEach(function(m) {
        var div = document.createElement('div');
        div.className = 'chat-message ' + (m.user_id === me ? 'own' : 'other');
        var meta = document.createElement('div');
        meta.className = 'chat-msg-meta';
        meta.textContent = (m.user_id ? m.user_id.substring(0, 8) : '') + ' · ' + (m.created_at ? new Date(m.created_at).toLocaleTimeString() : '');
        div.appendChild(document.createTextNode(m.content || ''));
        div.appendChild(meta);
        container.appendChild(div);
    });
}

function onChatSend() {
    var input = document.getElementById('chatInput');
    if (!input || !shareCode) return;
    var content = (input.value || '').trim();
    if (!content) return;
    fetch(STUDENT_API + '/activity/' + encodeURIComponent(shareCode) + '/messages', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content })
    })
        .then(function(r) {
            if (r.ok) { input.value = ''; pollChat(); }
            else return r.json().then(function(d) { showNotification(d.error || 'Send failed', 'error'); });
        })
        .catch(function(e) { showNotification(tr('common.error.network', 'Network error.'), 'error'); });
}

function showNotification(message, type) {
    var el = document.getElementById('notification');
    if (el) {
        el.textContent = message;
        el.className = 'notification ' + (type || 'info');
        setTimeout(function() { el.className = 'notification'; }, 3000);
    }
}
