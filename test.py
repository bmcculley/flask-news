# -*- coding: utf-8 -*-
"""
    Flask login
    ~~~~~~~~~~~

    An example app showing the basic use of Flask login.

    :copyright: (c) 2018 by bmcculley.
    :license: MIT, see LICENSE for more details.
"""

import os
from app import *
import unittest
import bcrypt

class FlaskLoginTestCase(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
        db.create_all()
        user_dict = {
            "admin" : DBUser(username="admin", email="admin@example.com", password=bcrypt.hashpw(b"abc123", bcrypt.gensalt())),
            "guest" : DBUser(username="guest", email="guest@example.com", password=bcrypt.hashpw(b"password", bcrypt.gensalt()))}
        for key, user in user_dict.items():
            db.session.add(user)
        db.session.commit()
        self.app = app.test_client()


    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self, username, password):
        return self.app.post("/login", data=dict(
            username=username,
            password=password
        ), follow_redirects=True)


    def register(self, username, email, password):
        return self.app.post("/login", data=dict(
            username=username,
            email=email,
            password=password,
            vpassword=password
        ), follow_redirects=True)


    def logout(self):
        return self.app.get("/logout", follow_redirects=True)


    def test_home(self):
        rv = self.app.get("/")
        assert b"Hello, world!" in rv.data


    def test_login_logout(self):
        rv = self.login("admin", "abc123")
        assert b"Hello, world!" in rv.data
        rv = self.logout()
        assert b"Hello, world!" in rv.data
        rv = self.login("user", "default")
        assert b"Login failed" in rv.data


    def test_secret(self):
        rv = self.app.get("/secret")
        assert b"Redirecting..." in rv.data
        self.login("admin", "abc123")
        rv = self.app.get("/secret")
        assert b"Hello, admin" in rv.data
        rv = self.logout()
        assert b"Hello, world!" in rv.data


    def test_bad_registration(self):
        rv = self.register("admin", "admin@example.com", "abc123")
        assert b"Username or email already in use."


    def test_good_registration(self):
        rv = self.register("user2", "user2@example.com", "abc123")
        assert b"App Login" in rv.data
        

if __name__ == "__main__":
    unittest.main()
