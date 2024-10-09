from datetime import datetime
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    Crew,
    Flight,
    Order,
    Route,
    Ticket,
)
from airport.serializers import OrderListSerializer


class PrivateTicketApiTest(TestCase):
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
        self.flight2 = Flight.objects.create(
            route=self.route2,
            airplane=self.airplane1,
            departure_time=datetime(2023, 8, 28, 12, 30),
            arrival_time=datetime(2023, 8, 28, 13, 30),
        )
        self.flight2.crews.add(self.crew)
        self.order1 = Order.objects.create(user=self.user)
        self.ticket1 = Ticket.objects.create(
            row=9, seat=6, flight=self.flight1, order=self.order1
        )

    def test_add_ticket_to_order(self) -> None:
        payload = {
            "tickets": [
                {"row": 7, "seat": 6, "flight": self.flight1.id},
                {"row": 7, "seat": 4, "flight": self.flight2.id},
            ]
        }
        res = self.client.post(reverse("airport:order-list"), payload, format="json")
        ticket1_id = res.data["tickets"][0]["id"]
        ticket2_id = res.data["tickets"][1]["id"]

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        created_ticket1 = Ticket.objects.get(pk=ticket1_id)
        created_ticket2 = Ticket.objects.get(pk=ticket2_id)
        self.assertTrue(created_ticket1)
        self.assertTrue(created_ticket2)

        self.assertEqual(
            created_ticket1.order.created_at.replace(microsecond=0),
            self.order1.created_at.replace(microsecond=0),
        )
        self.assertEqual(
            created_ticket2.order.created_at.replace(microsecond=0),
            self.order1.created_at.replace(microsecond=0),
        )

        new_order = Order.objects.latest("created_at")
        self.assertEqual(new_order.user, self.user)

    def test_add_ticket_with_taken_seat_not_allowed(self) -> None:
        payload = {
            "tickets": [
                {"row": 9, "seat": 6, "flight": self.flight1.id},
            ]
        }
        initial_order_count = Order.objects.count()
        res = self.client.post(reverse("airport:order-list"), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Order.objects.count(), initial_order_count)

    def test_add_ticket_with_taken_seat_but_for_other_flight(self) -> None:
        payload = {
            "tickets": [
                {"row": 9, "seat": 6, "flight": self.flight2.id},
            ]
        }
        res = self.client.post(reverse("airport:order-list"), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_add_ticket_with_non_exist_seat(self) -> None:
        payload = {
            "tickets": [
                {"row": 9, "seat": 16, "flight": self.flight1.id},
            ]
        }
        res = self.client.post(reverse("airport:order-list"), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_ticket_with_non_exist_row(self) -> None:
        payload = {
            "tickets": [
                {"row": 15, "seat": 4, "flight": self.flight1.id},
            ]
        }
        res = self.client.post(reverse("airport:order-list"), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_tickets_with_taken_seat_and_other_with_correct_data(self) -> None:
        payload = {
            "tickets": [
                {"row": 4, "seat": 1, "flight": self.flight1.id},
                {"row": 9, "seat": 6, "flight": self.flight1.id},
            ]
        }
        res = self.client.post(reverse("airport:order-list"), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
