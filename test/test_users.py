"""
Tests for User endpoints:
  POST /register
  POST /login
  GET  /me
  GET  /all_users
  GET  /user/{id}
  PUT  /update_user/{id}
  DELETE /delete_user/{id}
  POST /forgot-password
  POST /reset-password
"""
import pytest
from conftest import auth_headers


# --------------------------------------------------------------------------- #
#  Registration                                                               #
# --------------------------------------------------------------------------- #

class TestRegister:
    def test_register_success(self, client):
        resp = client.post(
            "/register",
            data={"username": "newuser1", "email": "newuser1@mail.com", "password": "pass1234", "role": "student"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "newuser1"
        assert body["email"] == "newuser1@mail.com"
        assert body["role"] == "student"

    def test_register_duplicate_username(self, client):
        # First registration
        client.post("/register", data={"username": "dupuser", "email": "dup1@mail.com", "password": "pass", "role": "student"})
        # Second with same username
        resp = client.post("/register", data={"username": "dupuser", "email": "dup2@mail.com", "password": "pass", "role": "student"})
        assert resp.status_code == 400
        assert "Username already registered" in resp.json()["detail"]

    def test_register_duplicate_email(self, client):
        client.post("/register", data={"username": "emailuser1", "email": "shared@mail.com", "password": "pass", "role": "student"})
        resp = client.post("/register", data={"username": "emailuser2", "email": "shared@mail.com", "password": "pass", "role": "student"})
        assert resp.status_code == 400
        assert "Email already registered" in resp.json()["detail"]

    def test_register_invalid_role_rejected(self, client):
        """FastAPI validates the UserRole enum at the framework level.
        An unknown role like 'admin' is rejected with 422 before the handler runs."""
        resp = client.post(
            "/register",
            data={"username": "roleuser", "email": "roleuser@mail.com", "password": "pass", "role": "admin"},
        )
        assert resp.status_code == 422


# --------------------------------------------------------------------------- #
#  Login                                                                      #
# --------------------------------------------------------------------------- #

class TestLogin:
    def test_login_success(self, client):
        client.post("/register", data={"username": "loginuser", "email": "login@mail.com", "password": "secret", "role": "student"})
        resp = client.post("/login", data={"username": "loginuser", "password": "secret"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/register", data={"username": "wrongpass", "email": "wp@mail.com", "password": "correct", "role": "student"})
        resp = client.post("/login", data={"username": "wrongpass", "password": "wrong"})
        assert resp.status_code == 403

    def test_login_nonexistent_user(self, client):
        resp = client.post("/login", data={"username": "ghost", "password": "nope"})
        assert resp.status_code == 403


# --------------------------------------------------------------------------- #
#  /me                                                                        #
# --------------------------------------------------------------------------- #

class TestGetMe:
    def test_get_me_authenticated(self, client, student_token):
        resp = client.get("/me", headers=auth_headers(student_token))
        assert resp.status_code == 200
        assert "username" in resp.json()

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/me")
        assert resp.status_code == 401


# --------------------------------------------------------------------------- #
#  /all_users (instructor only)                                               #
# --------------------------------------------------------------------------- #

class TestGetAllUsers:
    def test_all_users_as_instructor(self, client, instructor_token):
        resp = client.get("/all_users", headers=auth_headers(instructor_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_all_users_as_student_forbidden(self, client, student_token):
        resp = client.get("/all_users", headers=auth_headers(student_token))
        assert resp.status_code == 403

    def test_all_users_unauthenticated(self, client):
        resp = client.get("/all_users")
        assert resp.status_code == 401


# --------------------------------------------------------------------------- #
#  /user/{id}                                                                 #
# --------------------------------------------------------------------------- #

class TestGetUserById:
    def test_get_user_by_valid_id(self, client, student_token):
        # Get own profile first to learn the id
        me = client.get("/me", headers=auth_headers(student_token)).json()
        resp = client.get(f"/user/{me['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == me["id"]

    def test_get_user_nonexistent(self, client):
        resp = client.get("/user/999999")
        assert resp.status_code == 404


# --------------------------------------------------------------------------- #
#  /update_user/{id}                                                          #
# --------------------------------------------------------------------------- #

class TestUpdateUser:
    def test_update_own_user(self, client, student_token):
        me = client.get("/me", headers=auth_headers(student_token)).json()
        resp = client.put(
            f"/update_user/{me['id']}",
            json={"username": "updated_student"},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "updated_student"

    def test_update_other_user_forbidden(self, client, student_token, instructor_token):
        # instructor's id
        instructor_me = client.get("/me", headers=auth_headers(instructor_token)).json()
        resp = client.put(
            f"/update_user/{instructor_me['id']}",
            json={"username": "hacked"},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 403


# --------------------------------------------------------------------------- #
#  /delete_user/{id}                                                          #
# --------------------------------------------------------------------------- #

class TestDeleteUser:
    def test_delete_own_user(self, client):
        # Register a temp user to delete
        client.post("/register", data={"username": "todelete", "email": "todelete@mail.com", "password": "pass", "role": "student"})
        token = client.post("/login", data={"username": "todelete", "password": "pass"}).json()["access_token"]
        me = client.get("/me", headers=auth_headers(token)).json()
        resp = client.delete(f"/delete_user/{me['id']}", headers=auth_headers(token))
        assert resp.status_code == 204

    def test_delete_nonexistent_user(self, client, instructor_token):
        resp = client.delete("/delete_user/999999", headers=auth_headers(instructor_token))
        assert resp.status_code == 404


# --------------------------------------------------------------------------- #
#  Password Reset                                                             #
# --------------------------------------------------------------------------- #

class TestForgotResetPassword:
    def test_forgot_password_nonexistent_email(self, client):
        resp = client.post("/forgot-password", json={"email": "nobody@mail.com"})
        assert resp.status_code == 404

    def test_forgot_password_valid_email(self, client):
        # Register a user
        client.post("/register", data={"username": "resetme", "email": "resetme@mail.com", "password": "pass", "role": "student"})
        resp = client.post("/forgot-password", json={"email": "resetme@mail.com"})
        assert resp.status_code == 200
        assert "reset_token" in resp.json()

    def test_reset_password_invalid_token(self, client):
        resp = client.post("/reset-password", json={"token": "invalid.token.here", "new_password": "newpass"})
        assert resp.status_code == 400

    def test_reset_password_valid_flow(self, client):
        client.post("/register", data={"username": "resetflow", "email": "resetflow@mail.com", "password": "oldpass", "role": "student"})
        token_resp = client.post("/forgot-password", json={"email": "resetflow@mail.com"})
        reset_token = token_resp.json()["reset_token"]

        resp = client.post("/reset-password", json={"token": reset_token, "new_password": "newpass123"})
        assert resp.status_code == 200

        # Verify new password works
        login_resp = client.post("/login", data={"username": "resetflow", "password": "newpass123"})
        assert login_resp.status_code == 200
