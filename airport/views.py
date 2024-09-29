from rest_framework import viewsets

from airport.serializers import CrewSerializer
from airport.models import Crew


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
