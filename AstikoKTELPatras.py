#!/usr/bin/env python
# coding=utf-8

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions
import os
import re
from geopy.geocoders import Nominatim
from geopy.distance import vincenty
import googlemaps
import datetime
import transitfeed
import time
import json


driver = webdriver.Chrome()
geolocator = Nominatim()

days = {
    '0' : "Δευτέρα",
    '1' : "Τρίτη",
    '2' : "Τετάρτη",
    '3' : "Πέμπτη",
    '4' : "Παρασκευή",
    '5' : "Σάββατο",
    '6' : "Κυριακή"
}

gmaps = googlemaps.Client(key='your-key-here')

start_url = "http://jsapi.3pi-telematics.com/templateFiles/#main"
driver.implicitly_wait(5)
driver.get(start_url)

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "AstikoKTELPatras",
                   name = "Urban Transportations of Patras Perfecture",
                   timezone = "Europe/Athens",
                   url = "http://www.astikopatras.gr")




daytimes = {
    '1 : ΤΕΡΨΙΘΕΑ-ΕΓΛΥΚΑΔΑ - ΚΑΤΕΥΘΥΝΣΗ: ΕΓΛΥΚΑΔΑ' : {
        '01234': ['6:20', '7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '6:40', '7:10', '8:10', '9:10', '10:10', '11:10', '12:10', '13:10', '14:10', '15:10', '16:10', '17:10', '18:10', '19:10', '20:10', '7:20', '8:20', '9:20', '10:20', '11:20', '12:20', '13:20', '14:20', '15:20', '16:20', '17:20', '18:20', '19:20', '20:20', '7:30', '8:30', '9:30', '10:30', '11:30', '12:30', '13:30', '14:30', '15:30', '16:30', '17:30', '18:30', '19:30', '20:30', '7:40', '8:40', '9:40', '10:40', '11:40', '12:40', '13:40', '14:40', '15:40', '16:40', '17:40', '18:40', '19:40', '20:40', '7:50', '8:50', '9:50', '10:50', '11:50', '12:50', '13:50', '14:50', '15:50', '16:50', '17:50', '18:50', '19:50', '20:50', '21:00', '22:00', '21:15', '22:15', '21:30', '22:30', '21:45', '22:40'],
        '02'   : ['15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '15:12', '16:12', '17:12', '18:12', '19:12', '20:12', '15:24', '16:24', '17:24', '18:24', '19:24', '20:24', '15:36', '16:36', '17:36', '18:36', '19:36', '20:36', '15:48', '16:48', '17:48', '18:48', '19:48', '20:48', '21:00', '22:00', '21:15', '22:15', '21:30', '22:30', '21:45', '22:40'],
        '5'    : ['6:20', '7:00', '6:40', '7:10', '8:00', '9:00', '8:10', '9:10', '10:00', '11:00', '10:10', '11:10', '10:20', '11:20', '10:30', '11:30', '10:40', '11:40', '10:50', '11:50', '12:00', '13:00', '12:10', '13:10', '12:20', '13:20', '12:30', '13:30', '12:40', '13:40', '12:50', '13:50', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:10', '22:10', '14:10', '15:15', '16:15', '17:15', '18:15', '19:15', '20:15', '21:30', '22:30', '14:20', '15:30', '16:30', '17:30', '18:30', '19:30', '20:30', '21:50', '22:40', '14:30', '15:45', '16:45', '17:45', '18:45', '19:45', '20:50', '14:40', '14:50', '7:20', '8:20', '9:20', '7:30', '8:30', '9:30', '7:40', '8:40', '9:40', '7:50', '8:50', '9:50'],
        '6'    : ['7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '7:30', '8:30', '9:30', '10:30', '11:30', '12:30', '13:30', '14:30', '15:20', '16:20', '17:20', '18:20', '19:20', '20:20', '21:20', '22:20', '15:40', '16:40', '17:40', '18:40', '19:40', '20:40', '21:40', '22:40'],
    },
    '1 : ΤΕΡΨΙΘΕΑ-ΕΓΛΥΚΑΔΑ - ΚΑΤΕΥΘΥΝΣΗ: ΤΕΡΨΙΘΕΑ' : {
        '01234': ['6:20', '7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '6:40', '7:10', '8:10', '9:10', '10:10', '11:10', '12:10', '13:10', '14:10', '15:10', '16:10', '17:10', '18:10', '19:10', '20:10', '7:20', '8:20', '9:20', '10:20', '11:20', '12:20', '13:20', '14:20', '15:20', '16:20', '17:20', '18:20', '19:20', '20:20', '7:30', '8:30', '9:30', '10:30', '11:30', '12:30', '13:30', '14:30', '15:30', '16:30', '17:30', '18:30', '19:30', '20:30', '7:40', '8:40', '9:40', '10:40', '11:40', '12:40', '13:40', '14:40', '15:40', '16:40', '17:40', '18:40', '19:40', '20:40', '7:50', '8:50', '9:50', '10:50', '11:50', '12:50', '13:50', '14:50', '15:50', '16:50', '17:50', '18:50', '19:50', '20:50', '21:00', '22:00', '21:15', '22:15', '21:30', '22:30', '21:45', '22:40'],
        '02'   : ['15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '15:12', '16:12', '17:12', '18:12', '19:12', '20:12', '15:24', '16:24', '17:24', '18:24', '19:24', '20:24', '15:36', '16:36', '17:36', '18:36', '19:36', '20:36', '15:48', '16:48', '17:48', '18:48', '19:48', '20:48', '21:00', '22:00', '21:15', '22:15', '21:30', '22:30', '21:45', '22:40'],
        '5'    : ['6:20', '7:00', '6:40', '7:10', '8:00', '9:00', '8:10', '9:10', '7:20', '8:20', '9:20', '7:30', '8:30', '9:30', '7:40', '8:40', '9:40', '7:50', '8:50', '9:50', '10:00', '11:00', '10:10', '11:10', '10:20', '11:20', '10:30', '11:30', '10:40', '11:40', '10:50', '11:50', '12:00', '13:00', '12:10', '13:10', '12:20', '13:20', '12:30', '13:30', '12:40', '13:40', '12:50', '13:50', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:10', '22:10', '14:10', '15:15', '16:15', '17:15', '18:15', '19:15', '20:15', '21:30', '22:30', '14:20', '15:30', '16:30', '17:30', '18:30', '19:30', '20:30', '21:50', '22:40', '14:30', '15:45', '16:45', '17:45', '18:45', '19:45', '20:50', '14:40', '14:50'],
        '6'    : ['7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '7:30', '8:30', '9:30', '10:30', '11:30', '12:30', '13:30', '14:30', '15:20', '16:20', '17:20', '18:20', '19:20', '20:20', '21:20', '22:20', '15:40', '16:40', '17:40', '18:40', '19:40', '20:40', '21:40', '22:40'],
    },
    '1 : ΠΛΑΖ-ΡΩΜΑΝΟΥ - ΚΑΤΕΥΘΥΝΣΗ: ΤΕΡΨΙΘΕΑ ΡΩΜΑΝΟΥ ΕΛΕΚΙΣΤΡΑ' : {
        '01234' : ['14:50']
    },
    '1 : ΠΛΑΖ-ΡΩΜΑΝΟΥ - ΚΑΤΕΥΘΥΝΣΗ: ΕΛΕΚΙΣΤΡΑ ΡΩΜΑΝΟΥ ΤΕΡΨΙΘΕΑ' : {
        '01234' : ['07:00']
    },
    '1 : ΤΕΡΨΙΘΕΑ-ΔΙΑΚΟΥ - ΚΑΤΕΥΘΥΝΣΗ: ΔΙΑΚΟΥ' : {},
    '1 : ΤΕΡΨΙΘΕΑ-ΔΙΑΚΟΥ - ΚΑΤΕΥΘΥΝΣΗ: ΤΕΡΨΙΘΕΑ' : {},
    '1 : ΤΕΡΨΙΘΕΑ-ΔΙΑΚΟΥ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΛΥΚΟΧΩΡΟ ΔΙΑΚΟΥ' : {},
    '1 : ΡΩΜΑΝΟΥ - ΣΥΝΟΡΑ - ΚΑΤΕΥΘΥΝΣΗ: ΡΩΜΑΝΟΥ-ΣΥΝΟΡΑ' : {},
    '2 : ΤΑΡΑΜΠΟΥΡΑ - ΝΕΟΣ ΔΡΟΜΟΣ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΣΥΧΑΙΝΑ ΝΕΟ ΔΡΟΜΟ' : {},
    '2 : ΤΑΡΑΜΠΟΥΡΑ - ΝΕΟΣ ΔΡΟΜΟΣ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΤΑΡΑΜΠΟΥΡΑ Τ.Ε.Ι.' : {},
    '2 : ΤΑΡΑΜΠΟΥΡΑ - ΝΕΟΣ ΔΡΟΜΟΣ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΝΕΟ ΔΡΟΜΟ ΥΠΗΡΕΣΙΑΚΟ ΠΡΩΙ' : {},
    '2 : ΤΑΡΑΜΠΟΥΡΑ - ΝΕΟΣ ΔΡΟΜΟΣ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΤΕΙ ΤΕΛΕΥΤΑΙΟ ΒΡΑΔΥΝΟ' : {},
    '3 : ΖΑΡΟΥΧΛΕΪΚΑ - ΘΕΡΜΟΠΥΛΩΝ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΘΕΡΜΟΠΥΛΩΝ' : {},
    "3 : ΖΑΡΟΥΧΛΕΪΚΑ - ΘΕΡΜΟΠΥΛΩΝ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΖΑΡΟΥΧΛΕ'Ι'ΚΑ" : {},
    "3 : ΖΑΡΟΥΧΛΕΪΚΑ - ΘΕΡΜΟΠΥΛΩΝ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΖΑΡΟΥΧΛΕΙΚΑ ΛΕΥΚΑ" : {},
    '4 : ΑΡΟΗ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΑΡΟΗ' : {},
    '4 : ΑΡΟΗ - ΚΑΤΕΥΘΥΝΣΗ: ΑΡΟΗ ΠΑΤΡΑ' : {},
    '4 : ΑΡΟΗ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΑΡΟΗ ΣΑΒΒΑΤΟ' : {},
    '4 : ΑΡΟΗ - ΚΑΤΕΥΘΥΝΣΗ: ΑΡΟΗ ΠΑΤΡΑ ΣΑΒΒΑΤΟ' : {},
    "5 : ΤΣΟΥΚΑΛΕΙΚΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΤΣΟΥΚΑΛΕΊ'ΚΑ" : {},
    "5 : ΤΣΟΥΚΑΛΕΙΚΑ - ΚΑΤΕΥΘΥΝΣΗ: ΤΣΟΥΚΑΛΕ'Ι'ΚΑ  ΠΑΤΡΑ" : {},
    "5 : ΤΣΟΥΚΑΛΕΙΚΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΜΟΝΟΔΕΝΔΡΙ ΤΣΟΥΚΑΛΕ'Ι'ΚΑ" : {},
    "5 : ΤΣΟΥΚΑΛΕΙΚΑ - ΚΑΤΕΥΘΥΝΣΗ: ΤΣΟΥΚΑΛΕ'Ι'ΚΑ ΜΟΝΟΔΕΝΔΡΙ ΠΑΤΡΑ" : {},
    "6 : ΠΑΝΕΠΙΣΤΗΜΙΟ-EXPRESS - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΠΑΝΕΠΙΣΤΗΜΙΟ (EXPRESS)" : {},
    "6 : ΠΑΝΕΠΙΣΤΗΜΙΟ-EXPRESS - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΝΕΠΙΣΤΗΜΙΟ ΠΑΤΡΑ (EXPRESS)" : {},
    '6 : ΕΡΜΟΥ - ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΠΑΝΕΠΙΣΤΗΜΙΟ ΝΟΣΟΚΟΜΕΙΟ' : {},
    '6 : ΕΡΜΟΥ - ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ - ΚΑΤΕΥΘΥΝΣΗ: ΠΡΟΣ ΠΑΤΡΑ' : {},
    '6 : ΠΑΡΑΛΙΑ ΠΡΟΑΣΤΕΙΟΥ - ΚΑΣΤΕΛΛΟΚΑΜΠΟΣ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΡΑΛΙΑ ΠΡΟΑΣΤΕΙΟΥ - ΚΑΣΤΕΛΛΟΚΑΜΠΟΣ' : {},
    '6 : ΒΟΥΝΤΕΝΗ  - ΚΑΤΕΥΘΥΝΣΗ: ΒΟΥΝΤΕΝΗ' : {},
    '6 : ΒΟΥΝΤΕΝΗ  - ΚΑΤΕΥΘΥΝΣΗ: ΒΟΥΝΤΕΝΗ ΠΑΤΡΑ' : {},
    '6 : ΑΝΩ ΚΑΣΤΡΙΤΣΙ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ' : {},
    '6 : ΑΝΩ ΚΑΣΤΡΙΤΣΙ - ΚΑΤΕΥΘΥΝΣΗ: ΑΝΩ ΚΑΣΤΡΙΤΣΙ' : {},
    '6 : ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ - ΡΙΟ - ΑΓ. ΒΑΣΙΛΕΙΟΣ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ' : {},
    '6 : ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ - ΡΙΟ - ΑΓ. ΒΑΣΙΛΕΙΟΣ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ' : {},
    '6 : ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ - ΡΙΟ - ΑΓ. ΒΑΣΙΛΕΙΟΣ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΝΕΠΙΣΤΗΜΙΟ-ΝΟΣΟΚΟΜΕΙΟ-ΑΓ. ΒΑΣΙΛΕΙΟΣ-ΔΗΜΟΡΗΓ.-ΡΙΟ' : {},
    '6 : ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ - ΡΙΟ - ΑΓ. ΒΑΣΙΛΕΙΟΣ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ - ΡΙΟ' : {},
    '8 : ΠΑΤΡΑ - ΚΑΛΛΙΘΕΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΚΑΛΛΙΘΕΑ ΘΕΑ' : {},
    '8 : ΠΑΤΡΑ - ΚΑΛΛΙΘΕΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ Πρ. ΗΛΙΑΣ ΚΑΛΛΙΘΕΑ ΘΕΑ' : {},
    '8 : ΠΑΤΡΑ - ΚΑΛΛΙΘΕΑ - ΚΑΤΕΥΘΥΝΣΗ: ΚΑΛΛΙΘΕΑ ΘΕΑ ΠΑΤΡΑ' : {},
    '8 : ΠΑΤΡΑ - ΚΑΛΛΙΘΕΑ - ΚΑΤΕΥΘΥΝΣΗ: ΚΑΛΛΙΘΕΑ ΠΑΤΡΑ' : {},
    '8 : ΠΑΤΡΑ - ΚΑΛΛΙΘΕΑ - ΚΑΤΕΥΘΥΝΣΗ: ΚΑΛΛΙΘΕΑ ΘΕΑ ΔΕΜΕΝΙΚΑ' : {},
    '8 : ΠΑΤΡΑ - ΚΑΛΛΙΘΕΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΚΑΛΛΙΘΕΑ' : {},
    '8 : ΠΑΤΡΑ - ΚΑΛΛΙΘΕΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΔΕΜΕΝΙΚΑ ΚΑΛΛΙΘΕΑ' : {},
    '8 : ΠΑΤΡΑ - ΚΑΛΛΙΘΕΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ Προφ.ΗΛΙΑΣ ΚΑΛΛΙΘΕΑ' : {},
    '8 : ΠΑΤΡΑ - ΚΑΛΛΙΘΕΑ - ΚΑΤΕΥΘΥΝΣΗ: ΚΑΛΛΙΘΕΑ Προφ. ΗΛΙΑΣ ΠΑΤΡΑ' : {},
    '8 : ΑΝΩ - ΚΑΤΩ ΟΒΡΥΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΑΝΩ ΚΑΤΩ ΟΒΡΥΑ' : {},
    '8 : ΑΝΩ - ΚΑΤΩ ΟΒΡΥΑ - ΚΑΤΕΥΘΥΝΣΗ: Α.Κ. ΟΒΡΥΑ ΠΑΤΡΑ' : {},
    '8 : ΑΝΩ - ΚΑΤΩ ΟΒΡΥΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΔΕΜΕΝΙΚΑ ΑΝΩ ΚΑΤΩ ΟΒΡΥΑ' : {},
    '8 : ΑΝΩ - ΚΑΤΩ ΟΒΡΥΑ - ΚΑΤΕΥΘΥΝΣΗ: Α. Κ. ΟΒΡΥΑ ΔΕΜΕΜΕΝΙΚΑ ΠΑΤΡΑ' : {},
    '8 : ΑΝΩ - ΚΑΤΩ ΟΒΡΥΑ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ Πρ.ΗΛΙΑΣ. Α.Κ.Οβρυα' : {},
    '8 : ΑΝΩ - ΚΑΤΩ ΟΒΡΥΑ - ΚΑΤΕΥΘΥΝΣΗ: ΟΒΡΥΑ ΔΕΜΕΝΙΚΑ ΚΟΥΚΟΥΛΙ ΠΑΤΡΑ' : {},
    '9 : ΠΑΤΡΑ - ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ ΜΕΣΩ ΕΛΛΗΝΟΣ ΣΤΡΑΤΙΩΤΟΥ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΝΕΠΙΣΤΗΜΙΟ ΝΟΣΟΚΟΜΕΙΟ ΜΕΣΩ ΕΛΛΗΝΟΣ ΣΤΡΑΤΙΩΤΟΥ' : {},
    '9 : ΠΑΤΡΑ - ΠΑΝΕΠΙΣΤΗΜΙΟ - ΝΟΣΟΚΟΜΕΙΟ ΜΕΣΩ ΕΛΛΗΝΟΣ ΣΤΡΑΤΙΩΤΟΥ - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΤΡΑ ΜΕΣΩ ΕΛΛΗΝΟΣ ΣΤΡΑΤΙΩΤΟΥ' : {},
    '11 : ΠΑΡΚΙΝ ΤΕΡΨΙΘΕΑ (ΔΕΛΦΙΝΙ) - ΚΑΤΕΥΘΥΝΣΗ: ΠΑΡΚΙΝΓΚ ΤΕΡΨΙΘΕΑ' : {},
    '18 : ΛΙΜΑΝΙ - ΚΑΤΕΥΘΥΝΣΗ: ΛΙΜΑΝΙ' : {},
    '18 : ΛΙΜΑΝΙ - ΚΑΤΕΥΘΥΝΣΗ: ΝΕΟ ΛΙΜΑΝΙ-ΠΑΤΡΑ' : {},
}

station_list = []
station_locations = []
station_objects = []
durations = {}
service_ids = []
route_ids = []

# Find the line select element
line_select = Select(driver.find_element_by_xpath("//select[@id='line']"))
for line_index, line in enumerate(line_select.options[1:]):
    line_select.select_by_index(line_index + 1)



    # Now, find the direction select element
    direction_select = Select(driver.find_element_by_xpath("//select[@id='direction']"))
    for direction_index, direction in enumerate(direction_select.options[1:]):
        _direction_select = Select(driver.find_element_by_xpath("//select[@id='direction']"))
        _direction_select.select_by_index(direction_index + 1)

        route_id = line.text.encode("utf-8") + " - ΚΑΤΕΥΘΥΝΣΗ: " + direction.text.encode("utf-8")

        if route_id not in daytimes.keys():
            print("#### RouteID %s not in keys" % route_id)
            continue

        if not daytimes[route_id].keys():
            print("#### RouteID %s has no service" % route_id)
            continue

        print("RouteID: %s" % route_id)
        route = schedule.AddRoute(short_name = "",
                                  long_name = route_id,
                                  route_type = "Bus")

        route_station_list = []

        # Now, find the stop select element
        stop_select = Select(driver.find_element_by_xpath("//select[@id='station']"))
        for stop_index, stop in enumerate(stop_select.options[1:]):
            stop_select.select_by_index(stop_index + 1)


            lng, lat = driver.current_url.split("_")[-1].split(",")
            stop_id, stop_name = driver.current_url.split("_")[1:3]

            route_station_list.append(stop_id)

            if stop_id not in station_list:

                stop_obj = schedule.AddStop(lng = lng,
                                            lat = lat,
                                            name = stop_name.encode("utf-8"),
                                            stop_id = stop_id.encode("utf-8"))

                station_list.append(stop_id)
                station_objects.append(stop_obj)
                stop_location = (lng, lat)
                station_locations.append(stop_location)
            else:
                stop_obj = station_objects[station_list.index(stop_id)]
                stop_location = station_locations[station_list.index(stop_id)]

        # Let's do a bit of cleanup for the cached stations
        for retry in range(5):
            cached_stations = driver.find_elements_by_xpath("//div[@id='cachedStations']/span/span")
            for cached_station in cached_stations[::-1]:
                ActionChains(driver).move_to_element(cached_station).click().perform()

            time.sleep(5)
        # Now that we have all stops for this route directions,
        # let's populate the trips for this route direction

        for service_days, service_times in daytimes[route_id].iteritems():

            service_id = route_id
            for service_day_index in service_days:
                service_id += '_' + days[service_day_index]

            service_period = transitfeed.ServicePeriod(service_id)
            for service_day_index in service_days:
                service_period.SetDayOfWeekHasService(int(service_day_index))

            today = datetime.datetime.today()
            service_period.SetStartDate(today.strftime('%Y%m%d'))
            service_period.SetEndDate((today + datetime.timedelta(weeks=3 * 4)).strftime('%Y%m%d'))
            schedule.AddServicePeriodObject(service_period)

            for service_time in service_times:
                trip = route.AddTrip(schedule, headsign=route_id, service_period=service_period)

                previous_stop = {
                    'time': '',
                    'location': ''
                }
                for trip_stop_index, trip_stop in enumerate(route_station_list):

                    stop_location = station_locations[station_list.index(trip_stop)]

                    if not previous_stop['time']:
                        stop_time = datetime.datetime.strptime(service_time, "%H:%M")
                        trip.AddStopTime(station_objects[station_list.index(trip_stop)], stop_time = stop_time.strftime("%H:%M:%S"))
                    else:
                        # Add stop time in relevance to the previous stop

                        distance = vincenty(previous_stop['location'], stop_location).meters
                        # print("Distance from previous stop (%s) to current stop (%s) in meters: %s" % (previous_stop['location'], stop_location, distance))

                        # Assume 30 km/h
                        duration = distance / 8.3
                        # print("Duration %s" % duration)
                        stop_time = previous_stop['time'] + datetime.timedelta(seconds=duration)
                        '''
                        resp = gmaps.distance_matrix(origins=previous_stop['location'],
                                                     destinations=stop_location,
                                                     mode='driving')

                        # Get duration in minutes
                        print("Distance from previous stop (%s) to current stop (%s)" % (previous_stop['location'], stop_location))
                        duration = resp['rows'][0]['elements'][0]['duration']['value'] / float(60)
                        print("Duration %s" % duration)
                        stop_time = previous_stop['time'] + datetime.timedelta(minutes=duration)
                        '''


                        trip.AddStopTime(station_objects[station_list.index(trip_stop)], stop_time=stop_time.strftime("%H:%M:%S"))


                    previous_stop['time'] = stop_time
                    previous_stop['location'] = stop_location






schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)

driver.quit()
