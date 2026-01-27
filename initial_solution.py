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
    delivery_only = [c.id for c in instance.customers if c.type == "D"]
    pickup_delivery_pairs = []

    # Build P-DL pairs
    for p_id, dl_id in instance.pd_pairs.items():
        pickup_delivery_pairs.append((p_id, dl_id))

    # Distribute delivery-only customers to trucks using round-robin
    random.shuffle(delivery_only)
    for i, cust_id in enumerate(delivery_only):
        truck_id = i % params.num_trucks
        sol.truck_routes[truck_id].append(cust_id)

    # Distribute P-DL pairs to trucks
    random.shuffle(pickup_delivery_pairs)
    for i, (p_id, dl_id) in enumerate(pickup_delivery_pairs):
        truck_id = i % params.num_trucks
        # Add pickup first, then delivery (maintaining precedence)
        sol.truck_routes[truck_id].append(p_id)
        sol.truck_routes[truck_id].append(dl_id)

    # Optimize each route with nearest neighbor
    for truck_id in range(params.num_trucks):
        if sol.truck_routes[truck_id]:
            sol.truck_routes[truck_id] = nearest_neighbor_route(
                sol.truck_routes[truck_id], instance
            )

    sol.makespan = evaluate_solution(sol)
    return sol


def nearest_neighbor_route(customers: List[int], instance: Instance) -> List[int]:
    """Optimize route using nearest neighbor while respecting P-DL precedence"""
    if len(customers) <= 1:
        return customers

    route = []
    unvisited = set(customers)
    current = 0  # start from depot

    # Track pickup-delivery pairs
    pickup_done = set()

    while unvisited:
        nearest = None
        min_dist = float("inf")

        for cust_id in unvisited:
            cust = instance.customers[cust_id - 1]

            # Check precedence constraint for DL customers
            if cust.type == "DL":
                # Find corresponding pickup
                pickup_id = None
                for p_id, d_id in instance.pd_pairs.items():
                    if d_id == cust_id:
                        pickup_id = p_id
                        break

                # Skip DL if pickup not done yet
                if pickup_id and pickup_id in unvisited:
                    continue

            # Calculate distance
            dist = instance.dist_matrix[current][cust_id]

            # Prefer customers with earlier ready times (tie-breaker)
            penalty = 0
            if cust.type in ["D", "DL"]:
                penalty = cust.ready_time * 0.01  # Small penalty for later ready times

            adjusted_dist = dist + penalty

            if adjusted_dist < min_dist:
                min_dist = adjusted_dist
                nearest = cust_id

        if nearest is None:
            # Should not happen if logic is correct
            nearest = list(unvisited)[0]

        route.append(nearest)
        unvisited.remove(nearest)

        # Mark pickup as done
        cust = instance.customers[nearest - 1]
        if cust.type == "P":
            pickup_done.add(cust.pair_id)

        current = nearest

    return route
