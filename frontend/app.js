document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
        if (tab.dataset.tab === 'dashboard') loadDashboard();
    });
});

// shared resume state
let _resumeFile = null, _resumeText = '';

const _fileAnalyze = document.getElementById('file-analyze');
const _textAnalyze = document.getElementById('resume-text-analyze');
const _dropZone = document.getElementById('drop-zone');
const _dropLabel = document.getElementById('drop-zone-label');

function _setDropFile(file) {
    _resumeFile = file;
    _resumeText = '';
    _textAnalyze.value = '';
    _dropZone.classList.add('has-file');
    _dropLabel.innerHTML = `<strong>${file.name}</strong> &mdash; click to change`;
    _clearMatchCache();
}

_fileAnalyze.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) _setDropFile(file);
});

_dropZone.addEventListener('dragover', e => { e.preventDefault(); _dropZone.classList.add('drag-over'); });
_dropZone.addEventListener('dragleave', () => _dropZone.classList.remove('drag-over'));
_dropZone.addEventListener('drop', e => {
    e.preventDefault();
    _dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) _setDropFile(file);
});

_textAnalyze.addEventListener('input', e => {
    _resumeText = e.target.value;
    _resumeFile = null;
    document.getElementById('file-name-analyze').textContent = '';
    _clearMatchCache();
});

function _clearMatchCache() {
    Object.keys(localStorage)
        .filter(k => k.startsWith('jb_cache_'))
        .forEach(k => localStorage.removeItem(k));
}

function toast(msg, type = 'info') {
    const el = document.createElement('div');
    el.className = 'toast toast-' + type;
    el.textContent = msg;
    document.getElementById('toast-container').appendChild(el);
    setTimeout(() => el.remove(), 3000);
}

function setLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    if (loading) { btn.classList.add('loading'); btn.disabled = true; }
    else { btn.classList.remove('loading'); btn.disabled = false; }
}

async function apiPost(url, formData) {
    const res = await fetch(url, { method: 'POST', body: formData });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Request failed'); }
    return res.json();
}

async function apiGet(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error('Request failed');
    return res.json();
}

function getResumeInput() {
    const fd = new FormData();
    if (_resumeFile) fd.append('file', _resumeFile);
    else if (_resumeText.trim()) fd.append('text', _resumeText.trim());
    else return null;
    return fd;
}

function scoreColor(score) {
    if (score >= 70) return '#059669';
    if (score >= 40) return '#D97706';
    return '#DC2626';
}

function scoreLabel(score) {
    if (score >= 80) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    if (score >= 30) return 'Needs Work';
    return 'Poor';
}

function scoreBadgeClass(score) {
    if (score >= 70) return 'score-high';
    if (score >= 40) return 'score-mid';
    return 'score-low';
}

function renderScoreRing(score, color) {
    const circumference = 2 * Math.PI * 42;
    const offset = circumference - (score / 100) * circumference;
    return `<div class="score-ring">
        <svg width="110" height="110" viewBox="0 0 110 110">
            <circle class="track" cx="55" cy="55" r="42"/>
            <circle class="progress" cx="55" cy="55" r="42"
                stroke="${color}" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"/>
        </svg>
        <div class="score-value">${score}</div>
    </div>
    <div class="score-label" style="color:${color}">${scoreLabel(score)}</div>`;
}

