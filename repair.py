import numpy as np
import random
import math
import copy
from typing import List, Dict, Tuple, Set
import time

from solution import Solution
from evaluate import calculate_truck_time, evaluate_solution

def greedy_insertion(sol: Solution, removed: List[int]) -> Solution:
    """Insert removed customers greedily"""
    new_sol = sol.copy()

    for cust_id in removed:
        best_cost = float('inf')
        best_truck = 0
        best_pos = 0

        # Try inserting in each truck route
        for truck_id in range(len(new_sol.truck_routes)):
            route = new_sol.truck_routes[truck_id]

            # Try each position
            for pos in range(len(route) + 1):
                test_route = route[:pos] + [cust_id] + route[pos:]

                if new_sol.check_truck_route(truck_id, test_route):
                    cost = calculate_truck_time(new_sol, truck_id, test_route)
                    if cost < best_cost:
                        best_cost = cost
                        best_truck = truck_id
                        best_pos = pos

        # Insert at best position
        new_sol.truck_routes[best_truck].insert(best_pos, cust_id)

    new_sol.makespan = evaluate_solution(new_sol)
    return new_sol

def regret_insertion(sol: Solution, removed: List[int]) -> Solution:
    """Insert customers using regret-2 heuristic"""
    new_sol = sol.copy()

    while removed:
        max_regret = -float('inf')
        best_customer = None
        best_truck = 0
        best_pos = 0

        for cust_id in removed:
            costs = []
            positions = []

            # Find best and second-best insertion
            for truck_id in range(len(new_sol.truck_routes)):
                route = new_sol.truck_routes[truck_id]

                for pos in range(len(route) + 1):
                    test_route = route[:pos] + [cust_id] + route[pos:]

                    if new_sol.check_truck_route(truck_id, test_route):
                        cost = calculate_truck_time(new_sol, truck_id, test_route)
                        costs.append(cost)
                        positions.append((truck_id, pos))

            if len(costs) >= 2:
                costs_sorted = sorted(costs)
                regret = costs_sorted[1] - costs_sorted[0]

                if regret > max_regret:
                    max_regret = regret
                    best_customer = cust_id
                    best_pos_idx = costs.index(costs_sorted[0])
                    best_truck, best_pos = positions[best_pos_idx]
            elif len(costs) == 1:
                if max_regret < 0:
                    best_customer = cust_id
                    best_truck, best_pos = positions[0]
                    max_regret = 0

        if best_customer is None:
            # Insert remaining randomly
            cust_id = removed[0]
            best_truck = random.randint(0, len(new_sol.truck_routes) - 1)
            best_pos = len(new_sol.truck_routes[best_truck])
        else:
            cust_id = best_customer

        new_sol.truck_routes[best_truck].insert(best_pos, cust_id)
        removed.remove(cust_id)

    new_sol.makespan = evaluate_solution(new_sol)
    return new_sol