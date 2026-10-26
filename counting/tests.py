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
        self.assertIn(b"/api/auth/", resp_sample.content)

        resp_ext = self.client.get("/extension/")
        self.assertEqual(resp_ext.status_code, 200)
        self.assertEqual(resp_ext["Content-Type"], "application/javascript")
