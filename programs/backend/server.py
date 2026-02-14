import json
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT_DIR = Path(__file__).resolve().parents[2]
HOST = "0.0.0.0"
PORT = 8000
MAX_MESSAGES = 200

MESSAGES = []
NEXT_ID = 1


def now_unix() -> int:
    return int(time.time())


class ChatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path).path

        if parsed_path == "/api/messages":
            self.respond_json({"messages": MESSAGES})
            return

        static_path = self.resolve_static_path(parsed_path)
        if static_path and static_path.is_file():
            self.respond_file(static_path)
            return

        self.respond_text("Not Found", HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed_path = urlparse(self.path).path
        if parsed_path != "/api/messages":
            self.respond_text("Not Found", HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        payload = self.parse_json(raw_body)
        if payload is None:
            self.respond_text("Invalid JSON", HTTPStatus.BAD_REQUEST)
            return

        name = str(payload.get("name", "")).strip()[:20]
        text = str(payload.get("text", "")).strip()[:200]
        if not name or not text:
            self.respond_text("name and text are required", HTTPStatus.BAD_REQUEST)
            return

        self.add_message(name=name, text=text)
        self.respond_json({"ok": True}, HTTPStatus.CREATED)

    def resolve_static_path(self, requested_path: str):
        path = "/" if requested_path == "" else requested_path
        relative = "index.html" if path == "/" else path.lstrip("/")
        candidate = (ROOT_DIR / relative).resolve()

        # Prevent path traversal outside workspace root.
        if ROOT_DIR not in candidate.parents and candidate != ROOT_DIR:
            return None
        return candidate

    def respond_file(self, file_path: Path):
        suffix = file_path.suffix.lower()
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(suffix, "application/octet-stream")

        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_text(self, text: str, status=HTTPStatus.OK):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def parse_json(self, raw_body: bytes):
        try:
            return json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    def add_message(self, name: str, text: str):
        global NEXT_ID
        MESSAGES.append(
            {
                "id": NEXT_ID,
                "name": name,
                "text": text,
                "timestamp": now_unix(),
            }
        )
        NEXT_ID += 1
        if len(MESSAGES) > MAX_MESSAGES:
            del MESSAGES[:-MAX_MESSAGES]

    def log_message(self, format, *args):
        return


def run():
    server = ThreadingHTTPServer((HOST, PORT), ChatHandler)
    print(f"Chat server running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