function renderSkillTags(skills, cls, limit = 0) {
    if (!limit || skills.length <= limit) {
        return skills.map(s => `<span class="skill-tag ${cls}">${s}</span>`).join('');
    }
    const visible = skills.slice(0, limit);
    const rest = skills.length - limit;
    const allJson = JSON.stringify(skills).replace(/"/g, '&quot;');
    return visible.map(s => `<span class="skill-tag ${cls}">${s}</span>`).join('') +
        `<span class="skill-tag more" onclick="this.parentElement.innerHTML=JSON.parse(this.dataset.all).map(s=>'<span class=\\'skill-tag ${cls}\\'>'+s+'</span>').join('')" data-all="${allJson}">+${rest} more</span>`;
}

async function analyzeResume() {
    const fd = getResumeInput();
    if (!fd) return toast('Provide a resume file or text', 'error');
    setLoading('btn-analyze', true);
    try {
        const data = await apiPost('/api/resumes/analyze', fd);
        renderAnalyzeResults(data);
        toast('Analysis complete', 'success');
    } catch (e) { toast(e.message, 'error'); }
    setLoading('btn-analyze', false);
}

function renderAnalyzeResults(d) {
    const el = document.getElementById('analyze-results');
    const color = scoreColor(d.overall_score);
    el.innerHTML = `
        <div class="result-section">
            <h3>Overall Score</h3>
            ${renderScoreRing(d.overall_score, color)}
        </div>
        <div class="result-section">
            <h3>Profile</h3>
            <ul class="info-list">
                ${d.name ? `<li><span class="info-label">Name</span><span class="info-value">${d.name}</span></li>` : ''}
                ${d.email ? `<li><span class="info-label">Email</span><span class="info-value">${d.email}</span></li>` : ''}
                ${d.phone ? `<li><span class="info-label">Phone</span><span class="info-value">${d.phone}</span></li>` : ''}
                <li><span class="info-label">Experience</span><span class="info-value">${d.experience_years} years</span></li>
                <li><span class="info-label">Category</span><span class="info-value"><span class="category-badge">${d.category}</span> <small style="color:var(--text-muted)">(${(d.category_confidence * 100).toFixed(0)}%)</small></span></li>
            </ul>
        </div>
        <div class="result-section">
            <h3>Summary</h3>
            <p style="font-size:0.875rem;line-height:1.75;color:var(--text-secondary);max-width:65ch">${d.summary}</p>
        </div>
        ${d.skills?.length ? `<div class="result-section">
            <h3>Skills (${d.skills.length})</h3>
            <div class="skill-tags">${renderSkillTags(d.skills, 'default', 8)}</div>
        </div>` : ''}
        ${d.strengths?.length ? `<div class="result-section">
            <h3>Strengths</h3>
            ${d.strengths.map(s => `<div class="strength-item">✓ ${s}</div>`).join('')}
        </div>` : ''}
        ${d.weaknesses?.length ? `<div class="result-section">
            <h3>Areas to Improve</h3>
            ${d.weaknesses.map(s => `<div class="weakness-item">⚠ ${s}</div>`).join('')}
        </div>` : ''}
        ${d.highlights?.length ? `<div class="result-section">
            <h3>Highlights</h3>
            <ul class="info-list">${d.highlights.map(h => `<li style="border:none;padding:5px 0;font-size:0.875rem;color:var(--text-secondary)">${h}</li>`).join('')}</ul>
        </div>` : ''}
        ${d.skills_by_category ? `<div class="result-section">
            <h3>Skills by Category</h3>
            ${Object.entries(d.skills_by_category).map(([cat, skills]) => `
                <div style="margin-bottom:12px">
                    <div style="font-size:0.75rem;font-weight:600;color:var(--text-muted);margin-bottom:5px;text-transform:uppercase;letter-spacing:0.8px">${cat}</div>
                    <div class="skill-tags">${renderSkillTags(skills, 'default', 6)}</div>
                </div>
            `).join('')}
        </div>` : ''}
    `;
}

async function findMatches() {
    const fd = getResumeInput();
    if (!fd) return toast('Provide a resume', 'error');
    const topK = document.getElementById('match-topk').value;
    
    // check cache
    const cached = _cacheGet('match', topK);
    if (cached) {
        renderMatchResults(cached.data.matches);
        toast(`Found ${cached.data.count} matches (cached ${_cacheAge(cached.ts)})`, 'info');
        return;
    }

    fd.append('top_k', topK);
    setLoading('btn-match', true);
    try {
        const data = await apiPost('/api/match/find', fd);
        _cacheSet('match', topK, data);
        renderMatchResults(data.matches);
        toast(`Found ${data.count} matches`, 'success');
    } catch (e) { toast(e.message, 'error'); }
    setLoading('btn-match', false);
}

async function fullAnalysis() {
    const fd = getResumeInput();
    if (!fd) return toast('Provide a resume', 'error');
    const topK = document.getElementById('match-topk').value;

    // check cache
    const cached = _cacheGet('full', topK);
    if (cached) {
        renderFullAnalysis(cached.data);
        toast(`Loaded from cache (${_cacheAge(cached.ts)})`, 'info');
        return;
    }

    fd.append('top_k', topK);
    setLoading('btn-full-analysis', true);
    try {
        const data = await apiPost('/api/match/full-analysis', fd);
        _cacheSet('full', topK, data);
        renderFullAnalysis(data);
        toast('Full analysis complete', 'success');
    } catch (e) { toast(e.message, 'error'); }
    setLoading('btn-full-analysis', false);
}

// ── Result Cache (12h TTL, keyed by resume + top_k) ─────────────────────────
const CACHE_TTL = 12 * 60 * 60 * 1000;

function _cacheKey(type, resumeKey, topK) {
    return `jb_cache_${type}_${topK}_${resumeKey}`;
}

function _resumeKey() {
    // use file name+size or first 120 chars of text as identity
    if (_resumeFile) return `${_resumeFile.name}_${_resumeFile.size}`;
    return _resumeText.trim().slice(0, 120);
}

function _cacheGet(type, topK) {
    try {
        const raw = localStorage.getItem(_cacheKey(type, _resumeKey(), topK));
        if (!raw) return null;
        const { ts, data } = JSON.parse(raw);
        if (Date.now() - ts > CACHE_TTL) return null;
        return { data, ts };
    } catch { return null; }
}

function _cacheSet(type, topK, data) {
    try {
        localStorage.setItem(_cacheKey(type, _resumeKey(), topK), JSON.stringify({ ts: Date.now(), data }));
    } catch { /* storage full — skip */ }
}

function _cacheAge(ts) {
    const mins = Math.floor((Date.now() - ts) / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    return `${Math.floor(mins / 60)}h ${mins % 60}m ago`;
}

let _swipeMatches = [], _swipeIndex = 0, _swipeLiked = [], _swipeHistory = [];

function renderMatchResults(matches) {
    const el = document.getElementById('match-results');
    const wrapper = document.getElementById('swipe-deck-wrapper');
    if (!matches?.length) {
        el.innerHTML = '<div class="empty-state"><p>No matches found. Try adding jobs first.</p></div>';
        el.classList.remove('hidden');
        wrapper.classList.add('hidden');
        return;
    }
    el.classList.add('hidden');
    wrapper.classList.remove('hidden');
    _swipeMatches = matches;
    _swipeIndex = 0;
    _swipeLiked = [];
    _swipeHistory = [];
    document.getElementById('swipe-liked-list').classList.add('hidden');
    _renderDeck();
}

function _renderDeck() {
    const deck = document.getElementById('swipe-deck');
    deck.innerHTML = '';
    const remaining = _swipeMatches.slice(_swipeIndex);
    if (!remaining.length) {
        deck.innerHTML = `<div class="swipe-done">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            <p>You've seen all matches!</p>
            <small>${_swipeLiked.length} job${_swipeLiked.length !== 1 ? 's' : ''} liked</small>
        </div>`;
        _renderLikedList();
        return;
    }
    // render back cards first (bottom of stack), top card last
    remaining.slice(0, 3).reverse().forEach((m, i) => {
        const card = _buildCard(m);
        // i=2 is back, i=1 is middle, i=0 is top card
        card.dataset.stackPos = i;
        deck.appendChild(card);
    });
    // top card is the last appended (highest z-index via CSS :first-child won't work)
    // so we manually set z-index
    Array.from(deck.children).forEach((c, i) => {
        c.style.zIndex = i; // last child = highest z
    });
    const topCard = deck.lastElementChild;
    topCard.style.transform = '';
    _attachDrag(topCard, remaining[0]);
}

function _buildCard(m) {
    const color = scoreColor(m.score);
    const card = document.createElement('div');
    card.className = 'swipe-card';
    card.innerHTML = `
        <div class="swipe-overlay like">LIKE 👍</div>
        <div class="swipe-overlay nope">NOPE ✕</div>
        <div class="swipe-card-rank">#${_swipeMatches.indexOf(m) + 1} Match</div>
        <div class="swipe-card-title">${m.job_title}</div>
        <div class="swipe-card-company">${m.company}</div>
        <div class="swipe-score-bar"><div class="swipe-score-fill" style="width:${m.score}%;background:${color}"></div></div>
        <div class="swipe-card-meta">
            <span style="font-size:0.85rem;font-weight:700;color:${color}">${m.score}%</span>
            ${m.location ? `<span>📍 ${m.location}</span>` : ''}
            ${m.salary_range ? `<span>💰 ${m.salary_range}</span>` : ''}
            ${m.category_match ? `<span style="color:var(--emerald)">✓ Category</span>` : ''}
            <span>Coverage ${m.skill_coverage || 0}%</span>
        </div>
        ${m.description ? `<p class="swipe-card-desc">${m.description.substring(0, 180)}${m.description.length > 180 ? '…' : ''}</p>` : ''}
        ${m.skill_overlap?.length ? `<div class="swipe-card-skills"><div class="skills-label">Matched Skills</div><div class="skill-tags">${renderSkillTags(m.skill_overlap, 'matched', 6)}</div></div>` : ''}
        ${m.missing_skills?.length ? `<div class="swipe-card-skills"><div class="skills-label">Missing Skills</div><div class="skill-tags">${renderSkillTags(m.missing_skills, 'missing', 5)}</div></div>` : ''}
    `;
    return card;
}

function _attachDrag(card, match) {
    let startX = 0, startY = 0, curX = 0, curY = 0, active = false;
    const likeOv = card.querySelector('.swipe-overlay.like');
    const nopeOv = card.querySelector('.swipe-overlay.nope');

    card.addEventListener('pointerdown', e => {
        if (e.button !== undefined && e.button !== 0) return;
        card.setPointerCapture(e.pointerId);
        startX = e.clientX;
        startY = e.clientY;
        curX = 0; curY = 0;
        active = true;
        card.classList.add('is-dragging');
    });

    card.addEventListener('pointermove', e => {
        if (!active) return;
        curX = e.clientX - startX;
        curY = e.clientY - startY;
        card.style.transform = `translate(${curX}px, ${curY}px) rotate(${curX * 0.08}deg)`;
        const ratio = Math.min(Math.abs(curX) / 80, 1);
        likeOv.style.opacity = curX > 0 ? ratio : 0;
        nopeOv.style.opacity = curX < 0 ? ratio : 0;
    });

    card.addEventListener('pointerup', e => {
        if (!active) return;
        active = false;
        card.classList.remove('is-dragging');
        card.releasePointerCapture(e.pointerId);
        if (curX > 80) _commitSwipe(card, match, 'right');
        else if (curX < -80) _commitSwipe(card, match, 'left');
        else {
            card.style.transition = 'transform 0.3s ease';
            card.style.transform = '';
            likeOv.style.opacity = 0;
            nopeOv.style.opacity = 0;
            setTimeout(() => card.style.transition = '', 300);
        }
    });

    card.addEventListener('pointercancel', () => {
        active = false;
        card.classList.remove('is-dragging');
        card.style.transform = '';
        likeOv.style.opacity = 0;
        nopeOv.style.opacity = 0;
    });
}

function _commitSwipe(card, match, dir) {
    const tx = dir === 'right' ? 600 : -600;
    card.style.transition = 'transform 0.35s ease, opacity 0.35s ease';
    card.style.transform = `translate(${tx}px, 40px) rotate(${dir === 'right' ? 20 : -20}deg)`;
    card.style.opacity = '0';
    _swipeHistory.push({ match, dir, index: _swipeIndex });
    if (dir === 'right') _swipeLiked.push(match);
    _swipeIndex++;
    setTimeout(_renderDeck, 350);
}

function swipeAction(dir) {
    const deck = document.getElementById('swipe-deck');
    const top = deck.lastElementChild;
    if (!top || top.classList.contains('swipe-done') || _swipeIndex >= _swipeMatches.length) return;
    _commitSwipe(top, _swipeMatches[_swipeIndex], dir);
}

function swipeUndo() {
    if (!_swipeHistory.length) return;
    const last = _swipeHistory.pop();
    if (last.dir === 'right') _swipeLiked = _swipeLiked.filter(m => m !== last.match);
    _swipeIndex = last.index;
    _renderDeck();
}

function _renderLikedList() {
    const el = document.getElementById('swipe-liked-list');
    if (!_swipeLiked.length) { el.classList.add('hidden'); return; }
    el.classList.remove('hidden');
    el.innerHTML = `<h4>❤️ Liked Jobs (${_swipeLiked.length})</h4>` +
        _swipeLiked.map(m => `<div class="swipe-liked-item">
            <div><div class="job-name">${m.job_title}</div><div class="job-co">${m.company}</div></div>
            <span class="match-score-badge ${scoreBadgeClass(m.score)}">${m.score}%</span>
        </div>`).join('');
}

function renderFullAnalysis(data) {
    const el = document.getElementById('match-results');
    let html = '';

    if (data.resume_review) {
        const r = data.resume_review;
        const color = scoreColor(r.overall_score);
        html += `<div class="result-section">
            <h3>Resume Review</h3>
            ${renderScoreRing(r.overall_score, color)}
            <div class="stat-grid" style="margin-top:16px">
                <div class="stat-card"><div class="stat-value" style="font-size:0.9rem">${r.category}</div><div class="stat-label">Category</div></div>
                <div class="stat-card"><div class="stat-value">${r.skills?.length || 0}</div><div class="stat-label">Skills</div></div>
                <div class="stat-card"><div class="stat-value">${r.experience_years}</div><div class="stat-label">Years Exp</div></div>
            </div>
        </div>`;
    }

    if (data.job_matches?.length) {
        html += `<div class="result-section"><h3>Top Job Matches</h3></div>`;
        html += data.job_matches.map(m => `
            <div class="match-card">
                <div class="match-card-header">
                    <div><div class="match-card-title">${m.job_title}</div><div class="match-card-company">${m.company}</div></div>
                    <span class="match-score-badge ${scoreBadgeClass(m.score)}">${m.score}%</span>
                </div>
                <div class="match-meta">
                    ${m.location ? `<span>📍 ${m.location}</span>` : ''}
                    ${m.salary_range ? `<span>💰 ${m.salary_range}</span>` : ''}
                    <span>Coverage ${m.skill_coverage || 0}%</span>
                </div>
                ${m.description ? `<p style="font-size:0.82rem;color:var(--text-secondary);line-height:1.6;margin-bottom:10px">${m.description.substring(0, 200)}${m.description.length > 200 ? '…' : ''}</p>` : ''}
                ${m.skill_overlap?.length ? `<div style="margin-bottom:4px"><span style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--emerald)">Matched</span><div class="skill-tags" style="margin-top:4px">${renderSkillTags(m.skill_overlap, 'matched', 6)}</div></div>` : ''}
                ${m.missing_skills?.length ? `<div style="margin-top:6px"><span style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:var(--rose)">Missing</span><div class="skill-tags" style="margin-top:4px">${renderSkillTags(m.missing_skills, 'missing', 6)}</div></div>` : ''}
            </div>
        `).join('');
    }

    if (data.skill_gaps?.length) {
        html += `<div class="result-section">
            <h3>Skill Gaps (Across All Matches)</h3>
            <div class="skill-tags">${renderSkillTags(data.skill_gaps, 'missing', 10)}</div>
        </div>`;
    }

    if (data.interview_questions?.length) {
        html += `<div class="result-section"><h3>Interview Questions</h3>
            ${data.interview_questions.map(q => `
                <div class="interview-card">
                    <span class="q-category q-cat-${q.category}">${q.category}</span>
                    <div class="q-text">${q.question}</div>
                    <div class="q-difficulty">Difficulty: ${q.difficulty}</div>
                </div>
            `).join('')}
        </div>`;
    }

    if (data.career_suggestions?.length) {
        html += `<div class="result-section"><h3>Career Path Suggestions</h3>
            ${data.career_suggestions.map(c => `
                <div class="career-card">
                    <h4>From: ${c.current_role}</h4>
                    <div class="career-path-list">${c.suggested_roles.map(r => `<span class="career-step">${r}</span>`).join('')}</div>
                    ${c.skills_to_acquire?.length ? `<div style="margin-top:8px;font-size:0.8rem;color:var(--text-secondary)">Skills to acquire: ${c.skills_to_acquire.join(', ')}</div>` : ''}
                    <div style="margin-top:6px;font-size:0.75rem;color:var(--text-muted)">${c.timeline}</div>
                </div>
            `).join('')}
        </div>`;
    }

    el.innerHTML = html || '<div class="empty-state"><p>No analysis data</p></div>';
}

async function addJob() {
    const title = document.getElementById('job-title').value.trim();
    const company = document.getElementById('job-company').value.trim();
    const desc = document.getElementById('job-desc').value.trim();
    if (!title || !company || !desc) return toast('Fill in title, company, and description', 'error');
    const body = {
        title, company, description: desc,
        requirements: document.getElementById('job-requirements').value.split(',').map(s => s.trim()).filter(Boolean),
        location: document.getElementById('job-location').value.trim(),
        salary_range: document.getElementById('job-salary').value.trim()
    };
    try {
        const res = await fetch('/api/jobs/add', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
        const data = await res.json();
        toast(`Job added: ${data.job_id} (${data.category})`, 'success');
        ['job-title','job-company','job-desc','job-requirements','job-location','job-salary'].forEach(id => document.getElementById(id).value = '');
    } catch (e) { toast(e.message, 'error'); }
}

async function searchJobs() {
    const query = document.getElementById('job-search-query').value.trim();
    if (!query) return toast('Enter a search query', 'error');
    try {
        const data = await apiGet(`/api/jobs/search?query=${encodeURIComponent(query)}`);
        renderJobList(data.results);
        toast(`Found ${data.count} jobs`, 'success');
    } catch (e) { toast(e.message, 'error'); }
}

async function listJobs() {
    try {
        const data = await apiGet('/api/jobs/list');
        renderJobList(data.jobs);
        toast(`${data.count} jobs in database`, 'info');
    } catch (e) { toast(e.message, 'error'); }
}

function renderJobList(jobs) {
    const el = document.getElementById('jobs-results');
    if (!jobs?.length) { el.innerHTML = '<div class="empty-state"><p>No jobs found</p></div>'; return; }
    el.innerHTML = jobs.map(j => {
        const m = j.metadata || {};
        return `<div class="job-card">
            <h4>${m.title || 'Untitled'}</h4>
            <div class="company">${m.company || ''}</div>
            <div class="meta">
                ${m.location ? `<span>📍 ${m.location}</span>` : ''}
                ${m.salary_range ? `<span>💰 ${m.salary_range}</span>` : ''}
                ${m.category ? `<span class="category-badge">${m.category}</span>` : ''}
                ${m.job_type ? `<span>${m.job_type}</span>` : ''}
            </div>
            <p style="font-size:0.82rem;color:var(--text-secondary);margin-top:8px;line-height:1.6">${(j.document || '').substring(0, 200)}...</p>
        </div>`;
    }).join('');
}

function setQuestion(q) {
    document.getElementById('qa-question').value = q;
}

async function askQuestion() {
    const question = document.getElementById('qa-question').value.trim();
    const context = document.getElementById('qa-context').value.trim();
    if (!question) return toast('Enter a question', 'error');
    if (!context) return toast('Provide context (resume/job text)', 'error');
    const fd = new FormData();
    fd.append('question', question);
    fd.append('resume_text', context);
    try {
        const data = await apiPost('/api/match/qa', fd);
        const el = document.getElementById('qa-results');
        const prev = el.innerHTML.includes('empty-state') ? '' : el.innerHTML;
        el.innerHTML = `
            <div class="qa-answer">
                <div class="qa-question-label">Q: ${question}</div>
                <div class="answer-text">${data.answer}</div>
                <div class="confidence">Confidence: ${(data.confidence * 100).toFixed(1)}%</div>
            </div>
        ` + prev;
    } catch (e) { toast(e.message, 'error'); }
}

async function loadDashboard() {
    const el = document.getElementById('dashboard-content');
    try {
        const [dash, skills] = await Promise.all([apiGet('/api/analytics/dashboard'), apiGet('/api/analytics/skills-demand')]);
        el.innerHTML = `
            <div class="dash-card">
                <h3>Overview</h3>
                <div class="stat-grid">
                    <div class="stat-card"><div class="stat-value">${dash.total_jobs}</div><div class="stat-label">Total Jobs</div></div>
                    <div class="stat-card"><div class="stat-value">${Object.keys(dash.categories).length}</div><div class="stat-label">Categories</div></div>
                    <div class="stat-card"><div class="stat-value">${Object.keys(dash.locations).length}</div><div class="stat-label">Locations</div></div>
                </div>
            </div>
            <div class="dash-card">
                <h3>Jobs by Category</h3>
                <div class="bar-chart">
                    ${(dash.top_categories || []).map(([cat, count]) => {
                        const pct = dash.total_jobs ? (count / dash.total_jobs * 100) : 0;
                        return `<div class="bar-item">
                            <div class="bar-label"><span>${cat}</span><span>${count}</span></div>
                            <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
                        </div>`;
                    }).join('')}
                </div>
            </div>
            <div class="dash-card">
                <h3>Top Skills in Demand</h3>
                <div class="bar-chart">
                    ${(skills.skills_demand || []).slice(0, 15).map(([skill, count]) => {
                        const max = skills.skills_demand[0]?.[1] || 1;
                        const pct = (count / max * 100);
                        return `<div class="bar-item">
                            <div class="bar-label"><span>${skill}</span><span>${count}</span></div>
                            <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:#059669"></div></div>
                        </div>`;
                    }).join('')}
                </div>
            </div>
            <div class="dash-card">
                <h3>Locations</h3>
                <div class="bar-chart">
                    ${Object.entries(dash.locations).sort((a,b) => b[1]-a[1]).map(([loc, count]) => {
                        const pct = dash.total_jobs ? (count / dash.total_jobs * 100) : 0;
                        return `<div class="bar-item">
                            <div class="bar-label"><span>${loc || 'Unknown'}</span><span>${count}</span></div>
                            <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:#D97706"></div></div>
                        </div>`;
                    }).join('')}
                </div>
            </div>
        `;
    } catch (e) {
        el.innerHTML = `<div class="empty-state"><p>Failed to load dashboard: ${e.message}</p></div>`;
    }
}
