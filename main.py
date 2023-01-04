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
    airport_list = {key if val['departures'] else "": val for key, val in ACTIVE_AIRPORTS.items()}
    if "" in airport_list:
        del airport_list[""]

    for code, data in sorted(airport_list.items(), key=lambda element: element[1]['departures'], reverse=True):
        print(f"{code} has {data['departures']} departures")
    return airport_list


def airports_by_arrivals():
    """
    Sorts list by number of arrivals
    TODO: extract sort to list function, make this print only.
    """
    airport_list = { key if val['arrivals'] else "": val for key, val in ACTIVE_AIRPORTS.items() }
    if "" in airport_list:
        del airport_list[""]

    for code, data in sorted(airport_list.items(), key=lambda element: element[1]['arrivals'], reverse=True):
        print(f"{code} has {data['arrivals']} arrivals")
    return airport_list


def airports_by_total():
    """
    Sorts list by total traffic
    TODO: extract sort to list function, make this print only.
    """
    airport_list = dict(ACTIVE_AIRPORTS.items())
    if "" in airport_list:
        del airport_list[""]

    for code, data in sorted(airport_list.items(), key=lambda element: element[1]['arrivals'] + element[1]['departures'], reverse=True):
        print(f"{code} has {data['arrivals']} arrivals and {data['departures']}")
    return airport_list


def prune_to_xa():
    """
    Prunes the airport list to only XA airports
    Achieves this by checking if ICAO code starts with K or P
    TODO: Check for edge cases, irregular airport codes.
    """
    only_xa_airports = {code: ACTIVE_AIRPORTS[code] for code in filter(lambda code: code.startswith(("K", "C", "P", "PA", "PH", "TJ", "C")), ACTIVE_AIRPORTS.keys())}

    print("Pruned list to XA airports!")
    return only_xa_airports


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
            json_response = json.load(file)
    except FileNotFoundError:
        print("wazzup.json not found. Will create!")
    except Exception as e:
        print(f'Other error occurred: {e}')

    # Extract timestamp from JSON, get current time
    try:
        last_request = datetime.strptime(json_response['updatedAt'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC)
    except Exception as e:
        json_response = 1
    now = datetime.now(tz_London)

    # If whazzup.json is outdated, nonexistent or corrupted, fetch it from Whazzup API
    if json_response == 1 or last_request + timedelta(minutes=15) < now:
        print("last request was more than 15 minutes ago! Updating...")
        try:
            response = requests.get('https://api.ivao.aero/v2/tracker/whazzup')
            response.raise_for_status()
            # access JSOn content
            json_response = response.json()

        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except Exception as e:
            print(f'Other error occurred: {e}')

        with open('whazzup.json', 'w+') as file:
            json.dump(json_response, file)
    else:
        print("last request was less than 15 minutes ago! Using cached data...")

    online_pilots = len(json_response["clients"]["pilots"])

    online_atcs = len(json_response["clients"]["atcs"])

    arrival_airports = []
    departure_airports = []

    for i in range(online_pilots):
        departure_airports.append(json_response["clients"]["pilots"][i]["flightPlan"]["departureId"])
        arrival_airports.append(json_response["clients"]["pilots"][i]["flightPlan"]["arrivalId"])

    new_airport = {}

    for airport in [str(ap) for ap in filter(lambda ap: not(ap in new_airport), departure_airports + arrival_airports)]:
        new_airport[airport] = {'departures': departure_airports.count(airport), 'arrivals': arrival_airports.count(airport)}

    return online_pilots, online_atcs, new_airport


if __name__ == '__main__':
    ONLINE_PILOTS, ONLINE_ATCS, ACTIVE_AIRPORTS = startup()
    while True:
        print_menu()
        option = ''
        try:
            option = int(input('Enter your choice: '))
        except:     # TODO: specify exception type
            print('Wrong input. Please enter a number ...')
        match option:
            case 1:
                airports_by_departures()
            case 2:
                airports_by_arrivals()
            case 3:
                airports_by_total()
            case 4:
                ACTIVE_AIRPORTS = prune_to_xa()
            case 5:
                print('Thanks for using my statistics tool!')
                sys.exit()
            case _:
                print('Invalid option. Please enter a number between 1 and 5.')
