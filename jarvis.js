/* ═══════════════════════════════════════════════════════════
   J.A.R.V.I.S. — Frontend Brain
   ═══════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    var SERVER = 'http://127.0.0.1:7777';
    var recognition = null;
    var synth = window.speechSynthesis;
    var voice = null;
    var listening = false;
    var speaking = false;
    var voiceOn = true;
    var chatHist = [];
    var STORAGE = 'jarvis-chat-v1';

    // ── Init ───────────────────────────────────────────────
    function init() {
        loadChat();
        setupSR();
        setupTTS();
        bindUI();
        checkServer();
        setInterval(checkServer, 15000);
        setStatus('Systems online, Sir.');
    }

    // ── Persistence ────────────────────────────────────────
    function loadChat() {
        try { chatHist = JSON.parse(localStorage.getItem(STORAGE) || '[]'); } catch (e) { chatHist = []; }
        renderChat();
    }
    function saveChat() {
        try { localStorage.setItem(STORAGE, JSON.stringify(chatHist.slice(-50))); } catch (e) {}
    }

    // ── Speech Recognition ─────────────────────────────────
    function setupSR() {
        var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) { setStatus('⚠️ Microphone unavailable'); return; }

        recognition = new SR();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'ru-RU';

        recognition.onstart = function () {
            listening = true;
            document.getElementById('micBtn').classList.add('listening');
            document.getElementById('visualizer').classList.add('active');
            setStatus('Listening...');
            setTranscript('Speak, Sir.', false);
        };

        recognition.onend = function () {
            listening = false;
            document.getElementById('micBtn').classList.remove('listening');
            document.getElementById('visualizer').classList.remove('active');
            if (!speaking) setStatus('Systems online.');
        };

        recognition.onerror = function (e) {
            listening = false;
            document.getElementById('micBtn').classList.remove('listening');
            document.getElementById('visualizer').classList.remove('active');
            if (e.error === 'not-allowed') setStatus('❌ Microphone access denied');
            else if (e.error === 'no-speech') setStatus('Silence detected.');
            else setStatus('Systems online.');
        };

        recognition.onresult = function (ev) {
            var interim = '', final = '';
            for (var i = ev.resultIndex; i < ev.results.length; i++) {
                var t = ev.results[i][0].transcript;
                if (ev.results[i].isFinal) final += t; else interim += t;
            }
            if (interim) setTranscript(interim, false);
            if (final) { setTranscript(final, true); processInput(final.trim()); }
        };
    }

    // ── Text-to-Speech (JARVIS voice) ─────────────────────
    function setupTTS() {
        if (!synth) return;
        function pick() {
            var vs = synth.getVoices();
            voice = vs.find(function (v) { return v.name.indexOf('Yuri') > -1; })
                || vs.find(function (v) { return v.name.indexOf('Daniel') > -1; })
                || vs.find(function (v) { return v.lang.indexOf('ru') === 0; })
                || vs.find(function (v) { return v.lang.indexOf('en') === 0; })
                || vs[0];
        }
        pick();
        if (synth.onvoiceschanged !== undefined) synth.onvoiceschanged = pick;
    }

    function say(text) {
        if (!synth || !voiceOn) return;
        synth.cancel();
        var u = new SpeechSynthesisUtterance(text);
        u.voice = voice;
        u.lang = 'ru-RU';
        u.rate = 1.0;
        u.pitch = 0.7;
        u.onstart = function () { speaking = true; setStatus('🔊 Speaking...'); };
        u.onend = function () { speaking = false; setStatus('Systems online.'); };
        u.onerror = function () { speaking = false; setStatus('Systems online.'); };
        synth.speak(u);
    }

    // ── Input Processing ───────────────────────────────────
    function processInput(text) {
        addMsg('user', text);
        var low = text.toLowerCase().trim();

        // ── Local commands (no server needed) ──
        if (/(время|сколько времени|час|time)/.test(low)) {
            var t = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
            reply('The time is ' + t + ', Sir.');
            return;
        }
        if (/(дата|число|день|date)/.test(low)) {
            var d = new Date().toLocaleDateString('ru-RU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
            reply('Today is ' + d + ', Sir.');
            return;
        }
        if (/(шутка|anecdote|joke|рассмеши)/.test(low)) { joke(); return; }
        if (/голос (включ|выкл|on|off)/.test(low)) {
            voiceOn = low.indexOf('включ') > -1 || low.indexOf('on') > -1;
            reply(voiceOn ? 'Voice enabled.' : 'Voice disabled.');
            return;
        }

        // ── Server commands ──
        if (/(открой|запусти|open)/.test(low)) {
            var app = after(low, ['открой', 'запусти', 'open']);
            if (app) api('/api/open', { app: app });
            else reply('What shall I open, Sir?');
            return;
        }
        if (/(выйди из|закрой|quit|exit|close)/.test(low)) {
            var app = after(low, ['выйди из', 'закрой', 'quit', 'exit', 'close']);
            if (app) api('/api/quit', { app: app });
            else reply('Which application shall I close, Sir?');
            return;
        }
        if (/(громкость|volume)/.test(low)) {
            var v = 'up';
            if (/убавь|уменьш|down|тише/.test(low)) v = 'down';
            else if (/выключ|mute|отключи/.test(low)) v = 'mute';
            else if (/\d+/.test(low)) v = low.match(/\d+/)[0];
            api('/api/volume', { val: v });
            return;
        }
        if (/(яркость|brightness)/.test(low)) {
            var v = 'up';
            if (/убавь|уменьш|down|темн|ниже/.test(low)) v = 'down';
            else if (/\d+/.test(low)) v = low.match(/\d+/)[0];
            api('/api/brightness', { val: v });
            return;
        }
        if (/(батаре|заряд|battery)/.test(low)) { api('/api/battery'); return; }
        if (/(погода|weather)/.test(low)) { api('/api/weather', { city: 'Ташкент' }); return; }
        if (/(система|info|инфо)/.test(low)) { api('/api/info'); return; }
        if (/(создай папку|mkdir)/.test(low)) {
            var p = after(low, ['создай папку', 'mkdir']);
            if (p) api('/api/mkdir', { path: p });
            else reply('What shall I name the folder, Sir?');
            return;
        }
        if (/(создай файл|touch)/.test(low)) {
            var p = after(low, ['создай файл', 'touch']);
            if (p) api('/api/touch', { path: p });
            else reply('What shall I name the file, Sir?');
            return;
        }
        if (/(список|ls|покажи файлы)/.test(low)) {
            var p = after(low, ['список', 'ls', 'покажи файлы']) || '~';
            api('/api/ls', { path: p });
            return;
        }
        if (/(найди|поищи|search|загугли)/.test(low)) {
            var q = after(low, ['найди', 'поищи', 'search', 'загугли']);
            if (q) api('/api/search', { q: q });
            else reply('What shall I search for, Sir?');
            return;
        }

        // ── Default: AI chat via OpenAI ──
        aiChat(text);
    }

    // ── AI Chat ────────────────────────────────────────────
    function aiChat(text) {
        setStatus('🧠 Thinking...');
        chatHist.push({ role: 'user', content: text });

        api('/api/chat', null, {
            method: 'POST',
            body: JSON.stringify({ messages: chatHist.slice(-15) })
        }).then(function (res) {
            if (res.ok) {
                chatHist.push({ role: 'assistant', content: res.msg });
                saveChat();
                reply(res.msg);
            } else {
                reply(res.msg || 'Connection error, Sir.');
            }
        });
    }

    // ── Server API ─────────────────────────────────────────
    function api(path, params, opts) {
        var url = SERVER + path;
        if (params) {
            var qs = Object.keys(params).map(function (k) { return k + '=' + encodeURIComponent(params[k]); }).join('&');
            url += '?' + qs;
        }
        var fetchOpts = opts || {};
        fetchOpts.signal = AbortSignal.timeout(5000);

        return fetch(url, fetchOpts)
            .then(function (r) { return r.json(); })
            .catch(function () {
                return { ok: false, msg: '❌ Server offline. Run: python3 server.py' };
            });
    }

    function checkServer() {
        api('/api/ping').then(function (d) {
            var dot = document.getElementById('serverDot');
            var st = document.getElementById('serverStatus');
            if (d.ok) {
                dot.classList.add('on');
                st.textContent = 'J.A.R.V.I.S. online';
            } else {
                dot.classList.remove('on');
                st.textContent = 'Server offline';
            }
        });
    }

    // ── Helpers ────────────────────────────────────────────
    function after(text, kws) {
        for (var i = 0; i < kws.length; i++) {
            var idx = text.toLowerCase().indexOf(kws[i]);
            if (idx !== -1) {
                var r = text.substring(idx + kws[i].length).trim();
                if (r.length > 0) return r;
            }
        }
        return null;
    }

    function reply(text) { addMsg('jarvis', text); say(text); }

    function joke() {
        var js = [
            'A SQL query walks into a bar, sees two tables and asks: "Can I join you?"',
            'There are only 10 types of people in the world: those who understand binary and those who don\'t.',
            'Why do programmers prefer dark mode? Because light attracts bugs.',
            'A programmer\'s wife tells him: "Go to the store and buy a loaf of bread. If they have eggs, buy a dozen." He comes home with 12 loaves.',
            'Debugging is like being the detective in a crime movie where you are also the murderer.',
            'There are only two hard things in CS: cache invalidation and naming things.',
            'It works on my machine. Then we ship it and the user\'s machine catches fire.',
            'I don\'t have mass. I have a gravitational personality.',
        ];
        reply(js[Math.floor(Math.random() * js.length)]);
    }

    // ── UI Updates ─────────────────────────────────────────
    function setStatus(text) {
        var el = document.getElementById('status');
        if (el) el.textContent = text;
    }

    function setTranscript(text, isFinal) {
        var el = document.getElementById('transcript');
        if (el) {
            el.textContent = text;
            el.className = 'transcript' + (isFinal ? ' final' : '');
        }
    }

    function addMsg(role, text) {
        var chat = document.getElementById('chat');
        if (!chat) return;

        var div = document.createElement('div');
        div.className = 'msg ' + role;

        var label = role === 'user' ? 'You' : 'J.A.R.V.I.S.';
        var time = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

        div.innerHTML = '<div class="msg-label">' + label + '</div>'
            + '<div class="msg-text">' + esc(text) + '</div>'
            + '<div class="msg-time">' + time + '</div>';

        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;

        // Keep max 30 messages
        while (chat.children.length > 30) chat.removeChild(chat.firstChild);
    }

    function renderChat() {
        var chat = document.getElementById('chat');
        if (!chat) return;
        chat.innerHTML = '';
        chatHist.slice(-15).forEach(function (m) {
            var div = document.createElement('div');
            div.className = 'msg ' + m.role;
            var label = m.role === 'user' ? 'You' : 'J.A.R.V.I.S.';
            div.innerHTML = '<div class="msg-label">' + label + '</div>'
                + '<div class="msg-text">' + esc(m.content) + '</div>';
            chat.appendChild(div);
        });
        chat.scrollTop = chat.scrollHeight;
    }

    function esc(t) { var d = document.createElement('div'); d.textContent = t; return d.innerHTML; }

    // ── UI Bindings ────────────────────────────────────────
    function bindUI() {
        // Mic
        document.getElementById('micBtn').addEventListener('click', function () {
            if (!recognition) { setStatus('⚠️ Microphone unavailable'); return; }
            if (listening) recognition.stop();
            else { try { recognition.start(); } catch (e) {} }
        });

        // Text input
        var inp = document.getElementById('textInput');
        var btn = document.getElementById('sendBtn');
        function send() {
            var t = inp.value.trim();
            if (t) { processInput(t); inp.value = ''; inp.focus(); }
        }
        btn.addEventListener('click', send);
        inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); send(); } });

        // Quick commands
        document.querySelectorAll('.qbtn').forEach(function (b) {
            b.addEventListener('click', function () {
                var cmd = this.getAttribute('data-cmd');
                if (cmd) processInput(cmd);
            });
        });

        // Visualizer
        setInterval(function () {
            document.getElementById('visualizer').classList.toggle('active', listening || speaking);
        }, 300);
    }

    // ── Start ──────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', init);
})();
