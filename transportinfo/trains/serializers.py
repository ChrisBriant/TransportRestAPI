from rest_framework import serializers
from datetime import datetime
from django.db.models import Q
from .models import Service,LatestDepartures
#from .models import *


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id','departuretime','arrivaltime','depfriendly','arrfriendly')

class TrainServicesSerializer(serializers.ModelSerializer):
    earliest_service = serializers.DateTimeField()
    services = serializers.SerializerMethodField()

    class Meta:
        model = LatestDepartures
        fields = ('station','station_name','earliest_service','services')

    def get_services(self,obj):
        services = Service.objects.filter(departure = obj)
        servicedata = ServiceSerializer(services,many=True)
        return servicedata.data
