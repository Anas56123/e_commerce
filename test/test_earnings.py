import pytest #type:ignore
from conftest import auth_headers


class TestBalance:
    def test_balance_unauthenticated(self, client):
        resp = client.get("/api/v1/earnings/balance")
        assert resp.status_code == 401

    def test_balance_student_forbidden(self, client, student_token):
        resp = client.get("/api/v1/earnings/balance", headers=auth_headers(student_token))
        assert resp.status_code == 403

    def test_balance_instructor(self, client, instructor_token):
        resp = client.get("/api/v1/earnings/balance", headers=auth_headers(instructor_token))
        assert resp.status_code == 200
        body = resp.json()
        assert "total_earnings" in body
        assert "withdrawn" in body
        assert "available_balance" in body


class TestPayoutMethods:
    def test_get_payout_methods_unauthenticated(self, client):
        resp = client.get("/api/v1/earnings/payout-methods")
        assert resp.status_code == 401

    def test_get_payout_methods_student_forbidden(self, client, student_token):
        resp = client.get("/api/v1/earnings/payout-methods", headers=auth_headers(student_token))
        assert resp.status_code == 403

    def test_get_payout_methods_empty(self, client, instructor_token):
        resp = client.get("/api/v1/earnings/payout-methods", headers=auth_headers(instructor_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_add_payout_method(self, client, instructor_token):
        resp = client.post(
            "/api/v1/earnings/payout-methods",
            json={"provider": "paypal", "account_id": "instructor@paypal.com", "is_default": 1},
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["provider"] == "paypal"
        assert body["is_default"] == 1

    def test_add_payout_method_student_forbidden(self, client, student_token):
        resp = client.post(
            "/api/v1/earnings/payout-methods",
            json={"provider": "stripe", "account_id": "acct_test", "is_default": 0},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 403


class TestWithdrawals:
    def test_withdraw_unauthenticated(self, client):
        resp = client.post("/api/v1/earnings/withdraw", json={"amount": 10.0})
        assert resp.status_code == 401

    def test_withdraw_student_forbidden(self, client, student_token):
        resp = client.post("/api/v1/earnings/withdraw", json={"amount": 10.0}, headers=auth_headers(student_token))
        assert resp.status_code == 403

    def test_withdraw_no_payout_method(self, client):
        client.post("/register", data={"username": "nopayout_inst", "email": "nopayout@mail.com", "password": "pass", "role": "instructor"})
        token = client.post("/login", data={"username": "nopayout_inst", "password": "pass"}).json()["access_token"]
        resp = client.post("/api/v1/earnings/withdraw", json={"amount": 1.0}, headers=auth_headers(token))
        assert resp.status_code == 400

    def test_withdraw_insufficient_funds(self, client, instructor_token):
        resp = client.post(
            "/api/v1/earnings/withdraw",
            json={"amount": 999999.0},
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 400
        assert "insufficient" in resp.json()["detail"].lower()

    def test_get_withdrawals_unauthenticated(self, client):
        resp = client.get("/api/v1/earnings/withdrawals")
        assert resp.status_code == 401

    def test_get_withdrawals_empty_or_list(self, client, instructor_token):
        resp = client.get("/api/v1/earnings/withdrawals", headers=auth_headers(instructor_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
