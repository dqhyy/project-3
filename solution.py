import copy

from model import Instance, Parameters

class DroneTrip:
    def __init__(self):
        self.items = []  # List of customer IDs to resupply
        self.meet_truck = -1  # Which truck to meet
        self.meet_node = -1  # Meet at which customer node
        self.depart_time = 0.0
        self.return_time = 0.0
        self.flight_time = 0.0

class Solution:
    def __init__(self, instance: Instance, params: Parameters):
        self.instance = instance
        self.params = params
        self.truck_routes = [[] for _ in range(params.num_trucks)]
        self.drone_trips = []
        self.makespan = float('inf')

    def copy(self):
        new_sol = Solution(self.instance, self.params)
        new_sol.truck_routes = [route.copy() for route in self.truck_routes]
        new_sol.drone_trips = copy.deepcopy(self.drone_trips)
        new_sol.makespan = self.makespan
        return new_sol

    def is_feasible(self):
        """Check if solution is feasible"""
        # Check all customers are served
        served = set()
        for route in self.truck_routes:
            served.update(route)

        n_customers = len(self.instance.customers)
        if len(served) != n_customers:
            return False

        # Check capacity and time constraints
        for truck_id, route in enumerate(self.truck_routes):
            if not self.check_truck_route(truck_id, route):
                return False

        return True

    def check_truck_route(self, truck_id, route):
        """Check truck route feasibility"""
        if not route:
            return True

        load = 0
        time = 0
        depot = 0

        # Check pickup-delivery precedence
        pickup_served = {}

        prev = depot
        for cust_id in route:
            cust = self.instance.customers[cust_id - 1]

            # Travel time
            time += self.instance.dist_matrix[prev][cust_id] / self.params.truck_speed

            # Check ready time for delivery customers
            if cust.type in ['D', 'DL']:
                time = max(time, cust.ready_time)

            # Check pickup-delivery order
            if cust.type == 'P':
                pickup_served[cust.pair_id] = True
                load += cust.weight
            elif cust.type == 'DL':
                if cust.pair_id not in pickup_served:
                    return False
                load -= cust.weight
            else:  # 'D'
                # Will be handled by resupply logic
                pass

            # Service time
            time += self.params.delta

            # Check capacity
            if load > self.params.M_T:
                return False

            prev = cust_id

        return True
 