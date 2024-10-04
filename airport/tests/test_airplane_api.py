from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from airport.models import Airplane, AirplaneType
from airport.serializers import AirplaneListSerializer, AirplaneDetailSerializer

AIRPLANES_URL = reverse("airport:airplane-list")


class PublicAirplaneApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.airplane_type = AirplaneType.objects.create(name="test-type")
        self.airplane1 = Airplane.objects.create(
            name="Test Boeing",
            rows=10,
            seats_in_row=6,
            airplane_type=self.airplane_type,
        )
        self.airplane2 = Airplane.objects.create(
            name="Test Airbus",
            rows=10,
            seats_in_row=6,
            airplane_type=self.airplane_type,
        )

    def test_list_airplanes(self) -> None:
        res = self.client.get(AIRPLANES_URL)
        airplanes = Airplane.objects.all()
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_airplanes_by_name(self) -> None:
        res = self.client.get(AIRPLANES_URL, {"name": "boeing"})

        serializer1 = AirplaneListSerializer(self.airplane1)
        serializer2 = AirplaneListSerializer(self.airplane2)

        self.assertNotIn(serializer2.data, res.data)
        self.assertIn(serializer1.data, res.data)

    def test_retrieve_airplane_detail(self) -> None:
        url = reverse("airport:airplane-detail", args=[self.airplane1.id])
        res = self.client.get(url)

        serializer = AirplaneDetailSerializer(self.airplane1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_create_airplane_not_allowed(self) -> None:
        data = {
            "name": "New Boeing",
            "rows": 12,
            "seats_in_row": 9,
            "airplane_type": self.airplane_type,
        }
        res = self.client.post(AIRPLANES_URL, data)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_airplane_not_allowed(self) -> None:
        url = reverse("airport:airplane-detail", args=[self.airplane1.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateAirplaneApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "Testpassword123@"
        )
        self.client.force_authenticate(self.user)

        self.airplane_type = AirplaneType.objects.create(name="test-type")
        self.airplane1 = Airplane.objects.create(
            name="Test Boeing",
            rows=10,
            seats_in_row=6,
            airplane_type=self.airplane_type,
        )

    def test_create_airplane_forbidden(self) -> None:
        data = {
            "name": "New Boeing",
            "rows": 12,
            "seats_in_row": 9,
            "airplane_type": self.airplane_type,
        }
        res = self.client.post(AIRPLANES_URL, data)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_airplane_forbidden(self) -> None:
        url = reverse("airport:airplane-detail", args=[self.airplane1.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminUserAirplaneApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "Testpassword123@", is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.airplane_type = AirplaneType.objects.create(name="test-type")
        self.airplane1 = Airplane.objects.create(
            name="Test Boeing",
            rows=10,
            seats_in_row=6,
            airplane_type=self.airplane_type,
        )

    def test_create_airplane(self) -> None:
        payload = {
            "name": "New Boeing",
            "rows": 12,
            "seats_in_row": 9,
            "airplane_type": self.airplane_type.id,
        }
        res = self.client.post(AIRPLANES_URL, payload)
        airplane = Airplane.objects.get(pk=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            if key == "airplane_type":
                self.assertEqual(payload[key], airplane.airplane_type.id)
            else:
                self.assertEqual(payload[key], getattr(airplane, key))

    def test_update_airplane(self) -> None:
        payload = {
            "name": "Changed Boeing",
            "rows": 12,
            "seats_in_row": 9,
            "airplane_type": self.airplane_type.id,
        }
        url = reverse("airport:airplane-detail", args=[self.airplane1.id])
        res = self.client.patch(url, payload)
        airplane = Airplane.objects.get(pk=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for key in payload:
            if key == "airplane_type":
                self.assertEqual(payload[key], airplane.airplane_type.id)
            else:
                self.assertEqual(payload[key], getattr(airplane, key))

    def test_delete_airplane(self) -> None:
        url = reverse("airport:airplane-detail", args=[self.airplane1.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
