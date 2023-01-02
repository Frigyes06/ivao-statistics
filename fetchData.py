"""
Copyright (c) 2023 Frigyes Erdosi-Szucs
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
"""

# TODO: camelCase all variable names, disambiguate names

import sys
import requests
from requests.exceptions import HTTPError
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import json


"""
Airport class, used to construct the dict list of airports in the code
Most likely replacable.
TODO: Replace class with dict construction in code
"""
class Airport:
    def __init__(self, code, deparures, arrivals):
        self.code = str(code)
        self.departures = deparures
        self.arrivals = arrivals

    def __str__(self):
        return f"code: {self.code}, departures: {self.departures}, arrivals: {self.arrivals}"


"""
Dict used in printing of menu options
"""
menuOptions = {
    1: 'List airports ranked by departures',
    2: 'List airports ranked by arrivals',
    3: 'List airports ranked by total traffic.',
    4: 'Prune list to XA airports',
    5: 'Exit',
}


"""
Used in sorting lists by number of departures
"""
def getDepartures(airport):
    return airport.get('departures')


"""
Used in sorting lists by number of arrivals
"""
def getArrivals(airport):
    return airport.get('arrivals')


"""
Used in sorting lists by total traffic (arrivals + departures)
"""
def getAll(airport):
    return airport.get('arrivals') + airport.get('departures')


"""
Sorts list by number of departures
TODO: extract sort to list function, make this print only.
"""
def airportsByDepartures(activeAirports):
    activeAirports.sort(key=getDepartures, reverse=True)
    airportList = []
    for airport in activeAirports:
        if airport['departures'] > 0:
            airportList.append(airport)
    for airport in airportList:
        print(f"{airport['code']} has {airport['departures']} departures")
    return airportList


"""
Sorts list by number of arrivals
TODO: extract sort to list function, make this print only.
"""
def airportsByArrivals(activeAirports):
    activeAirports.sort(key=getArrivals, reverse=True)
    airportList = []
    for airport in activeAirports:
        if airport['arrivals'] > 0:
            airportList.append(airport)
    for airport in airportList:
        print(f"{airport['code']} has {airport['arrivals']} arrivals")
    return airportList


"""
Sorts list by total traffic
TODO: extract sort to list function, make this print only.
"""
def airportsByTotal(activeAirports):
    activeAirports.sort(key=getAll, reverse=True)
    for airport in activeAirports:
        print(f"{airport['code']} has {airport['arrivals']} arrivals and {airport['departures']} departures")
    return activeAirports


"""
Prunes the airport list to only XA airports
Achieves this by checking if ICAO code starts with K or P
TODO: Check for edge cases, irregular airport codes.
"""
def pruneListToXA(activeAirports):
    airportList = []
    for airport in activeAirports:
        if airport['code'].startswith("K") or airport['code'].startswith("P"):
            airportList.append(airport)
    print("Pruned list to XA airports!")
    return airportList


"""
Prints out the CLI menu, as well as some basic statistics
"""
def print_menu():
    print(f"There are currently {online_pilots} pilots online")
    print(f"There are currently {online_atcs} ATCs online")
    for key, value in menuOptions.items():
        print(key, '--', value)


# TODO: Put all this (here to main function) inside a setup/startup function
utc = pytz.UTC
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

if __name__ == '__main__':
    while True:
        print_menu()
        option = ''
        try:
            option = int(input('Enter your choice: '))
        except:     # TODO: specify exception type
            print('Wrong input. Please enter a number ...')
        # Check what choice was entered and act accordingly
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
            sys.exit()
        else:
            print('Invalid option. Please enter a number between 1 and 5.')
