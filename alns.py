# alns_solver.py

from greedy import greedy_solution
from data_structures import TruckRoute, TruckVisit, DroneTrip
from config import *
from utils import travel_time, euclid
import random
import copy
import math

# ---- cost function ----
def compute_cost(trucks, drones):
    cost = 0.0
    for tr in trucks:
        cost += tr.current_time
    for d in drones:
        cost += (d.return_time - d.depart_time)
    return cost

# ---- extract C1 ----
def get_C1(trucks):
    out = []
    for tr in trucks:
        for v in tr.visits:
            if "delivery(C1)" in v.note:
                out.append(v.req_id)
    return out

# ---- remove operators ----
def random_remove(solution, k):
    c1 = get_C1(solution)
    return random.sample(c1, min(k, len(c1)))

def worst_remove(solution, k):
    score = []
    for tr in solution:
        for i, v in enumerate(tr.visits):
            if "delivery(C1)" not in v.note:
                continue
            prev = tr.visits[i-1].loc if i > 0 else DEPOT
            inc = travel_time(prev, v.loc, TRUCK_SPEED)
            score.append((inc, v.req_id))
    score.sort(reverse=True)
    return [rid for _, rid in score[:k]]

def related_remove(solution, k):
    c1 = get_C1(solution)
    if not c1:
        return []
    seed = random.choice(c1)
    seed_loc = None
    for tr in solution:
        for v in tr.visits:
            if v.req_id == seed:
                seed_loc = v.loc
                break
        if seed_loc:
            break
    if seed_loc is None:
        return []
    dist = []
    for tr in solution:
        for v in tr.visits:
            if "delivery(C1)" in v.note:
                dist.append((euclid(seed_loc, v.loc), v.req_id))
    dist.sort()
    return [rid for _, rid in dist[:k]]

# ---- insert operator ----
def greedy_insert(solution, requests_map, to_insert):
    """
    Insert each request in `to_insert` by choosing the truck (append at end)
    that yields the smallest arrival time (considering travel time and ready_time).
    We create TruckVisit objects directly.
    """
    for rid in to_insert:
        if rid not in requests_map:
            continue
        req = requests_map[rid]
        best_tr = None
        best_arrival = float('inf')
        for tr in solution:
            tt = travel_time(tr.current_loc, req.delivery, TRUCK_SPEED)
            arrival = max(tr.current_time + tt, req.ready_time)
            if arrival < best_arrival:
                best_arrival = arrival
                best_tr = tr
        if best_tr is None:
            continue
        # Create TruckVisit with correct arrival/depart and append
        arrive = best_arrival
        depart = arrive + DELTA
        tv = TruckVisit(req_id=req.id,
                        loc=req.delivery,
                        arrive=arrive,
                        depart=depart,
                        load_after=best_tr.current_load,
                        note='delivery(C1)')
        best_tr.visits.append(tv)
        best_tr.current_loc = tv.loc
        best_tr.current_time = tv.depart
        # current_load unchanged for C1 (assumed resupplied by drone or not)

# ---- ALNS Main ----
def run_alns(requests):
    # baseline
    best_tr, best_dr, _ = greedy_solution(requests, return_log=False)
    # deep-copy baseline to be safe
    best_tr = copy.deepcopy(best_tr)
    best_dr = copy.deepcopy(best_dr)

    best_cost = compute_cost(best_tr, best_dr)

    requests_map = {r.id: r for r in requests}

    destroy_ops = [random_remove, worst_remove, related_remove]
    repair_ops = [greedy_insert]

    curr_tr = copy.deepcopy(best_tr)
    curr_dr = copy.deepcopy(best_dr)
    curr_cost = best_cost

    T = INITIAL_TEMPERATURE

    for it in range(ALNS_ITER):
        k = random.randint(REMOVAL_MIN, REMOVAL_MAX)
        destroy = random.choice(destroy_ops)
        repair = random.choice(repair_ops)

        removed = destroy(curr_tr, k)

        # clone current solution to work on
        new_tr = copy.deepcopy(curr_tr)
        new_dr = copy.deepcopy(curr_dr)

        # remove selected C1 visits
        for tr in new_tr:
            tr.visits = [v for v in tr.visits if not (v.req_id in removed and "delivery(C1)" in v.note)]

        # reset truck status so append times are computed from current values (we append at end)
        # (Note: simple approach; if you want to recompute full routes, call a recompute function)
        for tr in new_tr:
            # recompute current_loc and current_time from existing visits
            if tr.visits:
                last = tr.visits[-1]
                tr.current_loc = last.loc
                tr.current_time = last.depart
            else:
                tr.current_loc = DEPOT
                tr.current_time = 0.0
            # current_load left as is (we assume C1 doesn't change load)

        # repair (insert removed back)
        repair(new_tr, requests_map, removed)

        # (optional) recompute drone assignments and accurate times here if you have such function
        # For now, we compute a simple cost based on truck current_time and drone durations (none updated)
        new_cost = compute_cost(new_tr, new_dr)

        # acceptance (simulated annealing)
        accept = False
        if new_cost < curr_cost:
            accept = True
        else:
            delta = curr_cost - new_cost
            try:
                prob = math.exp(delta / max(1e-9, T))
            except OverflowError:
                prob = 0.0
            if random.random() < prob:
                accept = True

        if accept:
            curr_tr = new_tr
            curr_dr = new_dr
            curr_cost = new_cost
            if curr_cost < best_cost:
                best_tr = copy.deepcopy(curr_tr)
                best_dr = copy.deepcopy(curr_dr)
                best_cost = curr_cost

        # cool temperature
        T *= COOLING_RATE

    return best_tr, best_dr, best_cost
