"""
Tests for Cart & Shopping endpoints:
  GET    /api/v1/cart/
  POST   /api/v1/cart/add/{course_id}
  DELETE /api/v1/cart/remove/{course_id}
  POST   /api/v1/cart/wishlist/{course_id}
  GET    /api/v1/cart/wishlist
  GET    /api/v1/cart/purchases
  POST   /api/v1/cart/checkout
"""
import pytest
from conftest import auth_headers


class TestCart:
    def test_get_cart_unauthenticated(self, client):
        resp = client.get("/api/v1/cart/")
        assert resp.status_code == 401

    def test_get_cart_empty(self, client, student_token):
        resp = client.get("/api/v1/cart/", headers=auth_headers(student_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_add_nonexistent_course_to_cart(self, client, student_token):
        resp = client.post("/api/v1/cart/add/999999", headers=auth_headers(student_token))
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Course not found"

    def test_add_to_cart_unauthenticated(self, client):
        resp = client.post("/api/v1/cart/add/1")
        assert resp.status_code == 401

    def test_remove_from_cart_not_in_cart(self, client, student_token):
        resp = client.delete("/api/v1/cart/remove/999999", headers=auth_headers(student_token))
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Item not in cart"

    def test_remove_from_cart_unauthenticated(self, client):
        resp = client.delete("/api/v1/cart/remove/1")
        assert resp.status_code == 401

    def test_checkout_empty_cart(self, client, student_token):
        resp = client.post("/api/v1/cart/checkout", headers=auth_headers(student_token))
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_checkout_unauthenticated(self, client):
        resp = client.post("/api/v1/cart/checkout")
        assert resp.status_code == 401


class TestWishlist:
    def test_get_wishlist_unauthenticated(self, client):
        resp = client.get("/api/v1/cart/wishlist")
        assert resp.status_code == 401

    def test_get_wishlist_empty(self, client, student_token):
        resp = client.get("/api/v1/cart/wishlist", headers=auth_headers(student_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_move_nonexistent_course_to_wishlist(self, client, student_token):
        # Should succeed (it just skips cart deletion and creates wishlist item if course doesn't exist in cart)
        resp = client.post("/api/v1/cart/wishlist/999999", headers=auth_headers(student_token))
        # May 200 (moves anyway) or another error - just ensure authenticated path works
        assert resp.status_code in (200, 404)

    def test_wishlist_unauthenticated(self, client):
        resp = client.post("/api/v1/cart/wishlist/1")
        assert resp.status_code == 401


class TestPurchases:
    def test_get_purchases_unauthenticated(self, client):
        resp = client.get("/api/v1/cart/purchases")
        assert resp.status_code == 401

    def test_get_purchases_empty(self, client, student_token):
        resp = client.get("/api/v1/cart/purchases", headers=auth_headers(student_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
