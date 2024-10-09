from datetime import datetime, timezone
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Count, F
from rest_framework.test import APIClient
from rest_framework import status

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    Crew,
    Flight,
    Route,
)
from airport.serializers import FlightListSerializer, FlightDetailSerializer


FLIGHTS_URL = reverse("airport:flight-list")


class PublicFlightApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.airplane_type = AirplaneType.objects.create(name="test-type")
        self.airplane1 = Airplane.objects.create(
            name="Test Boeing",
            rows=10,
            seats_in_row=6,
            airplane_type=self.airplane_type,
        )

        self.airport1 = Airport.objects.create(
            name="Test Ukrainian Airport",
            closet_big_city="Kyiv",
        )
        self.airport2 = Airport.objects.create(
            name="Test Polish Airport",
            closet_big_city="Krakow"
        )
        self.route1 = Route.objects.create(
            source=self.airport1, destination=self.airport2, distance=500
        )
        self.route2 = Route.objects.create(
            source=self.airport2, destination=self.airport1, distance=500
        )

        self.crew = Crew.objects.create(
            first_name="TestName",
            last_name="TestSurname"
        )
        self.flight1 = Flight.objects.create(
            route=self.route1,
            airplane=self.airplane1,
            departure_time=datetime(2023, 8, 30, 12, 30),
            arrival_time=datetime(2023, 8, 30, 13, 30),
        )
        self.flight1.crews.add(self.crew)
        self.flight2 = Flight.objects.create(
            route=self.route2,
            airplane=self.airplane1,
            departure_time=datetime(2023, 8, 28, 12, 30),
            arrival_time=datetime(2023, 8, 28, 13, 30),
        )
        self.flight2.crews.add(self.crew)

    def test_list_flights(self) -> None:
        res = self.client.get(FLIGHTS_URL)
        flights = Flight.objects.annotate(
            tickets_available=(
                (F("airplane__rows") * F("airplane__seats_in_row")) - Count("tickets")
            )
        )
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_flights_by_route_id(self) -> None:
        res = self.client.get(FLIGHTS_URL, {"route": f"{self.route2.id}"})

        matching_flights = Flight.objects.filter(route=self.route2).annotate(
            tickets_available=(
                (F("airplane__rows") * F("airplane__seats_in_row")) - Count("tickets")
            )
        )

        serializer = FlightListSerializer(matching_flights, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_flight_detail(self) -> None:
        url = reverse("airport:flight-detail", args=[self.flight1.id])
        res = self.client.get(url)

        serializer = FlightDetailSerializer(self.flight1)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_create_flight_not_allowed(self) -> None:
        data = {
            "route": self.route1,
            "airplane": self.airplane1,
            "departure_time": datetime(2023, 8, 30, 12, 30),
            "arrival_time": datetime(2023, 8, 30, 13, 30),
        }
        res = self.client.post(FLIGHTS_URL, data)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_flight_not_allowed(self) -> None:
        url = reverse("airport:flight-detail", args=[self.flight1.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateFlightApiTest(TestCase):
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

        self.airport1 = Airport.objects.create(
            name="Test Ukrainian Airport",
            closet_big_city="Kyiv",
        )
        self.airport2 = Airport.objects.create(
            name="Test Polish Airport",
            closet_big_city="Krakow"
        )
        self.route1 = Route.objects.create(
            source=self.airport1, destination=self.airport2, distance=500
        )
        self.route2 = Route.objects.create(
            source=self.airport2, destination=self.airport1, distance=500
        )
        self.crew = Crew.objects.create(
            first_name="TestName",
            last_name="TestSurname"
        )
        self.flight1 = Flight.objects.create(
            route=self.route1,
            airplane=self.airplane1,
            departure_time=datetime(2023, 8, 30, 12, 30),
            arrival_time=datetime(2023, 8, 30, 13, 30),
        )
        self.flight1.crews.add(self.crew)

    def test_create_flight_forbidden(self) -> None:
        data = {
            "route": self.route1,
            "airplane": self.airplane1,
            "departure_time": datetime(2023, 8, 30, 12, 30),
            "arrival_time": datetime(2023, 8, 30, 13, 30),
        }
        res = self.client.post(FLIGHTS_URL, data)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_flight_forbidden(self) -> None:
        url = reverse("airport:flight-detail", args=[self.flight1.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminUserFlightApiTest(TestCase):
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
        self.airport1 = Airport.objects.create(
            name="Test Ukrainian Airport",
            closet_big_city="Kyiv",
        )
        self.airport2 = Airport.objects.create(
            name="Test Polish Airport", closet_big_city="Krakow"
        )
        self.route1 = Route.objects.create(
            source=self.airport1, destination=self.airport2, distance=500
        )
        self.route2 = Route.objects.create(
            source=self.airport2, destination=self.airport1, distance=500
        )
        self.crew = Crew.objects.create(
            first_name="TestName", last_name="TestSurname"
        )
        self.flight1 = Flight.objects.create(
            route=self.route1,
            airplane=self.airplane1,
            departure_time=datetime(2023, 8, 30, 12, 30),
            arrival_time=datetime(2023, 8, 30, 13, 30),
        )
        self.flight1.crews.add(self.crew)

    def test_create_flight(self) -> None:
        payload = {
            "route": self.route1.id,
            "airplane": self.airplane1.id,
            "departure_time": datetime(2023, 8, 30, 12, 30, tzinfo=timezone.utc),
            "arrival_time": datetime(2023, 8, 30, 13, 30, tzinfo=timezone.utc),
        }
        res = self.client.post(FLIGHTS_URL, payload)
        flight = Flight.objects.get(pk=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload:
            if key == "route":
                self.assertEqual(payload[key], flight.route.id)
            elif key == "airplane":
                self.assertEqual(payload[key], flight.airplane.id)
            else:
                self.assertEqual(payload[key], getattr(flight, key))

    def test_update_flight(self) -> None:
        payload = {
            "route": self.route2.id,
            "airplane": self.airplane1.id,
            "departure_time": datetime(2023, 8, 30, 12, 30, tzinfo=timezone.utc),
            "arrival_time": datetime(2023, 8, 30, 13, 30, tzinfo=timezone.utc),
        }
        url = reverse("airport:flight-detail", args=[self.flight1.id])
        res = self.client.patch(url, payload)
        flight = Flight.objects.get(pk=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for key in payload:
            if key == "route":
                self.assertEqual(payload[key], flight.route.id)
            elif key == "airplane":
                self.assertEqual(payload[key], flight.airplane.id)
            else:
                self.assertEqual(payload[key], getattr(flight, key))

    def test_delete_flight(self) -> None:
        url = reverse("airport:flight-detail", args=[self.flight1.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
