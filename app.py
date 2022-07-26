from time import time
import requests
import os
import numpy as np
from flask import Flask, render_template, request, session, url_for, current_app, redirect, flash, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import folium
import polyline
import geopy.distance
from shapely.geometry import LineString, Point
import json
import math
#Set-ExecutionPolicy Unrestricted -Scope Process

f = open("secret_codes.json")
secret_data = json.load(f)
f.close()
# comment
app = Flask(__name__)
app.secret_key = "hello"
cycleapi_key = secret_data["bike_routing_api_key"]
positionstack_key = secret_data["positionstack_api_key"]

headers = {"accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding" : "gzip, deflate, br",
    "accept-language" : "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7,pl-PL;q=0.6,pl;q=0.5",
    "cache-control" : "max-age=0",
    "cookie" : "iterableEndUserId=mr.dajman@yahoo.pl; sp=16d9a67e-f220-4af6-bf8d-04bd51b661ac; _ga=GA1.2.1321818476.1647106578; _gid=GA1.2.1845175847.1647869148; _sp_ses.047d=*; _strava4_session=g3au0oi5iqhbrerm87nspeudidongqel; fbm_284597785309=base_domain=.www.strava.com; fbsr_284597785309=bZZCacHQHStNSJXRmUUph4R8nxQ0JNfDGr0eUBWZeJY.eyJ1c2VyX2lkIjoiMTQ1ODA0NzA5MDg3Mzg4MSIsImNvZGUiOiJBUUJKYVJEUHNpaUZGRkZ6Y0ZoZm1rS3U1NXBBb2NtTzBLc3ZoRXZrVF9OaUNOSXdsWWZCd1FRV2JldUVZUlotM2dfSERITkdsdW50TmV1aERlRUVvSnFUZ3VEa2FtdEhQOXpmcy1JZUhiaGpGV1BWclFvcGQ0d0FyZS1fc0FrUXlvNjFuOFVLNm5fZHdWbzUyVVlKZENxeXkyWWh4bnlGOVpIODZHSk9VWTg4M21OZlVhUnpCQUNFWUNhMjhVNGxrYnNLTm9xaVVLcGd0SncxMk4zUF91RWcxRnE0TUFsMHRfelg5S1dlSFcwc2ZoY2FyUG01bDQzdjlpTS1jRFZtbEFlNmVzVElfMDR3c3IyLXVtbEx3VXpUbEg1dnE2dmdZRk1HaVRvTzM1VEFWQl9IMzJKdC1acVNmYWpoOEZtS2dleWl4NFdZNTEwVnFtU2cteXFsMm04OVNZbER0STlrOW0ybDU3N3V4Z0hmdnciLCJvYXV0aF90b2tlbiI6IkVBQUFBUWtOWkFrdDBCQURpRk9zeFpCWEpxdmI5dFNTQkdQSXNSd3IwSHV1WkNma0ZUN1V4c1d5VGg4S1ZPVUpJb1I1WkNWMVBYQ1dyUHJwYlJaQVFJS0NVdUFwTFhRVEtuMTJ6bHdDVmY3VTIxbmJTNVBpOXV6elNESG1ydmxOazJ3NWJsVzc0MTZvcHoxbUVNelN1UlB1ODF4eDlIa2x6eWZNYWtrb2o2c1IydEFnRGQzMVg2RmNnT1RySWpvMXNaRCIsImFsZ29yaXRobSI6IkhNQUMtU0hBMjU2IiwiaXNzdWVkX2F0IjoxNjQ3ODg5MTc1fQ; _sp_id.047d=6064eedf-92b3-4b99-a9a1-7f57806dbe04.1641494797.5.1647889184.1647193197.c99d5daf-a2aa-4cd0-be59-083e39307701",
    "if-none-match" : 'W/"aded48b2f071f9aa44e2d6735f291037"',
    "sec-ch-ua" : '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    "sec-ch-ua-mobile" : "?0",
    "sec-ch-ua-platform" : '"Windows"',
    "sec-fetch-dest" : 'document',
    "sec-fetch-mode" : 'navigate',
    'sec-fetch-site' : 'none',
    'sec-fetch-user' : '?1',
    'upgrade-insecure-requests' : '1',
    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36'}

@app.route('/')
def stations_map():
    location_string = "Pantin"
    get_location(location_string)
    #"itinerarypoints":"2.238156,48.862088|2.403847,48.895546"}    
    
    plan_profile = "fastest"
    start_point = (2.238156,48.862088)
    end_point = (2.403847,48.895546)
    [route_line, time_route] = calculate_route(plan_profile, start_point, end_point)
    #[route_line, time_route, line] = route_map()
    polyline_route = polyline.encode(route_line)

    route_line_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Route line</p>""")

    folium.PolyLine(route_line, color = "#0000FF", opacity = 1, control = False).add_to(route_line_layer)

    linestring_route = LineString(route_line)

    first_point = route_line[0]
    last_point = route_line[-1]

    target_lap_time = 25
    estimated_laps = math.ceil(time_route / float(target_lap_time))

    lap_change_points = []
    for i in range(estimated_laps-1):
        lap_change_point = route_line[int((len(route_line)/estimated_laps)*(i+1))]
        lap_change_points.append(lap_change_point)

    print(lap_change_points)
    #time

    print(first_point, last_point)
    print(time_route)
    print(estimated_laps)

    ### VELIB MAP ###

    url = "https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_information.json"
    r_station_information = requests.get(url)
    res = check_response(r_station_information)
    print(res)
    if res != 1:
        return "Error!"#render_template("error_page.html", error_nb = res)
    
    #station status thing
    url = "https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json"
    r_station_status = requests.get(url)
    res = check_response(r_station_status)
    print(res)
    if res != 1:
        return "Error!"#render_template("error_page.html", error_nb = res)
    
    stations_status = r_station_status.json()["data"]["stations"]

    x = [station_status for station_status in stations_status if station_status["station_id"]==516709288]
    print(x)

    start_coords = (48.855, 2.3433)
    stations_points_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Runs</p>""")

    print(r_station_information.json()["data"]["stations"][0])
    
    start_list = []
    end_list = []

    for station in r_station_information.json()["data"]["stations"]:

        current_station_status = [station_status for station_status in stations_status if station_status["station_id"]==station["station_id"]][0]

        tooltip_html = """<p>Name: {}</p>
                        <p>Mechanical Bikes Available: {}</p>
                        <p>Electrical Bikes Available: {}</p>
                        <p>Docks Available: {}</p>
                        """.format(station["name"],
                                current_station_status["num_bikes_available_types"][0]["mechanical"],
                                current_station_status["num_bikes_available_types"][1]["ebike"],
                                current_station_status["num_docks_available"])

        #station["lat"],station["lon"]
        #first_point
        dist1 = geopy.distance.distance((station["lat"],station["lon"]), first_point).m
        dist2 = geopy.distance.distance((station["lat"],station["lon"]), last_point).m
        dist_all = Point((station["lat"],station["lon"])).distance(linestring_route) * 1000
        #print(dist_all)
        
        # start list
        if len(start_list) < 10:
            start_list.append((station,dist1))
        elif dist1 < start_list[-1][1]:
            trunc_list = start_list[:-1]
            trunc_list.append((station,dist1))
            start_list = trunc_list
            start_list = sorted(start_list,key=lambda i:i[1])

        
        # end list
        if len(end_list) < 20:
            end_list.append((station,dist2))
        elif dist2 < end_list[-1][1]:
            trunc_list = end_list[:-1]
            trunc_list.append((station,dist2))
            end_list = trunc_list
            end_list = sorted(end_list,key=lambda i:i[1])

        #if dist1 < 1000 or dist2 < 1000:
         #   circle_color ="#00FF00"
        if dist_all < 0.3: #0.3 basically on the track; 3 - good distance
            circle_color = "#FF0000"
        else:
            circle_color ="#FFBB00"
        folium.Circle((station["lat"],station["lon"]), 
                        color = circle_color, 
                        radius = 20,
                        fill = True,
                        tooltip = tooltip_html).add_to(stations_points_layer)


    for (station,dist) in start_list+end_list:
        folium.Circle((station["lat"],station["lon"]), 
                        color = "#000000", 
                        radius = 25,
                        fill = False,
                        tooltip = tooltip_html).add_to(stations_points_layer)

    
    for lap_change_point in lap_change_points:
        print(lap_change_point)
        folium.Circle(lap_change_point, 
                        color = "#000000", 
                        radius = 200,
                        fill = True,
                        tooltip = tooltip_html).add_to(stations_points_layer)

    folium_map = folium.Map(location=start_coords, zoom_start=12, tiles='cartodbpositron', height="100%")
    folium_map.add_child(stations_points_layer)
    folium_map.add_child(route_line_layer)

    map_div = folium_map._repr_html_()

    return render_template("stationsmap.html", map=map_div[96:], focus_id = 2)

