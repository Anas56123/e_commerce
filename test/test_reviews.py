"""
Tests for Course Review endpoints:
  GET  /api/v1/reviews/{course_id}
  POST /api/v1/reviews/{course_id}
"""
import pytest
from conftest import auth_headers


class TestReviews:
    def test_get_reviews_no_auth(self, client):
        """Anyone can read reviews — no auth required."""
        resp = client.get("/api/v1/reviews/1")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_reviews_nonexistent_course(self, client):
        """Non-existent course → empty list (router doesn't 404 on GET)."""
        resp = client.get("/api/v1/reviews/999999")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_add_review_unauthenticated(self, client):
        resp = client.post("/api/v1/reviews/1", json={"course_id": 1, "rating": 5})
        assert resp.status_code == 401

    def test_add_review_nonexistent_course(self, client, student_token):
        resp = client.post(
            "/api/v1/reviews/999999",
            json={"course_id": 999999, "rating": 4, "comment": "Nice"},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Course not found"

    def test_add_review_not_enrolled(self, client, instructor_token, student_token):
        """Must be enrolled to leave a review."""
        # Create a course but don't enroll the student
        c = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Review Course", "description": "desc", "price": 10.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        resp = client.post(
            f"/api/v1/reviews/{course_id}",
            json={"course_id": course_id, "rating": 5, "comment": "Great!"},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 403
        assert "enrolled" in resp.json()["detail"].lower()

    def test_add_review_invalid_rating(self, client, instructor_token, student_token):
        """Rating must be 1-5."""
        c = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Rating Course", "description": "desc", "price": 0.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        # Enroll the student first
        client.post(f"/api/v1/enrollments/{course_id}", headers=auth_headers(student_token))

        resp = client.post(
            f"/api/v1/reviews/{course_id}",
            json={"course_id": course_id, "rating": 6, "comment": "Too good!"},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 400
        assert "Rating" in resp.json()["detail"]

    def test_add_review_success_and_duplicate(self, client, instructor_token, student_token):
        """Successful review + duplicate review rejected."""
        c = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Success Review Course", "description": "desc", "price": 0.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        # Enroll
        client.post(f"/api/v1/enrollments/{course_id}", headers=auth_headers(student_token))

        # First review — should succeed
        resp = client.post(
            f"/api/v1/reviews/{course_id}",
            json={"course_id": course_id, "rating": 4, "comment": "Good course"},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 200
        assert resp.json()["rating"] == 4

        # Duplicate review — should be rejected
        dup = client.post(
            f"/api/v1/reviews/{course_id}",
            json={"course_id": course_id, "rating": 3, "comment": "Changed mind"},
            headers=auth_headers(student_token),
        )
        assert dup.status_code == 400
        assert "already reviewed" in dup.json()["detail"].lower()
