from flask import Flask
from flask import request

app = Flask(__name__)


import sqlite3

con = sqlite3.connect("database.db", check_same_thread=False)
con.row_factory = sqlite3.Row
cur = con.cursor()


@app.route("/auth/", methods=["POST"])
def check_auth():

    user_id = request.json["id"]
    user_pass = request.json["pass"]

    cur.execute(
        "select * from user where user_id=:user_id and pass=:user_pass",
        {"user_id": user_id, "user_pass": user_pass},
    )
    query_result = [dict(row) for row in cur.fetchall()]

    if len(query_result) == 0:
        return {"error": "User Not Found"}, 401

    return {"user_type": query_result[0]["type"], "user_id": query_result[0]["id"]}, 200


@app.route("/route/chose-station/", methods=["POST"])
def vote_station():
    user_id = request.json["user_id"]
    user_station_id = request.json["user_station_id"]
    route_date = request.json["route_date"]
    cur.execute(
        "insert into daily_vote values (null, ?, ?, ?)",
        (user_id, user_station_id, route_date),
    )
    con.commit()
    return {"msg": "succesfully saved"}, 200


@app.route("/route/certain", methods=["POST"])
def get_route_certain_car():
    return "Hello World!"


@app.route("/station/list", methods=["GET"])
def get_station_list():
    cur.execute(
        "select * from station"
    )
    query_result = [dict(row) for row in cur.fetchall()]
    return {"station_list":query_result},200


@app.route("/station/add", methods=["POST"])
def add_station():
    station_name = request.json["station_name"]
    station_lat = request.json["station_lat"]
    station_lon = request.json["station_lon"]
    cur.execute(
        "insert into station values (null, ?, ?, ?)",
        (station_name, station_lat, station_lon),
    )
    con.commit()
    return {"msg": "succesfully saved"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=105, debug=True)
