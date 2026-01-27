import numpy as np
import random
import math
import copy
from typing import List, Dict, Tuple, Set
import time

class Parameters:
    def __init__(self):
        # Truck parameters
        self.M_T = 50
        self.truck_speed = 30
        self.delta = 3 / 60
        self.delta_t = 5 / 60

        # Drone parameters
        self.M_D = 2
        self.drone_speed = 60
        self.L_d = 90 / 60
        self.delta_prime = 5 / 60
        self.delta_d = 5 / 60

        # Fleet size
        self.num_trucks = 2
        self.num_drones = 2

        # ALNS parameters - OPTIMIZED for 100 customers
        self.max_iterations = 2000  # Increased for larger instances
        self.destroy_rate = 0.25  # Start with 25%
        self.temp_start = 100
        self.cooling_rate = 0.9975  # Slower cooling for more iterations
        self.weights = {'destroy': [1.0] * 3, 'repair': [1.0] * 2}
        self.scores = [15, 8, 2]  # Increased rewards for better solutions

class Customer:
    __slots__ = ['id', 'x', 'y', 'type', 'ready_time', 'pair_id', 'weight']
    
    def __init__(self, id, x, y, type, ready_time, pair_id):
        self.id = id
        self.x = x
        self.y = y
        self.type = type
        self.ready_time = ready_time / 60
        self.pair_id = pair_id
        self.weight = 1

class Instance:
    def __init__(self, filename):
        self.customers = []
        self.depot = Customer(0, 10, 10, 'DEPOT', 0, 0)
        self.load_instance(filename)
        self.dist_matrix = self.compute_distances()
        self.euclidean_dist_cache = {}  # Cache for euclidean distances
        self.n_customers = len(self.customers)
        self.pd_pairs = self.build_pd_pairs()

    def load_instance(self, filename):
        """Load instance - OPTIMIZED"""
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line:
                continue

            parts = line.split()
            if len(parts) >= 6:
                try:
                    id = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    type = parts[3]
                    ready = float(parts[4])
                    pair = int(parts[5])
                    self.customers.append(Customer(id, x, y, type, ready, pair))
                except ValueError:
                    continue

        print(f"Loaded {len(self.customers)} customers from {filename}")

        # Print customer distribution
        types = {}
        for c in self.customers:
            types[c.type] = types.get(c.type, 0) + 1
        print(f"Customer types: {types}")

    def build_pd_pairs(self):
        """Build P-DL pairs mapping - OPTIMIZED"""
        pairs = {}
        dl_dict = {c.pair_id: c.id for c in self.customers if c.type == 'DL'}
        
        for c in self.customers:
            if c.type == 'P' and c.pair_id in dl_dict:
                pairs[c.id] = dl_dict[c.pair_id]
        
        return pairs

    def compute_distances(self):
        """Compute Manhattan distance matrix - OPTIMIZED"""
        n = len(self.customers) + 1
        dist = np.zeros((n, n), dtype=np.float32)  # Use float32 for memory
        
        # Pre-compute coordinates
        coords = np.array([[self.depot.x, self.depot.y]] + 
                         [[c.x, c.y] for c in self.customers], dtype=np.float32)
        
        # Vectorized Manhattan distance
        for i in range(n):
            dist[i] = np.abs(coords[:, 0] - coords[i, 0]) + np.abs(coords[:, 1] - coords[i, 1])
        
        return dist

    def euclidean_distance(self, i: int, j: int) -> float:
        """Euclidean distance with caching"""
        if i > j:
            i, j = j, i
        
        key = (i, j)
        if key in self.euclidean_dist_cache:
            return self.euclidean_dist_cache[key]
        
        all_nodes = [self.depot] + self.customers
        dx = all_nodes[i].x - all_nodes[j].x
        dy = all_nodes[i].y - all_nodes[j].y
        dist = math.sqrt(dx * dx + dy * dy)
        
        self.euclidean_dist_cache[key] = dist
        return dist