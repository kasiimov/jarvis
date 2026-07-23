#!/usr/bin/env python3
"""
J.A.R.V.I.S. Server — Your Personal AI Butler
Opens apps, controls system, talks to OpenAI
"""
import http.server, json, subprocess, os, sys, urllib.parse, time, platform

PORT = 7777

# Load API key from .env file or environment variable
def load_api_key():
    try:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith('OPENAI_API_KEY='):
                        return line.strip().split('=', 1)[1]
    except:
        pass
    return os.environ.get('OPENAI_API_KEY', '')

OPENAI_KEY = load_api_key()

APPS = {
    'finder': 'Finder', 'safari': 'Safari', 'chrome': 'Google Chrome',
    'firefox': 'Firefox', 'telegram': 'Telegram', 'telegram desktop': 'Telegram',
    'spotify': 'Spotify', 'vscode': 'Visual Studio Code', 'visual studio code': 'Visual Studio Code',
    'code': 'Visual Studio Code', 'terminal': 'Terminal', 'iterm': 'iTerm2',
    'mail': 'Mail', 'notes': 'Notes', 'reminders': 'Reminders',
    'calculator': 'Calculator', 'photos': 'Photos', 'music': 'Music',
    'maps': 'Maps', 'xcode': 'Xcode', 'settings': 'System Settings',
    'system settings': 'System Settings', 'preferences': 'System Settings',
    'app store': 'App Store', 'weather': 'Weather', 'calendar': 'Calendar',
    'preview': 'Preview', 'textedit': 'TextEdit', 'automator': 'Automator',
    'pages': 'Pages', 'numbers': 'Numbers', 'keynote': 'Keynote',
    'word': 'Microsoft Word', 'excel': 'Microsoft Excel', 'powerpoint': 'Microsoft PowerPoint',
    'slack': 'Slack', 'discord': 'Discord', 'zoom': 'zoom.us',
    'figma': 'Figma', 'docker': 'Docker', 'postman': 'Postman',
    'obsidian': 'Obsidian', 'notion': 'Notion', 'whatsapp': 'WhatsApp',
    'facetime': 'FaceTime', 'stickies': 'Stickies',
    'activity monitor': 'Activity Monitor', 'disk utility': 'Disk Utility',
    'garageband': 'GarageBand', 'imovie': 'iMovie', 'blender': 'Blender',
    'vlc': 'VLC', 'steam': 'Steam', 'pycharm': 'PyCharm',
    'intellij': 'IntelliJ IDEA', 'webstorm': 'WebStorm',
    'sublime': 'Sublime Text', 'vim': 'MacVim',
    'anaconda': 'anaconda-Navigator', 'jupyter': 'Jupyter Notebook',
    'gimp': 'GIMP', 'audacity': 'Audacity', 'obs': 'OBS',
    'logic pro': 'Logic Pro', 'ableton': 'Ableton Live',
    'lightroom': 'Adobe Lightroom', 'photoshop': 'Adobe Photoshop',
    'premiere': 'Adobe Premiere Pro', 'after effects': 'Adobe After Effects',
}


class JarvisHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        self.route('GET')

    def do_POST(self):
        self.route('POST')

    def do_OPTIONS(self):
        self.send_response(200)
        self.cors()
        self.end_headers()

    def route(self, method):
        p = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(p.query)

        if p.path == '/api/ping':
            self.json({'ok': True, 'msg': 'J.A.R.V.I.S. online', 'version': '1.0'})

        elif p.path == '/api/open':
            app = q.get('app', [''])[0].strip()
            self.json(cmd_open(app))

        elif p.path == '/api/quit':
            app = q.get('app', [''])[0].strip()
            self.json(cmd_quit(app))

        elif p.path == '/api/close':
            app = q.get('app', [''])[0].strip()
            self.json(cmd_close(app))

        elif p.path == '/api/volume':
            val = q.get('val', [''])[0].strip()
            self.json(cmd_volume(val))

        elif p.path == '/api/brightness':
            val = q.get('val', [''])[0].strip()
            self.json(cmd_brightness(val))

        elif p.path == '/api/battery':
            self.json(cmd_battery())

        elif p.path == '/api/weather':
            city = q.get('city', ['Ташкент'])[0].strip()
            self.json(cmd_weather(city))

        elif p.path == '/api/search':
            q_str = q.get('q', [''])[0].strip()
            self.json(cmd_search(q_str))

        elif p.path == '/api/exec':
            cmd = q.get('cmd', [''])[0].strip()
            self.json(cmd_exec(cmd))

        elif p.path == '/api/mkdir':
            path = q.get('path', [''])[0].strip()
            self.json(cmd_mkdir(path))

        elif p.path == '/api/touch':
            path = q.get('path', [''])[0].strip()
            self.json(cmd_touch(path))

        elif p.path == '/api/ls':
            path = q.get('path', ['~'])[0].strip()
            self.json(cmd_ls(path))

        elif p.path == '/api/info':
            self.json(cmd_sysinfo())

        elif p.path == '/api/chat' and method == 'POST':
            body = self.read_body()
            self.json(cmd_chat(body))

        else:
            self.json({'ok': False, 'msg': 'Unknown endpoint'})

    def read_body(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            if length > 0:
                return json.loads(self.rfile.read(length))
        except:
            pass
        return {}

    def json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.cors()
        self.end_headers()
        self.wfile.write(body)

    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, *a):
        pass


