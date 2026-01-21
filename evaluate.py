from typing import List, Dict, Tuple, Set

from solution import Solution, DroneTrip

def schedule_drones(sol: Solution) -> Solution:
    """Schedule drone trips for delivery customers (type 'D')"""
    new_sol = sol.copy()
    new_sol.drone_trips = []

    # Identify delivery customers (type 'D') that need drone resupply
    delivery_customers = {}  # {truck_id: [(cust_id, position_in_route)]}

    for truck_id, route in enumerate(new_sol.truck_routes):
        delivery_customers[truck_id] = []
        for pos, cust_id in enumerate(route):
            cust = new_sol.instance.customers[cust_id - 1]
            if cust.type == 'D':
                delivery_customers[truck_id].append((cust_id, pos))

    # Schedule drones to resupply these customers
    # Strategy: Group nearby customers for the same truck
    available_drones = list(range(new_sol.params.num_drones))

    for truck_id in delivery_customers:
        if not delivery_customers[truck_id]:
            continue

        # Calculate truck timeline
        truck_timeline = calculate_truck_timeline(new_sol, truck_id)

        # Group delivery customers into drone trips
        customers_to_serve = delivery_customers[truck_id].copy()

        while customers_to_serve and available_drones:
            # Create a drone trip
            trip = DroneTrip()

            # Select up to M_D customers
            selected = customers_to_serve[:new_sol.params.M_D]
            customers_to_serve = customers_to_serve[new_sol.params.M_D:]

            trip.items = [cust_id for cust_id, _ in selected]
            trip.meet_truck = truck_id

            # Meet at the first customer location
            if selected:
                trip.meet_node = selected[0][0]
                meet_pos = selected[0][1]

                # Calculate timing
                if meet_pos < len(truck_timeline):
                    truck_arrival = truck_timeline[meet_pos]['arrival']

                    # Drone departs from depot when order is ready
                    earliest_ready = max([new_sol.instance.customers[c-1].ready_time
                                         for c in trip.items])

                    # Distance from depot to meeting point
                    meet_dist = new_sol.instance.euclidean_distance(0, trip.meet_node)
                    drone_travel = meet_dist / new_sol.params.drone_speed

                    # Drone departs at earliest possible time
                    trip.depart_time = max(earliest_ready,
                                          truck_arrival - drone_travel - new_sol.params.delta_prime)

                    # Drone flight time
                    trip.flight_time = drone_travel * 2 + new_sol.params.delta_prime
                    trip.return_time = trip.depart_time + trip.flight_time

                    # Check feasibility
                    if trip.flight_time <= new_sol.params.L_d:
                        new_sol.drone_trips.append(trip)

    return new_sol

def calculate_truck_timeline(sol: Solution, truck_id: int) -> List[Dict]:
    """Calculate arrival and departure times for each node in truck route"""
    timeline = []
    route = sol.truck_routes[truck_id]

    if not route:
        return timeline

    time = 0
    prev = 0

    for cust_id in route:
        cust = sol.instance.customers[cust_id - 1]

        # Travel time
        travel = sol.instance.dist_matrix[prev][cust_id] / sol.params.truck_speed
        time += travel

        # Wait for ready time
        if cust.type in ['D', 'DL']:
            time = max(time, cust.ready_time)

        arrival = time

        # Service time
        time += sol.params.delta
        departure = time

        timeline.append({
            'customer': cust_id,
            'arrival': arrival,
            'departure': departure
        })

        prev = cust_id

    return timeline
def evaluate_solution(sol: Solution) -> float:
    """Calculate makespan of solution"""
    if not sol.is_feasible():
        return float('inf')

    # Schedule drones first
    sol_with_drones = schedule_drones(sol)
    sol.drone_trips = sol_with_drones.drone_trips

    max_time = 0

    # Evaluate each truck route
    for truck_id, route in enumerate(sol.truck_routes):
        truck_time = calculate_truck_time(sol, truck_id, route)
        max_time = max(max_time, truck_time)

    # Evaluate drone completion times
    for trip in sol.drone_trips:
        max_time = max(max_time, trip.return_time)

    return max_time

def calculate_truck_time(sol: Solution, truck_id: int, route: List[int]) -> float:
    """Calculate completion time for a truck route"""
    if not route:
        return 0

    time = 0
    prev = 0

    for cust_id in route:
        cust = sol.instance.customers[cust_id - 1]

        # Travel time
        time += sol.instance.dist_matrix[prev][cust_id] / sol.params.truck_speed

        # Wait for ready time
        if cust.type in ['D', 'DL']:
            time = max(time, cust.ready_time)

        # Service time
        time += sol.params.delta

        prev = cust_id

    # Return to depot
    time += sol.instance.dist_matrix[prev][0] / sol.params.truck_speed

    return time