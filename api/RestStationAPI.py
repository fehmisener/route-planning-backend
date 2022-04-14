import sqlite3

from flask import Blueprint, request

con = sqlite3.connect("database.db", check_same_thread=False)
con.row_factory = sqlite3.Row
cur = con.cursor()

station_api = Blueprint("station_api", __name__)


@station_api.route("/station/list", methods=["GET"])
def get_station_list():

    cur.execute("select * from station")
    query_result = [dict(row) for row in cur.fetchall()]
    return {"station_list": query_result}, 200


@station_api.route("/station/add", methods=["POST"])
def add_station():

    station_name = request.json["station_name"]
    station_lat = request.json["station_lat"]
    station_lon = request.json["station_lon"]

    cur.execute(
        "insert into station values (null, ?, ?, ?)",
        (station_name, station_lat, station_lon),
    )
    con.commit()
    return {"msg": "Succesfully saved."}, 200
