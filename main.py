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

import sys
import requests
from requests.exceptions import HTTPError
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import json


class Airport:
    """
    Airport class, used to construct the dict list of airports in the code
    Most likely replacable.
    """

    def __init__(self, code, deparures, arrivals):
        self.code = str(code)
        self.departures = deparures
        self.arrivals = arrivals

    def __str__(self):
        return f"code: {self.code}, departures: {self.departures}, arrivals: {self.arrivals}"


MenuOptions = {
    1: 'List airports ranked by departures',
    2: 'List airports ranked by arrivals',
    3: 'List airports ranked by total traffic.',
    4: 'Prune list to XA airports',
    5: 'Exit',
}


def airports_by_departures():
    """
    Sorts list by number of departures
    TODO: extract sort to list function, make this print only.
    """
    airportList = filter(lambda element: element['departures'] > 0, sorted(ACTIVE_AIRPORTS, key=lambda element: element['departures'], reverse=True))

    for airport in airportList:
        print(f"{airport['code']} has {airport['departures']} departures")
    return airportList


def airports_by_arrivals():
    """
    Sorts list by number of arrivals
    TODO: extract sort to list function, make this print only.
    """
    airportList = filter(lambda element: element['arrivals'] > 0, sorted(ACTIVE_AIRPORTS, key=lambda element: element['arrivals'], reverse=True))
    
    for airport in airportList:
        print(f"{airport['code']} has {airport['arrivals']} arrivals")
    return airportList


def airports_by_total():
    """
    Sorts list by total traffic
    TODO: extract sort to list function, make this print only.
    """
    airportList = sorted(ACTIVE_AIRPORTS, key=lambda element: element['arrivals'] + element['departures'], reverse=True)
    for airport in airportList:
        print(f"{airport['code']} has {airport['arrivals']} arrivals and {airport['departures']} departures")
    return airportList


def prune_to_xa(activeAirports):
    """
    Prunes the airport list to only XA airports
    Achieves this by checking if ICAO code starts with K or P
    TODO: Check for edge cases, irregular airport codes.
    """
    airportList = filter(lambda element: element['code'].startswith(("K", "PA", "PH", "TJ", "C")), ACTIVE_AIRPORTS)
    """
    airportList = []
    for airport in ACTIVE_AIRPORTS:
        if airport['code'].startswith("K") or airport['code'].startswith("P"):
            airportList.append(airport)
    """
    print("Pruned list to XA airports!")
    return airportList


def print_menu():
    """Prints out the CLI menu, as well as some basic statistics"""
    print(f"There are currently {ONLINE_PILOTS} pilots online")
    print(f"There are currently {ONLINE_ATCS} ATCs online")
    for key, value in MenuOptions.items():
        print(key, '--', value)


def startup():
    """Startup function, fetches and processes JSON"""
    tz_London = timezone('Europe/London')

    # load whazzup.json, look for cached data.
    try:
        with open('whazzup.json', 'r') as file:
            jsonResponse = json.load(file)
    except FileNotFoundError:
        print("wazzup.json not found. Will create!")
    except Exception as e:
        print(f'Other error occurred: {e}')

    # Extract timestamp from JSON, get current time
    try:
        lastRequest = datetime.strptime(jsonResponse['updatedAt'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC)
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
        except Exception as e:
            print(f'Other error occurred: {e}')

        with open('whazzup.json', 'w+') as file:
            json.dump(jsonResponse, file)
    else:
        print("last request was less than 15 minutes ago! Using cached data...")

    onlinePilots = len(jsonResponse["clients"]["pilots"])

    onlineATCs = len(jsonResponse["clients"]["atcs"])

    activeAirports = []
    arrivalAirports = []
    departureAirports = []

    # TODO: Clean this sphagetti up, make it more phytony
    for i in range(onlinePilots):
        departureAirports.append(jsonResponse["clients"]["pilots"][i]["flightPlan"]["departureId"])
        arrivalAirports.append(jsonResponse["clients"]["pilots"][i]["flightPlan"]["arrivalId"])

    for airport in departureAirports:
        new_airport = vars(Airport(airport, departureAirports.count(airport), arrivalAirports.count(airport)))
        if new_airport not in activeAirports:
            activeAirports.append(new_airport)

    for airport in arrivalAirports:
        new_airport = vars(Airport(airport, departureAirports.count(airport), arrivalAirports.count(airport)))
        if new_airport not in activeAirports:
            activeAirports.append(new_airport)
    return onlinePilots, onlineATCs, activeAirports


if __name__ == '__main__':
    ONLINE_PILOTS, ONLINE_ATCS, ACTIVE_AIRPORTS = startup()
    while True:
        print_menu()
        option = ''
        try:
            option = int(input('Enter your choice: '))
        except:     # TODO: specify exception type
            print('Wrong input. Please enter a number ...')
        # Check what choice was entered and act accordingly
        if option == 1:
            airports_by_departures()
        elif option == 2:
            airports_by_arrivals()
        elif option == 3:
            airports_by_total()
        elif option == 4:
            ACTIVE_AIRPORTS = prune_to_xa(ACTIVE_AIRPORTS)
        elif option == 5:
            print('Thanks for using my statistics tool!')
            sys.exit()
        else:
            print('Invalid option. Please enter a number between 1 and 5.')
