"""Local-only static + Python API server. No package installation required."""
import os
import sys
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api.product_match import handler as APIHandler


def load_environment():
    path = ROOT / '.env.local'
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            if key.strip() in ('CODYSSEY_BASE_URL', 'CODYSSEY_API_KEY', 'CODYSSEY_MODEL'):
                os.environ.setdefault(key.strip(), value.strip().strip('\"\''))


class LocalHandler(APIHandler, SimpleHTTPRequestHandler):
    fixture = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/product_match':
            return APIHandler.do_GET(self)
        allowed = path in ('/', '/index.html', '/upload.html', '/detail.html', '/about.html') or path.startswith(('/css/', '/js/', '/images/'))
        resolved = Path(self.translate_path(self.path)).resolve()
        if not allowed or (resolved != ROOT and ROOT not in resolved.parents) or '..' in path or not resolved.is_file() and path != '/':
            self.send_error(404)
            return
        if self.fixture and (path == '/' or path.endswith('.html')):
            content = (ROOT / ('index.html' if path == '/' else path.lstrip('/'))).read_text()
            content = content.replace('<body ', '<body ').replace('<div class="page-shell">', '<p style="background:#fff7ce;padding:12px;text-align:center">UI TEST · 모의 AI 응답 — 실제 Codyssey 호출 아님</p><div class="page-shell">', 1)
            body = content.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_HEAD(self):
        self.send_error(405)

    def do_POST(self):
        if urlsplit(self.path).path != '/api/product_match':
            self.send_error(404)
            return
        return APIHandler.do_POST(self)


def serve(port=8080, handler=LocalHandler):
    load_environment()
    server = ThreadingHTTPServer(('127.0.0.1', port), handler)
    print(f'SLIG: http://127.0.0.1:{port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    serve()
