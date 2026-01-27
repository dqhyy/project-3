import numpy as np
import random
import math
import copy
from typing import List, Dict, Tuple, Set
import time

from solution import Solution
from evaluate import calculate_truck_time

def random_removal(sol: Solution, q: int) -> Tuple[Solution, List[int]]:
    """Randomly remove q customers (respecting P-DL pairs)"""
    new_sol = sol.copy()

    # Collect all customers, marking P-DL pairs
    all_customers = []
    for route in new_sol.truck_routes:
        all_customers.extend(route)

    if len(all_customers) == 0:
        return new_sol, []

    # Separate into independent customers and pairs
    independent = []  # Type 'D' customers
    pairs_to_remove = []  # (P, DL) tuples
    already_in_pair = set()

    for cust_id in all_customers:
        if cust_id in already_in_pair:
            continue
            
        cust = new_sol.instance.customers[cust_id - 1]
        
        if cust.type == 'D':
            independent.append(cust_id)
        elif cust.type == 'P':
            # Find corresponding DL
            dl_id = new_sol.instance.pd_pairs.get(cust_id)
            if dl_id and dl_id in all_customers:
                pairs_to_remove.append((cust_id, dl_id))
                already_in_pair.add(cust_id)
                already_in_pair.add(dl_id)

    # Determine how many to remove
    total_units = len(independent) + len(pairs_to_remove)
    q_units = min(q, total_units)
    
    removed = []
    
    # Remove pairs and independent customers
    while len(removed) < q and (independent or pairs_to_remove):
        if random.random() < 0.5 and pairs_to_remove:
            # Remove a pair
            pair = random.choice(pairs_to_remove)
            removed.extend(pair)
            pairs_to_remove.remove(pair)
        elif independent:
            # Remove an independent customer
            cust = random.choice(independent)
            removed.append(cust)
            independent.remove(cust)
        elif pairs_to_remove:
            # No independent left, remove pair
            pair = random.choice(pairs_to_remove)
            removed.extend(pair)
            pairs_to_remove.remove(pair)

    # Remove from routes
    for truck_id in range(len(new_sol.truck_routes)):
        new_sol.truck_routes[truck_id] = [
            c for c in new_sol.truck_routes[truck_id] if c not in removed
        ]

    return new_sol, removed

def worst_removal(sol: Solution, q: int) -> Tuple[Solution, List[int]]:
    """Remove q customers with highest cost (respecting P-DL pairs)"""
    new_sol = sol.copy()

    # Calculate removal cost for each customer/pair
    costs = []
    
    for truck_id, route in enumerate(new_sol.truck_routes):
        for i, cust_id in enumerate(route):
            cust = new_sol.instance.customers[cust_id - 1]
            
            if cust.type == 'D':
                # Independent customer - calculate removal cost
                before = calculate_truck_time(new_sol, truck_id, route)
                test_route = route[:i] + route[i+1:]
                after = calculate_truck_time(new_sol, truck_id, test_route)
                saving = before - after
                costs.append((saving, [cust_id], truck_id))
                
            elif cust.type == 'P':
                # Must remove pair together
                dl_id = new_sol.instance.pd_pairs.get(cust_id)
                if dl_id and dl_id in route:
                    dl_idx = route.index(dl_id)
                    before = calculate_truck_time(new_sol, truck_id, route)
                    # Remove both P and DL
                    test_route = [c for c in route if c not in [cust_id, dl_id]]
                    after = calculate_truck_time(new_sol, truck_id, test_route)
                    saving = before - after
                    costs.append((saving, [cust_id, dl_id], truck_id))

    if not costs:
        return new_sol, []

    # Sort by cost (descending - higher savings first)
    costs.sort(reverse=True)

    removed = []
    removed_set = set()
    
    for saving, customers, truck_id in costs:
        # Check if not already removed
        if any(c in removed_set for c in customers):
            continue
            
        removed.extend(customers)
        removed_set.update(customers)
        
        if len(removed) >= q:
            break

    # Remove from routes
    for truck_id in range(len(new_sol.truck_routes)):
        new_sol.truck_routes[truck_id] = [
            c for c in new_sol.truck_routes[truck_id] if c not in removed
        ]

    return new_sol, removed

def related_removal(sol: Solution, q: int) -> Tuple[Solution, List[int]]:
    """Remove q related customers by distance (respecting P-DL pairs)"""
    new_sol = sol.copy()

    all_customers = []
    for route in new_sol.truck_routes:
        all_customers.extend(route)

    if len(all_customers) == 0:
        return new_sol, []

    # Pick random seed customer
    seed = random.choice(all_customers)
    seed_cust = new_sol.instance.customers[seed - 1]

    removed = []
    
    # If seed is part of a pair, remove the pair
    if seed_cust.type == 'P':
        dl_id = new_sol.instance.pd_pairs.get(seed)
        if dl_id and dl_id in all_customers:
            removed = [seed, dl_id]
    elif seed_cust.type == 'DL':
        # Find corresponding P
        for p_id, d_id in new_sol.instance.pd_pairs.items():
            if d_id == seed:
                if p_id in all_customers:
                    removed = [p_id, seed]
                break
    else:
        removed = [seed]

    # Find nearest customers to seed
    distances = []
    for cust_id in all_customers:
        if cust_id not in removed:
            dist = sol.instance.dist_matrix[seed][cust_id]
            cust = new_sol.instance.customers[cust_id - 1]
            
            if cust.type == 'P':
                # Consider pair distance
                dl_id = new_sol.instance.pd_pairs.get(cust_id)
                distances.append((dist, [cust_id, dl_id] if dl_id else [cust_id]))
            elif cust.type == 'DL':
                # Check if P already removed
                p_id = None
                for pid, did in new_sol.instance.pd_pairs.items():
                    if did == cust_id:
                        p_id = pid
                        break
                if p_id not in removed:
                    distances.append((dist, [p_id, cust_id] if p_id else [cust_id]))
            else:
                distances.append((dist, [cust_id]))

    distances.sort()
    
    # Add nearest customers until reaching q
    for dist, customers in distances:
        if len(removed) >= q:
            break
        if all(c not in removed for c in customers):
            removed.extend(customers)

    # Remove from routes
    for truck_id in range(len(new_sol.truck_routes)):
        new_sol.truck_routes[truck_id] = [
            c for c in new_sol.truck_routes[truck_id] if c not in removed
        ]

    return new_sol, removed