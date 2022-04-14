import sqlite3

import pandas as pd
from flask import Blueprint, request

from CertainCarAlgorithm import main

con = sqlite3.connect("database.db", check_same_thread=False)
con.row_factory = sqlite3.Row
cur = con.cursor()

algorithm_api = Blueprint("algorithm_api", __name__)


@algorithm_api.route("/algorithm/limited-car/route-list", methods=["POST"])
def get_routes_for_limited_car():

    route_date = request.json["route_date"]

    df = pd.read_sql_query(
        """
    SELECT car_id,station_id,station_order,name,lat,lon,route_date
    FROM route as routes, station as stations
    WHERE routes.station_id = stations.id
    AND route_date == "{}"
    """.format(
            route_date
        ),
        con=con,
    )

    df_unique_id = df["car_id"].unique()
    routes_list = []
    for i in df_unique_id:
        temp_df = df.query("car_id == @i")
        routes_list.append(temp_df.to_dict(orient="records"))

    if len(routes_list) == 0:
        return {"msg": "No routes in table.", "status_code": 403}, 403
    return {
        "route_list": routes_list,
    }, 200


@algorithm_api.route("/algorithm/limited-car/route", methods=["POST"])
def get_route_for_user():

    user_id = request.json["user_id"]
    route_date = request.json["route_date"]

    cur.execute(
        """
        SELECT 
        * 
        FROM 
            route, station as stations 
        WHERE 
            car_id IN (
                SELECT 
                DISTINCT car_id 
                FROM 
                route 
                WHERE 
                station_id IN (
                    SELECT 
                    user_station_id 
                    FROM 
                    daily_vote 
                    WHERE 
                    user_id=:user_id AND route_date=:route_date
                )
                AND route.route_date=:route_date
            )
        AND route.station_id = stations.id AND route.route_date=:route_date
        """,
        {"user_id": user_id, "route_date": route_date},
    )
    query_result = [dict(row) for row in cur.fetchall()]

    if len(query_result) == 0:
        return {"msg": "No route for this user in table.", "status_code": 403}, 403
    return {"service_route": query_result, "user_id": user_id}, 200


@algorithm_api.route("/algorithm/limited-car/route-save", methods=["POST"])
def save_routes_for_limited_car():

    route_date = request.json["route_date"]
    route_list = main(route_date)

    try:
        for i in route_list:
            counter = 0
            for j in route_list[i]:
                cur.execute(
                    "insert into route values (?, ?, ?, ?)",
                    (i.split("_")[1], j["station_id"], counter, route_date),
                )
                con.commit()
                counter = counter + 1
        return route_list, 200
    except:
        return {
            "msg": 'You cannot calculate routes twice in one day. You can press the "Show Routes" button to see the route you calculated before.',
            "status_code": 400,
        }, 400


# TODO RETURN SPESIFIC ROUTE
