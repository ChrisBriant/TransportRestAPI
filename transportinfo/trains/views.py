from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
#from .serializers import *
from datetime import datetime
from dateutil import parser
from nredarwin.webservice import DarwinLdbSession
import json,os


@api_view(['GET'])
def helloworld(request):
    return Response("Hello World!")

@api_view(['GET'])
def traintest(request):
    darwinkey = os.environ.get('DARWIN_WEBSERVICE_API_KEY')
    darwin_sesh = DarwinLdbSession(wsdl="https://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx", api_key=darwinkey)
    board = darwin_sesh.get_station_board('BSW')
    print(board.location_name)

    services = board.train_services
    servicelist=[]
    for s in services:
        traindict = dict()
        service_details = darwin_sesh.get_service_details(s.service_id)
        traindict['departuretime'] = service_details.std
        traindict['callingpoints'] = []
        callingpoints = service_details.subsequent_calling_points
        for c in callingpoints:
            callingpointdict = dict()
            callingpointdict['code'] = c.crs
            callingpointdict['name'] = c.location_name
            callingpointdict['arrivaltime'] = c.st
            traindict['callingpoints'].append(callingpointdict)
        servicelist.append(traindict)
    [print(si['departuretime']) for si in servicelist for stop in si['callingpoints'] if stop['code'] == 'HAG']
    #for si in servicelist:
        #[print(stop) for stop in si['callingpoints'] if stop['code'] == 'HAG']
    return Response("Train Test")
