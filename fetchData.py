import requests
from requests.exceptions import HTTPError
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import json

class Airport:
    def __init__(self, code, deparures, arrivals):
        self.code = str(code)
        self.departures = deparures
        self.arrivals = arrivals
    def __str__(self):
        return f"[code: {self.code}, departures: {self.departures}, arrivals: {self.arrivals}]"

menu_options = {
    1: 'List airports ranked by departures',
    2: 'List airports ranked by arrivals',
    3: 'List airports ranked by total traffic.',
    4: 'Prune list to XA airports',
    5: 'Exit',
}

def getDepartures(airport):
    return airport.get('departures')

def getArrivals(airport):
    return airport.get('arrivals')

def getAll(airport):
    return airport.get('arrivals') + airport.get('departures')

def airportsByDepartures(activeAirports):
    activeAirports.sort(key=getDepartures, reverse=True)
    airportList=[]
    for airport in activeAirports:
        if airport['departures'] > 0:
            airportList.append(airport)
    for airport in airportList:
        print(f"{airport['code']} has {airport['departures']} departures")
    return airportList

def airportsByArrivals(activeAirports):
    activeAirports.sort(key=getArrivals, reverse=True)
    airportList=[]
    for airport in activeAirports:
        if airport['arrivals'] > 0:
            airportList.append(airport)
    for airport in airportList:
        print(f"{airport['code']} has {airport['arrivals']} arrivals")
    return airportList

def airportsByTotal(activeAirports):
    activeAirports.sort(key=getAll, reverse=True)
    for airport in activeAirports:
        print(f"{airport['code']} has {airport['arrivals']} arrivals and {airport['departures']} departures")
    return activeAirports

def pruneListToXA(activeAirports):
    airportList = []
    for airport in activeAirports:
        if airport['code'].startswith("K") or airport['code'].startswith("P"):
            airportList.append(airport)
    print("Pruned list to XA airports!")
    return airportList

def print_menu():
    print(f"There are currently {online_pilots} pilots online")
    print(f"There are currently {online_atcs} ATCs online")
    for key in menu_options.keys():
        print (key, '--', menu_options[key] )

utc=pytz.UTC
tz_London = timezone('Europe/London')

# load whazzup.json, look for cached data.
try:
    with open('whazzup.json', 'r') as file:
        jsonResponse = json.load(file)
except Exception as e:
    pass

# Extract timestamp from JSON, get current time
try:
    lastRequest = utc.localize(datetime.strptime(jsonResponse['updatedAt'], '%Y-%m-%dT%H:%M:%S.%fZ')) 
except Exception as e:
    jsonResponse = 1
now = datetime.now(tz_London)

# If whazzup.json is outdated, nonexistent or corrupted, fetch it from Whazzup API
if jsonResponse == 1 or lastRequest + timedelta(minutes=15) < now:
    print("last request was more than 15 minutes ago! Updating...")
    try:
        response = requests.get('https://api.ivao.aero/v2/tracker/whazzup')
        response.raise_for_status()
        # access JSOn content
        jsonResponse = response.json()
        #print("Entire JSON response")
        #print(jsonResponse)

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')
    
    with open('whazzup.json', 'w+') as file:
        json.dump(jsonResponse, file)
else:
    print("last request was less than 15 minutes ago! Using cached data...")

online_pilots = len(jsonResponse["clients"]["pilots"])

online_atcs = len(jsonResponse["clients"]["atcs"])

active_airports = []
arrival_airports = []
departure_airports = []

for i in range(online_pilots):
    departure_airports.append(jsonResponse["clients"]["pilots"][i]["flightPlan"]["departureId"])
    arrival_airports.append(jsonResponse["clients"]["pilots"][i]["flightPlan"]["arrivalId"])

for airport in departure_airports:
    new_airport = vars(Airport(airport, departure_airports.count(airport), arrival_airports.count(airport)))
    if new_airport not in active_airports:
        active_airports.append(new_airport)

for airport in arrival_airports:
    new_airport = vars(Airport(airport, departure_airports.count(airport), arrival_airports.count(airport)))
    if new_airport not in active_airports:
        active_airports.append(new_airport)

if __name__=='__main__':
    while(True):
        print_menu()
        option = ''
        try:
            option = int(input('Enter your choice: '))
        except:
            print('Wrong input. Please enter a number ...')
        #Check what choice was entered and act accordingly
        if option == 1:
            airportsByDepartures(active_airports)
        elif option == 2:
            airportsByArrivals(active_airports)
        elif option == 3:
            airportsByTotal(active_airports)
        elif option == 4:
            active_airports = pruneListToXA(active_airports)
        elif option == 5:
            print('Thanks for using my statistics tool!')
            exit()
        else:
            print('Invalid option. Please enter a number between 1 and 5.')
