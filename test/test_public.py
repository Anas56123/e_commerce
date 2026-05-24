"""
Tests for Public endpoints:
  GET  /api/v1/public/about
  POST /api/v1/public/contact
  GET  /api/v1/public/careers
  POST /api/v1/public/careers/{job_id}/apply
"""
import io
import pytest


class TestAbout:
    def test_get_about_no_auth(self, client):
        resp = client.get("/api/v1/public/about")
        assert resp.status_code == 200
        body = resp.json()
        assert "title" in body
        assert "description" in body
        assert "mission" in body
        assert "team" in body

    def test_about_team_is_list(self, client):
        body = client.get("/api/v1/public/about").json()
        assert isinstance(body["team"], list)


class TestContact:
    def test_submit_contact_form(self, client):
        resp = client.post(
            "/api/v1/public/contact",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Test Subject",
                "message": "Hello team!",
            },
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_submit_contact_missing_fields(self, client):
        resp = client.post("/api/v1/public/contact", json={"name": "John"})
        assert resp.status_code == 422  # Pydantic validation error


class TestCareers:
    def test_get_careers_no_auth(self, client):
        resp = client.get("/api/v1/public/careers")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_apply_nonexistent_job(self, client):
        resp = client.post(
            "/api/v1/public/careers/999999/apply",
            data={
                "applicant_name": "Jane Smith",
                "applicant_email": "jane@example.com",
                "cover_letter": "I am very interested.",
            },
            files={"resume": ("resume.pdf", io.BytesIO(b"fake pdf content"), "application/pdf")},
        )
        assert resp.status_code == 404
        assert "job listing not found" in resp.json()["detail"].lower()

    def test_apply_missing_resume(self, client):
        """Applying without uploading a resume should return 422."""
        resp = client.post(
            "/api/v1/public/careers/1/apply",
            data={
                "applicant_name": "Jane Smith",
                "applicant_email": "jane@example.com",
            },
        )
        assert resp.status_code == 422
