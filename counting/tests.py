import uuid

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from rest_framework.authtoken.models import Token

from counting import models

User = get_user_model()


class AuthAndActionsCounterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="luke", password="super", email="luke@soiree.tech"
        )
        self.staff_user = User.objects.create_user(
            username="admin_user", password="super", is_staff=True
        )
        self.token = Token.objects.create(user=self.user)

        self.tenant = models.Tenant.objects.create(name="Tenant 1", owner=self.user)
        self.project = models.Project.objects.create(
            name="Project 1", tenant=self.tenant
        )
        self.funnel = models.Funnel.objects.create(
            name="Funnel 1", project=self.project
        )
        self.action = models.Action.objects.create(name="ready", funnel=self.funnel)

    def test_api_auth_success(self):
        response = self.client.post(
            "/api/auth/",
            data={"username": "luke", "password": "super"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"token": self.token.key})

    def test_api_auth_no_slash_success(self):
        response = self.client.post(
            "/api/auth",
            data={"username": "luke", "password": "super"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"token": self.token.key})

    def test_api_auth_invalid_credentials(self):
        response = self.client.post(
            "/api/auth/",
            data={"username": "luke", "password": "wrongpassword"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_api_register_success(self):
        response = self.client.post(
            "/api/register/",
            data={
                "username": "newuser",
                "password": "secretpassword",
                "email": "newuser@example.com",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["username"], "newuser")
        self.assertIn("token", data)
        self.assertTrue(User.objects.filter(username="newuser").exists())

        # Verify token works for authorization
        registered_user = User.objects.get(username="newuser")
        self.assertEqual(Token.objects.get(user=registered_user).key, data["token"])

    def test_api_register_no_slash_success(self):
        response = self.client.post(
            "/api/register",
            data={
                "username": "newuser_noslash",
                "password": "secretpassword",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["username"], "newuser_noslash")
        self.assertIn("token", data)
        self.assertTrue(User.objects.filter(username="newuser_noslash").exists())

    def test_api_register_duplicate_username(self):
        response = self.client.post(
            "/api/register/",
            data={
                "username": "luke",
                "password": "secretpassword",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_action_hit_with_registered_user(self):
        reg_response = self.client.post(
            "/api/register/",
            data={
                "username": "tracker_user",
                "password": "tracker_password",
            },
            content_type="application/json",
        )
        self.assertEqual(reg_response.status_code, 201)
        user_token = reg_response.json()["token"]
        registered_user = User.objects.get(username="tracker_user")

        url = f"/api/actions/{self.action.pk}/hit/"
        response = self.client.post(
            url,
            data={"token": str(self.tenant.token)},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {user_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": "ok"})
        self.assertEqual(models.ActionCounter.objects.count(), 1)
        counter = models.ActionCounter.objects.first()
        self.assertEqual(counter.action, self.action)
        self.assertEqual(counter.user, registered_user)

    def test_action_hit_unauthenticated(self):
        url = f"/api/actions/{self.action.pk}/hit/"
        response = self.client.post(
            url,
            data={"token": str(self.tenant.token)},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(models.ActionCounter.objects.count(), 0)

    def test_action_hit_authenticated_missing_token(self):
        url = f"/api/actions/{self.action.pk}/hit/"
        response = self.client.post(
            url,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"failure": "token not present"})
        self.assertEqual(models.ActionCounter.objects.count(), 0)

    def test_action_hit_authenticated_empty_token(self):
        url = f"/api/actions/{self.action.pk}/hit/"
        for empty_val in ["", "   ", None]:
            with self.subTest(empty_val=empty_val):
                response = self.client.post(
                    url,
                    data={"token": empty_val},
                    content_type="application/json",
                    HTTP_AUTHORIZATION=f"Token {self.token.key}",
                )
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json(), {"failure": "token not present"})
                self.assertEqual(models.ActionCounter.objects.count(), 0)

    def test_action_hit_authenticated_invalid_token_format(self):
        url = f"/api/actions/{self.action.pk}/hit/"
        response = self.client.post(
            url,
            data={"token": "not-a-valid-uuid"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"failure": "invalid token"})
        self.assertEqual(models.ActionCounter.objects.count(), 0)

    def test_action_hit_authenticated_wrong_tenant_token(self):
        url = f"/api/actions/{self.action.pk}/hit/"
        random_uuid = str(uuid.uuid4())
        response = self.client.post(
            url,
            data={"token": random_uuid},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"failure": "invalid authorization"})
        self.assertEqual(models.ActionCounter.objects.count(), 0)

    def test_action_hit_authenticated_correct_tenant_token(self):
        url = f"/api/actions/{self.action.pk}/hit/"
        response = self.client.post(
            url,
            data={"token": str(self.tenant.token)},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": "ok"})
        self.assertEqual(models.ActionCounter.objects.count(), 1)
        counter = models.ActionCounter.objects.first()
        self.assertEqual(counter.action, self.action)
        self.assertEqual(counter.user, self.user)

    def test_sample_and_extension_views(self):
        resp_sample = self.client.get("/sample/")
        self.assertEqual(resp_sample.status_code, 200)
        self.assertIn(b"/api/register/", resp_sample.content)
        self.assertIn(b"/api/auth/", resp_sample.content)
        self.assertIn(b'id="token"', resp_sample.content)
        self.assertIn(b"Hit", resp_sample.content)

        resp_ext = self.client.get("/extension/")
        self.assertEqual(resp_ext.status_code, 200)
        self.assertEqual(resp_ext["Content-Type"], "application/javascript")

    def test_main_page_requires_staff_account(self):
        # Anonymous user should be redirected
        resp_anon = self.client.get("/")
        self.assertEqual(resp_anon.status_code, 302)
        self.assertIn("/admin/login/", resp_anon["Location"])

        # Non-staff authenticated user should also be redirected
        self.client.force_login(self.user)
        resp_non_staff = self.client.get("/")
        self.assertEqual(resp_non_staff.status_code, 302)
        self.assertIn("/admin/login/", resp_non_staff["Location"])

        # Staff user should be granted access
        self.client.force_login(self.staff_user)
        resp_staff = self.client.get("/")
        self.assertEqual(resp_staff.status_code, 200)
        self.assertIn(b"Action Counters Over Time", resp_staff.content)
        self.assertIn(b'id="chart-section"', resp_staff.content)
        self.assertIn(b'style="display: none;"', resp_staff.content)

    def test_funnel_statistics_empty_time_series(self):
        url = f"/api/funnels/{self.funnel.pk}/statistics/"
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["success"], "ok")
        self.assertEqual(data["result"], {"Funnel 1": {"ready": 0}})
        self.assertEqual(data["time_series"], [])

    def test_funnel_statistics_with_time_series(self):
        action2 = models.Action.objects.create(name="email", funnel=self.funnel)
        models.ActionCounter.objects.create(action=self.action, user=self.user)
        models.ActionCounter.objects.create(action=self.action, user=self.user)
        models.ActionCounter.objects.create(action=action2, user=self.user)

        url = f"/api/funnels/{self.funnel.pk}/statistics/"
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["success"], "ok")
        self.assertEqual(data["result"], {"Funnel 1": {"ready": 2, "email": 1}})
        self.assertEqual(len(data["time_series"]), 2)

        # verify time_series entries
        ready_entry = next(
            item for item in data["time_series"] if item["action"] == "ready"
        )
        self.assertEqual(ready_entry["count"], 2)
        self.assertIsNotNone(ready_entry["date"])

        email_entry = next(
            item for item in data["time_series"] if item["action"] == "email"
        )
        self.assertEqual(email_entry["count"], 1)
        self.assertIsNotNone(email_entry["date"])

    def test_funnel_statistics_unauthenticated(self):
        url = f"/api/funnels/{self.funnel.pk}/statistics/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
