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

url = "https://www.ktelkorinthias.gr/gr/routes/urban-routes"
driver.get(url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "KTELKorinthias",
                   name = "Suburban Transportations of Korinthia Perfecture",
                   timezone = "Europe/Athens",
                   url = "https://www.ktelkorinthias.gr")


# Retrieve route links
route_links = driver.find_elements_by_xpath("//div[@class='moduletable col-md-3 pull-right routes']/ul/li/div/div/a")
print("Found %s route links" % len(route_links))

route_urls = []
for route_link in route_links:
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

    directions = ['red', 'orange']

    for direction_index, direction in enumerate(directions):

        # Click on the tab to make trips visible
        tabs = driver.find_elements_by_xpath("//ul[@id='tabs']/li/a")
        print("Found %s tabs" % len(tabs))

        try:
            tabs[direction_index].click()
        except selenium.common.exceptions.WebDriverException:
            continue


        if direction == "red":
            route_id = driver.find_element_by_xpath("//div[@id='my-tab-content']/div[@id='%s']/h3" % direction).text.strip().encode("utf-8")
        else:
            route_id = driver.find_element_by_xpath("//div[@id='my-tab-content']/div[@id='%s']/div/h3" % direction).text.strip().encode("utf-8")

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
            # departure_location = geolocator.geocode(departure_stop + ", Greece")
            resp = gmaps.geocode(departure_stop + ", Κόρινθος, Ελλάδα")

            if not resp:
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
            # destination_location = geolocator.geocode(destination_stop + ", Greece")
            resp = gmaps.geocode(destination_stop + ", Κόρινθος, Ελλάδα")

            if not resp:
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

        # Retrieve the trip lines
        if direction == "red":
            trips = driver.find_elements_by_xpath("//div[@id='my-tab-content']/div[@id='%s']/table/tbody/tr" % direction)
        else:
            trips = driver.find_elements_by_xpath("//div[@id='my-tab-content']/div[@id='%s']/div/table/tbody/tr" % direction)

        print("Found %s trips" % (len(trips) - 1))

        service_ids = []
        for trip in trips[1:]:
            tds = trip.find_elements_by_xpath("td")

            # For every trip, retrieve the days it's in service
            service_id = route_id + "-"
            for td_index, td in enumerate(tds[1:-1]):
                if td.text.strip():
                    service_id += str(td_index)

            service_period = transitfeed.ServicePeriod(service_id)

            if service_id not in service_ids:
                service_ids.append(service_id)

                for td_index, td in enumerate(tds[1:-1]):
                    if td.text.strip():
                        service_period.SetDayOfWeekHasService(td_index)

                today = datetime.datetime.today()
                service_period.SetStartDate(today.strftime('%Y%m%d'))
                service_period.SetEndDate((today + datetime.timedelta(weeks=3 * 4)).strftime('%Y%m%d'))
                schedule.AddServicePeriodObject(service_period)

            trip_obj = route.AddTrip(schedule, headsign=route_id, service_period=service_period)

            departure_time = tds[0].text.strip().encode("utf-8")

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

            if departure_time.split(":")[0] == "24":
                time1 = datetime.datetime.strptime("00:" + departure_time.split(":")[1], "%H:%M")
            else:
                time1 = datetime.datetime.strptime(departure_time, "%H:%M")

            trip_obj.AddStopTime(departure_obj, stop_time=time1.strftime("%H:%M:%S"))

            # Add stop times for any intermediate stops
            if len(stops) > 2:
                print("This trip has intermediate stops")

                for stop in stops[1:-2]:

                    stop = stop.strip()

                    if stop not in station_list:

                        resp = gmaps.geocode(stop + ", Korinthia Greece")

                        if not resp:
                            continue

                        stop_location = resp[0]['geometry']['location']
                        print("Intermediate stop: %s. Location: %s" % (stop, stop_location))

                        stop_obj = schedule.AddStop(lng = stop_location['lng'],
                                                    lat = stop_location['lat'],
                                                    name = stop,
                                                    stop_id = stop.upper())

                        station_list.append(stop)
                        station_locations.append(stop_location)
                        station_objects.append(stop_obj)
                    else:
                        stop_obj = station_objects[station_list.index(stop)]
                        stop_location = station_locations[station_list.index(stop)]

                    print("Checking intermediate_duration from %s - %s to %s - %s" % (departure_stop, departure_location, stop, stop_location))
                    resp = gmaps.distance_matrix(origins = departure_location,
                                                 destinations = stop_location,
                                                 mode = 'driving')

                    # Get duration in minutes
                    print(resp)
                    intermediate_duration = resp['rows'][0]['elements'][0]['duration']['value'] / 60
                    print("It's %s" % intermediate_duration)

                    time = (time1 + datetime.timedelta(minutes = intermediate_duration)).strftime("%H:%M:%S")
                    if int(time.split(":")[0]) < int(time1.strftime("%H:%M:%S").split(":")[0]):
                        time = str(24 + int(time.split(":")[0])) + ":" + time.split(":")[1] + ":00"

                    trip_obj.AddStopTime(stop_obj, stop_time=time)


            print("Whole trip duration %s" % duration)
            time2 = (time1 + datetime.timedelta(minutes=duration)).strftime("%H:%M:%S")
            if int(time2.split(":")[0]) < int(time1.strftime("%H:%M:%S").split(":")[0]):
                time2 = str(24 + int(time2.split(":")[0])) + ":" + time2.split(":")[1] + ":00"

            trip_obj.AddStopTime(destination_obj, stop_time=time2)


schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)

driver.quit()
