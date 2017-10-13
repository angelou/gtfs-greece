#!/usr/bin/env python
# coding=utf-8

from selenium import webdriver
from selenium.webdriver.support.ui import Select
import selenium.common.exceptions
import os
import re
from geopy.geocoders import Nominatim
import googlemaps
import datetime
import transitfeed
import time
import json

driver = webdriver.Chrome()
geolocator = Nominatim()
gmaps = googlemaps.Client(key='your-key-here')

url = "http://www.astikoxanthis.gr/?page_id=19"
driver.get(url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "AstikoKTELXanthis",
                   name = "Urban Transportations of Ksanthi Perfecture",
                   timezone = "Europe/Athens",
                   url = "http://www.astikoxanthis.gr")


# Retrieve routes
routes = driver.find_elements_by_xpath("//table[@id='t3']/tbody/tr")
print("Found %s routes" % len(routes))

station_list = []
station_locations = []
station_objects = []
durations = {}
service_ids = []
route_ids = []

for route in routes:

    td = route.find_elements_by_xpath("td")

    departure_stop = "ΞΑΝΘΗ"
    print("Departure: %s" % departure_stop)
    destination_stop = td[0].text.strip().encode("utf-8")
    print("Destination: %s" % destination_stop)

    route_id = "ΞΑΝΘΗ - " + destination_stop
    print("RouteID: %s" % route_id)

    route = schedule.AddRoute(short_name="",
                              long_name=route_id,
                              route_type="Bus")

    if departure_stop not in station_list:
        resp = gmaps.geocode(departure_stop + ", Ξάνθη, Ελλάδα")

        if not resp:
            print("#### COULD NOT FIND DEPARTURE LOCATION")
            continue

        departure_location = resp[0]['geometry']['location']
        departure_obj = schedule.AddStop(lng=departure_location['lng'],
                                         lat=departure_location['lat'],
                                         name=departure_stop,
                                         stop_id=departure_stop.upper())

        station_list.append(departure_stop)
        station_locations.append(departure_location)
        station_objects.append(departure_obj)
    else:
        departure_obj = station_objects[station_list.index(departure_stop)]
        departure_location = station_locations[station_list.index(departure_stop)]

    if destination_stop not in station_list:
        resp = gmaps.geocode(destination_stop + ", Ξάνθη, Ελλάδα")

        if not resp:
            print("#### COULD NOT FIND DESTINATION LOCATION")
            continue

        destination_location = resp[0]['geometry']['location']
        destination_obj = schedule.AddStop(lng=destination_location['lng'],
                                           lat=destination_location['lat'],
                                           name=destination_stop,
                                           stop_id=destination_stop.upper())

        station_list.append(destination_stop)
        station_locations.append(destination_location)
        station_objects.append(destination_obj)
    else:
        destination_obj = station_objects[station_list.index(destination_stop)]
        destination_location = station_locations[station_list.index(destination_stop)]

    # Every route may have service Mon-Fri, Sat, Sun
    route_info = td[1].text.strip().encode("utf-8").split("\n")

    try:
        for line_index in range(0, len(route_info), 2):
            day = route_info[line_index].replace(":","").split()[1]
            print("Day: %s" % day)
            times = re.findall("\d{1,2}:\d{2}", route_info[line_index + 1])
            print("Times: %s" % times)

            service_id = route_id + " - " + day
            service_period = transitfeed.ServicePeriod(service_id)

            if "ΚΑΘΗΜΕΡΙΝΗΣ" in day:
                for day in range(0,5):
                    service_period.SetDayOfWeekHasService(day)
            elif "ΣΑΒΒΑΤΟΥ" in day:
                service_period.SetDayOfWeekHasService(5)
            elif "ΚΥΡΙΑΚΗΣ" in day:
                service_period.SetDayOfWeekHasService(6)

            today = datetime.datetime.today()
            service_period.SetStartDate(today.strftime('%Y%m%d'))
            service_period.SetEndDate((today + datetime.timedelta(weeks=3 * 4)).strftime('%Y%m%d'))
            schedule.AddServicePeriodObject(service_period)

            trip_obj = route.AddTrip(schedule, headsign=route_id, service_period=service_period)

            duration_id = route_id
            if duration_id not in durations:
                resp = gmaps.distance_matrix(origins=departure_location,
                                             destinations=destination_location,
                                             mode='driving')
                print(resp)

                # Get duration in minutes
                duration = resp['rows'][0]['elements'][0]['duration']['value'] / 60

                durations[duration_id] = duration
                print("Duration: %s" % duration)

            else:
                duration = durations[duration_id]

            for service_time in times:
                departure_time = datetime.datetime.strptime(service_time, "%H:%M")
                trip_obj.AddStopTime(departure_obj, stop_time=departure_time.strftime("%H:%M:%S"))

                time2 = (departure_time + datetime.timedelta(minutes=duration)).strftime("%H:%M:%S")
                if int(time2.split(":")[0]) < int(departure_time.strftime("%H:%M:%S").split(":")[0]):
                    time2 = str(24 + int(time2.split(":")[0])) + ":" + time2.split(":")[1] + ":00"

                trip_obj.AddStopTime(destination_obj, stop_time=time2)

    except IndexError:
        continue


schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)

driver.quit()
