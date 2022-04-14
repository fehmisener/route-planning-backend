import sqlite3

from flask import Blueprint, request

con = sqlite3.connect("database.db", check_same_thread=False)
con.row_factory = sqlite3.Row
cur = con.cursor()

account_api = Blueprint("account_api", __name__)


@account_api.route("/account/auth", methods=["POST"])
def check_auth():

    user_id = request.json["username"]
    user_pass = request.json["password"]

    cur.execute(
        "select * from user where user_id=:user_id and pass=:user_pass",
        {"user_id": user_id, "user_pass": user_pass},
    )
    query_result = [dict(row) for row in cur.fetchall()]

    if len(query_result) == 0:
        return {
            "msg": "User not found or one of the account information is incorrect.",
            "status_code": 401,
        }, 401
    return {
        "msg": "User account verifed. Succesfully login.",
        "user_type": query_result[0]["type"],
        "user_id": query_result[0]["id"],
        "status_code": 200,
    }, 200


@account_api.route("/account/register", methods=["POST"])
def register_user():

    user_id = request.json["username"]
    user_pass = request.json["password"]
    user_type = request.json["user_type"]

    cur.execute(
        "insert into user values (null, ?, ?, ?)",
        (user_id, user_pass, user_type),
    )
    con.commit()
    return {"msg": "Succesfully account created.", "status_code": 201}, 201


@account_api.route("/account/list", methods=["GET"])
def list_user():

    cur.execute("select * from user")
    query_result = [dict(row) for row in cur.fetchall()]

    if len(query_result) == 0:
        return ({"msg": "No user in table.", "status_code": 403},)
    return {"user_list": query_result, "status_code": 200}, 200
