// BillKaro — Web Chat Client

const SESSION_ID = localStorage.getItem('billkaro_session') || crypto.randomUUID();
localStorage.setItem('billkaro_session', SESSION_ID);

const messagesEl = document.getElementById('messages');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');
const stopBtn = document.getElementById('stopBtn');
const recordingIndicator = document.getElementById('recordingIndicator');

const fwdBtn = document.getElementById('fwdBtn');
const fwdPanel = document.getElementById('forwardedPanel');
const fwdCloseBtn = document.getElementById('fwdCloseBtn');
const fwdTextarea = document.getElementById('fwdTextarea');
const fwdSendBtn = document.getElementById('fwdSendBtn');

let mediaRecorder = null;
let audioChunks = [];

// --- Sample buttons ---

const SAMPLES = {
    hinglish: "Ramesh Traders ka invoice banao, 150kg cotton, 45000 rupees, 12% GST",
    forwarded: "Ramesh: Can you do 150kg cotton?\nYou: Yes, 300/kg works\nRamesh: Done. 12% GST right?\nYou: Yes, total 50400 with GST",
    kumar: "Invoice Kumar Enterprises 200kg steel rods 72000 18% GST",
};

document.querySelectorAll('.sample-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const text = SAMPLES[btn.dataset.sample];
        if (!text) return;
        addMessage(text, 'user');
        await sendToAPI({ text });
    });
});

// --- Send text ---

sendBtn.addEventListener('click', sendText);
textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendText();
    }
});

async function sendText() {
    const text = textInput.value.trim();
    if (!text) return;
    textInput.value = '';

    addMessage(text, 'user');
    await sendToAPI({ text });
}

// --- Voice recording ---

micBtn.addEventListener('click', toggleRecording);
stopBtn.addEventListener('click', stopRecording);

async function toggleRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        stopRecording();
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Use the best supported format
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
            ? 'audio/webm;codecs=opus'
            : MediaRecorder.isTypeSupported('audio/mp4')
                ? 'audio/mp4'
                : '';

        mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            stream.getTracks().forEach(t => t.stop());
            micBtn.classList.remove('recording');
            recordingIndicator.classList.add('hidden');

            const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
            addMessage('[Voice message]', 'user');
            await sendVoice(blob);
        };

        mediaRecorder.start();
        micBtn.classList.add('recording');
        recordingIndicator.classList.remove('hidden');
    } catch (err) {
        console.error('Mic access denied:', err);
        addMessage('Microphone access denied. Please allow mic access and try again.', 'bot');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
}

// --- Forwarded messages ---

fwdBtn.addEventListener('click', () => {
    fwdPanel.classList.toggle('hidden');
    if (!fwdPanel.classList.contains('hidden')) {
        fwdTextarea.focus();
    }
});

fwdCloseBtn.addEventListener('click', () => {
    fwdPanel.classList.add('hidden');
});

fwdSendBtn.addEventListener('click', async () => {
    const text = fwdTextarea.value.trim();
    if (!text) return;
    fwdTextarea.value = '';
    fwdPanel.classList.add('hidden');

    addMessage('[Forwarded messages]\n' + text, 'user');
    await sendToAPI({ text });
});

// --- API calls ---

async function sendToAPI({ text = '', button = '' }) {
    showTyping();

    const formData = new FormData();
    formData.append('session_id', SESSION_ID);
    if (text) formData.append('text', text);
    if (button) formData.append('button', button);

    try {
        const resp = await fetch('/api/chat', { method: 'POST', body: formData });
        const data = await resp.json();
        removeTyping();
        handleResponse(data);
    } catch (err) {
        removeTyping();
        addMessage('Connection error. Please try again.', 'bot');
    }
}

async function sendVoice(blob) {
    showTyping();

    const ext = blob.type.includes('webm') ? 'webm' : blob.type.includes('mp4') ? 'm4a' : 'webm';
    const formData = new FormData();
    formData.append('session_id', SESSION_ID);
    formData.append('audio', blob, `recording.${ext}`);

    try {
        const resp = await fetch('/api/voice', { method: 'POST', body: formData });
        const data = await resp.json();
        removeTyping();
        handleResponse(data);
    } catch (err) {
        removeTyping();
        addMessage('Connection error. Please try again.', 'bot');
    }
}

// --- Button clicks ---

async function onButtonClick(id) {
    addMessage(id.charAt(0).toUpperCase() + id.slice(1), 'user');
    await sendToAPI({ button: id });
}

// --- Response handling ---

function handleResponse(data) {
    // Convert markdown-like bold to HTML
    let html = escapeHtml(data.text)
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

    // Add PDF download link
    if (data.pdf) {
        const blob = b64toBlob(data.pdf, 'application/pdf');
        const url = URL.createObjectURL(blob);
        html += `<br><a href="${url}" download="invoice.pdf" class="pdf-link">Download Invoice PDF</a>`;
    }

    // Add buttons
    if (data.buttons && data.buttons.length) {
        html += '<div class="msg-buttons">';
        for (const btn of data.buttons) {
            html += `<button class="msg-btn" onclick="onButtonClick('${btn.id}')">${escapeHtml(btn.title)}</button>`;
        }
        html += '</div>';
    }

    addMessageHtml(html, 'bot');
}

// --- DOM helpers ---

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
    messagesEl.appendChild(div);
    scrollToBottom();
}

function addMessageHtml(html, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.innerHTML = `<div class="bubble">${html}</div>`;
    messagesEl.appendChild(div);
    scrollToBottom();
}

function showTyping() {
    const div = document.createElement('div');
    div.className = 'message bot';
    div.id = 'typing';
    div.innerHTML = '<div class="bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
    messagesEl.appendChild(div);
    scrollToBottom();
}

function removeTyping() {
    const el = document.getElementById('typing');
    if (el) el.remove();
}

function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function b64toBlob(b64, type) {
    const bytes = atob(b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    return new Blob([arr], { type });
}
