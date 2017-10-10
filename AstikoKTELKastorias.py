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

url = "http://astikoktelkastorias.gr"
driver.get(url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "AStikoKTELKastorias",
                   name = "Urban Transportations of Kastoria Perfecture",
                   timezone = "Europe/Athens",
                   url = "http://astikoktelkastorias.gr")


# Retrieve route links
route_links = driver.find_elements_by_xpath("//div[@class='g-block size-100']/ul[@class='g-sublevel']/li/a")
print("Found %s route links" % len(route_links))

route_urls = []

# Ignore the first link, it's a self reference
for route_link in route_links[1:]:
    href = route_link.get_attribute("href")
    route_urls.append(href)

station_list = []
station_locations = []
station_objects = []
durations = {}
service_ids = []
route_ids = []

for url in route_urls:
    print("Fetching %s" % url)
    driver.get(url)

    # Retrieve directions
    directionA = driver.find_element_by_xpath("//div[@class='moduletable ']/h3").text.strip().encode("utf-8")
    directionB = driver.find_element_by_xpath("//div[@class='moduletable ']/div[@class='custom']/h3").text.strip().encode("utf-8")
    directions = [directionA, directionB]
    print("Found %s directions" % len(directions))

    for direction_index, direction in enumerate(directions):
        # For some routes, the return direction does not list all stops
        # So, let's set it as a reverse list of the forward route
        if direction_index == 1:
            route_id = '-'.join(directions[0].split("-")[::-1])
        else:
            route_id = direction

        print("RouteID: %s" % route_id)

        route = schedule.AddRoute(short_name="",
                                  long_name=route_id,
                                  route_type="Bus")

        stops = route_id.split("-")


        departure_stop = stops[0].strip()
        print("Departure: %s" % departure_stop)
        destination_stop = stops[-1].strip()
        print("Destination: %s" % destination_stop)

        if departure_stop not in station_list:
            resp = gmaps.geocode(departure_stop + " Kastoria Greece")

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
            resp = gmaps.geocode(destination_stop + " Kastoria Greece")

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

        # For each direction, read all hours and days to construct the service IDs
        days = driver.find_elements_by_xpath("//div[@class='moduletable ']/div[@class='custom']/ul")
        print("Found %s days of service" % len(days))

        # Half the days refer to each direction
        direction_per_days = days[direction_index * (len(days) / len(directions)) : (direction_index + 1) * (len(days) / len(directions))]
        print("Checking %s days" % len(direction_per_days))

        service_days_times = {}

        service_id = route_id + "-"
        for direction_per_day in direction_per_days:
            # The first list element is the day
            day = direction_per_day.find_element_by_xpath("li[1]").text.strip().encode("utf-8")
            service_id += day

            times = direction_per_day.find_elements_by_xpath("li")[1:]

            for time in times:
                time = re.search("\d{2}:\d{2}", time.text.strip().encode("utf-8")).group()
                if time not in service_days_times:
                    service_days_times[time] = []
                service_days_times[time].append(day)

        print(service_id)
        service_period = transitfeed.ServicePeriod(service_id)

        if service_id not in service_ids:

            service_ids.append(service_id)

            for service_time, days in service_days_times.iteritems():
                if "Καθημερινές" in days:
                    for day in range(0,5):
                        service_period.SetDayOfWeekHasService(day)
                if "Τετάρτες" in days:
                    service_period.SetDayOfWeekHasService(2)
                if "Σάββατο" in days:
                    service_period.SetDayOfWeekHasService(5)
                if "Κυριακή" in days:
                    service_period.SetDayOfWeekHasService(6)

            today = datetime.datetime.today()
            service_period.SetStartDate(today.strftime('%Y%m%d'))
            service_period.SetEndDate((today + datetime.timedelta(weeks=3 * 4)).strftime('%Y%m%d'))
            schedule.AddServicePeriodObject(service_period)

        trip = route.AddTrip(schedule, headsign=route_id, service_period=service_period)

        departure_time = datetime.datetime.strptime(service_time, "%H:%M")
        trip.AddStopTime(departure_obj, stop_time=departure_time.strftime("%H:%M:%S"))

        # Calculate the distance between departure and destination stops
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

        print("Whole trip duration %s" % duration)
        time2 = (departure_time + datetime.timedelta(minutes=duration)).strftime("%H:%M:%S")
        if int(time2.split(":")[0]) < int(departure_time.strftime("%H:%M:%S").split(":")[0]):
            time2 = str(24 + int(time2.split(":")[0])) + ":" + time2.split(":")[1] + ":00"

        trip.AddStopTime(destination_obj, stop_time=time2)


schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)

driver.quit()
