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
from folium.plugins import MousePosition
from datetime import datetime
#Set-ExecutionPolicy Unrestricted -Scope Process

f = open("secret_codes.json")
secret_data = json.load(f)
f.close()
# comment
app = Flask(__name__)
app.secret_key = "hello"
cycleapi_key = secret_data["bike_routing_api_key"]
positionstack_key = secret_data["positionstack_api_key"]

# headers = {"accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#     "accept-encoding" : "gzip, deflate, br",
#     "accept-language" : "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7,pl-PL;q=0.6,pl;q=0.5",
#     "cache-control" : "max-age=0",
#     "cookie" : "iterableEndUserId=mr.dajman@yahoo.pl; sp=16d9a67e-f220-4af6-bf8d-04bd51b661ac; _ga=GA1.2.1321818476.1647106578; _gid=GA1.2.1845175847.1647869148; _sp_ses.047d=*; _strava4_session=g3au0oi5iqhbrerm87nspeudidongqel; fbm_284597785309=base_domain=.www.strava.com; fbsr_284597785309=bZZCacHQHStNSJXRmUUph4R8nxQ0JNfDGr0eUBWZeJY.eyJ1c2VyX2lkIjoiMTQ1ODA0NzA5MDg3Mzg4MSIsImNvZGUiOiJBUUJKYVJEUHNpaUZGRkZ6Y0ZoZm1rS3U1NXBBb2NtTzBLc3ZoRXZrVF9OaUNOSXdsWWZCd1FRV2JldUVZUlotM2dfSERITkdsdW50TmV1aERlRUVvSnFUZ3VEa2FtdEhQOXpmcy1JZUhiaGpGV1BWclFvcGQ0d0FyZS1fc0FrUXlvNjFuOFVLNm5fZHdWbzUyVVlKZENxeXkyWWh4bnlGOVpIODZHSk9VWTg4M21OZlVhUnpCQUNFWUNhMjhVNGxrYnNLTm9xaVVLcGd0SncxMk4zUF91RWcxRnE0TUFsMHRfelg5S1dlSFcwc2ZoY2FyUG01bDQzdjlpTS1jRFZtbEFlNmVzVElfMDR3c3IyLXVtbEx3VXpUbEg1dnE2dmdZRk1HaVRvTzM1VEFWQl9IMzJKdC1acVNmYWpoOEZtS2dleWl4NFdZNTEwVnFtU2cteXFsMm04OVNZbER0STlrOW0ybDU3N3V4Z0hmdnciLCJvYXV0aF90b2tlbiI6IkVBQUFBUWtOWkFrdDBCQURpRk9zeFpCWEpxdmI5dFNTQkdQSXNSd3IwSHV1WkNma0ZUN1V4c1d5VGg4S1ZPVUpJb1I1WkNWMVBYQ1dyUHJwYlJaQVFJS0NVdUFwTFhRVEtuMTJ6bHdDVmY3VTIxbmJTNVBpOXV6elNESG1ydmxOazJ3NWJsVzc0MTZvcHoxbUVNelN1UlB1ODF4eDlIa2x6eWZNYWtrb2o2c1IydEFnRGQzMVg2RmNnT1RySWpvMXNaRCIsImFsZ29yaXRobSI6IkhNQUMtU0hBMjU2IiwiaXNzdWVkX2F0IjoxNjQ3ODg5MTc1fQ; _sp_id.047d=6064eedf-92b3-4b99-a9a1-7f57806dbe04.1641494797.5.1647889184.1647193197.c99d5daf-a2aa-4cd0-be59-083e39307701",
#     "if-none-match" : 'W/"aded48b2f071f9aa44e2d6735f291037"',
#     "sec-ch-ua" : '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
#     "sec-ch-ua-mobile" : "?0",
#     "sec-ch-ua-platform" : '"Windows"',
#     "sec-fetch-dest" : 'document',
#     "sec-fetch-mode" : 'navigate',
#     'sec-fetch-site' : 'none',
#     'sec-fetch-user' : '?1',
#     'upgrade-insecure-requests' : '1',
#     'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36'}

@app.route('/')
def location_query():

    # get station points
    stations_points_layer = velib_map_layer()
    
    # create map
    
    print("INFO[{}]:\tCreating Velib map".format(datetime.now().time()))
    start_coords = (48.855, 2.3433)
    folium_map = folium.Map(location=start_coords, zoom_start=12, tiles='cartodbpositron', height="100%")
    folium_map.add_child(stations_points_layer)

    map_div = folium_map._repr_html_()
    print("INFO[{}]:\tVelib map created".format(datetime.now().time()))
    
    return render_template("columnmap_query.html", map=map_div[96:])

