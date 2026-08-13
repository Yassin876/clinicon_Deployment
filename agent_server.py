"""
agent_server.py
سيرفر HTTP يلف الـ Agent (orchestrator) — عشان الفرونت يقدر يكلّمه.

الفرونت بيبعت POST /chat مع {\"message\": \"...\"} وهيرجعله {\"reply\": \"...\"}
بيستخدم الـ Authorization header لتمرير توكن المريض الفعلي.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import time

from langchain_core.messages import SystemMessage
from app.orchestrator import create_agent, chat

# Per-session agents — keyed by session_id
sessions: dict = {}
SESSION_TIMEOUT = 3600  # 1 hour


def _get_or_create_session(session_id: str, patient_token: str = None) -> dict:
    """Get existing session or create a new one with the patient token."""
    if session_id in sessions:
        sessions[session_id]["last_active"] = time.time()
        # Update token if a new one comes in (e.g. refresh)
        if patient_token:
            sessions[session_id]["patient_token"] = patient_token
        return sessions[session_id]

    session = {
        "agent": create_agent(patient_token=patient_token),
        "user_set": False,
        "last_active": time.time(),
        "patient_token": patient_token,
    }
    sessions[session_id] = session
    return session


def _cleanup_old_sessions():
    """Remove sessions older than SESSION_TIMEOUT."""
    now = time.time()
    expired = [sid for sid, s in sessions.items() if now - s["last_active"] > SESSION_TIMEOUT]
    for sid in expired:
        del sessions[sid]


def _extract_token(handler: "AgentHandler") -> str:
    """استخرج الـ JWT Token من الـ Authorization header."""
    auth = handler.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):]
    return ""


class AgentHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError) as e:
            print(f"  [agent] Client disconnected before response was sent ({e})")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            return self._send_json({"status": "ok", "model": "agent", "active_sessions": len(sessions)})
        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        session_id = body.get("session_id", "default")
        # استخرج التوكن من الـ header أولاً، ثم من الـ body كـ fallback
        patient_token = _extract_token(self) or body.get("patient_token", "")

        if self.path == "/chat":
            message = body.get("message", "")

            if not message:
                return self._send_json({"error": "message مطلوب"}, 400)

            state = _get_or_create_session(session_id, patient_token=patient_token)

            # لو الفرونت بعت بيانات المستخدم (أول رسالة بس)
            if not state["user_set"]:
                user_name = body.get("user_name", "")
                if user_name:
                    ctx = f"[معلومات المريض الحالي] الاسم: {user_name}. لو احتجت اسمه في الحجز استخدم الاسم ده مباشرة من غير ما تسأله."
                    state["agent"]["history"].append(SystemMessage(content=ctx))
                    state["user_set"] = True
                    print(f"  [agent] User context ({session_id}): {user_name}")

            try:
                reply = chat(state["agent"], message, patient_token=patient_token or None)
                _cleanup_old_sessions()
                return self._send_json({"reply": reply})
            except Exception as e:
                import traceback
                print(f"  [agent] Error ({session_id}): {e}")
                traceback.print_exc()
                return self._send_json({"reply": "حصلت مشكلة — جرّب تاني كمان شوية."})

        if self.path == "/reset":
            if session_id in sessions:
                del sessions[session_id]
            return self._send_json({"message": "تم بدء محادثة جديدة"})

        self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        print(f"  [agent] {args[0]}")


if __name__ == "__main__":
    import sys
    PORT = 8200
    print(f"[Agent] Starting on http://localhost:{PORT}")
    print(f"[Agent] Loading LangChain / Ollama (this may take 60-90 seconds)...")
    print(f"[Agent] POST /chat  — send message (with session_id + Authorization header)")
    print(f"[Agent] POST /reset — new conversation")
    print()
    sys.stdout.flush()

    server = ThreadingHTTPServer(("0.0.0.0", PORT), AgentHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nاتوقّف.")
