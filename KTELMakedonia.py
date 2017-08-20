#!/usr/bin/env python
# coding=utf-8

from selenium import webdriver
from selenium.webdriver.support.ui import Select
import selenium.common.exceptions
import os
import re
from geopy.geocoders import Nominatim
import datetime
import transitfeed

driver = webdriver.Chrome()
geolocator = Nominatim()

start_url = "http://ktelmacedonia.gr/en/routes/tid=%s"
# start_url = "http://ktelmacedonia.gr/gr/routes/tid=%s"

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "MakedoniaIntercity", \
                   name = "Macedonia Intercity Bus Station", \
                   timezone = "Europe/Athens", \
                   url = "http://ktelmacedonia.gr")

first_stop_written = False


for route_id in range(1,40):

    url = start_url % route_id
    print "\n\nFetching %s" % url
    driver.get(url)

    try:
        lineSelector_from = Select(driver.find_element_by_xpath("//select[@class='local-station'][@name='from']"))
    except selenium.common.exceptions.NoSuchElementException:
        continue

    first_stop = lineSelector_from.options[0].text.strip()
    location = geolocator.geocode(first_stop.encode("utf-8") + ", Greece", timeout = None)

    print("Location for %s: %s, %s" % (first_stop.encode("utf-8"), location.latitude, location.longitude))

    if not first_stop_written:

        first_stop_obj = schedule.AddStop(lng = location.longitude, \
                                          lat = location.latitude, \
                                          name = first_stop,
                                          stop_id=first_stop.upper())
        first_stop_written = True

    # Select one of the available lines
    lineSelector = Select(driver.find_element_by_xpath("//select[@class='local-station'][@name='to']"))

    print("\n\nFound %s lines" % (len(lineSelector.options) - 1))

    for line_index, line in enumerate(lineSelector.options[1:]):

        print("\nSelecting line %s" % line.text.strip())
        lineSelector.select_by_index(line_index + 1)

        # Wait for the page to be updated
        driver.implicitly_wait(10)

        next_stop = line.text.strip()

        location = geolocator.geocode(next_stop.encode("utf-8") + ", Greece", timeout = None)

        if not location:
            print("### COULD NOT FIND LOCATION FOR %s" % next_stop)
            continue

        print("Location for %s: %s, %s" % (next_stop, location.latitude, location.longitude))

        next_stop_obj = schedule.AddStop(lng = location.longitude, \
                                         lat = location.latitude, \
                                         name = next_stop)
        route_id = first_stop + "-" + next_stop

        route = schedule.AddRoute(short_name= "", \
                                  long_name=first_stop.upper()+"-"+next_stop.upper(), \
                                  route_type="Bus")

        # Read the values of the table
        route_rows = driver.find_elements_by_xpath("//tr[@class='routerow']")

        print("\nFound %s route rows" % len(route_rows))

        service_ids = []
        for row in route_rows:
            print("Row: %s" % row.text.strip())
            info = row.text.strip().split()
            print("Info: %s" % info)

            if (len(info) < 10) or (":" not in info[0]):
                print("### PROBLEM WITH LINE ###")
                continue

            days = "".join(info[1:8]).replace("-","")
            service_id =  "%s-%s" % (route_id, days)
            if service_id not in service_ids:
                service_ids.append(service_id)

                service_period = transitfeed.ServicePeriod(service_id)
                print("Service days: %s" % info[1:8])
                for day in info[1:8]:
                    if day != "-":
                        service_period.SetDayOfWeekHasService(int(day) - 1)

                today = datetime.datetime.today()
                service_period.SetStartDate(today.strftime('%Y%m%d'))
                service_period.SetEndDate((today + datetime.timedelta(weeks=3*4)).strftime('%Y%m%d'))
                schedule.AddServicePeriodObject(service_period)

            trip = route.AddTrip(schedule, headsign=route_id, service_period=service_period)

            print("Departure: %s" % info[0])
            print("Arrival: %s" % info[8])

            departure_time = info[0]
            arrival_time = info[8]

            if departure_time.split(":")[0] == "24":
                time1 = "00:" + departure_time.split(":")[1] + ":00"
            else:
                time1 = datetime.datetime.strptime(departure_time, "%H:%M").strftime("%H:%M:%S")

            if int(arrival_time.split(":")[0]) < int(departure_time.split(":")[0]):
                time2 = str(24 + int(arrival_time.split(":")[0])) + ":" + arrival_time.split(":")[1] + ":00"
            else:
                time2 = datetime.datetime.strptime(arrival_time, "%H:%M").strftime("%H:%M:%S")

            trip.AddStopTime(first_stop_obj, stop_time=time1)
            trip.AddStopTime(next_stop_obj,  stop_time=time2)

schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)
