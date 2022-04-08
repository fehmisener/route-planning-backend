from flask import Flask
from flask_cors import CORS

from RestAccountAPI import account_api
from RestRouteAPI import route_api
from RestStationAPI import station_api

app = Flask(__name__)
app.register_blueprint(account_api)
app.register_blueprint(route_api)
app.register_blueprint(station_api)
CORS(app)

if __name__ == "__main__":
    app.run()
