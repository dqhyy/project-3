import numpy as np
import random
import math
import copy
from typing import List, Dict, Tuple, Set
import time

from solution import Solution
from evaluate import calculate_truck_time

def random_removal(sol: Solution, q: int) -> Solution:
    """Randomly remove q customers"""
    new_sol = sol.copy()

    all_customers = []
    for route in new_sol.truck_routes:
        all_customers.extend(route)

    if len(all_customers) == 0:
        return new_sol

    q = min(q, len(all_customers))
    removed = random.sample(all_customers, q)

    for truck_id in range(len(new_sol.truck_routes)):
        new_sol.truck_routes[truck_id] = [
            c for c in new_sol.truck_routes[truck_id] if c not in removed
        ]

    return new_sol, removed

def worst_removal(sol: Solution, q: int) -> Solution:
    """Remove q customers with highest cost"""
    new_sol = sol.copy()

    # Calculate removal cost for each customer
    costs = []
    for truck_id, route in enumerate(new_sol.truck_routes):
        for i, cust_id in enumerate(route):
            # Cost = time saved by removing this customer
            before = calculate_truck_time(new_sol, truck_id, route)
            test_route = route[:i] + route[i+1:]
            after = calculate_truck_time(new_sol, truck_id, test_route)
            costs.append((before - after, cust_id, truck_id))

    if not costs:
        return new_sol, []

    # Sort by cost (descending)
    costs.sort(reverse=True)

    q = min(q, len(costs))
    removed = [costs[i][1] for i in range(q)]

    for truck_id in range(len(new_sol.truck_routes)):
        new_sol.truck_routes[truck_id] = [
            c for c in new_sol.truck_routes[truck_id] if c not in removed
        ]

    return new_sol, removed

def related_removal(sol: Solution, q: int) -> Solution:
    """Remove q related customers (by distance)"""
    new_sol = sol.copy()

    all_customers = []
    for route in new_sol.truck_routes:
        all_customers.extend(route)

    if len(all_customers) == 0:
        return new_sol, []

    # Pick random seed customer
    seed = random.choice(all_customers)

    # Find q-1 nearest customers to seed
    distances = []
    for cust_id in all_customers:
        if cust_id != seed:
            dist = sol.instance.dist_matrix[seed][cust_id]
            distances.append((dist, cust_id))

    distances.sort()
    q = min(q, len(all_customers))
    removed = [seed] + [distances[i][1] for i in range(min(q-1, len(distances)))]

    for truck_id in range(len(new_sol.truck_routes)):
        new_sol.truck_routes[truck_id] = [
            c for c in new_sol.truck_routes[truck_id] if c not in removed
        ]

    return new_sol, removed
