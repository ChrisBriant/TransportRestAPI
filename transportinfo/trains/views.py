from django.shortcuts import render
from django.utils import timezone
from django.db.models import Min
from transportinfo.settings import DARWIN_SESH
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
#from .serializers import *
from datetime import datetime
from dateutil import parser
import json,os,pytz, requests as reqs
from datetime import datetime
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
        stationdict = dict()
        stationdict['from'] = station
        stationdict['name'] = board.location_name
        stationdict['servicelist']=[]
        services = board.train_services

        for s in services:
            traindict = dict()
            service_details = DARWIN_SESH.get_service_details(s.service_id)
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
        for s in services:
            #Create service
            service_details = DARWIN_SESH.get_service_details(s.service_id)
            departuretime = datetime.strptime(datenow + " " + service_details.std,'%d/%m/%Y %H:%M').astimezone(pytz.timezone("Europe/London"))
            callingpoints = service_details.subsequent_calling_points
            for c in callingpoints:
                if c.crs == destination:
                    arrivaltime = datetime.strptime(datenow + " " + c.st,'%d/%m/%Y %H:%M').astimezone(pytz.timezone("Europe/London"))
                    service = Service.objects.create(
                        departuretime = departuretime,
                        arrivaltime = arrivaltime,
                        depfriendly = departuretime.strftime('%H:%M'),
                        arrfriendly = arrivaltime.strftime('%H:%M'),
                        departure = departure
                    )

def updateservices_OLD(stationname,destination):
    now = datetime.now()

    # dd/mm/YY H:M:S
    datenow = now.strftime("%d/%m/%Y")
    board = DARWIN_SESH.get_station_board(stationname)
    stationdict = dict()
    stationdict['from'] = stationname
    stationdict['name'] = board.location_name
    stationdict['servicelist']=[]
    services = board.train_services
    if len(services) > 0:
        for s in services:
            traindict = dict()
            service_details = DARWIN_SESH.get_service_details(s.service_id)
            traindict['departuretime'] = datetime.strptime(datenow + " " + service_details.std,'%d/%m/%Y %H:%M').astimezone(pytz.timezone("Europe/London"))
            traindict['callingpoints'] = []
            callingpoints = service_details.subsequent_calling_points
            for c in callingpoints:
                if c.crs == destination:
                    callingpointdict = dict()
                    callingpointdict['code'] = c.crs
                    callingpointdict['name'] = c.location_name
                    callingpointdict['arrivaltime'] = datetime.strptime(datenow + " " + c.st,'%d/%m/%Y %H:%M').astimezone(pytz.timezone("Europe/London"))

                    traindict['callingpoints'].append(callingpointdict)
            if len(traindict['callingpoints']) > 0:
                stationdict['servicelist'].append(traindict)
        if len(stationdict['servicelist']) > 0:
            #For getting the minimum departure
            departures = [s['departuretime'] for s in stationdict['servicelist']]
            #Store the train departure object in the database
            stationdata = json.dumps(stationdict, default=convert_date_time)
            LatestDepartures.objects.create(
                station = stationname,
                earliest = min(departures),
                services = stationdata,
                destination = destination
            )
            return stationdata
        else:
            return None
    else:
        return None

@api_view(['GET'])
def trainslatest_OLD(request):
    #Collect information from query the stations from and the destination
    startstations = request.query_params['start'].split(",")
    destination = request.query_params['dest']

    #Get the info from the database
    stationservices = []
    for startstation in startstations:
        #Get the date time as the timezone appropriate for the UK
        utc_time = datetime.now()
        tz = pytz.timezone('Europe/London')
        now_uk_time = pytz.utc.localize(utc_time, is_dst=None).astimezone(tz)
        print(timezone.now().astimezone(pytz.utc))
        print(now_uk_time.astimezone(pytz.utc))
        #latestdepartures  = LatestDepartures.objects.filter(station=startstation,destination=destination,earliest__gte=timezone.now().astimezone(pytz.utc))
        latestdepartures  = LatestDepartures.objects.annotate(earliest_service=Min('service__departuretime')).filter(station=startstation,destination=destination,earliest_service__gte=timezone.now()).values('earliest_service','service__departuretime','service__arrivaltime')
        #[print(d.earliest) for d in latestdepartures ]
        print(latestdepartures)
        if len(latestdepartures) > 0:
            stationservices.append(latestdepartures)
        else:
            #pass
            if updateservices(startstation,destination):
                #Rerun query to get new entries
                latestdepartures  = LatestDepartures.objects.annotate(earliest_service=Min('service__departuretime')).filter(station=startstation,destination=destination,earliest_service__gte=timezone.now()).values()
                stationservices.append(latestdepartures)
        print(stationservices)
        #stationservices=json.loads(json.dumps(stationservices));
        #stationservices = [s.name for s in stationservices]
        #outdata = TrainServicesSerializer(data=stationservices,many=True)
        #if outdata.is_valid():
            #pass
        #else:
            #print(outdata.errors)
    return Response(json.dumps(stationservices,default=convert_date_time))
    #return Response(outdata.data)



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
    latestdepartures  = LatestDepartures.objects.annotate(earliest_service=Min('service__departuretime')).filter(station__in=startstations,destination=destination,earliest_service__gte=timezone.now())
    if len(latestdepartures) > 0:
        outdata = TrainServicesSerializer(latestdepartures,many=True)
    else:
        for startstation in startstations:
            updateservices(startstation,destination)
        #if updateservices(startstation,destination):
            #Rerun query to get new entries
        latestdepartures  = LatestDepartures.objects.annotate(earliest_service=Min('service__departuretime')).filter(station=startstation,destination=destination,earliest_service__gte=timezone.now())
        outdata = TrainServicesSerializer(latestdepartures,many=True)
    return Response(outdata.data)




#Bus information seems difficult to revisit at another time
@api_view(['GET'])
def busses(request):
    url = "https://transportapi.com/v3/uk/public/journey/from/lonlat:-2.126938,52.430035/to/lonlat:-1.890006,52.474318.json?app_id=MY_APP_ID&app_key=MY_APP_KEY&service=southeast"
    response = reqs.get(url)        # To execute get request
    print(response.status_code)     # To print http response code
    print(response.text)            # To print formatted JSON respons
    response_data = json.loads(response.text)
    for route in response_data["routes"]:
        for routepart in route["route_parts"]:
            if routepart["mode"] == "bus":
                print(routepart["from_point_name"],routepart["departure_time"])
    #[ print(route['duration']) for route in response_data["routes"] ]
    return Response("Busses")