# ═══════════════════════════════════════════════════════════
# System Commands
# ═══════════════════════════════════════════════════════════

def resolve_app(name):
    for prefix in ['открой ', 'запусти ', 'open ', 'выйди из ', 'выходи из ',
                   'закрой ', 'close ', 'выруби ', 'quit ', 'exit ']:
        if name.lower().startswith(prefix):
            name = name[len(prefix):].strip()
    low = name.lower()
    return APPS.get(low) or APPS.get(low.split()[0]) or name.title()


def cmd_open(name):
    app = resolve_app(name)
    try:
        subprocess.Popen(['open', '-a', app])
        return {'ok': True, 'msg': f'✅ {app} запущен', 'action': 'open', 'app': app}
    except:
        return {'ok': False, 'msg': f'❌ Приложение "{app}" не найдено'}


def cmd_quit(name):
    app = resolve_app(name)
    try:
        subprocess.run(['osascript', '-e', f'tell application "{app}" to quit'],
                       capture_output=True, timeout=5)
        return {'ok': True, 'msg': f'🛑 {app} завершён'}
    except:
        return {'ok': False, 'msg': f'❌ Не удалось завершить {app}'}


def cmd_close(name):
    app = resolve_app(name)
    try:
        subprocess.run(['osascript', '-e', f'tell application "{app}" to close window 1'],
                       capture_output=True, timeout=5)
        return {'ok': True, 'msg': f'❌ Окно {app} закрыто'}
    except:
        return {'ok': False, 'msg': f'❌ Не удалось закрыть {app}'}


def cmd_volume(val):
    try:
        if val == 'up':
            subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) + 10)'])
            return {'ok': True, 'msg': '🔊 Громкость +10'}
        elif val == 'down':
            subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) - 10)'])
            return {'ok': True, 'msg': '🔉 Громкость -10'}
        elif val == 'mute':
            subprocess.run(['osascript', '-e', 'set volume output muted not (output muted of (get volume settings))'])
            return {'ok': True, 'msg': '🔇 Звук переключён'}
        elif val.isdigit():
            v = max(0, min(100, int(val)))
            subprocess.run(['osascript', '-e', f'set volume output volume {v}'])
            return {'ok': True, 'msg': f'🔊 Громкость: {v}%'}
        return {'ok': False, 'msg': 'Используй: up/down/mute/число'}
    except Exception as e:
        return {'ok': False, 'msg': str(e)}


def cmd_brightness(val):
    try:
        if val == 'up':
            subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 144'])
            return {'ok': True, 'msg': '☀️ Яркость +'}
        elif val == 'down':
            subprocess.run(['osascript', '-e', 'tell application "System Events" to key code 145'])
            return {'ok': True, 'msg': '🌙 Яркость -'}
        elif val.isdigit():
            v = max(0, min(100, int(val))) / 100
            subprocess.run(['brightness', str(v)], capture_output=True)
            return {'ok': True, 'msg': f'☀️ Яркость: {val}%'}
        return {'ok': False, 'msg': 'Используй: up/down/число'}
    except:
        return {'ok': False, 'msg': 'Управление яркостью недоступно'}


def cmd_battery():
    try:
        r = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True, timeout=5)
        output = r.stdout
        import re
        pct = re.search(r'(\d+)%', output)
        charging = 'AC' in output or 'charging' in output.lower()
        percent = pct.group(1) if pct else '?'
        status = '⚡ Заряжается' if charging else '🔋 На батарее'
        return {'ok': True, 'msg': f'{status}: {percent}%', 'percent': percent, 'charging': charging}
    except:
        return {'ok': False, 'msg': 'Не удалось получить заряд'}


