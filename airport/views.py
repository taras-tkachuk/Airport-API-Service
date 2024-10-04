from django.db.models import F, Count, Prefetch
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from airport.models import (
    Crew,
    Airport,
    AirplaneType,
    Route,
    Airplane,
    Order,
    Flight,
    Ticket,
)
from airport.permissions import IsAdminOrReadOnly
from airport.serializers import (
    CrewSerializer,
    AirportSerializer,
    AirplaneTypeSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    RouteSerializer,
    AirplaneListSerializer,
    AirplaneDetailSerializer,
    AirplaneSerializer,
    OrderSerializer,
    OrderListSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    FlightSerializer,
)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminOrReadOnly,)


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    permission_classes = (IsAdminOrReadOnly,)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all().select_related("source", "destination")
    permission_classes = (IsAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer

        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = (IsAdminOrReadOnly,)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all().select_related("airplane_type")
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get("name")

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer

        if self.action == "retrieve":
            return AirplaneDetailSerializer

        return AirplaneSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "name",
                type={"type": "string"},
                description="Filter by name (example: ?name=Boeing)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        queryset = self.queryset.select_related(
            "route__source",
            "route__destination",
            "airplane__airplane_type"
        ).prefetch_related(
            "crews",
        ).annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets")
            )
        )

        route = self.request.query_params.get("route")
        if route:
            route_id = int(route)
            queryset = queryset.filter(route__id=route_id)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer

        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "route",
                type={"type": "number"},
                description="Filter by route id (example: ?route=1)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        def get_prefetch_obj(
            prefetch_alias, prefetched_class, *inner_prefetches
        ):
            return Prefetch(
                lookup=prefetch_alias,
                queryset=prefetched_class.objects.select_related(*inner_prefetches),
            )

        queryset = self.queryset.filter(user=self.request.user).prefetch_related(
            get_prefetch_obj(
                "tickets",
                Ticket,
                "flight__route__destination",
                "flight__airplane",
                "flight__route__source",
            ), "tickets__flight__crews"
        )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
