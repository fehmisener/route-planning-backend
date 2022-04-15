import sqlite3
from math import atan2, cos, radians, sin, sqrt

import pandas as pd
from scipy.spatial.distance import pdist, squareform

con = sqlite3.connect("database.db", check_same_thread=False)


class Route(object):
    def __init__(self, capacity, id):

        self.items = []
        self.load = 0
        self.capacity = capacity
        self.total_distance = 0
        self.car_id = id

    def append(self, item, load, distance):

        self.items.append(item)
        self.load += load
        self.total_distance += distance

    def change_capacity(self, capacity):
        self.capacity = capacity

    def __str__(self):

        return "Route List: {} | Route Load: {} | Route Total Distance: {} | Car Capacity: {}".format(
            self.items, self.load, self.total_distance, self.capacity
        )


def dist(x, y):
    """Function to compute the distance between two points x, y according to Havelsin Formula"""
    R = 6373.0

    lat1 = radians(x[0])
    lon1 = radians(x[1])
    lat2 = radians(y[0])
    lon2 = radians(y[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

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


def read_car_capacity():

    df = pd.read_sql_query(
        """ 
        SELECT car_id, car_capacity 
        FROM car 
        ORDER BY car_capacity DESC
        """,
        con,
    )

    if len(df) == 0:
        raise Exception("No car in table")

    return df.to_dict("list")


def sum_numbers(numbers):
    total = 0
    for number in numbers:
        total += number
    return total


def diff_list(li1, li2):
    li_dif = [i for i in li1 + li2 if i not in li1 or i not in li2]
    return li_dif


def find_belongs_route(route_list, station_id):

    route_index = 0
    for route in route_list:
        if station_id in route.items:
            return route_index
        else:
            route_index += 1
    return -1


def calculate_savings(demands, distance_matrix):

    k = 1
    z = 1
    list = []
    df_list = []
    len_distance_matrix = len(distance_matrix)

    for i in range(0, len_distance_matrix):

        k = i + 1
        for j in range(i + 1, len_distance_matrix - 1):

            sum = (
                distance_matrix[str(z)][str(k + 1)]
                + distance_matrix[str(z)][str(j + 2)]
                - distance_matrix[str(k + 1)][str(j + 2)]
            )
            list.append(sum)

            var = {
                "station_1": k,
                "station_2": j + 1,
                "station_1_demand": demands[k],
                "station_2_demand": demands[j + 1],
                "savings": sum,
                "distance": distance_matrix[str(k + 1)][str(j + 2)],
            }
            df_list.append(var)
        k += 1

    df = pd.DataFrame(df_list).sort_values(by=["savings"], ascending=False)
    df = df.reset_index()
    return df


def print_with_names(df, route_list):
    for route in route_list:
        str_route = ""
        for i in route.items:

            key = int(i)
            df["id"][key - 1]
            str_route += (
                str(df["id"][key - 1])
                + "("
                + str(key)
                + ") | "
                + str(df["name"][key - 1])
                + " -> "
            )
        print(str_route)


def print_routes(route_list):
    for route in route_list:
        print(route)


def main(route_date):

    df = read_daily_votes(route_date)
    df_matrix = df.copy()
    df_matrix = df_matrix.drop(columns=["id", "name", "passenger_count"])
    df_matrix.loc[-1] = [40.822195372435836, 29.921651689109996]
    df_matrix.index = df_matrix.index + 1
    df_matrix.sort_index(inplace=True)

    distances = pdist(df_matrix.values, metric=dist)

    points = [f"{i}" for i in range(1, len(df_matrix) + 1)]
    distance_matrix = pd.DataFrame(squareform(distances), columns=points, index=points)

    data = {}
    data["distance_matrix"] = distance_matrix
    data["demands"] = [0] + df["passenger_count"].to_list()
    data["vehicle_capacities"] = read_car_capacity()["car_capacity"]
    data["vehicle_id"] = read_car_capacity()["car_id"]

    route_list = []
    unique_list = []
    counter = -1
    k = 0

    df_savings = calculate_savings(data["demands"], data["distance_matrix"])

    for index, row in df_savings.iterrows():

        station_1_id = int(row["station_1"])
        station_1_demand = row["station_1_demand"]

        station_2_id = int(row["station_2"])
        station_2_demand = row["station_2_demand"]

        if station_1_id in unique_list and station_2_id in unique_list:

            pass
        elif station_1_id in unique_list or station_2_id in unique_list:

            station_id, station_demand, connection_station_id = (
                (station_2_id, station_2_demand, station_1_id)
                if station_1_id in unique_list
                else (station_1_id, station_1_demand, station_2_id)
            )
            route_id = find_belongs_route(route_list, connection_station_id)

            if (
                station_demand + route_list[route_id].load
                <= route_list[route_id].capacity
                and route_id != -1
            ):

                route_list[route_id].append(station_id, station_demand, row["distance"])
                unique_list.append(station_id)
        else:

            counter += 1

            if counter == len(data["vehicle_capacities"]):
                break
            if (station_1_demand + station_2_demand) <= data["vehicle_capacities"][
                counter
            ]:

                new_route = Route(
                    capacity=data["vehicle_capacities"][counter],
                    id=data["vehicle_id"][counter],
                )

                new_route.append(station_1_id, station_1_demand, row["distance"])
                new_route.append(station_2_id, station_2_demand, 0)

                route_list.append(new_route)
                unique_list.append(station_1_id)
                unique_list.append(station_2_id)

            else:
                counter -= 1
                pass
            
    customer_list = [i for i in range(1, len(data["distance_matrix"]))]
    cant_add = diff_list(customer_list, unique_list)

    if any(cant_add):
        counter += 1
        if ( len(cant_add) == 1 and counter < len(data["vehicle_capacities"]) ):

            distance = data["distance_matrix"]["1"][str(cant_add[0] + 1)]
            new_route = Route(
                capacity=data["vehicle_capacities"][counter],
                id=data["vehicle_id"][counter],
            )
            new_route.append(cant_add[0], data["demands"][cant_add[0]], distance)
            route_list.append(new_route)

        else:
            capacity_count = 0
            new_route = Route(0, -1)
            temp_i = 0
            start_flag = True

            for i in cant_add:
                capacity_count += data["demands"][i]

                if start_flag == True:

                    new_route.append(i, data["demands"][i], 0)
                    temp_i = i
                    start_flag = False
                else:
                    distance = data["distance_matrix"][str(temp_i + 1)][str(i + 1)]
                    new_route.append(i, data["demands"][i], distance)

            new_route.change_capacity(capacity_count)
            route_list.append(new_route)

    print_with_names(df, route_list)
    print("--------------------")
    print_routes(route_list)

    routes_dict = {}
    for i in route_list:

        station_list = []
        for point in i.items:

            station_list.append(
                {
                    "station_id": str(df["id"][point - 1]),
                    "station_name": df["name"][point - 1],
                    "station_lat": df["lat"][point - 1],
                    "station_lon": df["lon"][point - 1],
                }
            )
        routes_dict["car_{}".format(i.car_id)] = station_list

    car_list = []
    for i in route_list:

        car_list.append(
            {
                "car_id": i.car_id,
                "car_load": i.load,
                "car_capacity": i.capacity,
                "car_total_distance": i.total_distance,
            }
        )

    return routes_dict, car_list


if __name__ == "__main__":
    main("16/4/2022")
