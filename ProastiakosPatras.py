#!/usr/bin/env python
# coding=utf-8

import os
import re
from geopy.geocoders import Nominatim
import datetime
import transitfeed
import time
from collections import OrderedDict

geolocator = Nominatim()

gtfs_file = os.path.basename(__file__).replace(".py",".zip")

schedule = transitfeed.Schedule()

schedule.AddAgency(agency_id = "ProastiakosPatras", \
                   name = "Προστιακός Σιδηρόδρομος Πατρών", \
                   timezone = "Europe/Athens", \
                   url = "http://www.trainose.gr/επιβατικό-έργο/προαστιακός-σιδηρόδρομος/προαστιακός-πάτρας/")


stations_dict = OrderedDict()

stations_dict["Agios Andreas"] = {
                        "first_arrival"   : "06:26",
                        "first_departure" : "06:30",
                        "return_first_arrival"    : "07:26",
                        "return_first_departure"  : "07:30",
                        "longitude"  : 38.23949,
                        "latitude"   : 21.72743
                        }

stations_dict["Patra"] = {
                        "first_arrival"   : "06:33",
                        "first_departure" : "06:34",
                        "return_first_arrival"    : "07:22",
                        "return_first_departure"  : "07:23",
                        "longitude"  : 38.24989,
                        "latitude"   : 21.73502
    }

stations_dict["Stadio Panachaikis"] = {
                        "first_arrival"   : "06:38",
                        "first_departure" : "06:38",
                        "return_first_arrival"    : "07:18",
                        "return_first_departure"  : "07:18",
                        "longitude"  : 38.26219,
                        "latitude"   : 21.74222
    }

stations_dict["Agyia"] = {
                        "first_arrival"   : "06:40",
                        "first_departure" : "06:40",
                        "return_first_arrival"    : "07:16",
                        "return_first_departure"  : "07:16",
                        "longitude"  : 38.27125,
                        "latitude"   : 21.7476
            }

stations_dict["Mpozaitika"] = {
                        "first_arrival"   : "06:43",
                        "first_departure" : "06:43",
                        "return_first_arrival"    : "07:13",
                        "return_first_departure"  : "07:13",
                        "longitude"  : 38.28166,
                        "latitude"   : 21.76479
    }

stations_dict["Kastelokampos"] = {
                        "first_arrival"   : "06:45",
                        "first_departure" : "06:45",
                        "return_first_arrival"    : "07:11",
                        "return_first_departure"  : "07:11",
                        "longitude"  : 38.29116,
                        "latitude"   : 21.771219
    }

stations_dict["Rio"] = {

                        "first_arrival"   : "06:50",
                        "first_departure" : "06:50",
                        "return_first_arrival"    : "07:09",
                        "return_first_departure"  : "07:09",
                        "longitude"  : 38.30083,
                        "latitude"   : 21.78222
    }

stations_dict["Aktaio"] = {
                        "first_arrival"   : "06:52",
                        "first_departure" : "06:52",
                        "return_first_arrival"    : "07:03",
                        "return_first_departure"  : "07:03",
                        "longitude"  : 38.30446,
                        "latitude"   : 21.79217,
    }

stations_dict["Agios Vasileios"] = {

                        "first_arrival"   : "06:55",
                        "first_departure" : "06:55",
                        "return_first_arrival"    : "07:01",
                        "return_first_departure"  : "07:01",
                        "longitude"  : 38.3144,
                        "latitude"   : 21.81492,
    }


for stop_value, stop_info in stations_dict.iteritems():
    stations_dict[stop_value]["object"] = schedule.AddStop(lng = stop_info["longitude"],
                                                      lat = stop_info["latitude"],
                                                      name = stop_value,
                                                      stop_id = stop_value.upper())

route = schedule.AddRoute(short_name = "",
                          long_name = "Agios Andreas - Agios Vasileios".upper(),
                          route_type = "Rail")



# 17 end-to-end δρομολόγια
for trip_id in range(0, 34):

    print("trip_id: %s" % trip_id)
    if (trip_id % 2) == 0:
        service_id = "Agios Andreas - Agios Vasileios - %s" % (trip_id + 1)
    else:
        service_id = "Agios Vasileios - Agios Andreas - %s" % (trip_id + 1)

    hours_to_add = trip_id / 2
    service_period = transitfeed.ServicePeriod(service_id)
    for day in range(0, 7):
        service_period.SetDayOfWeekHasService(day)

    today = datetime.datetime.today()
    service_period.SetStartDate(today.strftime('%Y%m%d'))
    service_period.SetEndDate((today + datetime.timedelta(weeks=3*4)).strftime('%Y%m%d'))
    schedule.AddServicePeriodObject(service_period)

    trip = route.AddTrip(schedule, headsign = service_id, service_period = service_period)

    if (trip_id % 2) == 0:
        station_info = stations_dict.values()
        arrival_key = 'first_arrival'
        departure_key = 'first_departure'
    else:
        station_info = stations_dict.values()[-1::-1]
        arrival_key = 'return_first_arrival'
        departure_key = 'return_first_departure'

    for station in station_info:
        time1 = datetime.datetime.strptime(station[arrival_key], "%H:%M")
        time2 = datetime.datetime.strptime(station[departure_key], "%H:%M")

        arrival_time = (time1 + datetime.timedelta(hours = hours_to_add)).strftime("%H:%M:%S")
        departure_time = (time2 + datetime.timedelta(hours = hours_to_add)).strftime("%H:%M:%S")
        print("Arr: %s - Dep: %s" % (arrival_time, departure_time))

        trip.AddStopTime(station['object'], arrival_time = arrival_time, departure_time = departure_time)

schedule.Validate()

schedule.WriteGoogleTransitFeed(gtfs_file)
