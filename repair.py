import numpy as np
import random
import math
import copy
from typing import List, Dict, Tuple, Set
import time

from solution import Solution
from evaluate import calculate_truck_time, evaluate_solution

def greedy_insertion(sol: Solution, removed: List[int]) -> Solution:
    """Insert removed customers greedily - OPTIMIZED"""
    new_sol = sol.copy()

    # Separate removed customers into pairs and independent
    to_insert = []
    inserted = set()

    for cust_id in removed:
        if cust_id in inserted:
            continue
            
        cust = new_sol.instance.customers[cust_id - 1]
        
        if cust.type == 'D':
            to_insert.append([cust_id])
        elif cust.type == 'P':
            dl_id = new_sol.instance.pd_pairs.get(cust_id)
            if dl_id and dl_id in removed:
                to_insert.append([cust_id, dl_id])
                inserted.add(cust_id)
                inserted.add(dl_id)
            else:
                to_insert.append([cust_id])
        elif cust.type == 'DL':
            p_id = None
            for pid, did in new_sol.instance.pd_pairs.items():
                if did == cust_id:
                    p_id = pid
                    break
            if p_id and p_id in removed and p_id not in inserted:
                to_insert.append([p_id, cust_id])
                inserted.add(p_id)
                inserted.add(cust_id)
            elif p_id not in removed:
                to_insert.append([cust_id])

    # Insert each unit
    for customers in to_insert:
        best_cost = float('inf')
        best_truck = 0
        best_positions = []

        # Limit search space for large instances
        max_positions_to_check = 50  # Don't check all positions if route is very long

        for truck_id in range(len(new_sol.truck_routes)):
            route = new_sol.truck_routes[truck_id]

            if len(customers) == 1:
                # Single customer - sample positions intelligently
                cust_id = customers[0]
                
                # Always check: start, end, and random samples
                positions_to_check = [0, len(route)]
                if len(route) > 2:
                    # Add evenly spaced positions
                    step = max(1, len(route) // min(10, len(route)))
                    positions_to_check.extend(range(step, len(route), step))
                
                for pos in positions_to_check[:max_positions_to_check]:
                    test_route = route[:pos] + [cust_id] + route[pos:]
                    
                    if new_sol.check_truck_route(truck_id, test_route):
                        cost = calculate_truck_time(new_sol, truck_id, test_route)
                        if cost < best_cost:
                            best_cost = cost
                            best_truck = truck_id
                            best_positions = [pos]
            else:
                # Pair - more restricted search
                p_id, dl_id = customers
                route_len = len(route)
                
                # Sample positions intelligently
                p_positions = [0, route_len]
                if route_len > 2:
                    step = max(1, route_len // min(5, route_len))
                    p_positions.extend(range(step, route_len, step))
                
                for p_pos in p_positions[:20]:  # Limit P positions
                    # For each P position, try a few DL positions
                    dl_positions = [p_pos + 1, route_len + 1]
                    if route_len - p_pos > 2:
                        dl_positions.append(p_pos + (route_len - p_pos) // 2)
                    
                    for dl_pos in dl_positions[:10]:  # Limit DL positions
                        if dl_pos <= p_pos:
                            continue
                            
                        test_route = route[:p_pos] + [p_id] + route[p_pos:dl_pos] + [dl_id] + route[dl_pos:]
                        
                        if new_sol.check_truck_route(truck_id, test_route):
                            cost = calculate_truck_time(new_sol, truck_id, test_route)
                            if cost < best_cost:
                                best_cost = cost
                                best_truck = truck_id
                                best_positions = [p_pos, dl_pos]

        # Insert at best position
        if len(customers) == 1:
            if best_positions:
                new_sol.truck_routes[best_truck].insert(best_positions[0], customers[0])
            else:
                new_sol.truck_routes[best_truck].append(customers[0])
        else:
            if best_positions:
                p_id, dl_id = customers
                p_pos, dl_pos = best_positions
                new_sol.truck_routes[best_truck].insert(p_pos, p_id)
                new_sol.truck_routes[best_truck].insert(dl_pos, dl_id)
            else:
                new_sol.truck_routes[best_truck].extend(customers)

    new_sol.makespan = evaluate_solution(new_sol)
    return new_sol

def regret_insertion(sol: Solution, removed: List[int]) -> Solution:
    """Insert customers using regret-2 - OPTIMIZED"""
    new_sol = sol.copy()

    # Separate removed into units
    to_insert = []
    inserted = set()

    for cust_id in removed:
        if cust_id in inserted:
            continue
            
        cust = new_sol.instance.customers[cust_id - 1]
        
        if cust.type == 'D':
            to_insert.append([cust_id])
        elif cust.type == 'P':
            dl_id = new_sol.instance.pd_pairs.get(cust_id)
            if dl_id and dl_id in removed:
                to_insert.append([cust_id, dl_id])
                inserted.add(cust_id)
                inserted.add(dl_id)
            else:
                to_insert.append([cust_id])
        elif cust.type == 'DL':
            p_id = None
            for pid, did in new_sol.instance.pd_pairs.items():
                if did == cust_id:
                    p_id = pid
                    break
            if p_id and p_id in removed and p_id not in inserted:
                to_insert.append([p_id, cust_id])
                inserted.add(p_id)
                inserted.add(cust_id)

    # Regret insertion loop
    while to_insert:
        max_regret = -float('inf')
        best_unit = None
        best_truck = 0
        best_positions = []

        # OPTIMIZATION: Process only top N candidates when many customers remain
        units_to_evaluate = to_insert
        if len(to_insert) > 20:
            # Prioritize units with earlier ready times
            units_to_evaluate = sorted(to_insert, 
                key=lambda u: min(new_sol.instance.customers[c-1].ready_time for c in u))[:20]

        for unit in units_to_evaluate:
            costs = []
            positions = []

            for truck_id in range(len(new_sol.truck_routes)):
                route = new_sol.truck_routes[truck_id]

                if len(unit) == 1:
                    # Sample positions
                    cust_id = unit[0]
                    positions_to_try = [0, len(route)]
                    if len(route) > 2:
                        step = max(1, len(route) // 5)
                        positions_to_try.extend(range(step, len(route), step))
                    
                    for pos in positions_to_try[:15]:  # Limit positions
                        test_route = route[:pos] + [cust_id] + route[pos:]
                        
                        if new_sol.check_truck_route(truck_id, test_route):
                            cost = calculate_truck_time(new_sol, truck_id, test_route)
                            costs.append(cost)
                            positions.append((truck_id, [pos]))
                            
                            if len(costs) >= 5:  # Early stopping - found enough options
                                break
                else:
                    # Pair - very limited search
                    p_id, dl_id = unit
                    route_len = len(route)
                    
                    # Try only key positions
                    p_positions = [0, route_len] if route_len <= 10 else [0, route_len // 2, route_len]
                    
                    for p_pos in p_positions[:5]:
                        dl_positions = [p_pos + 1, route_len + 1]
                        
                        for dl_pos in dl_positions[:3]:
                            if dl_pos <= p_pos:
                                continue
                                
                            test_route = route[:p_pos] + [p_id] + route[p_pos:dl_pos] + [dl_id] + route[dl_pos:]
                            
                            if new_sol.check_truck_route(truck_id, test_route):
                                cost = calculate_truck_time(new_sol, truck_id, test_route)
                                costs.append(cost)
                                positions.append((truck_id, [p_pos, dl_pos]))
                                
                                if len(costs) >= 3:
                                    break

            # Calculate regret
            if len(costs) >= 2:
                costs_sorted = sorted(costs)
                regret = costs_sorted[1] - costs_sorted[0]
                
                if regret > max_regret:
                    max_regret = regret
                    best_unit = unit
                    best_idx = costs.index(costs_sorted[0])
                    best_truck, best_positions = positions[best_idx]
            elif len(costs) == 1:
                if max_regret < 0:
                    best_unit = unit
                    best_truck, best_positions = positions[0]
                    max_regret = 0

        # Insert best unit
        if best_unit is None:
            best_unit = to_insert[0]
            best_truck = 0
            best_positions = [len(new_sol.truck_routes[0])]

        if len(best_unit) == 1:
            new_sol.truck_routes[best_truck].insert(best_positions[0], best_unit[0])
        else:
            p_id, dl_id = best_unit
            p_pos, dl_pos = best_positions
            new_sol.truck_routes[best_truck].insert(p_pos, p_id)
            new_sol.truck_routes[best_truck].insert(dl_pos, dl_id)

        to_insert.remove(best_unit)

    new_sol.makespan = evaluate_solution(new_sol)
    return new_sol