@app.route('/stationchoice/', methods = ['POST'])
def start_station_choice():

    # retrieve queries from the html form
    start_location = request.form['start_locations']
    end_location = request.form['end_locations']
    
    # retrieve the coordinates from the queries
    start_lat = start_location.split(",,")[1]
    start_lon = start_location.split(",,")[2]
    end_lat = end_location.split(",,")[1]
    end_lon = end_location.split(",,")[2]
    
    start_point = (start_lat, start_lon)
    end_point = (end_lat, end_lon)
    
    session["start_point"] = start_point
    session["end_point"] = end_point
    
    # get velib layer
    stations_points_layer_start = velib_map_layer(station_choice_start = True, choice_position = start_point)
    
    # create the map
    start_coords1 = start_point
    folium_map1 = folium.Map(location=start_coords1, zoom_start=16, tiles='cartodbpositron', height="100%")
    folium.Circle(start_point, 
            color = "#00FF00", 
            radius = 100,
            fill = True).add_to(folium_map1)
    folium_map1.add_child(stations_points_layer_start)
    map_div1 = folium_map1._repr_html_()
    
    # get velib layer
    stations_points_layer_end = velib_map_layer(station_choice_end = True, choice_position = end_point)
    
    start_coords2 = end_point
    folium_map2 = folium.Map(location=start_coords2, zoom_start=16, tiles='cartodbpositron', height="100%")
    folium.Circle(end_point, 
            color = "#FF0000", 
            radius = 100,
            fill = True).add_to(folium_map2)
    folium_map2.add_child(stations_points_layer_end)
    
    map_div2 = folium_map2._repr_html_()
    
    map_div1 = map_div1.replace("position: relative;","position: static;")
    map_div2 = map_div2.replace("position: relative;","position: static;")
    
    return render_template("columnmap_2maps.html", map1=map_div1[96:], map2=map_div2[96:], focus_id = 2)

@app.route('/stationchoice2/', methods = ['POST'])
def end_station_choice():

    # retrieve queries from the html form
    station_coords = request.form['station_coords']
    station_coords_split = station_coords.split(",,")
    print(station_coords_split)
    if station_coords_split[0] == "True":
        print("Start location session")
        session["start_station"] = (station_coords_split[1],station_coords_split[2])
    if station_coords_split[0] != "True":
        print("End location session")
        session["end_station"] = (station_coords_split[1],station_coords_split[2])
    print(station_coords)
    
    # # retrieve the coordinates from the queries
    # start_lat = start_location.split(",,")[1]
    # start_lon = start_location.split(",,")[2]
    # end_lat = end_location.split(",,")[1]
    # end_lon = end_location.split(",,")[2]
    
    # start_point = (start_lat, start_lon)
    # end_point = (end_lat, end_lon)
    
    # # get velib layer
    # stations_points_layer = velib_map_layer(station_choice = True, choice_position = start_point)
    
    # # create the map
    # start_coords1 = start_point
    # folium_map1 = folium.Map(location=start_coords1, zoom_start=16, tiles='cartodbpositron', height="100%")
    # folium.Circle(start_point, 
    #         color = "#00FF00", 
    #         radius = 100,
    #         fill = True).add_to(folium_map1)
    # folium_map1.add_child(stations_points_layer)
    # map_div1 = folium_map1._repr_html_()
    
    
    # # start_coords2 = end_point
    # # folium_map2 = folium.Map(location=start_coords2, zoom_start=16, tiles='cartodbpositron', height="100%")
    # # folium.Circle(end_point, 
    # #         color = "#FF0000", 
    # #         radius = 100,
    # #         fill = True).add_to(folium_map2)
    # # folium_map2.add_child(stations_points_layer)
    
    # # map_div2 = folium_map2._repr_html_()
    
    # map_div1 = map_div1.replace("position: relative;","position: static;")
    # # map_div2 = map_div2.replace("position: relative;","position: static;")
    
    # return render_template("columnmap_start_selection.html", map=map_div1[96:], focus_id = 2)
    return("Start")