# def route_map():
#      #"itinerarypoints":"2.238156,48.862088|2.403847,48.895546"}
    
#     start_coords = (48.855, 2.3433)
#     route_line = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Runs</p>""")

#     folium.PolyLine(line, color = "#0000FF", opacity = 1, control = False).add_to(route_line)

#     return (route_line, time_route, line)

def calculate_route(plan_profile, start_point, end_point):
    url = "https://www.cyclestreets.net/api/journey.json"
    start_point_string = ",".join(str(v) for v in start_point)
    end_point_string = ",".join(str(v) for v in end_point)
    itinerary_points = start_point_string + "|" + end_point_string
    r = requests.get(url, params = {"key":cycleapi_key,
                                    "plan":plan_profile,
                                    "itinerarypoints":itinerary_points})
    print(r.url)

    res = check_response(r)

    print(res)
    if res != 1:
        return "Error!"

    l1 = r.json()["marker"][0]["@attributes"]["coordinates"]
    l2 = list(l1.split(" "))
    l3 = []
    for item in l2:
        temp = map(float, item.split(',')[::-1]) # needed to inverse lat and lon for line printing
        l3.append(tuple(temp))

    time_route = (float(r.json()["marker"][0]["@attributes"]["time"])/60)

    line = l3

    return (line, time_route)

def get_location(location_string):
    url = "http://api.positionstack.com/v1/forward"
    
    r = requests.get(url, params = {"access_key":positionstack_key,
                                    "query":location_string})
    print(r.url)

    res = check_response(r)
    print(res)
    
    print(r.json())
    


def check_response(response):
    if response.ok:
        print("INFO:\tSuccessfully retrieved request")
        return 1
    else:
        print(response)
        errors = response.json()["errors"]
        print("INFO:\tRequest isn't retrieved succesfully. Nb of errors: {}.".format(len(errors)))
        for error in errors:
            print("ERROR:\t{}: {} {}".format(error["resource"],error["code"],error["field"]))
            if error["resource"] == "Application" and error["code"] == "exceeded":
                print("ERROR:\tWait 15 minutes for the query limit to renew")
                return 2
            else: print(errors)
            if error["resource"] == "Athlete" and error["code"] == "invalid":
                print("ERROR:\Invalid Access token. Logout and Login")
                return 3
            return 0

if __name__ == '__main__':
    app.run(debug=True)
