import numpy as np
import random
import math
import copy
from typing import List, Dict, Tuple, Set
import time

class Parameters:
    def __init__(self):
        # Truck parameters
        self.M_T = 50  # truck capacity
        self.truck_speed = 30  # km/h
        self.delta = 3 / 60  # service time (hours)
        self.delta_t = 5 / 60  # depot receive time (hours)

        # Drone parameters
        self.M_D = 2  # drone capacity (small instance)
        self.drone_speed = 60  # km/h
        self.L_d = 90 / 60  # max flight time (hours)
        self.delta_prime = 5 / 60  # loading/unloading time

        # Fleet size
        self.num_trucks = 2
        self.num_drones = 2

        # ALNS parameters
        self.max_iterations = 1000
        self.destroy_rate = 0.3  # remove 30% of customers
        self.temp_start = 100
        self.cooling_rate = 0.995
        self.weights = {'destroy': [1.0] * 3, 'repair': [1.0] * 2}
        self.scores = [10, 5, 1]  # best, better, accepted

class Customer:
    def __init__(self, id, x, y, type, ready_time, pair_id):
        self.id = id
        self.x = x
        self.y = y
        self.type = type  # 'D', 'P', 'DL'
        self.ready_time = ready_time / 60  # convert to hours
        self.pair_id = pair_id
        self.weight = 1

class Instance:
    def __init__(self, filename):
        self.customers = []
        self.depot = Customer(0, 10, 10, 'DEPOT', 0, 0)
        self.load_instance(filename)
        self.dist_matrix = self.compute_distances()
        self.n_customers = len(self.customers)

    def load_instance(self, filename):
        """Load instance from file with format: id X Y type ready_time pair_id"""
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line.startswith('#') or not line:
                    continue

                # Parse data line
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        id = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        type = parts[3]  # 'D', 'P', or 'DL'
                        ready = float(parts[4])
                        pair = int(parts[5])
                        self.customers.append(Customer(id, x, y, type, ready, pair))
                    except ValueError as e:
                        print(f"Warning: Could not parse line: {line}")
                        print(f"Error: {e}")
                        continue

        print(f"Loaded {len(self.customers)} customers from {filename}")

        # Print customer distribution by type
        types = {}
        for c in self.customers:
            types[c.type] = types.get(c.type, 0) + 1
        print(f"Customer types: {types}")

    def compute_distances(self):
        n = len(self.customers) + 1
        dist = np.zeros((n, n))
        all_nodes = [self.depot] + self.customers

        for i in range(n):
            for j in range(n):
                if i != j:
                    # Manhattan distance for truck
                    dx = abs(all_nodes[i].x - all_nodes[j].x)
                    dy = abs(all_nodes[i].y - all_nodes[j].y)
                    dist[i][j] = dx + dy
        return dist

    def euclidean_distance(self, i, j):
        """Euclidean distance for drone"""
        all_nodes = [self.depot] + self.customers
        dx = all_nodes[i].x - all_nodes[j].x
        dy = all_nodes[i].y - all_nodes[j].y
        return math.sqrt(dx * dx + dy * dy)