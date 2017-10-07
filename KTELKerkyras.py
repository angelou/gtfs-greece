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

url = "https://greenbuses.gr/el/routes-gr"
driver.get(url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "GreenBuses",
                   name = "Intercity Buses of Kerkyra",
                   timezone = "Europe/Athens",
                   url = "https://greenbuses.gr")


# Retrieve the list of route areas
route_areas = driver.find_elements_by_xpath("//div[@id='leftMenu']/details")

print("Found %s route areas" % len(route_areas))

# Click on all areas to expand the list of URLs for all routes
for route_area in route_areas:
    route_area.click()

# Collect the list of URLs for all routes
route_links = driver.find_elements_by_xpath("//div[@id='leftMenu']/details/a")
print("Found %s route links" % len(route_links))

# Extract the href attribute for each URL
route_urls = []

for route_link in route_links:
    route_urls.append(route_link.get_attribute("href"))

# Scrape every route URL
stop_ids = []
stop_objects = []
for route_url in route_urls:

    print("Fetching %s" % route_url)
    driver.get(route_url)

    route_text = driver.find_element_by_xpath("//div[@id='idcode']/h13").text.encode("utf-8").strip().replace("♦", "")

    route_code = route_text.split("-")[0].strip()
    print("route_code: %s" % route_code)

    for route_direction in ["from", "to"]:
        departure_stop, destination_stop = [stop.strip() for stop in driver.find_element_by_xpath("//div[@class='%s']/div[@class='h14']" % route_direction).text.strip().encode("utf-8").split("⇨")]

        print("departure_stop:  %s" % departure_stop)
        print("destination_stop: %s" % destination_stop)

        if departure_stop not in stop_ids:
            departure_location = geolocator.geocode(departure_stop + " Kerkyra, Greece")
            if not departure_location:
                continue

            print("Adding stop: %s" % departure_stop)
            departure_object = schedule.AddStop(lng = departure_location.longitude,
                                                lat = departure_location.latitude,
                                                name = departure_stop,
                                                stop_id = departure_stop.upper())

            stop_objects.append(departure_object)
            stop_ids.append(departure_stop)

        else:
            departure_object = stop_objects[stop_ids.index(departure_stop)]

        if destination_stop not in stop_ids:
            destination_location = geolocator.geocode(destination_stop + " Kerkyra, Greece")
            if not destination_location:
                continue

            print("Adding stop: %s" % destination_stop)
            destination_object = schedule.AddStop(lng = destination_location.longitude,
                                                   lat = destination_location.latitude,
                                                   name = destination_stop,
                                                   stop_id = destination_stop.upper())

            stop_objects.append(destination_object)
            stop_ids.append(destination_stop)

        else:
            destination_object = stop_objects[stop_ids.index(destination_stop)]

        route_id = route_code + "-" + departure_stop + "-" + destination_stop
        route = schedule.AddRoute(short_name = "",
                                  long_name = route_id.upper(),
                                  route_type = "Bus")

        service_period = transitfeed.ServicePeriod(route_id)

        today = datetime.datetime.today()
        service_period.SetStartDate(today.strftime('%Y%m%d').encode("utf-8"))
        service_period.SetEndDate((today + datetime.timedelta(weeks=3*4)).strftime('%Y%m%d').encode("utf-8"))

        hour_spans = driver.find_elements_by_xpath("//div[@class='%s']/p/span" % route_direction)

        duration_text = driver.find_element_by_xpath("//div[@id='section-to-print']/div[@class='bot-text']").text.encode("utf-8").strip()

        duration = re.search("\d{1,2}:\d{2}", duration_text).group()
        print("Duration: %s" % duration)

        hours_to_add, minutes_to_add = [int(hour_segment) for hour_segment in duration.split(":")]

        for hour_span_index, hour_span in enumerate(hour_spans):

            hour_span_text = hour_span.text.encode("utf-8")

            if hour_span_text and ("-" not in hour_span_text) :
                if hour_span_index == 0:
                    for day in range(0,5):
                        service_period.SetDayOfWeekHasService(day)
                elif hour_span_index == 1:
                    service_period.SetDayOfWeekHasService(5)
                elif hour_span_index == 2:
                    service_period.SetDayOfWeekHasService(6)

                print("Hour span: %s" % hour_span_text)
                hours = [re.search("\d{1,2}:\d{2}", hour.strip()).group() for hour in hour_span_text.split(",")]
                print("Hours: %s" % hours)

                for hour in hours:

                    trip = route.AddTrip(schedule, headsign = route_id, service_period = service_period)
                    time1 = datetime.datetime.strptime(hour, "%H:%M")
                    trip.AddStopTime(departure_object, stop_time = time1.strftime("%H:%M:%S"))

                    time2 = (time1 + datetime.timedelta(hours = hours_to_add, minutes = minutes_to_add)).strftime("%H:%M:%S").encode("utf-8")
                    if int(time2.split(":")[0]) < int(time1.strftime("%H:%M:%S").split(":")[0]):
                        time2 = (str(24 + int(time2.split(":")[0])) + ":" + time2.split(":")[1] + ":00").encode("utf-8")

                    trip.AddStopTime(destination_object, stop_time = time2)

        schedule.AddServicePeriodObject(service_period)

schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)

driver.quit()
