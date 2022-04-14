from flask import Flask
from flask_cors import CORS

from api.RestAccountAPI import account_api
from api.RestAlgorithmAPI import algorithm_api
from api.RestRouteAPI import route_api
from api.RestStationAPI import station_api

app = Flask(__name__)
app.register_blueprint(account_api)
app.register_blueprint(route_api)
app.register_blueprint(station_api)
app.register_blueprint(algorithm_api)
CORS(app)

if __name__ == "__main__":
    app.run(debug=True)
