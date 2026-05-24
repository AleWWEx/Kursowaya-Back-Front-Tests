from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.salon.models import Appointment, Transaction
from apps.salon.test_base import CourseApiTestCase

User = get_user_model()


class ServerApiTests(CourseApiTestCase):

    def test_s01_register_client_success(self):
        """S-01: регистрация клиента."""
        email = "new_client_s01@test.local"
        response = self.client.post(
            "/api/auth/register/",
            {
                "full_name": "Новый Клиент Тест",
                "email": email,
                "password": "securepass8",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email__iexact=email)
        self.assertEqual((user.role.role_name or "").lower(), "client")
        self.assertTrue(user.check_password("securepass8"))

    def test_s02_register_short_password(self):
        """S-02: регистрация с коротким паролем."""
        email = "short_pw_s02@test.local"
        response = self.client.post(
            "/api/auth/register/",
            {
                "full_name": "Короткий Пароль",
                "email": email,
                "password": "short",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(email__iexact=email).exists())

    def test_s03_login_jwt(self):
        """S-03: вход JWT."""
        response = self.client.post(
            "/api/auth/login/",
            {"username": self.client_a.email, "password": "clientpass12"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], self.client_a.email)

    def test_s04_profile_without_token(self):
        """S-04: профиль без токена."""
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, 401)

    def test_s05_services_list_public(self):
        """S-05: список услуг без авторизации."""
        response = self.client.get("/api/services/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, list))
        self.assertGreater(len(response.data), 0)
        item = response.data[0]
        for field in ("id", "service_name", "price", "category"):
            self.assertIn(field, item)

    def test_s06_create_service_forbidden_for_client(self):
        """S-06: создание услуги клиентом."""
        before = self.client.get("/api/services/").data
        count_before = len(before) if isinstance(before, list) else 0
        response = self.client.post(
            "/api/services/",
            {
                "service_name": "Услуга от клиента S06",
                "duration_minutes": 30,
                "price": "500.00",
                "category": "Тест",
            },
            format="json",
            **self.auth(self.client_a),
        )
        self.assertEqual(response.status_code, 403)
        after = self.client.get("/api/services/").data
        count_after = len(after) if isinstance(after, list) else 0
        self.assertEqual(count_before, count_after)

    def test_s07_appointment_in_past(self):
        """S-07: запись в прошлом."""
        response = self.client.post(
            "/api/appointments/",
            self.appointment_payload(start=self.past_start()),
            format="json",
            **self.auth(self.client_a),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("start_datetime", response.data)

    def test_s08_overlapping_master_slots(self):
        """S-08: пересечение слотов мастера."""
        start = self.future_start(hours=2)
        first = self.client.post(
            "/api/appointments/",
            self.appointment_payload(start=start),
            format="json",
            **self.auth(self.client_a),
        )
        self.assertIn(first.status_code, (200, 201))

        second = self.client.post(
            "/api/appointments/",
            self.appointment_payload(client=self.client_b, start=start),
            format="json",
            **self.auth(self.client_b),
        )
        self.assertGreaterEqual(second.status_code, 400)
        self.assertLess(second.status_code, 500)
        active = Appointment.objects.filter(
            master=self.master,
            start_datetime__isnull=False,
        ).exclude(status__status_code__iexact="cancelled")
        self.assertEqual(active.count(), 1)

    def test_s09_client_sees_only_own_appointments(self):
        """S-09: список записей только своего клиента."""
        self.client.post(
            "/api/appointments/",
            self.appointment_payload(start=self.future_start(days=8)),
            format="json",
            **self.auth(self.client_a),
        )
        self.client.post(
            "/api/appointments/",
            self.appointment_payload(
                client=self.client_b,
                start=self.future_start(days=9),
            ),
            format="json",
            **self.auth(self.client_b),
        )

        response = self.client.get("/api/appointments/", **self.auth(self.client_a))
        self.assertEqual(response.status_code, 200)
        for row in response.data:
            self.assertEqual(row["client"]["id"], self.client_a.pk)

    def test_s10_pay_appointment(self):
        """S-10: оплата записи администратором."""
        created = self.client.post(
            "/api/appointments/",
            self.appointment_payload(start=self.future_start(days=10)),
            format="json",
            **self.auth(self.client_a),
        )
        self.assertIn(created.status_code, (200, 201))
        appointment_id = created.data["id"]

        pay = self.client.post(
            f"/api/appointments/{appointment_id}/pay/",
            {"amount": "1500.00"},
            format="json",
            **self.auth(self.admin),
        )
        self.assertEqual(pay.status_code, 201)
        self.assertTrue(Transaction.objects.filter(appointment_id=appointment_id).exists())
        appointment = Appointment.objects.get(pk=appointment_id)
        self.assertEqual(appointment.payment_status, Appointment.PaymentStatus.PAID)
