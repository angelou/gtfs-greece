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

url = "http://www.ktel-imathias.gr/trips"
driver.get(url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "KTELImatheias",
                   name = "Urban and Suburban Transportations of Imatheia Perfecture",
                   timezone = "Europe/Athens",
                   url = "http://www.ktel-imathias.gr")


# Retrieve route links
# Route urls might be covering more that one pages

pages = driver.find_elements_by_xpath("//div[@class='pagination']/a[@class='navlinks']")[-1].text
print("Routes are listed in %s different pages" % pages)

route_urls = []
for page in range(1, int(pages) + 1):
    page_url = "http://www.ktel-imathias.gr/trips/view_all/%s" % page
    driver.get(page_url)

    route_links = driver.find_elements_by_xpath("//h2/a")

    print("Found %s route URLs" % len(route_links))

    for route_link in route_links:
        href = route_link.get_attribute("href")
        route_urls.append(href)


station_list = []
station_locations = []
station_objects = []
durations = {}
service_ids = []
route_ids = []

for url in route_urls[:-1]:
    print("Fetching %s" % url)
    driver.get(url)

    # Retrieve all stops
    stops = driver.find_elements_by_xpath("//div[@class='kd-list icon-list']/ul/li")
    print("Found %s stops" % len(stops))


    # Retrieve route id
    route_id = driver.find_element_by_xpath("//div[@class='col-md-6']/h1").text.split(",")[0].strip().encode("utf-8")
    print("RouteID: %s" % route_id)

    route = schedule.AddRoute(short_name = "",
                              long_name = route_id,
                              route_type = "Bus")

    # Retrieve trips
    trips = driver.find_elements_by_xpath("//div[@class='col-md-12']/table[@class='kd-table kd-tableone']/tbody/tr")
    print("Found %s trips" % len(trips))


    # Add stop times for every trip
    for trip in trips:

        tds = trip.find_elements_by_xpath("td")

        # For every trip, retrieve the days it's in service
        service_id = route_id
        for td_index, td in enumerate(tds[1:]):
            try:
                td.find_element_by_xpath("i[@class='fa fa-check']")
                service_id += "_" + days[td_index]
            except:
                pass

        # If the trip was no service days, don't bother adding it to the dataset
        if service_id == (route_id + "-"):
            continue

        service_period = transitfeed.ServicePeriod(service_id)

        if service_id not in service_ids:
            service_ids.append(service_id)

            for td_index, td in enumerate(tds[1:]):
                try:
                    td.find_element_by_xpath("i[@class='fa fa-check']")
                    service_period.SetDayOfWeekHasService(td_index)
                except:
                    pass

            today = datetime.datetime.today()
            service_period.SetStartDate(today.strftime('%Y%m%d'))
            service_period.SetEndDate((today + datetime.timedelta(weeks=3*4)).strftime('%Y%m%d'))
            schedule.AddServicePeriodObject(service_period)

        trip = route.AddTrip(schedule, headsign=route_id, service_period=service_period)

        departure_time = tds[0].text.strip().encode("utf-8")

        for stop_index, stop in enumerate(stops):
            stop = stop.text.encode("utf-8")

            if stop not in station_list:
                resp = gmaps.geocode(stop)

                if not resp:
                    continue

                location = resp[0]['geometry']['location']
                stop_obj = schedule.AddStop(lng = location['lng'],
                                            lat = location['lat'],
                                            name = stop,
                                            stop_id = stop.upper())

                station_list.append(stop)
                station_locations.append(location)
                station_objects.append(stop_obj)
            else:
                stop_object = station_objects[station_list.index(stop)]
                location = station_locations[station_list.index(stop)]

            if stop_index == 0:
                time1 = datetime.datetime.strptime(departure_time, "%H:%M")
                trip.AddStopTime(stop_obj, stop_time=time1.strftime("%H:%M:%S"))
                departure_location = location
            else:
                duration_id = json.dumps(departure_location) + "-" + json.dumps(location)

                if duration_id not in durations:
                    # Calculate the distance between departure and destination stops
                    resp = gmaps.distance_matrix(origins = departure_location,
                                                 destinations = location,
                                                 mode = 'driving')
                    print(resp)

                    # Get duration in minutes
                    intermediate_duration = resp['rows'][0]['elements'][0]['duration']['value'] / 60
                    print("It's %s" % intermediate_duration)
                    durations[duration_id] = intermediate_duration
                else:
                    intermediate_duration = durations[duration_id]

                time = (time1 + datetime.timedelta(minutes = intermediate_duration)).strftime("%H:%M:%S")
                if int(time.split(":")[0]) < int(time1.strftime("%H:%M:%S").split(":")[0]):
                    time = str(24 + int(time.split(":")[0])) + ":" + time.split(":")[1] + ":00"

                try:
                    trip.AddStopTime(stop_obj, stop_time=time)
                except transitfeed.problems.OtherProblem:
                    print("#### OUT OF ORDER STOP")
                    continue


schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)

driver.quit()
