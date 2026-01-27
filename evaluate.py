from typing import List, Dict, Tuple, Set
import numpy as np

from solution import Solution, DroneTrip

def schedule_drones(sol: Solution) -> Solution:
    """Schedule drone trips for delivery customers (type 'D') - OPTIMIZED"""
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

    # If no deliveries to resupply, return
    total_deliveries = sum(len(v) for v in delivery_customers.values())
    if total_deliveries == 0:
        return new_sol

    # Pre-calculate truck timelines for all trucks (avoid recalculation)
    truck_timelines = {}
    for truck_id in range(len(new_sol.truck_routes)):
        if delivery_customers.get(truck_id):
            truck_timelines[truck_id] = calculate_truck_timeline(new_sol, truck_id)

    # Schedule drones to resupply these customers
    for truck_id in delivery_customers:
        if not delivery_customers[truck_id]:
            continue

        truck_timeline = truck_timelines[truck_id]
        customers_to_serve = delivery_customers[truck_id].copy()

        while customers_to_serve:
            trip = DroneTrip()

            # Select up to M_D customers for this trip
            batch_size = min(len(customers_to_serve), new_sol.params.M_D)
            selected = customers_to_serve[:batch_size]
            customers_to_serve = customers_to_serve[batch_size:]

            trip.items = [cust_id for cust_id, _ in selected]
            trip.meet_truck = truck_id
            trip.meet_node = selected[0][0]
            meet_pos = selected[0][1]

            # Calculate timing
            if meet_pos < len(truck_timeline):
                truck_arrival = truck_timeline[meet_pos]['arrival']

                # Pre-calculate earliest ready time
                earliest_ready = max([new_sol.instance.customers[c-1].ready_time
                                     for c in trip.items])

                # Use pre-calculated euclidean distance
                meet_dist = new_sol.instance.euclidean_distance(0, trip.meet_node)
                drone_travel_time = meet_dist / new_sol.params.drone_speed

                ideal_depart = truck_arrival - drone_travel_time - new_sol.params.delta_prime
                trip.depart_time = max(earliest_ready, ideal_depart)

                trip.flight_time = drone_travel_time * 2 + new_sol.params.delta_prime
                trip.return_time = trip.depart_time + trip.flight_time

                if trip.flight_time <= new_sol.params.L_d:
                    new_sol.drone_trips.append(trip)

    return new_sol

def calculate_truck_timeline(sol: Solution, truck_id: int) -> List[Dict]:
    """Calculate arrival and departure times - OPTIMIZED"""
    timeline = []
    route = sol.truck_routes[truck_id]

    if not route:
        return timeline

    time = 0.0
    prev = 0

    # Pre-fetch parameters
    truck_speed = sol.params.truck_speed
    delta = sol.params.delta
    dist_matrix = sol.instance.dist_matrix
    customers = sol.instance.customers

    for cust_id in route:
        cust = customers[cust_id - 1]

        # Travel time
        time += dist_matrix[prev][cust_id] / truck_speed

        # Wait for ready time
        if cust.type in ['D', 'DL']:
            time = max(time, cust.ready_time)

        arrival = time
        time += delta

        timeline.append({
            'customer': cust_id,
            'arrival': arrival,
            'departure': time
        })

        prev = cust_id

    return timeline

def evaluate_solution(sol: Solution) -> float:
    """Calculate makespan - OPTIMIZED"""
    if not sol.is_feasible():
        return float('inf')

    # Schedule drones once
    sol_with_drones = schedule_drones(sol)
    sol.drone_trips = sol_with_drones.drone_trips

    max_time = 0.0

    # Evaluate all truck routes
    for truck_id, route in enumerate(sol.truck_routes):
        if route:
            truck_time = calculate_truck_time(sol, truck_id, route)
            max_time = max(max_time, truck_time)

    # Evaluate drone completion times
    if sol.drone_trips:
        max_drone_time = max(trip.return_time for trip in sol.drone_trips)
        max_time = max(max_time, max_drone_time)

    return max_time

def calculate_truck_time(sol: Solution, truck_id: int, route: List[int]) -> float:
    """Calculate completion time - OPTIMIZED with caching"""
    if not route:
        return 0.0

    time = 0.0
    prev = 0

    # Pre-fetch to avoid repeated attribute lookups
    truck_speed = sol.params.truck_speed
    delta = sol.params.delta
    delta_t = sol.params.delta_t
    dist_matrix = sol.instance.dist_matrix
    customers = sol.instance.customers

    for cust_id in route:
        cust = customers[cust_id - 1]

        # Travel time
        time += dist_matrix[prev][cust_id] / truck_speed

        # Wait for ready time
        if cust.type in ['D', 'DL']:
            time = max(time, cust.ready_time)

        # Service time
        time += delta
        prev = cust_id

    # Return to depot
    time += dist_matrix[prev][0] / truck_speed
    time += delta_t

    return time

# Cache for incremental evaluation
def calculate_truck_time_incremental(sol: Solution, truck_id: int, route: List[int], 
                                     insert_pos: int, insert_cust: int,
                                     prev_time: float = None) -> float:
    """Calculate truck time incrementally when inserting a customer - FAST"""
    if prev_time is None:
        return calculate_truck_time(sol, truck_id, route)
    
    # For now, fallback to full calculation
    # Can be optimized further with delta calculation
    return calculate_truck_time(sol, truck_id, route)