@app.route('/routeplanningmap/', methods = ['POST'])
def route_planning_map():

    # retrieve queries from the html form
    start_location = request.form['start_locations']
    end_location = request.form['end_locations']
    
    # retrieve the coordinates from the queries
    start_lat = start_location.split(",,")[1]
    start_lon = start_location.split(",,")[2]
    end_lat = end_location.split(",,")[1]
    end_lon = end_location.split(",,")[2]
    
    start_point = (start_lon, start_lat)
    end_point = (end_lon, end_lat)
    
    # profile for the routing API
    plan_profile = "fastest"
    
    map_div = velib_and_route_map(plan_profile, start_point, end_point)
    

    return render_template("stationsmap.html", map=map_div[96:], focus_id = 2)

@app.route('/locationquerycheck/', methods = ['POST'])
def location_query_check():

    # retrieve choice of the location (html radio form)
    
    print("INFO[{}]:\tRetrieving adress from a form".format(datetime.now().time()))
    start_location = request.form['start_location']
    end_location = request.form['end_location']

    # create the start points layer
    print("INFO[{}]:\tCreate Start/End point layer".format(datetime.now().time()))
    [start_points_layer, end_points_layer, start_list_to_html, end_list_to_html] = start_end_points_layer(start_location, end_location)
    print("INFO[{}]:\tCompleted Start/End point layer".format(datetime.now().time()))
    # create velib points layer
    print("INFO[{}]:\tCreate velib map layer".format(datetime.now().time()))
    stations_points_layer = velib_map_layer()
    print("INFO[{}]:\tCompleted velib map layer".format(datetime.now().time()))
    
    # create the map
    
    print("INFO[{}]:\tCreate map".format(datetime.now().time()))
    start_coords = (48.855, 2.3433)
    folium_map = folium.Map(location=start_coords, zoom_start=12, tiles='cartodbpositron', height="100%")
    folium_map.add_child(start_points_layer)
    folium_map.add_child(end_points_layer)
    folium_map.add_child(stations_points_layer)

    map_div = folium_map._repr_html_()
    print("INFO[{}]:\tCompleted map".format(datetime.now().time()))
    
    return render_template("columnmap.html", 
                           map=map_div[96:], 
                           start_list=start_list_to_html, 
                           end_list=end_list_to_html)


@app.route('/confirmstations/', methods = ['POST'])
def confirm_stations():
    print(session["start_station"])
    print(session["end_station"])
    
    stations_points_layer = velib_map_layer()
    
    start_station = session["start_station"]
    end_station = session["end_station"]
    #print("Start station:")
    #print(start_station)
    [route_line, time_route] = calculate_route("fastest", reversed(start_station), reversed(end_station))

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

    print(first_point, last_point)
    print(time_route)
    print(estimated_laps)

    start_coords = (48.855, 2.3433)

    folium_map = folium.Map(location=start_coords, zoom_start=12, tiles='cartodbpositron', height="100%")
    folium_map.add_child(stations_points_layer)
    folium_map.add_child(route_line_layer)
    
    map_div = folium_map._repr_html_()
    
    return render_template("stationsmap.html", 
                           map=map_div[96:])


def start_end_points_layer(start_location, end_location):
    
    print("INFO[{}]:\tGetting start location".format(datetime.now().time()))
    start_json = get_location(start_location)
    print("INFO[{}]:\tGetting end location".format(datetime.now().time()))
    end_json = get_location(end_location)
    print("INFO[{}]:\tCompleted getting end location".format(datetime.now().time()))

    start_points_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Start Points</p>""")
    end_points_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">End Points</p>""")
    
    
    start_list_to_html = []
    end_list_to_html = []
    if len(start_json["data"]) == 0:
        print("No coordinates found that correspond to the given location")
    else:
        for data in start_json["data"]:
            print()
            print(data)
            print()
            #print(data["data"])
            lat = data["latitude"]
            lon = data["longitude"]
            
            name = data["name"]
            locality = data["locality"]
            start_list_to_html.append(name+", "+locality+",,"+str(lat)+",,"+str(lon))
            
            folium.Circle((lat,lon), 
                        color = "#00FF00", 
                        radius = 200,
                        fill = True).add_to(start_points_layer)

    if len(end_json["data"]) == 0:
        print("No coordinates found taht correspond to the given location")
    else:
        for data in end_json["data"]:
            #print(data)
            lat = data["latitude"]
            lon = data["longitude"]
            
            name = data["name"]
            locality = data["locality"]
            end_list_to_html.append(name+", "+locality+",,"+str(lat)+",,"+str(lon))
            
            folium.Circle((lat,lon), 
                        color = "#FF0000", 
                        radius = 200,
                        fill = True).add_to(end_points_layer)
    
    return([start_points_layer, end_points_layer, start_list_to_html, end_list_to_html])


