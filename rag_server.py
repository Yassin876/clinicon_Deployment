"""
rag_server.py
سيرفر بسيط يعرض نظام الـ RAG كـ API.
الـ Agent بينده على POST /search عشان يجاوب على الأسئلة الطبية.

شغّله في terminal منفصل:
  python rag_server.py
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json

from rag.vector_store import init_store
from rag.chatbot import answer


class RAGHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            print("  [rag] Client disconnected before response was sent")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path == "/search":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            query = body.get("query", "")
            if not query:
                return self._send_json({"error": "query مطلوب"}, 400)
            try:
                result = answer(query)
                return self._send_json(result)
            except Exception as e:
                print(f"  [rag] Error: {e}")
                return self._send_json({"error": str(e)}, 500)

        self._send_json({"error": "not found"}, 404)

    def do_GET(self):
        if self.path == "/health":
            return self._send_json({"status": "ok"})
        if self.path == "/rebuild":
            print("[RAG] Rebuilding vector store...")
            init_store(force_rebuild=True)
            return self._send_json({"status": "rebuilt", "message": "Vector store rebuilt successfully"})
        self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        print(f"  [rag] {args[0]}")


if __name__ == "__main__":
    import sys
    PORT = 8100
    force = "--rebuild" in sys.argv

    print("[RAG] Initializing vector store..." + (" (FORCE REBUILD)" if force else ""))
    init_store(force_rebuild=force)

    server = ThreadingHTTPServer(("0.0.0.0", PORT), RAGHandler)
    print(f"[RAG] Server running on http://localhost:{PORT}")
    print("اضغط Ctrl+C عشان توقّفه")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nاتوقّف.")
