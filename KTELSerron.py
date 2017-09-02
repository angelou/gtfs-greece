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

url = "http://www.ktelserron.gr/Routes"
driver.get(url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "KTELSerron", \
                   name = "Intercity Buses of Lesvos", \
                   timezone = "Europe/Athens", \
                   url = "http://www.ktelserron.gr")


# Retrieve the list of destinations

destinations = driver.find_elements_by_xpath("//*[@id='ctl01']/div[4]/div/div/div[3]/div[1]/div/ul/li")

print("Found %s destinations" % len(destinations))


station_list = []
station_objects = []
for destination_index, destination_in_list in enumerate(destinations):

    destination_in_list.click()
    driver.implicitly_wait(10)

    # For every destination, find the tables of routes
    routes_tables = driver.find_elements_by_xpath("//*[@id='#%s']/div[@class='tables-tab']" % (destination_index + 1))

    print("Found %s routes for destination %s" % (len(routes_tables), destination_index))

    for routes_table in routes_tables:

        # Find the Departute and Destination cities
        departure, destination = routes_table.find_elements_by_xpath("div[@class='row table-header-details']/div[@class='col-md-12']/span[@class='td-route-description']")

        route_note = routes_table.find_elements_by_xpath("div[@class='row table-header-details']/div[@class='col-md-12']/span[@class='route-titles']")[-1]

        departure = departure.text.encode("utf-8")
        print("Departure: %s" % departure)

        if departure not in station_list:
            station_list.append(departure)
            departure_location = geolocator.geocode(departure + ", Greece")

            departure_object = schedule.AddStop(lng = departure_location.longitude, \
                                                lat = departure_location.latitude, \
                                                name = departure,
                                                stop_id = departure.upper())

            station_objects.append(departure_object)

        else:
            departure_object = station_objects[station_list.index(departure)]


        destination = destination.text.encode("utf-8")
        print("Destination: %s" % destination)

        if destination not in station_list:
            station_list.append(destination)
            destination_location = geolocator.geocode(destination_in_list.text.encode("utf-8") + ", Greece")
            print("%s, %s" % (destination_location.latitude, destination_location.longitude))

            destination_object = schedule.AddStop(lng = destination_location.longitude, \
                                                  lat = destination_location.latitude, \
                                                  name = destination,
                                                  stop_id = destination.upper())

            station_objects.append(destination_object)

        else:
            destination_object = station_objects[station_list.index(destination)]

        route_id = departure + "-" + destination + route_note.text.encode("utf-8")
        print("route_id: %s" % route_id)

        route = schedule.AddRoute(short_name = "", \
                                  long_name = route_id.upper(), \
                                  route_type = "Bus")

        # Extract the route info
        info_rows = routes_table.find_elements_by_xpath("table[@class='table table-striped route-table']/tbody/tr")

        # Depending on the number of rows, we get different info
        service_period = transitfeed.ServicePeriod(route_id)

        today = datetime.datetime.today()
        service_period.SetStartDate(today.strftime('%Y%m%d').encode("utf-8"))
        service_period.SetEndDate((today + datetime.timedelta(weeks=3*4)).strftime('%Y%m%d').encode("utf-8"))

        duration = routes_table.find_element_by_xpath("table[@class='table table-striped route-table']/tfoot/tr/td/div[1]/span[2]/span[2]").text.strip().encode("utf-8")

        added_hours = re.search("\d+\s+ώρ", duration)
        if added_hours:
            hours_to_add = int(added_hours.group().split()[0])
        else:
            hours_to_add = 0

        added_minutes = re.search("\d+\s+λεπτά", duration)
        if added_minutes:
            minutes_to_add = int(added_minutes.group().split()[0])
        else:
            minutes_to_add = 0

        for info_row in info_rows:

            info_parts = info_row.find_elements_by_xpath("td")

            day_info = info_parts[0].text.strip().encode("utf-8")
            hour_info = info_parts[1].text.strip().encode("utf-8")


            if "Δευτέρα έως Παρασκευή" in day_info:
                for day in range(0, 5):
                    service_period.SetDayOfWeekHasService(day)

            if "Σάββατο" in day_info:
                if "ΔΕΝ ΥΠΑΡΧΟΥΝ" not in hour_info:
                    service_period.SetDayOfWeekHasService(5)

            if "Κυριακή" in day_info:
                if "ΔΕΝ ΥΠΑΡΧΟΥΝ" not in hour_info:
                    service_period.SetDayOfWeekHasService(6)

            if "Καθημερινά" in day_info:
                for day in  range(0, 7):
                    service_period.SetDayOfWeekHasService(day)

            if "•" in hour_info:
                separator = "•"
            elif "-" in hour_info:
                separator = "-"
            else:
                separator = " "

            hours = [value.strip() for value in hour_info.split(separator)]

            for hour in hours:
                if not re.match("\d{2}:\d{2}", hour):
                    continue

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
