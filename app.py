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
from folium.features import DivIcon
from datetime import datetime
import seaborn as sns
#Set-ExecutionPolicy Unrestricted -Scope Process

f = open("secret_codes.json")
secret_data = json.load(f)
f.close()
# comment
app = Flask(__name__)
app.secret_key = "hello"
cycleapi_key = secret_data["bike_routing_api_key"]
positionstack_key = secret_data["positionstack_api_key"]
geoapify_key = secret_data["geoapify_api_key"]

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
    
    session["start_end_choice_flag"] = 0
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
    print(session["random"])
    print("ELOOOOOO!")
    print("Session3", session["lap_change_points"])
    
    html_out = "nothing"
    # retrieve queries from the html form
    station_coords = request.form['station_coords']
    station_coords_split = station_coords.split(",,")
    #print(station_coords_split)
    print("2222222222222222222222")
    print(session["change_stations"])
    print(session["lap_change_points"])
    if station_coords_split[0] == "True":
        session["start_end_choice_flag"] += 1
        print("Start location session")
        session["start_station"] = (station_coords_split[3],station_coords_split[4])
    if station_coords_split[1] == "True":
        session["start_end_choice_flag"] += 1
        print("End location session")
        session["end_station"] = (station_coords_split[3],station_coords_split[4])
    if station_coords_split[2] == "True":
        session["start_end_choice_flag"] = 0
        print("Change location session")
        session["change_stations"].append((station_coords_split[3],station_coords_split[4]))
        if len(session["change_stations"])<session["change_stations_nb"]:
            [_, map_div] = create_single_change_map(session["lap_change_points"])
            html_out = """
            <div style="height: 100%">
            """ + map_div[96:] + "</div>"
    #print(station_coords)
    
    if session["start_end_choice_flag"] == 1:
        html_out = """
        <h1 style="text-align: center; padding: 70px 0;">Choose the second point =)</h1>
        """
    
    if session["start_end_choice_flag"] == 2:
        html_out = """
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
        <!--<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">-->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx" crossorigin="anonymous">
        </head>
        <div style="text-align: center; padding: 70px 0;">
        <form action = "{}" method = "post" target="_parent">
        <input type="submit" class="btn btn-primary btn-lg" value="Select the locations"/>
        </form>
        </div>
        """.format(url_for('confirm_stations'))
    
    return(html_out)

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


@app.route('/confirmstationschanges/', methods = ['POST'])
def confirm_stations():
    print("CONFIRM STATIONS PAGE")
    #print(session["start_station"])
    #print(session["end_station"])
    
    start_station = session["start_station"]
    end_station = session["end_station"]
    #print("Start station:")
    #print(start_station)
    [route_line, time_route] = calculate_route("fastest", reversed(start_station), reversed(end_station))
    
    target_lap_time = 27
    estimated_laps = math.ceil(time_route / float(target_lap_time))

    session["change_stations_nb"] = estimated_laps - 1
    
    lap_change_points = []
    for i in range(estimated_laps-1):
        lap_change_point = route_line[int((len(route_line)/estimated_laps)*(i+1))]
        lap_change_points.append(lap_change_point)

    #print(lap_change_points)
    
    session["random"] ="SMILE =)"
    session["change_stations"] = []
    #session["route_line"] = route_line
    session["lap_change_points"] = lap_change_points
    #print("ELOOOOOO!")
    #print("Session1", session["lap_change_points"])
    [map_div, map_div2] = create_single_change_map(lap_change_points)

    
    return render_template("columnmap_2maps.html", 
                           map1=map_div[96:],
                           map2=map_div2[96:])


def create_single_change_map(lap_change_points):
    [route_line, _] = calculate_route("fastest", reversed(session["start_station"]), reversed(session["end_station"]))
    
    linestring_route = LineString(route_line)
    route_line_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Route line</p>""")
    folium.PolyLine(route_line, color = "#0000FF", opacity = 1, control = False).add_to(route_line_layer)

    # change points layer
    change_points_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Runs</p>""")
    for point in lap_change_points:
        #print(point)
        folium.Circle(point, 
                color = "#000000", 
                radius = 400,
                fill = True).add_to(change_points_layer)
    ###

    start_coords = (48.855, 2.3433)

    folium_map = folium.Map(location=start_coords, zoom_start=12, tiles='cartodbpositron', height="100%")
    folium_map.add_child(change_points_layer)
    folium_map.add_child(route_line_layer)
    
    map_div = folium_map._repr_html_()
    
    
    
    if len(lap_change_points)>0:
        #print("length")
        #print(len(session["change_stations"]))
        folium_map.location = lap_change_points[len(session["change_stations"])]
        stations_points_layer = velib_map_layer(change_points_flag = True, choice_position = lap_change_points[len(session["change_stations"])], linestring = linestring_route)
        bounds = stations_points_layer.get_bounds()
        folium_map.fit_bounds(bounds)
        folium_map.add_child(stations_points_layer)
            
        map_div2 = folium_map._repr_html_()
    else:
        map_div2 = "NO CHANGE POINTS ;)"
    
    
    print("ELOOOOOO!")
    print("Session2", session["lap_change_points"])
    
    return(map_div, map_div2)
        

