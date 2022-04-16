import sqlite3

import pandas as pd
from flask import Blueprint, request

from RouteCalculationAlgorithm import main

con = sqlite3.connect("database.db", check_same_thread=False)
con.row_factory = sqlite3.Row
cur = con.cursor()

car_api = Blueprint("car_api", __name__)

@car_api.route("/car/list", methods=["GET"])
def get_car_table():

    cur.execute("SELECT * from car ORDER BY car_capacity DESC ")
    query_result = [dict(row) for row in cur.fetchall()]

    if ( len(query_result) != 0 ):
        return {"car_list": query_result,"status_code": 200}, 200
    else:
        return {"msg": "No car in table","status_code": 401}, 401

@car_api.route("/car/add", methods=["POST"])
def add_car_table():

    car_capaciy = request.json["car_capacity"]

    cur.execute(
        "INSERT into car values (null, ?, ?)",
        (car_capaciy, 1),
    )
    con.commit()
    return {"msg": "Succesfully saved.","status_code": 200}, 200

@car_api.route("/car/update-capacity", methods=["PUT"])
def change_car_capacity():

    car_id= request.json["car_id"]
    car_capaciy = request.json["car_capacity"]

    cur.execute(
        "UPDATE car SET car_capacity=:car_capaciy WHERE car_id=:car_id",
        {"car_capaciy" :car_capaciy,"car_id": car_id}
    )
    con.commit()
    return {"msg": "Succesfully changed car capacity.","status_code": 200}, 200

@car_api.route("/car/delete-car", methods=["DELETE"])
def clear_daily_vote_table():

    car_id = request.json["car_id"]

    cur.execute(
        "DELETE FROM car where car_id=:car_id",
        {"car_id": car_id},
    )
    con.commit()

    return {"msg": "Car deleted.", "status_code": 200}, 200