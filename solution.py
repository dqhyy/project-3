import copy
from typing import List

from model import Instance, Parameters


class DroneTrip:
    def __init__(self):
        self.items = []
        self.meet_truck = -1
        self.meet_node = -1
        self.depart_time = 0.0
        self.return_time = 0.0
        self.flight_time = 0.0


class Solution:
    def __init__(self, instance: Instance, params: Parameters):
        self.instance = instance
        self.params = params
        self.truck_routes = [[] for _ in range(params.num_trucks)]
        self.drone_trips = []
        self.makespan = float("inf")

        # Cache for feasibility checks
        self._feasibility_cache = {}

    def copy(self):
        new_sol = Solution(self.instance, self.params)
        new_sol.truck_routes = [route.copy() for route in self.truck_routes]
        new_sol.drone_trips = copy.deepcopy(self.drone_trips)
        new_sol.makespan = self.makespan
        return new_sol

    def is_feasible(self) -> bool:
        """Check if solution is feasible - OPTIMIZED"""
        # Check all customers are served exactly once
        served = set()
        for route in self.truck_routes:
            for cust_id in route:
                if cust_id in served:
                    return False
                served.add(cust_id)

        n_customers = len(self.instance.customers)
        if len(served) != n_customers:
            return False

        # Check each truck route
        for truck_id, route in enumerate(self.truck_routes):
            if not self.check_truck_route(truck_id, route):
                return False

        return True

    def check_truck_route(self, truck_id: int, route: List[int]) -> bool:
        """Check truck route feasibility - OPTIMIZED"""
        if not route:
            return True

        # Create cache key
        route_key = tuple(route)
        if route_key in self._feasibility_cache:
            return self._feasibility_cache[route_key]

        load = 0
        time = 0.0

        # Pre-fetch frequently accessed data
        customers = self.instance.customers
        dist_matrix = self.instance.dist_matrix
        truck_speed = self.params.truck_speed
        delta = self.params.delta
        M_T = self.params.M_T

        # Track pickups
        pickup_served = set()
        prev = 0

        for cust_id in route:
            cust = customers[cust_id - 1]

            # Travel time
            time += dist_matrix[prev][cust_id] / truck_speed

            # Wait for ready time
            if cust.type in ["D", "DL"]:
                time = max(time, cust.ready_time)

            # Check precedence and update load
            if cust.type == "P":
                pickup_served.add(cust.pair_id)
                load += cust.weight
            elif cust.type == "DL":
                if cust.pair_id not in pickup_served:
                    self._feasibility_cache[route_key] = False
                    return False
                load -= cust.weight

            # Check capacity
            if load > M_T or load < 0:
                self._feasibility_cache[route_key] = False
                return False

            time += delta
            prev = cust_id

        # Final load must be 0
        result = load == 0
        self._feasibility_cache[route_key] = result
        return result

    def get_pd_pair(self, cust_id: int):
        """Get paired customer ID"""
        cust = self.instance.customers[cust_id - 1]

        if cust.type == "P":
            return self.instance.pd_pairs.get(cust_id)
        elif cust.type == "DL":
            for p_id, d_id in self.instance.pd_pairs.items():
                if d_id == cust_id:
                    return p_id
        return None