def start_end_points_layer(start_location, end_location):
    
    api = 2
    print("INFO[{}]:\tGetting start location".format(datetime.now().time()))
    if api == 2:
        start_json = get_location2(start_location)
    else:
        start_json = get_location(start_location)
    print("INFO[{}]:\tGetting end location".format(datetime.now().time()))
    if api == 2:
        end_json = get_location2(end_location)
    else:
        end_json = get_location(end_location)
    print("INFO[{}]:\tCompleted getting end location".format(datetime.now().time()))

    start_points_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Start Points</p>""")
    end_points_layer = folium.FeatureGroup("""<p style="color:red; display:inline-block;">End Points</p>""")
    
    start_list_to_html = []
    end_list_to_html = []

    if api == 2:
        #print(start_json["features"])
        if len(start_json["features"]) == 0:
            print("No coordinates found that correspond to the given location")
        else:
            for data in start_json["features"]:
                formatted = data["properties"]["formatted"]

                lat = data["properties"]["lat"]
                lon = data["properties"]["lon"]
                
                start_list_to_html.append(formatted+",,"+str(lat)+",,"+str(lon))
                
                folium.Circle((lat,lon), 
                            color = "#00FF00", 
                            radius = 200,
                            fill = True).add_to(start_points_layer)
        
        
        if len(end_json["features"]) == 0:
            print("No coordinates found that correspond to the given location")
        else:
            for data in end_json["features"]:
                formatted = data["properties"]["formatted"]

                lat = data["properties"]["lat"]
                lon = data["properties"]["lon"]
                
                end_list_to_html.append(formatted+",,"+str(lat)+",,"+str(lon))
                
                folium.Circle((lat,lon), 
                            color = "#FF0000", 
                            radius = 200,
                            fill = True).add_to(end_points_layer)
    
    
    else:
        if len(start_json["data"]) == 0:
            print("No coordinates found that correspond to the given location")
        else:
            for data in start_json["data"]:
                #print()
                #print(data)
                #print()
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

    #print(lap_change_points)
#
    #print(first_point, last_point)
    #print(time_route)
    #print(estimated_laps)

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


def velib_map_layer(station_choice_start = False, station_choice_end = False, change_points_flag = False, choice_position =(0,0), linestring = ""):
    #velib_map_layer(change_points_flag = 1, line = route_line)

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
        if station_choice_start or station_choice_end or change_points_flag:
            #print((station["lat"],station["lon"]), choice_position)
            distance_to_point = geopy.distance.distance((station["lat"],station["lon"]), choice_position).m
            if distance_to_point > 1200:
                continue


        current_station_status = [station_status for station_status in stations_status if station_status["station_id"]==station["station_id"]][0]
        tooltip_html = ""
        popup_html = None
        total_score = 50

        if station_choice_start:
            distance_score = 1000 - distance_to_point
            bike_score = min(int(current_station_status["num_bikes_available_types"][0]["mechanical"])*2,10)
            total_score = round(float(distance_score * bike_score)/100.0)
        
        
        if station_choice_end:
            distance_score = 1000 - distance_to_point
            dock_score = min(int(current_station_status["num_docks_available"])*2,10)
            total_score = round(float(distance_score * dock_score)/100.0) # range 0 - 100
        
        if change_points_flag:
            dist_line = Point((station["lat"],station["lon"])).distance(linestring) * 1000
            distance_score = max(10-dist_line,0)
            dock_score = min(int(current_station_status["num_docks_available"])*2,10)
            total_score = round(float(distance_score * dock_score)) # range 0 - 100

        if station_choice_start or station_choice_end or change_points_flag:
            #print("ELOOOOOO!")
            #print("Session4", session["lap_change_points"])
            popup_html = """<p>Name: {}</p>
                            <p>Station score: {}%</p>
                            <form action = "{}" method = "post">
                                <input type="hidden" id="station_coords" name="station_coords" value={}>
                                <input type="submit" class="btn btn-primary btn-lg" value="Select this station"/>
                            </form>
                            """.format(station["name"],
                                total_score,
                                url_for('end_station_choice'),
                                str(station_choice_start)+",,"+str(station_choice_end)+",,"+str(change_points_flag)+",,"+str(station["lat"])+",,"+str(station["lon"]))
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
  
        palette = list(sns.color_palette("gist_rainbow", 300).as_hex())

        folium.Circle((station["lat"],station["lon"]), 
                        # color = "#FFBB00", 
                        color = palette[total_score], 
                        radius = 20,
                        fill = True,
                        tooltip = tooltip_html,
                        popup = popup_html).add_to(stations_points_layer)

        # folium.Circle(
        #                 (station["lat"],station["lon"]),
        #                 radius = 10,
        #                 icon=DivIcon(
        #                     icon_size=(250,36),
        #                     icon_anchor=(0,0),
        #                     html='<div style="font-size: 20pt">{}</div>'.format(total_score),
        #                     )
        #                 ).add_to(stations_points_layer)
        
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
    
    #dist_all = Point((station["lat"],station["lon"])).distance(linestring_route) * 1000

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

    #print(r.json())
    
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
    print(r)
    #print(r.json())
    print(res)
    # print(r)
    if res != 1:
        return "Error!"
    #print(r.json())
    #exit()
    return(r.json())

def get_location2(location_string):

    #https://api.geoapify.com/v1/geocode/search?text=30%20Rue%20Etienne%20Marcel%20France&apiKey=23a88986ab3a487b92419472b008cbb5
    url = "https://api.geoapify.com/v1/geocode/search"
    
    r = requests.get(url, params = {"apiKey":geoapify_key,
                                    "text":location_string})
    
    print(r.url)
    res = check_response(r)
    print(r)
    #print(r.json())
    print(res)
    # print(r)
    if res != 1:
        return "Error!"
    #print(r.json())
    #exit()
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
