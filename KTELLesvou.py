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

url = "http://www.ktel-lesvou.gr/index.php?option=dromologia&new_lang=en"
driver.get(url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "KTELLesvou", \
                   name = "Intercity Buses of Lesvos", \
                   timezone = "Europe/Athens", \
                   url = "http://www.ktel-lesvou.gr")


# First stop is always the city of Mytilene

first_stop_text = "Mytilene"
print("Station A: %s" % first_stop_text)

first_stop_location = geolocator.geocode(first_stop_text.encode("utf-8") + " Mytilini, Greece")
print("Location for Station A: %s, %s" % (first_stop_location.latitude, first_stop_location.longitude))

first_stop_obj = schedule.AddStop(lng = first_stop_location.longitude, \
                                  lat = first_stop_location.latitude, \
                                  name = first_stop_text,
                                  stop_id = first_stop_text.upper())

# Find the divs holding destination and routes
routes = driver.find_elements_by_xpath("//div[@id='places']/ul")

# The last two divs link to the routes
route_links = []
for route in routes[2:]:
    route_links.extend(route.find_elements_by_xpath("li/a"))

route_urls = []
for route_link in route_links:
    route_urls.append(route_link.get_attribute("href"))

for route_url in route_urls:

    print("Fetching %s" % route_url)
    driver.get(route_url)

    try:
        stop = driver.find_element_by_xpath("//div[@id='new_diva']/div/table[2]/tbody/tr[2]/td[1]")
    except selenium.common.exceptions.NoSuchElementException:
        continue

    stop_text = " ".join(stop.text.split()[1:]).strip()
    print("Stop: %s" % stop_text)

    location = geolocator.geocode(stop_text.encode("utf-8") + " Mytilini, Greece")
    if not location:
        continue

    print("Location for Station B: %s, %s" % (location.latitude, location.longitude))

    stop_obj = schedule.AddStop(lng = location.longitude, \
                                lat = location.latitude, \
                                name = stop_text,
                                stop_id = stop_text.upper())

    route = schedule.AddRoute(short_name = "", \
                              long_name = first_stop_text.upper() + "-" + stop_text.upper(), \
                              route_type = "Bus")

    for route_direction in range(1,3):

        if route_direction == 1:
            route_id = first_stop_text + "-" + stop_text
        else:
            route_id = stop_text + "-" + first_stop_text

        print("route_id: %s" % route_id)

        route_direction_A = driver.find_elements_by_xpath("//div[@id='new_diva']/div/table[%s]/tbody/tr[2]/td" % route_direction)

        service_days_times = {}
        for index, td in enumerate(route_direction_A[1:]):
            if "There is no route" in td.text:
                continue

            for service_time in td.text.strip().split("\n"):
                if service_time not in service_days_times:
                    service_days_times[service_time] = []

                service_days_times[service_time].append(str(index))

        service_ids = []
        for service_time, service_days in service_days_times.iteritems():
            print("service_time: %s" % service_time)
            print("service_days: %s" % service_days)

            service_id = "%s-%s" % (route_id, "".join(service_days))
            service_period = transitfeed.ServicePeriod(service_id)

            if service_id not in service_ids:
                service_ids.append(service_id)

                for day in service_days:
                    service_period.SetDayOfWeekHasService(int(day))

                today = datetime.datetime.today()
                service_period.SetStartDate(today.strftime('%Y%m%d'))
                service_period.SetEndDate((today + datetime.timedelta(weeks=3*4)).strftime('%Y%m%d'))
                schedule.AddServicePeriodObject(service_period)

            trip = route.AddTrip(schedule, headsign = route_id, service_period = service_period)

            time1 = datetime.datetime.strptime(service_time, "%H:%M")

            duration = driver.find_element_by_xpath("//div[@id='new_diva']/div[1]/table[2]/tbody/tr[3]/td").text.strip()

            added_hours = re.search("\d+\s+HOURS", duration)
            if added_hours:
                hours_to_add = int(added_hours.group().split()[0])
            else:
                hours_to_add = 0

            added_minutes = re.search("\d+\s+MINUTES", duration)
            if added_minutes:
                minutes_to_add = int(added_minutes.group().split()[0])
            else:
                minutes_to_add = 0

            time2 = (time1 + datetime.timedelta(hours = hours_to_add, minutes = minutes_to_add)).strftime("%H:%M:%S")

            if route_direction == 1:
                trip.AddStopTime(first_stop_obj, stop_time = time1.strftime("%H:%M:%S"))
                trip.AddStopTime(stop_obj, stop_time = time2)
            elif route_direction == 2:
                trip.AddStopTime(stop_obj, stop_time = time1.strftime("%H:%M:%S"))
                trip.AddStopTime(first_stop_obj, stop_time = time2)

schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)
