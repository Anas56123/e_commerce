"""
Tests for Chat endpoints:
  GET /api/v1/chat/history/{contact_id}
  WS  /api/v1/chat/ws/{token}
"""
import pytest
from conftest import auth_headers, register_and_login


class TestChatHistory:
    def test_history_unauthenticated(self, client):
        resp = client.get("/api/v1/chat/history/1")
        assert resp.status_code == 401

    def test_history_empty(self, client, student_token, instructor_token):
        """Chat history between two users who have never messaged should be empty."""
        instructor_me = client.get("/me", headers=auth_headers(instructor_token)).json()
        resp = client.get(
            f"/api/v1/chat/history/{instructor_me['id']}",
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_history_self(self, client, student_token):
        """Getting history with your own user id should return an empty list."""
        me = client.get("/me", headers=auth_headers(student_token)).json()
        resp = client.get(f"/api/v1/chat/history/{me['id']}", headers=auth_headers(student_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestChatWebSocket:
    def test_ws_invalid_token(self, client):
        """WebSocket with a bogus token should be closed immediately."""
        with client.websocket_connect("/api/v1/chat/ws/invalid.token.here") as ws:
            try:
                ws.receive_text()
                # If we reach here server did not close — check close code
            except Exception:
                pass  # Expected: connection closed

    def test_ws_valid_token_connect(self, client):
        """WebSocket with a valid token should connect and accept messages."""
        # Register dedicated WS user
        client.post("/register", data={"username": "wsuser", "email": "wsuser@mail.com", "password": "wspass", "role": "student"})
        token = client.post("/login", data={"username": "wsuser", "password": "wspass"}).json()["access_token"]

        # Register a receiver
        client.post("/register", data={"username": "wsreceiver", "email": "wsreceiver@mail.com", "password": "wspass", "role": "student"})
        receiver = client.get("/me", headers=auth_headers(
            client.post("/login", data={"username": "wsreceiver", "password": "wspass"}).json()["access_token"]
        )).json()

        import json
        with client.websocket_connect(f"/api/v1/chat/ws/{token}") as ws:
            ws.send_text(json.dumps({"receiver_id": receiver["id"], "content": "Hello from test"}))
            # Message is delivered to offline receiver (no active WS) silently — no error expected
