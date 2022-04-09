import sqlite3

from flask import Blueprint, request

from CertainCarAlgorithm import main

con = sqlite3.connect("database.db", check_same_thread=False)
con.row_factory = sqlite3.Row
cur = con.cursor()

algorithm_api = Blueprint("algorithm_api", __name__)


@algorithm_api.route("/algorithm/limited-car/route-list", methods=["POST"])
def get_routes_for_limited_car():

    route_date = request.json["route_date"]

    cur.execute(
        "select * from route where route_date=:route_date", {"route_date": route_date}
    )
    query_result = [dict(row) for row in cur.fetchall()]

    if len(query_result) == 0:
        return {"error": "No routes in table."}, 200
    return {
        "route_list": query_result,
    }, 200


@algorithm_api.route("/algorithm/limited-car/route-save", methods=["POST"])
def save_routes_for_limited_car():

    route_date = request.json["route_date"]

    route_list = main(route_date)

    for i in route_list:
        counter = 0
        for j in route_list[i]:
            cur.execute(
                "insert into route values (?, ?,?, ?)",
                (i.split("_")[1], j["station_id"], counter, route_date),
            )
            con.commit()
            counter = counter + 1

    return route_list, 200


@algorithm_api.route("/algorithm/limited-car/route", methods=["POST"])
def get_route_for_user():

    user_id = request.json["user_id"]
    route_date = request.json["route_date"]
    
    cur.execute(
    """
    SELECT 
    * 
    FROM 
        route 
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
                user_id=:user_id and route_date=:route_date
            )
        )
    """, {"user_id": user_id, "route_date": route_date}
    )
    query_result = [dict(row) for row in cur.fetchall()]

    if len(query_result) == 0:
        return {"error": "No routes in table for this user."}, 200
    return {
        "service_route": query_result,
    }, 200