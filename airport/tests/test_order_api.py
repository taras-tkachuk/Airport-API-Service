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


ORDERS_URL = reverse("airport:order-list")


class PublicOrderApiTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_order_list_for_unauthorized_user_forbidden(self) -> None:
        res = self.client.get(ORDERS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateOrderApiTest(TestCase):
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
            departure_time=datetime(2022, 8, 30, 12, 30),
            arrival_time=datetime(2022, 8, 30, 13, 30),
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
        self.order2 = Order.objects.create(user=self.user)
        self.ticket1 = Ticket.objects.create(
            row=9, seat=6, flight=self.flight1, order=self.order1
        )
        self.ticket2 = Ticket.objects.create(
            row=9, seat=5, flight=self.flight2, order=self.order2
        )

    def test_list_orders(self) -> None:
        res = self.client.get(ORDERS_URL)
        orders = Order.objects.all()
        serializer = OrderListSerializer(orders, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_create_order_without_tickets(self) -> None:
        payload = {"tickets": []}
        initial_order_count = Order.objects.count()
        res = self.client.post(reverse("airport:order-list"), payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Order.objects.count(), initial_order_count)

    def test_delete_order_not_allowed(self) -> None:
        url = reverse("airport:order-detail", args=[self.order1.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_order_not_allowed(self) -> None:
        url = reverse("airport:order-detail", args=[self.order1.id])
        res = self.client.put(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
