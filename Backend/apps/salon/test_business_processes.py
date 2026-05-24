from __future__ import annotations

from django.utils import timezone

from apps.salon.models import Appointment, AuditLog
from apps.salon.test_base import CourseApiTestCase


class BusinessProcessTests(CourseApiTestCase):
    """Сквозные сценарии предметной области."""

    def test_b01_appointment_lifecycle(self):
        """B-01: регистрация → запись → confirm → complete → оплата."""
        reg = self.client.post(
            "/api/auth/register/",
            {
                "full_name": "Жизненный Цикл Клиент",
                "email": "lifecycle_b01@test.local",
                "password": "lifecycle8",
            },
            format="json",
        )
        self.assertEqual(reg.status_code, 201)

        login = self.client.post(
            "/api/auth/login/",
            {"username": "lifecycle_b01@test.local", "password": "lifecycle8"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        access = login.data["access"]
        auth = {"HTTP_AUTHORIZATION": f"Bearer {access}"}

        created = self.client.post(
            "/api/appointments/",
            self.appointment_payload(start=self.future_start(days=11)),
            format="json",
            **auth,
        )
        self.assertIn(created.status_code, (200, 201))
        appointment_id = created.data["id"]

        confirmed = self.client.post(
            f"/api/appointments/{appointment_id}/confirm/",
            {},
            format="json",
            **self.auth(self.admin),
        )
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(confirmed.data["status"]["status_code"], "confirmed")

        completed = self.client.post(
            f"/api/appointments/{appointment_id}/complete/",
            {},
            format="json",
            **self.auth(self.admin),
        )
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.data["status"]["status_code"], "completed")

        paid = self.client.post(
            f"/api/appointments/{appointment_id}/pay/",
            {"amount": "1500.00"},
            format="json",
            **self.auth(self.admin),
        )
        self.assertEqual(paid.status_code, 201)

        appointment = Appointment.objects.get(pk=appointment_id)
        self.assertEqual(appointment.status.status_code, "completed")
        self.assertEqual(appointment.payment_status, Appointment.PaymentStatus.PAID)

        logs = AuditLog.objects.filter(action_object=f"appointment:{appointment_id}")
        action_types = set(logs.values_list("action_type", flat=True))
        for expected in ("created", "confirmed", "completed", "payment_created"):
            self.assertIn(expected, action_types)

    def test_b02_double_booking_rejected(self):
        """B-02: двойное бронирование одного слота."""
        start = self.future_start(days=12, hours=1)
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
        active = Appointment.objects.filter(master=self.master).exclude(
            status__status_code__iexact="cancelled"
        )
        self.assertEqual(active.count(), 1)

    def test_b03_client_cancel_with_comment(self):
        """B-03: отмена записи клиентом."""
        created = self.client.post(
            "/api/appointments/",
            self.appointment_payload(start=self.future_start(days=13)),
            format="json",
            **self.auth(self.client_a),
        )
        self.assertIn(created.status_code, (200, 201))
        appointment_id = created.data["id"]
        cancel_comment = "Отмена по личным причинам (B-03)"

        cancelled = self.client.delete(
            f"/api/appointments/{appointment_id}/",
            {"comment": cancel_comment},
            format="json",
            **self.auth(self.client_a),
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data["status"]["status_code"], "cancelled")
        self.assertIn(cancel_comment, cancelled.data.get("comment", ""))

        logs = AuditLog.objects.filter(
            action_object=f"appointment:{appointment_id}",
            action_type="cancelled",
        )
        self.assertTrue(logs.exists())

    def test_b04_rbac_foreign_appointment_hidden(self):
        """B-04: клиент B не видит запись клиента A."""
        created = self.client.post(
            "/api/appointments/",
            self.appointment_payload(start=self.future_start(days=14)),
            format="json",
            **self.auth(self.client_a),
        )
        self.assertIn(created.status_code, (200, 201))
        appointment_id = created.data["id"]

        listing = self.client.get("/api/appointments/", **self.auth(self.client_b))
        self.assertEqual(listing.status_code, 200)
        ids = [row["id"] for row in listing.data]
        self.assertNotIn(appointment_id, ids)

        detail = self.client.get(
            f"/api/appointments/{appointment_id}/",
            **self.auth(self.client_b),
        )
        self.assertEqual(detail.status_code, 404)

    def test_b05_audit_log_tracks_actions(self):
        """B-05: журнал аудита фиксирует цепочку действий."""
        created = self.client.post(
            "/api/appointments/",
            self.appointment_payload(start=self.future_start(days=15)),
            format="json",
            **self.auth(self.client_a),
        )
        self.assertIn(created.status_code, (200, 201))
        appointment_id = created.data["id"]

        self.client.post(
            f"/api/appointments/{appointment_id}/confirm/",
            {},
            format="json",
            **self.auth(self.admin),
        )
        self.client.delete(
            f"/api/appointments/{appointment_id}/",
            {"comment": "Отмена для аудита B-05"},
            format="json",
            **self.auth(self.client_a),
        )

        logs = AuditLog.objects.filter(action_object=f"appointment:{appointment_id}")
        action_types = set(logs.values_list("action_type", flat=True))
        for expected in ("created", "confirmed", "cancelled"):
            self.assertIn(expected, action_types)
