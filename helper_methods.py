def passenger_counter(passenger_list):
    total_passenger_count = 0
    for the_key, the_value in passenger_list.items():
        total_passenger_count = total_passenger_count + the_value
    return total_passenger_count
