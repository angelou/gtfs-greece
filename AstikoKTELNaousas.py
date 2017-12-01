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

url = "http://astna.gr/index.html"
driver.get(url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "AstikoKTELNaousas",
                   name = "ΚΤΕΛ Αστικών Γραμμών Νάουσας",
                   timezone = "Europe/Athens",
                   url = "http://astna.gr")


# Retrieve route links
route_links = []
route_links_partA = driver.find_elements_by_xpath("//div[@id='leftpanel']/div[@class='graypanel']/p[2]/span/a")
route_links.extend(route_links_partA)
route_links_partB = driver.find_elements_by_xpath("//div[@id='leftpanel']/div[@class='graypanel']/p[2]/a")
route_links.extend(route_links_partB)

route_urls = []
# Ignore the first link, it's a self reference
for route_link in route_links:
    href = route_link.get_attribute("href")
    route_urls.append(href)

print("Found %s route URLs" % len(route_urls))

station_list = []
station_locations = []
station_objects = []
durations = {}
service_ids = []
route_ids = []

for url in route_urls:
    print("Fetching %s" % url)
    driver.get(url)

    header = ""
    header_parts = driver.find_elements_by_xpath("//div[@id='contenttext']/div[1]/p[@class='titletext']")
    for header_part in header_parts:
        header += " " + header_part.text.encode("utf-8")

    route_id = "Νάουσα - " + " ".join(header.split()[4:])
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
        resp = gmaps.geocode(departure_stop + " Naousa, Imatheia, Greece")

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
        resp = gmaps.geocode(destination_stop + " Naousa, Imatheia, Greece")

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


    # Services are on Workdays and Saturday
    service_id_workday = route_id + " - Καθημερινές"
    service_period_workday = transitfeed.ServicePeriod(service_id_workday)
    for day in range(0, 5):
        service_period_workday.SetDayOfWeekHasService(day)

    service_id_saturday = route_id + " - Σάββατο"
    service_period_saturday = transitfeed.ServicePeriod(service_id_saturday)
    service_period_saturday.SetDayOfWeekHasService(5)

    today = datetime.datetime.today()
    service_period_workday.SetStartDate(today.strftime('%Y%m%d'))
    service_period_workday.SetEndDate((today + datetime.timedelta(weeks=7*4)).strftime('%Y%m%d'))
    service_period_saturday.SetStartDate(today.strftime('%Y%m%d'))
    service_period_saturday.SetEndDate((today + datetime.timedelta(weeks=7*4)).strftime('%Y%m%d'))
    schedule.AddServicePeriodObject(service_period_workday)
    schedule.AddServicePeriodObject(service_period_saturday)

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

    # Get trip lines
    trip_lines = driver.find_elements_by_xpath("//div[@id='contenttext']/div[@class='bodytext']/div[1]/table/tbody/tr")
    print("Found %s trip lines" % (len(trip_lines) - 1))

    for line in trip_lines:
        # For every line, we have 2 columns
        tds = line.find_elements_by_xpath("td")

        for td_index, td in enumerate(tds):
            td = td.text.strip()

            if "-" in td:
                continue

            if td_index == 0:
                service_period = service_period_workday
            else:
                service_period = service_period_saturday

            trip = route.AddTrip(schedule, headsign=route_id, service_period=service_period)
            departure_time = datetime.datetime.strptime(td, "%H:%M")
            trip.AddStopTime(departure_obj, stop_time=departure_time.strftime("%H:%M:%S"))

            time2 = (departure_time + datetime.timedelta(minutes=duration)).strftime("%H:%M:%S")
            trip.AddStopTime(destination_obj, stop_time=time2)


schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)

driver.quit()
