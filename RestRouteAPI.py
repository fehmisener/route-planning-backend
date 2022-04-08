import sqlite3

from flask import Blueprint, request

con = sqlite3.connect("database.db", check_same_thread=False)
con.row_factory = sqlite3.Row
cur = con.cursor()

route_api = Blueprint("route_api", __name__)


@route_api.route("/route/chose-station/", methods=["POST"])
def vote_station():

    user_id = request.json["user_id"]
    user_station_id = request.json["user_station_id"]
    route_date = request.json["route_date"]

    cur.execute(
        "insert into daily_vote values (null, ?, ?, ?)",
        (user_id, user_station_id, route_date),
    )
    con.commit()
    return {"msg": "Succesfully saved."}, 200


@route_api.route("/route/daily-vote/", methods=["GET"])
def get_daily_vote_list():

    route_date = request.json["route_date"]

    cur.execute(
        "select * from daily_vote where route_date=:route_date", {"route_date": route_date}
    )
    query_result = [dict(row) for row in cur.fetchall()]

    if len(query_result) == 0:
        return {"error": "No daily_vote in table."}, 200
    return {
        "daily_vote_list": query_result,
    }, 200
