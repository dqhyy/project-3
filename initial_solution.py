import numpy as np
import random
import math
import copy
from typing import List, Dict, Tuple, Set
import time

from model import Instance, Parameters
from evaluate import evaluate_solution
from solution import Solution
   
def create_initial_solution(instance: Instance, params: Parameters) -> Solution:
    """Create initial solution using nearest neighbor heuristic"""
    sol = Solution(instance, params)

    # Separate customers by type
    delivery_customers = [c.id for c in instance.customers if c.type in ['D']]
    pickup_customers = [(c.id, c.pair_id) for c in instance.customers if c.type == 'P']

    # Create pickup-delivery pairs
    pd_pairs = {}
    for p_id, pair_id in pickup_customers:
        delivery_id = None
        for c in instance.customers:
            if c.type == 'DL' and c.pair_id == pair_id:
                delivery_id = c.id
                break
        if delivery_id:
            pd_pairs[p_id] = delivery_id

    # Distribute customers to trucks using round-robin
    all_customers = delivery_customers + [p for p, _ in pickup_customers]
    random.shuffle(all_customers)

    for i, cust_id in enumerate(all_customers):
        truck_id = i % params.num_trucks
        sol.truck_routes[truck_id].append(cust_id)

        # If pickup, add corresponding delivery
        if cust_id in pd_pairs:
            sol.truck_routes[truck_id].append(pd_pairs[cust_id])

    # Optimize each route with nearest neighbor
    for truck_id in range(params.num_trucks):
        sol.truck_routes[truck_id] = nearest_neighbor_route(
            sol.truck_routes[truck_id], instance
        )

    sol.makespan = evaluate_solution(sol)
    return sol

def nearest_neighbor_route(customers: List[int], instance: Instance) -> List[int]:
    """Optimize route using nearest neighbor"""
    if len(customers) <= 1:
        return customers

    # Build route respecting pickup-delivery constraints
    pd_pairs = {}
    for c in instance.customers:
        if c.type == 'P':
            for c2 in instance.customers:
                if c2.type == 'DL' and c2.pair_id == c.pair_id:
                    pd_pairs[c.id] = c2.id

    route = []
    unvisited = set(customers)
    current = 0  # start from depot

    while unvisited:
        # Find nearest unvisited customer
        nearest = None
        min_dist = float('inf')

        for cust_id in unvisited:
            # Check if pickup-delivery constraint satisfied
            cust = instance.customers[cust_id - 1]
            if cust.type == 'DL':
                pickup_id = None
                for c in instance.customers:
                    if c.type == 'P' and c.pair_id == cust.pair_id:
                        pickup_id = c.id
                        break
                if pickup_id and pickup_id in unvisited:
                    continue  # skip delivery if pickup not done

            dist = instance.dist_matrix[current][cust_id]
            if dist < min_dist:
                min_dist = dist
                nearest = cust_id

        if nearest is None:
            # No valid customer, pick any
            nearest = list(unvisited)[0]

        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    return route