from rest_framework import serializers
from datetime import datetime
from django.db.models import Q
from .models import Service,LatestDepartures
import pytz
#from .models import *


class ServiceSerializer(serializers.ModelSerializer):
    missed = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ('id','departuretime','arrivaltime','depfriendly','arrfriendly','eta','schedule_status','missed')

    def get_missed(self,obj):
        if obj.departuretime <= pytz.utc.localize(datetime.now()):
            return True
        else:
            return False

class TrainServicesSerializer(serializers.ModelSerializer):
    #earliest_service = serializers.DateTimeField()
    services = serializers.SerializerMethodField()

    class Meta:
        model = LatestDepartures
        fields = ('station','station_name','services')

    def get_services(self,obj):
        services = Service.objects.filter(departure = obj)
        servicedata = ServiceSerializer(services,many=True)
        return servicedata.data
