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

days = {
    0 : "Δευτέρα",
    1 : "Τρίτη",
    2 : "Τετάρτη",
    3 : "Πέμπτη",
    4 : "Παρασκευή",
    5 : "Σάββατο",
    6 : "Κυριακή"
}

url = "https://www.ktel-thesprotias.gr/gr/dromologia"
driver.get(url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "KTELThesprotias",
                   name = "ΥΠΕΡΑΣΤΙΚΟ ΚΤΕΛ Ν. ΘΕΣΠΡΩΤΙΑΣ",
                   timezone = "Europe/Athens",
                   url = "https://www.ktel-thesprotias.gr/")


# Retrieve route links
route_links = driver.find_elements_by_xpath("//td[@class='list-title']/a")
print("Found %s route links" % len(route_links))

route_urls = []
for link in route_links:
    route_urls.append(link.get_attribute("href"))


station_list = []
station_locations = []
station_objects = []
durations = {}
service_ids = []
route_ids = []

for url in route_urls:
    print("Fetching %s" % url)
    driver.get(url)

    # Retrieve the directions of the route
    directions = driver.find_elements_by_xpath("//caption")
    print("Found %s directions" % len(directions))

    for direction_index, direction in enumerate(directions):

        route_id = direction.text.strip().encode("utf-8")
        print("RouteID: %s" % route_id)

        route = schedule.AddRoute(short_name = "",
                                  long_name = route_id,
                                  route_type = "Bus")

        stops = route_id.split("-")

        departure_stop = stops[0].strip()
        print("Departure: %s" % departure_stop)
        destination_stop = stops[-1].strip()
        print("Destination: %s" % destination_stop)

        if departure_stop not in station_list:
            resp = gmaps.geocode(departure_stop + ", Greece")


            if not resp:
                continue

            departure_location = resp[0]['geometry']['location']
            departure_obj = schedule.AddStop(lng = departure_location['lng'],
                                             lat = departure_location['lat'],
                                             name = departure_stop,
                                             stop_id = departure_stop.upper())

            station_list.append(departure_stop)
            station_locations.append(departure_location)
            station_objects.append(departure_obj)
        else:
            departure_obj = station_objects[station_list.index(departure_stop)]
            departure_location = station_locations[station_list.index(departure_stop)]

        if destination_stop not in station_list:
            resp = gmaps.geocode(destination_stop + ", Greece")

            if not resp:
                continue

            destination_location = resp[0]['geometry']['location']
            destination_obj = schedule.AddStop(lng = destination_location['lng'],
                                               lat = destination_location['lat'],
                                               name = destination_stop,
                                               stop_id = destination_stop.upper())

            station_list.append(destination_stop)
            station_locations.append(destination_location)
            station_objects.append(destination_obj)
        else:
            destination_obj = station_objects[station_list.index(destination_stop)]
            destination_location = station_locations[station_list.index(destination_stop)]

        trips = driver.find_elements_by_xpath("//div[@itemprop='articleBody']/table[%s]/tbody/tr" % (direction_index + 1))
        print("Found %s trips" % (len(trips)))

        service_ids = []
        for trip in trips:
            tds = trip.find_elements_by_xpath("td")

            if not tds[0].text.strip():
                continue

            # For every trip, retrieve the days it's in service
            service_id = route_id
            for td_index, td in enumerate(tds[1:-1]):
                if td.text.strip():
                    service_id += "_" + days[td_index]

            service_period = transitfeed.ServicePeriod(service_id)

            if service_id not in service_ids:
                service_ids.append(service_id)

                for td_index, td in enumerate(tds[1:-1]):
                    if td.text.strip():
                        service_period.SetDayOfWeekHasService(td_index)

                today = datetime.datetime.today()
                service_period.SetStartDate(today.strftime('%Y%m%d'))
                service_period.SetEndDate((today + datetime.timedelta(weeks=7*4)).strftime('%Y%m%d'))
                schedule.AddServicePeriodObject(service_period)

            trip = route.AddTrip(schedule, headsign=route_id, service_period=service_period)

            departure_time = tds[0].text.strip().encode("utf-8").replace(".", ":").replace(",", ":")

            # Calculate the distance between departure and destination stops
            duration_id = direction.text.encode("utf-8").strip()
            if duration_id not in durations:
                resp = gmaps.distance_matrix(origins = departure_location,
                                             destinations = destination_location,
                                             mode = 'driving')
                print(resp)

                # Get duration in minutes
                duration = resp['rows'][0]['elements'][0]['duration']['value'] / 60

                durations[duration_id] = duration
                print("Duration: %s" % duration)

            else:
                duration = durations[duration_id]

            time1 = datetime.datetime.strptime(departure_time, "%H:%M")
            trip.AddStopTime(departure_obj, stop_time=time1.strftime("%H:%M:%S"))

            time2 = (time1 + datetime.timedelta(minutes = duration)).strftime("%H:%M:%S")
            if int(time2.split(":")[0]) < int(time1.strftime("%H:%M:%S").split(":")[0]):
                time2 = str(24 + int(time2.split(":")[0])) + ":" + time2.split(":")[1] + ":00"

            trip.AddStopTime(destination_obj, stop_time=time2)


schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)

driver.quit()
