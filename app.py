import requests
import os
import numpy as np
from flask import Flask, render_template, request, session, url_for, current_app, redirect, flash, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import folium
import polyline
#Set-ExecutionPolicy Unrestricted -Scope Process

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'strava': {
        'id': "63388",
        'secret': 'cd53d9a8623c88f85fe7f59ca0c4e9a4e6c2ac5f'
    }
}
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

db = SQLAlchemy(app)
#lm = LoginManager(app)
#lm.login_view = 'index'

@app.route('/')
def index():
    return "Hello World!!!"

@app.route('/stations_map/')
def update_activities():

    url = "https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_information.json"
    r = requests.get(url)
    res = check_response(r)
    print(res)
    if res != 1:
        return "Error!"#render_template("error_page.html", error_nb = res)
    
    #station status thing
    url = "https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json"
    r2 = requests.get(url)
    res = check_response(r2)
    print(res)
    if res != 1:
        return "Error!"#render_template("error_page.html", error_nb = res)
    
    stations_status = r2.json()["data"]["stations"]

    x = [station_status for station_status in stations_status if station_status["station_id"]==516709288]
    print(x)

    start_coords = (48.855, 2.3433)
    stations_points = folium.FeatureGroup("""<p style="color:red; display:inline-block;">Runs</p>""")

    print(r.json()["data"]["stations"][0])
    # popup_html = """<p>Distance: {} km</p>
    #         <p>Date: {}</p>
    #         <form action = "{}" target="_blank" method = "post">
    #             <p><input type="hidden" id="postId" name="nm" value={}></p>
    #             <input type="submit" class="btn btn-primary" value="Show speed map"/>
    #         </form>""".format()
    
    line = polyline.decode("oxg_Iy|ppAl@wCdE}LfFsN|@_Ej@eEtAaMh@sGVuDNcDb@{PFyGdAi]FoC?q@sXQ_@?")

    folium.PolyLine(line, color = "#FF0000", opacity = 1, control = False).add_to(stations_points)
            
    for station in r.json()["data"]["stations"]:

        current_station_status = [station_status for station_status in stations_status if station_status["station_id"]==station["station_id"]][0]

        tooltip_html = """<p>Name: {}</p>
                        <p>Mechanical Bikes Available: {}</p>
                        <p>Electrical Bikes Available: {}</p>
                        <p>Docks Available: {}</p>
                        """.format(station["name"],
                                current_station_status["num_bikes_available_types"][0]["mechanical"],
                                current_station_status["num_bikes_available_types"][1]["ebike"],
                                current_station_status["num_docks_available"])

        folium.Circle((station["lat"],station["lon"]), 
                        color = "#FF0000", 
                        radius = 20,
                        fill = True,
                        tooltip = tooltip_html).add_to(stations_points)

    folium_map = folium.Map(location=start_coords, zoom_start=12, tiles='cartodbpositron', height="100%")
    folium_map.add_child(stations_points)

    map_div = folium_map._repr_html_()

    return render_template("stationsmap.html", map=map_div[96:], focus_id = 2)

    return "map page"


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
    db.create_all()
    app.run(debug=True)
