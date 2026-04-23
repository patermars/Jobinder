document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
        if (tab.dataset.tab === 'dashboard') loadDashboard();
    });
});

['analyze', 'match'].forEach(id => {
    const input = document.getElementById('file-' + id);
    if (input) input.addEventListener('change', e => {
        const name = e.target.files[0]?.name || '';
        document.getElementById('file-name-' + id).textContent = name;
    });
});

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

function getResumeInput(suffix) {
    const fileInput = document.getElementById('file-' + suffix);
    const textInput = document.getElementById('resume-text-' + suffix);
    const fd = new FormData();
    if (fileInput?.files?.length) fd.append('file', fileInput.files[0]);
    else if (textInput?.value?.trim()) fd.append('text', textInput.value.trim());
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
    const fd = getResumeInput('analyze');
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
    const fd = getResumeInput('match');
    if (!fd) return toast('Provide a resume', 'error');
    fd.append('top_k', document.getElementById('match-topk').value);
    setLoading('btn-match', true);
    try {
        const data = await apiPost('/api/match/find', fd);
        renderMatchResults(data.matches);
        toast(`Found ${data.count} matches`, 'success');
    } catch (e) { toast(e.message, 'error'); }
    setLoading('btn-match', false);
}

async function fullAnalysis() {
    const fd = getResumeInput('match');
    if (!fd) return toast('Provide a resume', 'error');
    fd.append('top_k', document.getElementById('match-topk').value);
    setLoading('btn-full-analysis', true);
    try {
        const data = await apiPost('/api/match/full-analysis', fd);
        renderFullAnalysis(data);
        toast('Full analysis complete', 'success');
    } catch (e) { toast(e.message, 'error'); }
    setLoading('btn-full-analysis', false);
}

function renderMatchResults(matches) {
    const el = document.getElementById('match-results');
    if (!matches?.length) { el.innerHTML = '<div class="empty-state"><p>No matches found. Try adding jobs first.</p></div>'; return; }
    el.innerHTML = matches.map((m, i) => `
        <div class="match-card" style="animation-delay:${i * 0.05}s">
            <div class="match-card-header">
                <div>
                    <div class="match-card-title">${m.job_title}</div>
                    <div class="match-card-company">${m.company}</div>
                </div>
                <span class="match-score-badge ${scoreBadgeClass(m.score)}">${m.score}%</span>
            </div>
            <div class="match-meta">
                ${m.location ? `<span>📍 ${m.location}</span>` : ''}
                ${m.salary_range ? `<span>💰 ${m.salary_range}</span>` : ''}
                ${m.category_match ? `<span>✓ Category match</span>` : ''}
                <span>Coverage: ${m.skill_coverage || 0}%</span>
            </div>
            ${m.skill_overlap?.length ? `<div style="margin-bottom:8px"><div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:4px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px">Matched</div><div class="skill-tags">${renderSkillTags(m.skill_overlap, 'matched', 6)}</div></div>` : ''}
            ${m.missing_skills?.length ? `<div><div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:4px;font-weight:600;text-transform:uppercase;letter-spacing:0.6px">Missing</div><div class="skill-tags">${renderSkillTags(m.missing_skills, 'missing', 6)}</div></div>` : ''}
        </div>
    `).join('');
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
                </div>
                ${m.skill_overlap?.length ? `<div class="skill-tags" style="margin-bottom:6px">${renderSkillTags(m.skill_overlap, 'matched', 6)}</div>` : ''}
                ${m.missing_skills?.length ? `<div class="skill-tags">${renderSkillTags(m.missing_skills, 'missing', 6)}</div>` : ''}
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
