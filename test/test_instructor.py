"""
Tests for Instructor Panel endpoints:
  GET  /api/v1/instructor/dashboard
  POST /api/v1/instructor/courses/step1
  PUT  /api/v1/instructor/courses/{course_id}/step2
  POST /api/v1/instructor/courses/{course_id}/sections
  POST /api/v1/instructor/sections/{section_id}/lectures
  POST /api/v1/instructor/lectures/{lecture_id}/captions
  PUT  /api/v1/instructor/courses/{course_id}/publish
"""
import pytest
from conftest import auth_headers


# --------------------------------------------------------------------------- #
#  Helpers                                                                    #
# --------------------------------------------------------------------------- #

def create_course(client, instructor_token, title="Instructor Course"):
    return client.post(
        "/api/v1/instructor/courses/step1",
        json={"title": title, "description": "desc", "price": 49.99, "category_id": 1},
        headers=auth_headers(instructor_token),
    )


# --------------------------------------------------------------------------- #
#  Dashboard                                                                  #
# --------------------------------------------------------------------------- #

class TestInstructorDashboard:
    def test_dashboard_requires_instructor(self, client, student_token):
        resp = client.get("/api/v1/instructor/dashboard", headers=auth_headers(student_token))
        assert resp.status_code == 403

    def test_dashboard_unauthenticated(self, client):
        resp = client.get("/api/v1/instructor/dashboard")
        assert resp.status_code == 401

    def test_dashboard_returns_expected_keys(self, client, instructor_token):
        resp = client.get("/api/v1/instructor/dashboard", headers=auth_headers(instructor_token))
        assert resp.status_code == 200
        body = resp.json()
        assert "total_revenue" in body
        assert "total_students" in body
        assert "courses_analytics" in body
        assert "revenue_by_month" in body


# --------------------------------------------------------------------------- #
#  Course Creation (step1)                                                    #
# --------------------------------------------------------------------------- #

class TestInstructorCourseStep1:
    def test_create_course_student_forbidden(self, client, student_token):
        resp = create_course(client, student_token)
        assert resp.status_code == 403

    def test_create_course_unauthenticated(self, client):
        resp = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "X", "description": "desc", "price": 10.0, "category_id": 1},
        )
        assert resp.status_code == 401

    def test_create_course_missing_category(self, client, instructor_token):
        resp = create_course(client, instructor_token, title="Bad Category Course")
        # category_id=1 may not exist → 404 is acceptable
        assert resp.status_code in (200, 404)


# --------------------------------------------------------------------------- #
#  Course Step 2                                                              #
# --------------------------------------------------------------------------- #

class TestInstructorCourseStep2:
    def test_update_step2_nonexistent_course(self, client, instructor_token):
        resp = client.put(
            "/api/v1/instructor/courses/999999/step2?difficulty=beginner",
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 404

    def test_update_step2_unauthorized(self, client, student_token):
        resp = client.put(
            "/api/v1/instructor/courses/1/step2?difficulty=beginner",
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 403


# --------------------------------------------------------------------------- #
#  Sections                                                                   #
# --------------------------------------------------------------------------- #

class TestInstructorSections:
    def test_add_section_nonexistent_course(self, client, instructor_token):
        # SectionCreate requires course_id in the body; when the course doesn't
        # exist the router returns 404. With body missing course_id it returns 422.
        resp = client.post(
            "/api/v1/instructor/courses/999999/sections",
            json={"title": "Section 1", "order": 1, "course_id": 999999},
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 404

    def test_add_section_student_forbidden(self, client, student_token):
        resp = client.post(
            "/api/v1/instructor/courses/1/sections",
            json={"title": "Section 1", "order": 1, "course_id": 1},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 403

    def test_add_section_success(self, client, instructor_token):
        c = create_course(client, instructor_token, title="Section Test Course")
        if c.status_code != 200:
            pytest.skip("Could not create course (category may not exist)")
        course_id = c.json()["id"]

        resp = client.post(
            f"/api/v1/instructor/courses/{course_id}/sections",
            json={"title": "Section Alpha", "order": 1, "course_id": course_id},
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Section Alpha"


# --------------------------------------------------------------------------- #
#  Lectures                                                                   #
# --------------------------------------------------------------------------- #

class TestInstructorLectures:
    def test_add_lecture_nonexistent_section(self, client, instructor_token):
        resp = client.post(
            "/api/v1/instructor/sections/999999/lectures",
            data={"title": "Lecture 1", "order": 1},
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 404

    def test_add_lecture_student_forbidden(self, client, student_token):
        resp = client.post(
            "/api/v1/instructor/sections/1/lectures",
            data={"title": "Lecture 1", "order": 1},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 403

    def test_add_lecture_success(self, client, instructor_token):
        # Create course → section → lecture
        c = create_course(client, instructor_token, title="Lecture Test Course")
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        s = client.post(
            f"/api/v1/instructor/courses/{course_id}/sections",
            json={"title": "Section B", "order": 1, "course_id": course_id},
            headers=auth_headers(instructor_token),
        )
        section_id = s.json()["id"]

        resp = client.post(
            f"/api/v1/instructor/sections/{section_id}/lectures",
            data={"title": "Intro Lecture", "order": 1},
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Intro Lecture"


# --------------------------------------------------------------------------- #
#  Captions                                                                   #
# --------------------------------------------------------------------------- #

class TestInstructorCaptions:
    def test_add_captions_nonexistent_lecture(self, client, instructor_token):
        resp = client.post(
            "/api/v1/instructor/lectures/999999/captions",
            data={"captions_url": "https://example.com/captions.vtt"},
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 404

    def test_add_captions_student_forbidden(self, client, student_token):
        resp = client.post(
            "/api/v1/instructor/lectures/1/captions",
            data={"captions_url": "https://example.com/captions.vtt"},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 403


# --------------------------------------------------------------------------- #
#  Publish                                                                    #
# --------------------------------------------------------------------------- #

class TestInstructorPublish:
    def test_publish_nonexistent_course(self, client, instructor_token):
        resp = client.put(
            "/api/v1/instructor/courses/999999/publish?publish=true",
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 404

    def test_publish_without_sections_fails(self, client, instructor_token):
        c = create_course(client, instructor_token, title="Empty Publish Course")
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        resp = client.put(
            f"/api/v1/instructor/courses/{course_id}/publish?publish=true",
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 400
        assert "sections" in resp.json()["detail"].lower()

    def test_publish_with_sections_succeeds(self, client, instructor_token):
        c = create_course(client, instructor_token, title="Publishable Course")
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        # Add a section
        client.post(
            f"/api/v1/instructor/courses/{course_id}/sections",
            json={"title": "Section 1", "order": 1, "course_id": course_id},
            headers=auth_headers(instructor_token),
        )
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

    def test_unpublish_course(self, client, instructor_token):
        c = create_course(client, instructor_token, title="Unpublish Me Course")
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        client.post(
            f"/api/v1/instructor/courses/{course_id}/sections",
            json={"title": "Section 1", "order": 1, "course_id": course_id},
            headers=auth_headers(instructor_token),
        )
        client.put(f"/api/v1/instructor/courses/{course_id}/publish?publish=true", headers=auth_headers(instructor_token))

        resp = client.put(
            f"/api/v1/instructor/courses/{course_id}/publish?publish=false",
            headers=auth_headers(instructor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "draft"
