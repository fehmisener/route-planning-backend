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

    try:
        cur.execute(
            "insert into daily_vote values (?, ?, ?)",
            (user_id, user_station_id, route_date),
        )
        con.commit()
        return {"msg": "Succesfully saved.", "status_code": 201}, 201
    except:
        return {
            "msg": "Can not reserve twice for selected date",
            "status_code": 400,
        }, 400


@route_api.route("/route/daily-vote/", methods=["GET"])
def get_daily_vote_list():

    route_date = request.json["route_date"]

    cur.execute(
        """
        SELECT stations.id, stations.name, count(*) as passenger_count
        FROM daily_vote as votes, station as stations
        WHERE votes.user_station_id == stations.id AND votes.route_date=:route_date
        GROUP BY votes.user_station_id
        ORDER BY stations.id DESC
        """,
        {"route_date": route_date},
    )
    query_result = [dict(row) for row in cur.fetchall()]

    if len(query_result) == 0:
        return {"msg": "No daily vote in table.", "status_code": 403}, 403
    return {
        "daily_vote_list": query_result,
        "route_date": route_date,
    }, 200
