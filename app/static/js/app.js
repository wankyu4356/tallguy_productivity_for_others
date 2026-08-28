// 딜사이트 News Clipper — 공통 UI 유틸

function showStatus(elementId, message, type = 'info') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.style.display = 'flex';
    const textEl = el.querySelector('p') || el;
    textEl.textContent = message;
    if (type === 'error') textEl.classList.add('log-error');
}

function appendLog(containerId, message, type = 'info') {
    const container = document.getElementById(containerId);
    if (!container) return;
    const p = document.createElement('p');
    p.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    p.classList.add(`log-${type}`);
    container.appendChild(p);
    container.scrollTop = container.scrollHeight;
}

/* ── 기사 선택 ──────────────────────────────────────
   같은 기사가 '추천'과 '전체 목록' 두 탭에 모두 나오므로,
   체크박스가 아니라 기사 ID 기준으로 세고 두 탭을 동기화한다.
   (예전에는 체크박스를 세서 8개 기사가 16개로 집계됐다.)
   ------------------------------------------------- */

function uniqueArticleIds(onlyChecked) {
    const sel = onlyChecked ? '.article-checkbox:checked' : '.article-checkbox';
    return new Set(Array.from(document.querySelectorAll(sel)).map(cb => cb.value));
}

function syncCheckbox(id, checked) {
    document.querySelectorAll(`.article-checkbox[value="${CSS.escape(id)}"]`)
        .forEach(cb => { cb.checked = checked; });
}

function selectAll(checked) {
    document.querySelectorAll('.article-checkbox').forEach(cb => { cb.checked = checked; });
    updateSelectionCount();
}

function updateSelectionCount() {
    const total = uniqueArticleIds(false).size;
    const selected = uniqueArticleIds(true).size;

    const countEl = document.getElementById('selection-count');
    if (countEl) countEl.textContent = `${selected} / ${total} 선택됨`;

    // 하단 액션바
    const bar = document.getElementById('action-count');
    if (bar) bar.textContent = selected;
    const totalEl = document.getElementById('action-total');
    if (totalEl) totalEl.textContent = total;

    const cta = document.getElementById('btn-confirm');
    if (cta) {
        cta.disabled = selected === 0;
        cta.textContent = selected === 0 ? '기사를 선택하세요' : `${selected}개로 문서 만들기`;
    }
}

// 한쪽 탭에서 체크하면 다른 탭의 같은 기사도 따라오게 한다
document.addEventListener('change', (e) => {
    const cb = e.target;
    if (!cb.classList || !cb.classList.contains('article-checkbox')) return;
    syncCheckbox(cb.value, cb.checked);
    updateSelectionCount();
});

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => { c.style.display = 'none'; });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    const panel = document.getElementById(`tab-${tabName}`);
    if (panel) {
        panel.style.display = 'block';
        // 탭 전환에 짧은 페이드를 주어 내용이 바뀐 걸 인지시킨다
        panel.classList.remove('tab-enter');
        void panel.offsetWidth;
        panel.classList.add('tab-enter');
    }
}

/* ── 토스트 ─────────────────────────────────────── */
function showToast(msg, kind = 'default') {
    document.querySelectorAll('.toast').forEach(t => t.remove());
    const t = document.createElement('div');
    t.className = 'toast' + (kind === 'error' ? ' toast-error' : '');
    t.textContent = msg;
    document.body.appendChild(t);
    requestAnimationFrame(() => t.classList.add('toast-in'));
    setTimeout(() => {
        t.classList.remove('toast-in');
        setTimeout(() => t.remove(), 260);
    }, 2400);
}

/* ── 경과 시간 표시 ─────────────────────────────── */
function startElapsed(elId, since = Date.now()) {
    const el = document.getElementById(elId);
    if (!el) return null;
    const tick = () => {
        const s = Math.floor((Date.now() - since) / 1000);
        const m = Math.floor(s / 60);
        el.textContent = m > 0 ? `${m}분 ${String(s % 60).padStart(2, '0')}초 경과`
                               : `${s}초 경과`;
    };
    tick();
    return setInterval(tick, 1000);
}
