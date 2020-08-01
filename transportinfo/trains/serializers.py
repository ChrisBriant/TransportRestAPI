from rest_framework import serializers
from datetime import datetime
from django.db.models import Q
#from .models import *

"""
class SchoolSerializer(serializers.ModelSerializer):
    poster_id = serializers.ReadOnlyField(source='poster.id')
    deaths = serializers.SerializerMethodField()

    class Meta:
        model = School
        fields = ('id','name','dateadded','deaths','poster_id')

    def get_deaths(self,obj):

        try:
            schooldeaths = Person.objects.filter(persondiedschool__school=obj)
            deathdata = PeopleSerializer(schooldeaths,many=True).data
        except Exception as e:
            deathdata = None
        return deathdata
        """