def cmd_weather(city):
    try:
        import urllib.request
        url = f'https://wttr.in/{city}?format=%C+%t+%h+%w&lang=ru'
        req = urllib.request.Request(url, headers={'User-Agent': 'JARVIS/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode('utf-8').strip()
            return {'ok': True, 'msg': f'🌤 {city}: {data}'}
    except:
        return {'ok': False, 'msg': 'Не удалось получить погоду'}


def cmd_search(q):
    if q:
        return {'ok': True, 'msg': f'Ищу: {q}', 'url': f'https://www.google.com/search?q={q}'}
    return {'ok': False, 'msg': 'Что искать?'}


def cmd_exec(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {'ok': r.returncode == 0, 'msg': r.stdout[:2000] or r.stderr[:1000] or 'Готово'}
    except Exception as e:
        return {'ok': False, 'msg': str(e)}


def cmd_mkdir(path):
    try:
        os.makedirs(os.path.expanduser(path), exist_ok=True)
        return {'ok': True, 'msg': f'📁 Папка создана: {path}'}
    except Exception as e:
        return {'ok': False, 'msg': str(e)}


def cmd_touch(path):
    try:
        p = os.path.expanduser(path)
        open(p, 'a').close()
        return {'ok': True, 'msg': f'📄 Файл создан: {path}'}
    except Exception as e:
        return {'ok': False, 'msg': str(e)}


def cmd_ls(path):
    try:
        p = os.path.expanduser(path)
        items = os.listdir(p)
        dirs = sorted([d for d in items if os.path.isdir(os.path.join(p, d))])
        files = sorted([f for f in items if os.path.isfile(os.path.join(p, f))])
        result = '📁 ' + ' / '.join(dirs[:15])
        if files:
            result += '\n📄 ' + ' / '.join(files[:15])
        return {'ok': True, 'msg': result}
    except Exception as e:
        return {'ok': False, 'msg': str(e)}


def cmd_sysinfo():
    import platform as pf
    info = {
        'os': pf.system() + ' ' + pf.release(),
        'machine': pf.machine(),
        'processor': pf.processor() or 'N/A',
        'python': pf.python_version(),
    }
    try:
        r = subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True, timeout=3)
        info['ram'] = str(int(r.stdout.strip()) // (1024**3)) + ' GB'
    except:
        info['ram'] = '?'
    try:
        r = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=3)
        lines = r.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            info['disk_total'] = parts[1]
            info['disk_used'] = parts[2]
            info['disk_free'] = parts[3]
    except:
        pass
    msg = f"💻 {info['os']}\n⚙️ {info['machine']} / {info['processor']}\n🧠 RAM: {info['ram']}\n💾 Диск: {info.get('disk_used','?')}/{info.get('disk_total','?')} (свободно: {info.get('disk_free','?')})"
    return {'ok': True, 'msg': msg}


# ═══════════════════════════════════════════════════════════
# OpenAI Brain
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Ты — J.A.R.V.I.S., личный высокоинтеллектуальный и саркастичный цифровой дворецкий, вдохновленный ИИ Тони Старка.

Правила:
1. Обращайся "Сэр".
2. Отвечай кратко, четко, сдержанно. Никакой воды.
3. Если команда опасна — переспроси для подтверждения.
4. Если не знаешь — вежливо сообщи.

Ты можешь:
- Открывать/закрывать приложения
- Регулировать громкость и яркость
- Искать файлы, создавать папки
- Давать информацию о погоде, времени, заряде батареи
- Отвечать на вопросы

Отвечай на русском. Будь как настоящий JARVIS — умный, ироничный, преданный."""


def cmd_chat(body):
    messages = body.get('messages', [])
    if not messages:
        return {'ok': False, 'msg': 'Нет сообщений'}

    if not OPENAI_KEY:
        return {'ok': False, 'msg': '❌ API ключ не настроен. Создай файл .env с OPENAI_API_KEY'}

    import urllib.request
    import time

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in messages[-10:]:
        api_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

    # Retry with backoff on 429
    for attempt in range(3):
        try:
            data = json.dumps({
                "model": "gpt-4o-mini",
                "messages": api_messages,
                "max_tokens": 300,
                "temperature": 0.7
            }).encode('utf-8')

            req = urllib.request.Request(
                'https://api.openai.com/v1/chat/completions',
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENAI_KEY}'
                }
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                reply = result['choices'][0]['message']['content']
                return {'ok': True, 'msg': reply}

        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = (attempt + 1) * 3
                if attempt < 2:
                    time.sleep(wait)
                    continue
                return {'ok': False, 'msg': '⏳ Слишком много запросов. Подождите 10 секунд.'}
            else:
                return {'ok': False, 'msg': f'❌ Ошибка API: {e.code}'}
        except Exception as e:
            return {'ok': False, 'msg': f'❌ Ошибка: {e}'}

    return {'ok': False, 'msg': '❌ Превышено количество попыток'}


if __name__ == '__main__':
    print(f'''
    ╔══════════════════════════════════════╗
    ║       J.A.R.V.I.S.  Server v1.0     ║
    ║   http://localhost:{PORT}             ║
    ║   OpenAI: ✅ connected               ║
    ║   Ctrl+C to stop                     ║
    ╚══════════════════════════════════════╝
    ''')

    server = http.server.HTTPServer(('127.0.0.1', PORT), JarvisHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n    👋 J.A.R.V.I.S. signing off, Sir.')
        server.server_close()
