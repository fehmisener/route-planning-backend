"""Capacited Vehicles Routing Problem (CVRP)."""

import sqlite3
from math import atan2, cos, radians, sin, sqrt

import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from scipy.spatial.distance import pdist, squareform

con = sqlite3.connect("database.db", check_same_thread=False)


def dist(x, y):
    """Function to compute the distance between two points x, y"""

    lat1 = radians(x[0])
    lon1 = radians(x[1])
    lat2 = radians(y[0])
    lon2 = radians(y[1])

    R = 6373.0

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c * 1000

    return int(distance)


def read_daily_votes(route_date):
    df = pd.read_sql_query(
        """
    SELECT stations.id, stations.name, stations.lat, stations.lon, count(*) as passenger_count
    FROM daily_vote as votes, station as stations
    WHERE votes.user_station_id == stations.id AND votes.route_date=="{}"
    GROUP BY votes.user_station_id
    ORDER BY stations.id ASC
    """.format(
            route_date
        ),
        con,
    )

    if len(df) == 0:
        raise Exception("Provided date can't find")

    return df


def get_routes(route_date, route_list):

    routes_dict = {}
    counter = 1
    df = read_daily_votes(route_date)

    for i in route_list:
        if len(i) == 2:
            continue

        station_list = []
        for point in i:
            if point == 0:
                station_list.append(
                    {
                        "station_id": 0,
                        "station_name": "Kocaeli Universitesi",
                        "station_lat": 40.822195372435836,
                        "station_lon": 29.921651689109996,
                    }
                )
            else:
                station_list.append(
                    {
                        "station_id": point,
                        "station_name": df["name"][point - 1],
                        "station_lat": df["lat"][point - 1],
                        "station_lon": df["lon"][point - 1],
                    }
                )

        routes_dict["car_{}".format(counter)] = station_list
        counter = counter + 1

    return routes_dict


def create_data_model(route_date):
    """Stores the data for the problem."""

    df = read_daily_votes(route_date)
    df_matrix = df.drop(columns=["id", "name", "passenger_count"])
    df_matrix.loc[-1] = [40.822195372435836, 29.921651689109996]  # adding a row
    df_matrix.index = df_matrix.index + 1  # shifting index
    df_matrix.sort_index(inplace=True)

    distances = pdist(df_matrix.values, metric=dist)
    distance_matrix = squareform(distances).tolist()

    data = {}
    data["distance_matrix"] = distance_matrix
    data["demands"] = [0] + df["passenger_count"].to_list()
    data["vehicle_capacities"] = [20, 30, 50]
    data["num_vehicles"] = 3
    data["depot"] = 0
    return data


def print_solution(data, manager, routing, solution,route_date):
    """Prints solution on console."""
    total_distance = 0
    total_load = 0
    route_list = []

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        route_distance = 0
        route_load = 0
        temp_route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data["demands"][node_index]
            plan_output += " {0} Load({1}) -> ".format(node_index, route_load)
            temp_route.append(node_index)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        temp_route.append(manager.IndexToNode(index))
        route_list.append(temp_route)
        plan_output += " {0} Load({1})\n".format(manager.IndexToNode(index), route_load)
        plan_output += "Distance of the route: {}m\n".format(route_distance)
        plan_output += "Load of the route: {}\n".format(route_load)
        # print(plan_output)
        total_distance += route_distance
        total_load += route_load

    routes_dict = {}
    counter = 1
    df = read_daily_votes(route_date)

    for i in route_list:
        if len(i) == 2:
            continue

        station_list = []
        for point in i:
            if point == 0:
                station_list.append(
                    {
                        "station_id": 0,
                        "station_name": "Kocaeli Universitesi",
                        "station_lat": 40.822195372435836,
                        "station_lon": 29.921651689109996,
                    }
                )
            else:
                station_list.append(
                    {
                        "station_id": point,
                        "station_name": df["name"][point - 1],
                        "station_lat": df["lat"][point - 1],
                        "station_lon": df["lon"][point - 1],
                    }
                )

        routes_dict["car_{}".format(counter)] = station_list
        counter = counter + 1

    return routes_dict


def main(route_date):
    """Solve the CVRP problem."""
    # Instantiate the data problem.

    data = create_data_model(route_date)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data["vehicle_capacities"],  # vehicle maximum capacities
        True,  # start cumul to zero
        "Capacity",
    )

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(1)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        return print_solution(data, manager, routing, solution,route_date)

if __name__ == "__main__":
    main()


# def print_routes():
#     for i in route_list:
#         if len(i) == 2:
#             continue
#         for point in i:
#             if point == 0:
#                 print("id:{} | name: {} ".format(0, "Kocaeli Universitesi"))
#             else:
#                 print("id:{} | name: {} ".format(point, df["name"][point - 1]))
#         print("--------------")
