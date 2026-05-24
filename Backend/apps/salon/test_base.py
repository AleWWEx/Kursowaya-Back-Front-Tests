"""Общие фикстуры для курсового тестирования API."""
from __future__ import annotations

from datetime import timedelta

from django.db.models.signals import post_save
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.salon.models import Appointment, Service, Status
from apps.salon.signals import ensure_ai_data_for_appointment
from apps.users.models import Role, User


class CourseApiTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(ensure_ai_data_for_appointment, sender=Appointment)

    @classmethod
    def tearDownClass(cls):
        post_save.connect(ensure_ai_data_for_appointment, sender=Appointment)
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        cls.role_client, _ = Role.objects.get_or_create(
            role_name="client", defaults={"role_description": "Клиент"}
        )
        cls.role_master, _ = Role.objects.get_or_create(
            role_name="master", defaults={"role_description": "Мастер"}
        )
        cls.role_admin, _ = Role.objects.get_or_create(
            role_name="admin", defaults={"role_description": "Администратор"}
        )
        for code, name in (
            ("pending", "Ожидает"),
            ("confirmed", "Подтверждена"),
            ("completed", "Завершена"),
            ("cancelled", "Отменена"),
        ):
            Status.objects.get_or_create(status_code=code, defaults={"status_name": name})

        cls.status_pending = Status.objects.get(status_code="pending")
        cls.status_confirmed = Status.objects.get(status_code="confirmed")
        cls.status_completed = Status.objects.get(status_code="completed")
        cls.status_cancelled = Status.objects.get(status_code="cancelled")

        cls.service, _ = Service.objects.get_or_create(
            service_name="Тестовая стрижка",
            defaults={
                "duration_minutes": 60,
                "price": "1500.00",
                "category": "Стрижки",
            },
        )

        cls.admin = User.objects.create_user(
            username="admin_course",
            email="admin_course@test.local",
            password="adminpass12",
            full_name="Админ Тест",
            role=cls.role_admin,
            is_staff=True,
        )
        cls.master = User.objects.create_user(
            username="master_course",
            email="master_course@test.local",
            password="masterpass12",
            full_name="Мастер Тест",
            role=cls.role_master,
        )
        cls.client_a = User.objects.create_user(
            username="client_a_course",
            email="client_a_course@test.local",
            password="clientpass12",
            full_name="Клиент А Тест",
            role=cls.role_client,
        )
        cls.client_b = User.objects.create_user(
            username="client_b_course",
            email="client_b_course@test.local",
            password="clientpass12",
            full_name="Клиент Б Тест",
            role=cls.role_client,
        )

    def auth(self, user: User) -> dict[str, str]:
        token = str(RefreshToken.for_user(user).access_token)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def future_start(self, *, hours: int = 0, days: int = 7) -> str:
        dt = timezone.now() + timedelta(days=days, hours=hours)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    def past_start(self) -> str:
        dt = timezone.now() - timedelta(days=1)
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    def appointment_payload(
        self,
        *,
        client: User | None = None,
        master: User | None = None,
        start: str | None = None,
        status: Status | None = None,
        comment: str = "",
    ) -> dict:
        return {
            "client_id": (client or self.client_a).pk,
            "master_id": (master or self.master).pk,
            "service_id": self.service.pk,
            "status_id": (status or self.status_pending).pk,
            "start_datetime": start or self.future_start(),
            "comment": comment,
        }