def velib_and_route_map(plan_profile, start_point, end_point):
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
    #print(x)

    start_coords = (48.855, 2.3433)
    stations_points_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Runs</p>""")

    #print(r_station_information.json()["data"]["stations"][0])
    
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
        #print(lap_change_point)
        folium.Circle(lap_change_point, 
                        color = "#000000", 
                        radius = 200,
                        fill = True,
                        tooltip = tooltip_html).add_to(stations_points_layer)

    folium_map = folium.Map(location=start_coords, zoom_start=12, tiles='cartodbpositron', height="100%")
    folium_map.add_child(stations_points_layer)
    folium_map.add_child(route_line_layer)

    map_div = folium_map._repr_html_()
    
    return(map_div)


def velib_map_layer(station_choice_start = False, station_choice_end = False, choice_position =(0,0)):

    ### VELIB MAP ###
    
    print("INFO[{}]:\tRetrieving Velib station information".format(datetime.now().time()))
    url = "https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_information.json"
    r_station_information = requests.get(url)
    res = check_response(r_station_information)
    print("INFO[{}]:\tVelib station information retrieved".format(datetime.now().time()))
    # print(res)
    if res != 1:
        return "Error!"#render_template("error_page.html", error_nb = res)
    
    #station status thing
    print("INFO[{}]:\tRetrieving Velib station status".format(datetime.now().time()))
    url = "https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json"
    r_station_status = requests.get(url)
    res = check_response(r_station_status)
    print("INFO[{}]:\tVelib station status retrieved".format(datetime.now().time()))
    # print(res)
    if res != 1:
        return "Error!"#render_template("error_page.html", error_nb = res)
    
    stations_status = r_station_status.json()["data"]["stations"]
    stations_points_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Runs</p>""")

    
    print("INFO[{}]:\tPrinting velib circles on the layer".format(datetime.now().time()))
    for station in r_station_information.json()["data"]["stations"]:
        if station_choice_start or station_choice_end:
            distance_to_point = geopy.distance.distance((station["lat"],station["lon"]), choice_position).m
            if distance_to_point > 1000:
                continue

        current_station_status = [station_status for station_status in stations_status if station_status["station_id"]==station["station_id"]][0]
        tooltip_html = ""
        popup_html = None
        if station_choice_start or station_choice_end:
            popup_html = """<p>Name: {}</p>
                            <form action = "{}" method = "post">
                                <input type="hidden" id="station_coords" name="station_coords" value={}>
                                <input type="submit" class="btn btn-primary btn-lg" value="Select this station"/>
                            </form>
                            """.format(station["name"],
                                url_for('end_station_choice'),
                                str(station_choice_start)+",,"+str(station["lat"])+",,"+str(station["lon"]))
        # if station_choice_start:
        #     session["start_station"] = (station["lat"],station["lon"])
        # if station_choice_end:
        #     session["end_station"] = (station["lat"],station["lon"])
                            
        tooltip_html = """<p>Name: {}</p>
                        <p>Mechanical Bikes Available: {}</p>
                        <p>Electrical Bikes Available: {}</p>
                        <p>Docks Available: {}</p>
                        """.format(station["name"],
                                current_station_status["num_bikes_available_types"][0]["mechanical"],
                                current_station_status["num_bikes_available_types"][1]["ebike"],
                                current_station_status["num_docks_available"])
        
        folium.Circle((station["lat"],station["lon"]), 
                        color = "#FFBB00", 
                        radius = 20,
                        fill = True,
                        tooltip = tooltip_html,
                        popup = popup_html).add_to(stations_points_layer)
        
    print("INFO[{}]:\tFinished printing velib circles on the layer".format(datetime.now().time()))

    return(stations_points_layer)

#@app.route('/')
def stations_map():
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

    print(r.json())
    
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
    # print(r)
    if res != 1:
        return "Error!"
    print(r.json())
    return(r.json())
    


def check_response(response):
    if response.ok:
        print("INFO[{}]:\tSuccessfully retrieved request".format(datetime.now().time()))
        return 1
    else:
        print(response)
        print(response.json())
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
