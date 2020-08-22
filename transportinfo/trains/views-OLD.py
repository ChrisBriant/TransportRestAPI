from django.shortcuts import render
from django.utils import timezone
from django.db.models import Min,Max
from transportinfo.settings import DARWIN_SESH
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
#from .serializers import *
from dateutil import parser
import json,os,pytz, requests as reqs
from datetime import datetime, timedelta
from .models import LatestDepartures, Service
from .serializers import TrainServicesSerializer


@api_view(['GET'])
def helloworld(request):
    return Response("Hello World!")

@api_view(['GET'])
def traintest(request):
    #Collect information from query the stations from and the destination
    startstations = request.query_params['start'].split(",")
    destination = request.query_params['dest']

    #Darwin setup


    #Station board for each start station
    stationservices = []
    for station in startstations:
        print(station)
        board = DARWIN_SESH.get_station_board(station)
        print(board.__dict__)
        stationdict = dict()
        stationdict['from'] = station
        stationdict['name'] = board.location_name
        stationdict['servicelist']=[]
        services = board.train_services

        for s in services:
            traindict = dict()
            service_details = DARWIN_SESH.get_service_details(s.service_id)
            #print(service_details.__dict__)
            traindict['departuretime'] = service_details.std
            traindict['callingpoints'] = []
            callingpoints = service_details.subsequent_calling_points
            for c in callingpoints:
                if c.crs == destination:
                    callingpointdict = dict()
                    callingpointdict['code'] = c.crs
                    callingpointdict['name'] = c.location_name
                    callingpointdict['arrivaltime'] = c.st
                    traindict['callingpoints'].append(callingpointdict)
            if len(traindict['callingpoints']) > 0:
                stationdict['servicelist'].append(traindict)
        stationservices.append(stationdict)
    print(stationservices)
    #stationservices = [{'name':s['name']} for s in stationservices]
    outdata = TrainServicesSerializer(data=stationservices,many=True)
    print(outdata.is_valid())
    #[print(si['departuretime']) for si in servicelist for stop in si['callingpoints'] if stop['code'] == 'HAG']
    #for si in servicelist:
        #[print(stop) for stop in si['callingpoints'] if stop['code'] == 'HAG']
    return Response(json.dumps(stationservices))

def convert_date_time(o):
    if isinstance(o, datetime):
        return o.__str__()

def updateservices(stationname,destination):
    now = datetime.now()
    # dd/mm/YY H:M:S
    datenow = now.strftime("%d/%m/%Y")
    try:
        board = DARWIN_SESH.get_station_board(stationname)
        stationdict = dict()
        services = board.train_services
        if len(services) > 0:
            #Create departure in DB
            departure = LatestDepartures.objects.create(
                station = stationname,
                station_name=board.location_name,
                destination = destination
            )
            destination_found_count = 0
            print("Nu,mber of services",len(services))
            for s in services:
                #Create service
                service_details = DARWIN_SESH.get_service_details(s.service_id)
                departuretime = datetime.strptime(datenow + " " + service_details.std,'%d/%m/%Y %H:%M').astimezone(pytz.timezone("Europe/London"))
                #Need to handle None
                if service_details.etd:
                    train_schedule_status = service_details.etd
                else:
                    train_schedule_status = "Not listed"
                if service_details.eta:
                    train_eta = service_details.eta
                else:
                    train_eta = "Not listed"
                callingpoints = service_details.subsequent_calling_points
                if len(callingpoints) > 0:
                    destination_found = False
                    for c in callingpoints:
                        print(c.crs,destination)
                        if c.crs == destination:
                            destination_found = True
                            destination_found_count += 1
                            arrivaltime = datetime.strptime(datenow + " " + c.st,'%d/%m/%Y %H:%M').astimezone(pytz.timezone("Europe/London"))
                            try:
                                tz = timezone('Europe/London')
                                service = Service.objects.create(
                                    departuretime = departuretime,
                                    arrivaltime = arrivaltime,
                                    depfriendly = departuretime.strftime('%H:%M'),
                                    #depfriendly = pytz.utc.localize(departuretime, is_dst=None).astimezone(tz).strftime('%H:%M'),
                                    arrfriendly = arrivaltime.strftime('%H:%M'),
                                    schedule_status = train_schedule_status,
                                    eta = train_eta,
                                    departure = departure
                                )
                            except Exception as e:
                                print(e)
                                departure.delete
                    if not destination_found:
                        #Remove the departure object if it doesn't exist
                        #print("THERE ARE NO CALLING POINTS")
                        departure.delete
        print("Nu,mber of services",destination_found_count)
    except Exception as e:
        print(e)




@api_view(['GET'])
def trainslatest(request):
    #Collect information from query the stations from and the destination
    startstations = request.query_params['start'].split(",")
    destination = request.query_params['dest']

    #Get the info from the database

    #Get the date time as the timezone appropriate for the UK
    #utc_time = datetime.now()
    #tz = pytz.timezone('Europe/London')
    #now_uk_time = pytz.utc.localize(utc_time, is_dst=None).astimezone(tz)
    #latestdepartures  = LatestDepartures.objects.annotate(earliest_service=Min('service__departuretime')).filter(station__in=startstations,destination=destination,earliest_service__gte=timezone.now())
    latestdepartures  = LatestDepartures.objects.annotate(earliest_service=Min('service__departuretime')).filter(station__in=startstations,destination=destination)
    #latestdepartures  = LatestDepartures.objects.filter(station__in=startstations,destination=destination).annotate(earliest_service=Min('service__departuretime'))

    if len(latestdepartures) > 0:
        if latestdepartures[0].earliest_service:
            earliest = latestdepartures[0].earliest_service
            print("Earliest Exists",earliest)
        else:
            earliest = timezone.now() + timedelta(minutes=-1)
            print("Earliest",earliest)
            #print(latestdepartures[0].__dict__)
            [print(l.__dict__) for l in latestdepartures]
        if earliest >= timezone.now():
            outdata = TrainServicesSerializer(latestdepartures,many=True)
        else:
            #purge database of old services
            [service.delete for service in latestdepartures]
            outdata = update_and_serialize(startstations,destination)
    else:
        outdata = update_and_serialize(startstations,destination)
    return Response(outdata.data)
    #return Response(json.dumps("true"))

#Update the services and then serialize for output
def update_and_serialize(startstations,destination):
    for startstation in startstations:
        updateservices(startstation,destination)
    #if updateservices(startstation,destination):
        #Rerun query to get new entries
    latestdepartures  = LatestDepartures.objects.annotate(earliest_service=Min('service__departuretime')).filter(station=startstation,destination=destination,earliest_service__gte=timezone.now())
    outdata = TrainServicesSerializer(latestdepartures,many=True)
    return outdata
