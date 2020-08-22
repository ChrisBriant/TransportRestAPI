from django.db import models


class LatestDepartures(models.Model):
    station = models.CharField(max_length=3,null=False)
    station_name = models.CharField(max_length=255,null=False)
    destination = models.CharField(max_length=3,null=False)
    daterecorded = models.DateTimeField(auto_now=True)

class Service(models.Model):
    departuretime = models.DateTimeField()
    arrivaltime = models.DateTimeField()
    depfriendly = models.CharField(max_length=5,null=False)
    arrfriendly = models.CharField(max_length=5,null=False)
    departure = models.ForeignKey(LatestDepartures, on_delete=models.CASCADE)
    eta = models.CharField(max_length=10,null=False)
    schedule_status = models.CharField(max_length=20,null=False)
