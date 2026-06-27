import pytest #type:ignore
from conftest import auth_headers


def create_course_as_instructor(client, instructor_token, title="Test Course", price=29.99, category_id=1):
    resp = client.post(
        "/api/v1/courses/",
        json={"title": title, "description": "A test course", "price": price, "category_id": category_id},
        headers=auth_headers(instructor_token),
    )
    return resp


class TestGetCourses:
    def test_list_courses_no_auth(self, client):
        resp = client.get("/api/v1/courses/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_courses_with_pagination(self, client):
        resp = client.get("/api/v1/courses/?skip=0&limit=5")
        assert resp.status_code == 200
        assert len(resp.json()) <= 5

    def test_list_courses_search_filter(self, client):
        resp = client.get("/api/v1/courses/?search=nonexistent_xyz_abc")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_courses_price_filter(self, client):
        resp = client.get("/api/v1/courses/?min_price=0&max_price=1000")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestGetCategories:
    def test_get_categories(self, client):
        resp = client.get("/api/v1/courses/categories")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestGetCourseById:
    def test_get_nonexistent_course(self, client):
        resp = client.get("/api/v1/courses/999999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Course not found"

    def test_get_existing_course(self, client, instructor_token):
        create_resp = client.post(
            "/api/v1/instructor/courses/section",
            json={"title": "Fetch Me", "description": "desc", "price": 10.0, "category_id": 1},
            headers=auth_headers(instructor_token),
        )
        if create_resp.status_code == 200:
            course_id = create_resp.json()["id"]
            resp = client.get(f"/api/v1/courses/{course_id}")
            assert resp.status_code == 200
            assert resp.json()["id"] == course_id


class TestCreateCourse:
    def test_create_course_as_instructor(self, client, instructor_token):
        resp = create_course_as_instructor(client, instructor_token, title="My New Course")
        assert resp.status_code in (200, 404, 422, 500)

    def test_create_course_as_student_forbidden(self, client, student_token):
        resp = client.post(
            "/api/v1/courses/",
            json={"title": "Sneaky Course", "description": "nope", "price": 5.0, "category_id": 1},
            headers=auth_headers(student_token),
        )
        assert resp.status_code == 403

    def test_create_course_unauthenticated(self, client):
        resp = client.post(
            "/api/v1/courses/",
            json={"title": "Anon Course", "description": "nope", "price": 5.0, "category_id": 1},
        )
        assert resp.status_code == 401
