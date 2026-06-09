// Matrix Rain
(function() {
    const c = document.getElementById('matrix-bg');
    if (!c) return;
    const ctx = c.getContext('2d');
    c.width = window.innerWidth;
    c.height = window.innerHeight;
    const cols = Math.floor(c.width / 18);
    const drops = Array(cols).fill(1);
    const chars = '01アイウエオ<>{}ABCDEF0123456789';
    setInterval(() => {
        ctx.fillStyle = 'rgba(8,8,16,0.05)';
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.fillStyle = '#00ff88';
        ctx.font = '13px Share Tech Mono';
        drops.forEach((y, i) => {
            ctx.fillText(chars[Math.floor(Math.random() * chars.length)], i * 18, y * 18);
            if (y * 18 > c.height && Math.random() > .975) drops[i] = 0;
            drops[i]++;
        });
    }, 55);
    window.addEventListener('resize', () => { c.width = window.innerWidth;
        c.height = window.innerHeight; });
})();

let monitorActive = false,
    alertPollInterval = null,
    lastAlertTs = null;

async function toggleMonitor() {
    const btn = document.getElementById('global-monitor-btn');
    const badge = document.getElementById('monitor-badge');
    const txt = document.getElementById('monitor-status-text');
    if (!monitorActive) {
        await fetch('/api/monitor/start', { method: 'POST' });
        monitorActive = true;
        btn.textContent = '■ STOP MONITOR';
        btn.classList.add('running');
        badge.classList.add('active');
        txt.textContent = 'LIVE';
        startAlertPolling();
        showToast('✅ Monitoring Shuru!', 'Network monitor chal raha hai.', 'green');
    } else {
        await fetch('/api/monitor/stop', { method: 'POST' });
        monitorActive = false;
        btn.textContent = '▶ START MONITOR';
        btn.classList.remove('running');
        badge.classList.remove('active');
        txt.textContent = 'OFFLINE';
        stopAlertPolling();
    }
}

function startAlertPolling() {
    alertPollInterval = setInterval(async() => {
        try {
            const r = await (await fetch('/api/alerts')).json();
            if (r.length > 0) {
                const l = r[r.length - 1];
                if (l.timestamp !== lastAlertTs && l.risk_level === 'HIGH') {
                    lastAlertTs = l.timestamp;
                    showToast('🚨 ' + l.attack_type.toUpperCase() + ' DETECTED!', l.hindi_label, 'red');
                    speakAlert(l.hindi_label);
                }
            }
        } catch (e) {}
    }, 3000);
}

function stopAlertPolling() { if (alertPollInterval) clearInterval(alertPollInterval); }

function showToast(title, msg, type = 'red') {
    const toast = document.getElementById('alert-toast');
    document.getElementById('toast-title').textContent = title;
    document.getElementById('toast-msg').textContent = msg;
    const inner = toast.querySelector('.toast-inner');
    const col = type === 'green' ? '#00ff88' : type === 'orange' ? '#ff8800' : '#ff2255';
    const bg = type === 'green' ? '#001a0d' : type === 'orange' ? '#1a0d00' : '#1a0010';
    inner.style.borderColor = col;
    inner.style.background = bg;
    toast.querySelector('.toast-title').style.color = col;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 5000);
}

function closeToast() { document.getElementById('alert-toast').classList.add('hidden'); }

function speakAlert(text) {
    if ('speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance('Khabardar! ' + text);
        u.lang = 'hi-IN';
        u.rate = 0.9;
        u.pitch = 1.1;
        window.speechSynthesis.speak(u);
    }
}

function riskBadge(l) {
    const cls = l === 'HIGH' ? 'badge-high' : l === 'MEDIUM' ? 'badge-medium' : 'badge-low';
    return `<span class="badge ${cls}">${l}</span>`;
}

function attackBadge(t) {
    if (!t) return '-';
    if (t === 'normal') return `<span class="badge badge-normal">NORMAL</span>`;
    return `<span class="badge badge-high">${t.replace(/_/g,' ').toUpperCase()}</span>`;
}

function fmtTime(ts) { return ts ? ts.split(' ')[1] || ts : '-'; }

(async function() {
    try {
        const d = await (await fetch('/api/monitor/status')).json();
        if (d.active) {
            monitorActive = true;
            document.getElementById('global-monitor-btn').textContent = '■ STOP MONITOR';
            document.getElementById('global-monitor-btn').classList.add('running');
            document.getElementById('monitor-badge').classList.add('active');
            document.getElementById('monitor-status-text').textContent = 'LIVE';
            startAlertPolling();
        }
    } catch (e) {}
})();