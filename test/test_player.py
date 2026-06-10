import pytest #type:ignore
from conftest import auth_headers


class TestPlayerStream:
    def test_stream_unauthenticated(self, client):
        resp = client.get("/api/v1/player/stream/1")
        assert resp.status_code == 401

    def test_stream_nonexistent_lecture(self, client, student_token):
        resp = client.get("/api/v1/player/stream/999999", headers=auth_headers(student_token))
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Lecture not found"

    def test_stream_not_enrolled(self, client, student_token, instructor_token):
        c = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Player Course", "description": "desc", "price": 0.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        s = client.post(
            f"/api/v1/instructor/courses/{course_id}/sections",
            json={"title": "S1", "order": 1},
            headers=auth_headers(instructor_token),
        )
        section_id = s.json()["id"]

        l = client.post(
            f"/api/v1/instructor/sections/{section_id}/lectures",
            data={"title": "L1", "order": 1},
            headers=auth_headers(instructor_token),
        )
        lecture_id = l.json()["id"]

        client.post("/register", data={"username": "streamstudent", "email": "ss@mail.com", "password": "pass", "role": "student"})
        token = client.post("/login", data={"username": "streamstudent", "password": "pass"}).json()["access_token"]

        resp = client.get(f"/api/v1/player/stream/{lecture_id}", headers=auth_headers(token))
        assert resp.status_code == 403

    def test_stream_enrolled_student(self, client, student_token, instructor_token):
        c = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Stream Me", "description": "desc", "price": 0.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]

        s = client.post(
            f"/api/v1/instructor/courses/{course_id}/sections",
            json={"title": "S1", "order": 1},
            headers=auth_headers(instructor_token),
        )
        section_id = s.json()["id"]

        l = client.post(
            f"/api/v1/instructor/sections/{section_id}/lectures",
            data={"title": "L1", "order": 1},
            headers=auth_headers(instructor_token),
        )
        lecture_id = l.json()["id"]

        client.post(f"/api/v1/enrollments/{course_id}", headers=auth_headers(student_token))

        resp = client.get(f"/api/v1/player/stream/{lecture_id}", headers=auth_headers(student_token))
        assert resp.status_code == 200
        assert "url" in resp.json()


class TestPlayerProgress:
    def test_update_progress_unauthenticated(self, client):
        resp = client.post("/api/v1/player/progress/1?playback_position=30")
        assert resp.status_code == 401

    def test_update_progress_nonexistent_lecture(self, client, student_token):
        resp = client.post(
            "/api/v1/player/progress/999999?playback_position=30",
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 404

    def test_update_progress_success(self, client, student_token, instructor_token):
        c = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Progress Player Course", "description": "desc", "price": 0.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]
        s = client.post(f"/api/v1/instructor/courses/{course_id}/sections", json={"title": "S1", "order": 1}, headers=auth_headers(instructor_token))
        l = client.post(f"/api/v1/instructor/sections/{s.json()['id']}/lectures", data={"title": "L1", "order": 1}, headers=auth_headers(instructor_token))
        lecture_id = l.json()["id"]

        client.post(f"/api/v1/enrollments/{course_id}", headers=auth_headers(student_token))

        resp = client.post(
            f"/api/v1/player/progress/{lecture_id}?playback_position=45.5&completed=false",
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["playback_position"] == 45.5
        assert body["completed"] is False


class TestPlayerNotes:
    def test_get_notes_unauthenticated(self, client):
        resp = client.get("/api/v1/player/notes/1")
        assert resp.status_code == 401

    def test_get_notes_empty(self, client, student_token):
        resp = client.get("/api/v1/player/notes/999999", headers=auth_headers(student_token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_add_note_unauthenticated(self, client):
        resp = client.post("/api/v1/player/notes/1", json={"lecture_id": 1, "content": "Note text", "timestamp": 12.5})
        assert resp.status_code == 401

    def test_add_note_success(self, client, student_token, instructor_token):
        c = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Notes Course", "description": "desc", "price": 0.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]
        s = client.post(f"/api/v1/instructor/courses/{course_id}/sections", json={"title": "S1", "order": 1}, headers=auth_headers(instructor_token))
        l = client.post(f"/api/v1/instructor/sections/{s.json()['id']}/lectures", data={"title": "L1", "order": 1}, headers=auth_headers(instructor_token))
        lecture_id = l.json()["id"]

        resp = client.post(
            f"/api/v1/player/notes/{lecture_id}",
            json={"lecture_id": lecture_id, "content": "Remember this!", "timestamp": 30.0},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 200
        assert resp.json()["content"] == "Remember this!"


class TestPlayerAttachments:
    def test_get_attachments_unauthenticated(self, client):
        resp = client.get("/api/v1/player/attachments/1")
        assert resp.status_code == 401

    def test_get_attachments_nonexistent_lecture(self, client, student_token):
        resp = client.get("/api/v1/player/attachments/999999", headers=auth_headers(student_token))
        assert resp.status_code == 404

    def test_get_attachments_empty(self, client, student_token, instructor_token):
        c = client.post(
            "/api/v1/instructor/courses/step1",
            json={"title": "Attachments Course", "description": "desc", "price": 0.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if c.status_code != 200:
            pytest.skip("Could not create course")
        course_id = c.json()["id"]
        s = client.post(f"/api/v1/instructor/courses/{course_id}/sections", json={"title": "S1", "order": 1}, headers=auth_headers(instructor_token))
        l = client.post(f"/api/v1/instructor/sections/{s.json()['id']}/lectures", data={"title": "L1", "order": 1}, headers=auth_headers(instructor_token))
        lecture_id = l.json()["id"]

        resp = client.get(f"/api/v1/player/attachments/{lecture_id}", headers=auth_headers(student_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
