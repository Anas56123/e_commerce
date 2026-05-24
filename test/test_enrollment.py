"""
Tests for Enrollment endpoints:
  POST /api/v1/enrollments/{course_id}
  GET  /api/v1/enrollments/my-courses
  POST /api/v1/enrollments/progress/{lecture_id}
"""
import pytest
from conftest import auth_headers


class TestEnrollments:
    def test_get_my_courses_unauthenticated(self, client):
        resp = client.get("/api/v1/enrollments/my-courses")
        assert resp.status_code == 401

    def test_get_my_courses_empty(self, client, student_token):
        resp = client.get("/api/v1/enrollments/my-courses", headers=auth_headers(student_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_enroll_nonexistent_course(self, client, student_token):
        resp = client.post("/api/v1/enrollments/999999", headers=auth_headers(student_token))
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Course not found"

    def test_enroll_unauthenticated(self, client):
        resp = client.post("/api/v1/enrollments/1")
        assert resp.status_code == 401

    def test_enroll_idempotent(self, client, student_token, instructor_token):
        """Enrolling in the same course twice should return the existing enrollment."""
        # Create a course to enroll in
        create_resp = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Enroll Test Course", "description": "desc", "price": 0.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if create_resp.status_code != 200:
            pytest.skip("Could not create course (category may not exist in test DB)")

        course_id = create_resp.json()["id"]
        resp1 = client.post(f"/api/v1/enrollments/{course_id}", headers=auth_headers(student_token))
        resp2 = client.post(f"/api/v1/enrollments/{course_id}", headers=auth_headers(student_token))
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["course_id"] == resp2.json()["course_id"]


class TestLectureProgress:
    def test_mark_nonexistent_lecture_complete(self, client, student_token):
        resp = client.post("/api/v1/enrollments/progress/999999", headers=auth_headers(student_token))
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Lecture not found"

    def test_mark_progress_unauthenticated(self, client):
        resp = client.post("/api/v1/enrollments/progress/1")
        assert resp.status_code == 401

    def test_mark_progress_not_enrolled(self, client, student_token, instructor_token):
        """Marking progress without enrollment should return 403."""
        # Create course + section + lecture
        c = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Progress Course", "description": "desc", "price": 0.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        s = client.post(
            f"/api/v1/instructor/courses/{course_id}/sections",
            json={"title": "Section 1", "order": 1},
            headers=auth_headers(instructor_token),
        )
        if s.status_code != 200:
            pytest.skip("Could not create section")
        section_id = s.json()["id"]

        l = client.post(
            f"/api/v1/instructor/sections/{section_id}/lectures",
            data={"title": "Lecture 1", "order": 1},
            headers=auth_headers(instructor_token),
        )
        if l.status_code != 200:
            pytest.skip("Could not create lecture")
        lecture_id = l.json()["id"]

        # Register a fresh student not enrolled in this course
        client.post("/register", data={"username": "notenrolled", "email": "ne@mail.com", "password": "pass", "role": "student"})
        token = client.post("/login", data={"username": "notenrolled", "password": "pass"}).json()["access_token"]

        resp = client.post(f"/api/v1/enrollments/progress/{lecture_id}", headers=auth_headers(token))
        assert resp.status_code == 403
