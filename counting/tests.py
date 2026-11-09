import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from counting import models
from counting.serializers import ActionCounterSerializer

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

        self.tenant = models.Tenant.objects.create(name="Tenant 1")
        self.tenant.owners.add(self.user)
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

    def test_counter_preserves_created_timestamp(self):
        timestamp = datetime(2026, 10, 30, 12, microsecond=123456, tzinfo=UTC)
        with patch("django.utils.timezone.now", return_value=timestamp):
            counter = models.ActionCounter.objects.create(
                action=self.action, user=self.user
            )
        counter.refresh_from_db()
        self.assertEqual(counter.created, timestamp)
        self.assertNotIn("created_ns", ActionCounterSerializer(counter).data)
        counter.save()
        counter.refresh_from_db()
        self.assertEqual(counter.created, timestamp)

    def test_bulk_counter_preserves_created_timestamp(self):
        timestamp = datetime(2026, 10, 30, 12, microsecond=123456, tzinfo=UTC)
        with patch("django.utils.timezone.now", return_value=timestamp):
            models.ActionCounter.objects.bulk_create(
                [models.ActionCounter(action=self.action, user=self.user)]
            )
        self.assertEqual(models.ActionCounter.objects.get().created, timestamp)

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

    def test_anonymous_registration(self):
        users = []
        for url in ["/api/register/anonymous/", "/api/register/anonymous"]:
            with self.subTest(url=url):
                result = self.client.post(url, data={}, content_type="application/json")
                self.assertEqual(result.status_code, 201)
                data = result.json()
                user = User.objects.get(pk=data["id"])
                self.assertEqual(data["username"], user.username)
                self.assertFalse(user.has_usable_password())
                self.assertEqual(user.email, "")
                self.assertFalse(user.is_staff)
                self.assertFalse(user.is_superuser)
                self.assertEqual(Token.objects.get(user=user).key, data["token"])
                hit = self.client.post(
                    f"/api/actions/{self.action.pk}/hit/",
                    data={"token": str(self.tenant.token)},
                    content_type="application/json",
                    HTTP_AUTHORIZATION=f"Token {data['token']}",
                )
                self.assertEqual(hit.status_code, 200)
                self.assertTrue(models.ActionCounter.objects.filter(user=user).exists())
                users.append(user.pk)
        self.assertNotEqual(*users)

    def test_anonymous_registration_requires_post(self):
        count = User.objects.count()
        self.assertEqual(self.client.get("/api/register/anonymous/").status_code, 405)
        self.assertEqual(User.objects.count(), count)

    def test_logout_deletes_token(self):
        # Token exists before logout
        self.assertTrue(
            Token.objects.filter(user=self.user, key=self.token.key).exists()
        )

        # Logout requires authentication
        resp = self.client.post("/api/logout/", data={}, content_type="application/json")
        self.assertEqual(resp.status_code, 401)

        # Logout with valid token
        resp = self.client.post(
            "/api/logout/",
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"detail": "Logged out"})

        # Token is deleted from the server
        self.assertFalse(Token.objects.filter(user=self.user).exists())

        # Subsequent requests with the old token are rejected
        resp = self.client.get(
            "/api/me/",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(resp.status_code, 401)

    def test_logout_no_slash(self):
        resp = self.client.post(
            "/api/logout",
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

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
        for payload in [
            {"token": str(self.tenant.token)},
            {"token": {"token": str(self.tenant.token)}},
        ]:
            with self.subTest(payload=payload):
                response = self.client.post(
                    url,
                    data=payload,
                    content_type="application/json",
                    HTTP_AUTHORIZATION=f"Token {self.token.key}",
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"success": "ok"})
        self.assertEqual(models.ActionCounter.objects.count(), 2)
        counter = models.ActionCounter.objects.first()
        self.assertEqual(counter.action, self.action)
        self.assertEqual(counter.user, self.user)

    def test_cors_preflight_and_headers_on_action_hit(self):
        url = f"/api/actions/{self.action.pk}/hit/"
        # Preflight OPTIONS request
        response = self.client.options(
            url,
            HTTP_ORIGIN="https://sample.example.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization, content-type",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Access-Control-Allow-Origin"], "https://sample.example.com"
        )
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
        self.assertIn(
            "authorization, content-type", response["Access-Control-Allow-Headers"]
        )
        self.assertIn("POST", response["Access-Control-Allow-Methods"])

        # Actual POST request
        response = self.client.post(
            url,
            data={"token": str(self.tenant.token)},
            content_type="application/json",
            HTTP_ORIGIN="https://sample.example.com",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Access-Control-Allow-Origin"], "https://sample.example.com"
        )
        self.assertEqual(response.json(), {"success": "ok"})

    def test_sample_and_extension_views(self):
        resp_sample = self.client.get("/sample/")
        self.assertEqual(resp_sample.status_code, 200)
        self.assertIn(reverse("sample-js").encode(), resp_sample.content)
        self.assertIn(b'id="token"', resp_sample.content)
        self.assertIn(b"Hit", resp_sample.content)

        resp_ext = self.client.get("/extension/")
        self.assertEqual(resp_ext.status_code, 200)
        self.assertEqual(
            resp_ext["Content-Type"], "application/javascript; charset=utf-8"
        )
        self.assertIn("window.Śledzik", resp_ext.content.decode("utf-8"))
        self.assertIn("Sec-Fetch-Dest", resp_ext["Vary"])

        resp_js = self.client.get(reverse("sample-js"))
        self.assertEqual(resp_js.status_code, 200)
        self.assertEqual(
            resp_js["Content-Type"], "application/javascript; charset=utf-8"
        )
        self.assertIn("window.Śledzik", resp_js.content.decode("utf-8"))
        self.assertIn(reverse("api-register-anonymous").encode(), resp_js.content)
        self.assertIn(reverse("token-actions").encode(), resp_js.content)
        self.assertIn(b"window.", resp_js.content)
        self.assertNotIn(b"{%", resp_js.content)

        resp_ext_js = self.client.get(reverse("extension-js"))
        self.assertEqual(resp_ext_js.status_code, 200)
        self.assertEqual(
            resp_ext_js["Content-Type"], "application/javascript; charset=utf-8"
        )
        self.assertIn("window.Śledzik", resp_ext_js.content.decode("utf-8"))
        self.assertIn("registerAnonymous", resp_ext_js.content.decode("utf-8"))

    def test_extension_navigation_has_favicon_but_scripts_receive_javascript(self):
        preview = self.client.get(reverse("extension"), HTTP_SEC_FETCH_DEST="document")
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview["Content-Type"], "text/html; charset=utf-8")
        self.assertIn(b'href="/favicon.ico?v=2"', preview.content)
        self.assertIn(b'<pre class="source-preview">', preview.content)
        self.assertIn(b"&quot;Authorization&quot;", preview.content)
        self.assertIn(reverse("extension-js").encode(), preview.content)
        for url, destination in [
            (reverse("extension"), "script"),
        ]:
            script = self.client.get(url, HTTP_SEC_FETCH_DEST=destination)
            self.assertEqual(
                script["Content-Type"], "application/javascript; charset=utf-8"
            )
            self.assertIn("window.Śledzik", script.content.decode())
            self.assertNotIn(b"<html", script.content)

    def test_main_page_accessible_to_all(self):
        # Anonymous user should be able to access the main page
        resp_anon = self.client.get("/")
        self.assertEqual(resp_anon.status_code, 200)
        self.assertIn(b"Action Counters Over Time", resp_anon.content)
        self.assertIn(b'id="chart-section"', resp_anon.content)

        # Authenticated non-staff user should also access the main page
        self.client.force_login(self.user)
        resp_user = self.client.get("/")
        self.assertEqual(resp_user.status_code, 200)
        self.assertIn(b"Action Counters Over Time", resp_user.content)

        # Staff user should also access the main page
        self.client.force_login(self.staff_user)
        resp_staff = self.client.get("/")
        self.assertEqual(resp_staff.status_code, 200)
        self.assertIn(b"Action Counters Over Time", resp_staff.content)

        resp_links = self.client.get(reverse("links"))
        self.assertEqual(resp_links.status_code, 200)
        self.assertIn(b"extension.js", resp_links.content)
        self.assertIn(reverse("extension-js").encode(), resp_links.content)
        self.assertIn(reverse("admin:index").encode(), resp_links.content)
        self.assertIn(reverse("extension").encode(), resp_links.content)
        self.assertIn(reverse("sample").encode(), resp_links.content)
        self.assertIn(reverse("home").encode(), resp_links.content)

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
        self.assertEqual(data["unique_viewers"], [])

    def test_funnel_statistics_with_time_series(self):
        action2 = models.Action.objects.create(name="email", funnel=self.funnel)
        models.ActionCounter.objects.create(action=self.action, user=self.user)
        models.ActionCounter.objects.create(action=self.action, user=self.user)
        models.ActionCounter.objects.create(action=action2, user=self.user)

        url = f"/api/funnels/{self.funnel.pk}/statistics/?granularity=day"
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
        self.assertIsNotNone(ready_entry["created"])

        email_entry = next(
            item for item in data["time_series"] if item["action"] == "email"
        )
        self.assertEqual(email_entry["count"], 1)
        self.assertIsNotNone(email_entry["created"])

    def test_statistics_exact_created_timestamp(self):
        for microsecond in [123456, 123457]:
            timestamp = datetime(2026, 10, 30, 12, microsecond=microsecond, tzinfo=UTC)
            with patch("django.utils.timezone.now", return_value=timestamp):
                models.ActionCounter.objects.create(action=self.action, user=self.user)
        response = self.client.get(
            f"/api/funnels/{self.funnel.pk}/statistics/?granularity=created",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["time_series"],
            [
                {
                    "created": "2026-10-30T12:00:00.123456+00:00",
                    "action": "ready",
                    "count": 1,
                },
                {
                    "created": "2026-10-30T12:00:00.123457+00:00",
                    "action": "ready",
                    "count": 1,
                },
            ],
        )

    def test_statistics_groups_by_bucket_and_action(self):
        action2 = models.Action.objects.create(name="email", funnel=self.funnel)
        samples = [
            (self.action, datetime(2026, 10, 30, 12, 10, tzinfo=UTC)),
            (self.action, datetime(2026, 10, 30, 12, 20, tzinfo=UTC)),
            (self.action, datetime(2026, 10, 30, 13, 10, tzinfo=UTC)),
            (self.action, datetime(2026, 10, 31, 12, tzinfo=UTC)),
            (action2, datetime(2026, 10, 30, 12, tzinfo=UTC)),
        ]
        for action, created in samples:
            counter = models.ActionCounter.objects.create(action=action, user=self.user)
            models.ActionCounter.objects.filter(pk=counter.pk).update(created=created)

        url = f"/api/funnels/{self.funnel.pk}/statistics/"
        for query, expected in [
            (
                "",
                [
                    ("2026-10-30T12:00:00+00:00", "email", 1),
                    ("2026-10-30T12:10:00+00:00", "ready", 1),
                    ("2026-10-30T12:20:00+00:00", "ready", 1),
                    ("2026-10-30T13:10:00+00:00", "ready", 1),
                    ("2026-10-31T12:00:00+00:00", "ready", 1),
                ],
            ),
            (
                "?granularity=day",
                [
                    ("2026-10-30T00:00:00+00:00", "email", 1),
                    ("2026-10-30T00:00:00+00:00", "ready", 3),
                    ("2026-10-31T00:00:00+00:00", "ready", 1),
                ],
            ),
            (
                "?granularity=hour",
                [
                    ("2026-10-30T12:00:00+00:00", "email", 1),
                    ("2026-10-30T12:00:00+00:00", "ready", 2),
                    ("2026-10-30T13:00:00+00:00", "ready", 1),
                    ("2026-10-31T12:00:00+00:00", "ready", 1),
                ],
            ),
            (
                "?granularity=month",
                [
                    ("2026-10-01T00:00:00+00:00", "email", 1),
                    ("2026-10-01T00:00:00+00:00", "ready", 4),
                ],
            ),
        ]:
            with self.subTest(query=query):
                response = self.client.get(
                    url + query, HTTP_AUTHORIZATION=f"Token {self.token.key}"
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.json()["time_series"],
                    [
                        {"created": created, "action": action, "count": count}
                        for created, action, count in expected
                    ],
                )

    def test_funnel_statistics_unauthenticated(self):
        url = f"/api/funnels/{self.funnel.pk}/statistics/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_statistics_calendar_windows(self):
        for created in [
            datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC),
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 31, 23, 59, 59, tzinfo=UTC),
            datetime(2026, 2, 1, tzinfo=UTC),
        ]:
            counter = models.ActionCounter.objects.create(
                action=self.action, user=self.user
            )
            models.ActionCounter.objects.filter(pk=counter.pk).update(created=created)
        for granularity, expected in [
            ("year", [("2025-01-01", 1), ("2026-01-01", 3)]),
            ("month", [("2025-12-01", 1), ("2026-01-01", 2), ("2026-02-01", 1)]),
            (
                "day",
                [
                    ("2025-12-31", 1),
                    ("2026-01-01", 1),
                    ("2026-01-31", 1),
                    ("2026-02-01", 1),
                ],
            ),
        ]:
            with self.subTest(granularity=granularity):
                result = self.client.get(
                    f"/api/funnels/{self.funnel.pk}/statistics/?granularity={granularity}",
                    HTTP_AUTHORIZATION=f"Token {self.token.key}",
                )
                self.assertEqual(result.status_code, 200)
                self.assertEqual(
                    result.json()["time_series"],
                    [
                        {
                            "created": f"{day}T00:00:00+00:00",
                            "action": "ready",
                            "count": count,
                        }
                        for day, count in expected
                    ],
                )

    def test_statistics_short_window_boundaries(self):
        start = datetime(2026, 10, 30, 12, tzinfo=UTC)
        for granularity, seconds in [
            ("hour", 3600),
            ("30min", 1800),
            ("15min", 900),
            ("5min", 300),
            ("1min", 60),
            ("12sec", 12),
        ]:
            with self.subTest(granularity=granularity):
                models.ActionCounter.objects.all().delete()
                end = start + timedelta(seconds=seconds)
                for created in [start, end - timedelta(microseconds=1), end]:
                    counter = models.ActionCounter.objects.create(
                        action=self.action, user=self.user
                    )
                    models.ActionCounter.objects.filter(pk=counter.pk).update(
                        created=created
                    )
                result = self.client.get(
                    f"/api/funnels/{self.funnel.pk}/statistics/?granularity={granularity}",
                    HTTP_AUTHORIZATION=f"Token {self.token.key}",
                )
                self.assertEqual(result.status_code, 200)
                self.assertEqual(
                    result.json()["time_series"],
                    [
                        {"created": start.isoformat(), "action": "ready", "count": 2},
                        {"created": end.isoformat(), "action": "ready", "count": 1},
                    ],
                )

    def test_unique_viewers_deduplicates_users_across_actions_per_window(self):
        action2 = models.Action.objects.create(name="email", funnel=self.funnel)
        other_user = User.objects.create_user(username="viewer")
        start = datetime(2026, 10, 30, 12, tzinfo=UTC)
        for user, action, created in [
            (self.user, self.action, start),
            (self.user, self.action, start + timedelta(seconds=1)),
            (self.user, action2, start + timedelta(seconds=2)),
            (other_user, action2, start + timedelta(seconds=3)),
            (self.user, self.action, start + timedelta(minutes=1)),
        ]:
            counter = models.ActionCounter.objects.create(action=action, user=user)
            models.ActionCounter.objects.filter(pk=counter.pk).update(created=created)
        other_funnel = models.Funnel.objects.create(name="Other", project=self.project)
        other_action = models.Action.objects.create(name="other", funnel=other_funnel)
        other_counter = models.ActionCounter.objects.create(
            action=other_action, user=self.staff_user
        )
        models.ActionCounter.objects.filter(pk=other_counter.pk).update(created=start)
        result = self.client.get(
            f"/api/funnels/{self.funnel.pk}/statistics/",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            result.json()["unique_viewers"],
            [
                {"created": start.isoformat(), "count": 2},
                {"created": (start + timedelta(minutes=1)).isoformat(), "count": 1},
            ],
        )

    def test_unique_viewers_requires_funnel_ownership(self):
        token = Token.objects.create(user=self.staff_user)
        result = self.client.get(
            f"/api/funnels/{self.funnel.pk}/statistics/",
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        self.assertEqual(result.status_code, 404)

    def test_actions_for_token_are_scoped_to_tenant(self):
        other_tenant = models.Tenant.objects.create(name="Other tenant")
        other_tenant.owners.add(self.staff_user)
        project = models.Project.objects.create(
            name="Other project", tenant=other_tenant
        )
        funnel = models.Funnel.objects.create(name="Other funnel", project=project)
        models.Action.objects.create(name="Hidden action", funnel=funnel)
        result = self.client.post(
            reverse("token-actions"),
            {"token": f" {self.tenant.token} "},
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            result.json(),
            [
                {
                    "id": self.action.pk,
                    "name": self.action.name,
                    "funnel": self.funnel.pk,
                    "order": 0,
                }
            ],
        )

    def test_actions_for_token_rejects_invalid_tokens(self):
        for token in [None, "", "invalid", str(uuid.uuid4())]:
            with self.subTest(token=token):
                result = self.client.post(
                    reverse("token-actions"),
                    {"token": token},
                    content_type="application/json",
                )
                self.assertEqual(result.status_code, 401)

    def test_actions_for_token_empty_tenant(self):
        tenant = models.Tenant.objects.create(name="Empty tenant")
        tenant.owners.add(self.user)
        result = self.client.post(
            reverse("token-actions"),
            {"token": str(tenant.token)},
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), [])

    def test_tenant_creation_includes_creator_and_selected_owners(self):
        for name, payload, expected in [
            ("Personal", {}, {self.user.pk}),
            (
                "Shared",
                {"owners": [self.staff_user.pk]},
                {self.user.pk, self.staff_user.pk},
            ),
        ]:
            result = self.client.post(
                "/api/tenants/",
                {"name": name, **payload},
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Token {self.token.key}",
            )
            self.assertEqual(result.status_code, 201)
            self.assertEqual(set(result.json()["owners"]), expected)

    def test_shared_owners_can_access_resources_without_duplicating_counts(self):
        self.tenant.owners.add(self.staff_user)
        counter = models.ActionCounter.objects.create(
            action=self.action, user=self.user
        )
        for user in [self.user, self.staff_user]:
            token, _ = Token.objects.get_or_create(user=user)
            headers = {"HTTP_AUTHORIZATION": f"Token {token.key}"}
            for resource, pk in [
                ("tenants", self.tenant.pk),
                ("projects", self.project.pk),
                ("funnels", self.funnel.pk),
                ("actions", self.action.pk),
                ("action-counters", counter.pk),
            ]:
                with self.subTest(user=user.pk, resource=resource):
                    result = self.client.get(f"/api/{resource}/", **headers)
                    self.assertEqual(result.status_code, 200)
                    self.assertEqual([item["id"] for item in result.json()], [pk])
            stats = self.client.get(
                f"/api/funnels/{self.funnel.pk}/statistics/", **headers
            )
            self.assertEqual(stats.status_code, 200)
            self.assertEqual(stats.json()["result"], {"Funnel 1": {"ready": 1}})
            self.assertEqual(stats.json()["time_series"][0]["count"], 1)
            project = self.client.post(
                "/api/projects/",
                {"name": f"Shared {user.pk}", "tenant": self.tenant.pk},
                content_type="application/json",
                **headers,
            )
            self.assertEqual(project.status_code, 201)
            models.Project.objects.get(pk=project.json()["id"]).delete()

    def test_owners_can_manage_membership_and_cannot_leave_tenant_ownerless(self):
        url = f"/api/tenants/{self.tenant.pk}/"
        headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        for owners in [[], [999999]]:
            result = self.client.patch(
                url, {"owners": owners}, content_type="application/json", **headers
            )
            self.assertEqual(result.status_code, 400)
        result = self.client.patch(
            url,
            {"owners": [self.user.pk, self.staff_user.pk]},
            content_type="application/json",
            **headers,
        )
        self.assertEqual(result.status_code, 200)
        self.tenant.owners.remove(self.user)
        self.assertEqual(self.client.get(url, **headers).status_code, 404)

    def test_non_owner_cannot_manage_tenant_or_attach_resources(self):
        token = Token.objects.create(user=self.staff_user)
        headers = {"HTTP_AUTHORIZATION": f"Token {token.key}"}
        result = self.client.patch(
            f"/api/tenants/{self.tenant.pk}/",
            {"owners": [self.staff_user.pk]},
            content_type="application/json",
            **headers,
        )
        self.assertEqual(result.status_code, 404)
        for resource, payload in [
            ("projects", {"name": "Forbidden", "tenant": self.tenant.pk}),
            ("funnels", {"name": "Forbidden", "project": self.project.pk}),
            ("actions", {"name": "Forbidden", "funnel": self.funnel.pk}),
            ("action-counters", {"action": self.action.pk}),
        ]:
            result = self.client.post(
                f"/api/{resource}/", payload, content_type="application/json", **headers
            )
            self.assertEqual(result.status_code, 400)

    def test_global_visits_counts_all_owned_tenants_once(self):
        self.tenant.owners.add(self.staff_user)
        models.ActionCounter.objects.create(action=self.action, user=self.user)
        models.ActionCounter.objects.create(action=self.action, user=self.user)
        for name, owner in [("Owned", self.user), ("Unrelated", self.staff_user)]:
            tenant = models.Tenant.objects.create(name=name)
            tenant.owners.add(owner)
            project = models.Project.objects.create(name=name, tenant=tenant)
            funnel = models.Funnel.objects.create(name=name, project=project)
            action = models.Action.objects.create(name=name, funnel=funnel)
            models.ActionCounter.objects.create(action=action, user=self.user)
        result = self.client.get(
            reverse("global-visits"), HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), {"visits": 3})

    def test_global_visits_empty_and_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("global-visits")).status_code, 401)
        result = self.client.get(
            reverse("global-visits"), HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), {"visits": 0})

    def test_actions_follow_funnel_order_in_lists_and_statistics(self):
        self.action.order = 20
        self.action.save()
        first = models.Action.objects.create(name="10", funnel=self.funnel, order=10)
        second = models.Action.objects.create(name="2", funnel=self.funnel, order=10)
        models.ActionCounter.objects.create(action=self.action, user=self.user)
        expected = [first.pk, second.pk, self.action.pk]
        self.assertEqual(
            list(self.funnel.action_set.values_list("pk", flat=True)), expected
        )
        headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        listed = self.client.get("/api/actions/", **headers)
        self.assertEqual([item["id"] for item in listed.json()], expected)
        sample = self.client.post(
            reverse("token-actions"),
            {"token": str(self.tenant.token)},
            content_type="application/json",
        )
        self.assertEqual([item["id"] for item in sample.json()], expected)
        stats = self.client.get(f"/api/funnels/{self.funnel.pk}/statistics/", **headers)
        self.assertEqual(stats.json()["action_order"], ["10", "2", "ready"])
        self.assertEqual(
            stats.json()["result"][self.funnel.name], {"10": 0, "2": 0, "ready": 1}
        )

    def test_action_order_can_be_edited_and_rejects_negative_values(self):
        url = f"/api/actions/{self.action.pk}/"
        headers = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}
        result = self.client.patch(
            url, {"order": 5}, content_type="application/json", **headers
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["order"], 5)
        invalid = self.client.patch(
            url, {"order": -1}, content_type="application/json", **headers
        )
        self.assertEqual(invalid.status_code, 400)
        self.action.refresh_from_db()
        self.assertEqual(self.action.order, 5)

    def test_current_user_matches_api_token_instead_of_admin_session(self):
        self.client.force_login(self.staff_user)
        result = self.client.get(
            reverse("current-user"), HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            result.json(), {"id": self.user.pk, "username": self.user.username}
        )

    def test_current_user_requires_token(self):
        self.assertEqual(self.client.get(reverse("current-user")).status_code, 401)
