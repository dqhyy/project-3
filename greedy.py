# greedy_solver.py

from config import *
from data_structures import TruckRoute, TruckVisit, DroneTrip
from utils import travel_time
from typing import List, Dict, Any

def greedy_solution(requests, return_log=False):
    trucks=[TruckRoute(i,[],0.0,DEPOT,0.0) for i in range(NUM_TRUCKS)]
    drones_busy=[0.0]*NUM_DRONES
    drone_trips=[]
    log={"visits":[], "assignments":[], "drone_trips":[]} if return_log else None

    def append_visit(tr, req_id, loc, ready, delta_load, note):
        tmove = travel_time(tr.current_loc, loc, TRUCK_SPEED)
        arrive = max(tr.current_time + tmove, ready)
        depart = arrive + DELTA
        tr.visits.append(TruckVisit(req_id, loc, arrive, depart, tr.current_load + delta_load, note))
        tr.current_loc = loc
        tr.current_time = depart
        tr.current_load += delta_load

    # 1. handle C2
    for r in [x for x in requests if x.type=="C2"]:
        best = min(trucks, key=lambda t:
                   max(t.current_time + travel_time(t.current_loc,r.pickup,TRUCK_SPEED), r.ready_time))
        append_visit(best, r.id, r.pickup, r.ready_time, r.demand, "pickup(C2)")
        append_visit(best, r.id, r.delivery, 0, -r.demand, "delivery(C2)")

    # 2. handle C1
    for r in [x for x in requests if x.type=="C1"]:
        best = min(trucks, key=lambda t:
                   max(t.current_time + travel_time(t.current_loc,r.delivery,TRUCK_SPEED), r.ready_time))
        append_visit(best, r.id, r.delivery, r.ready_time, 0, "delivery(C1)")

    # 3. assign drones (simple logic)
    for tr in trucks:
        for v in tr.visits:
            if "delivery(C1)" not in v.note: continue
            t_oneway = travel_time(DEPOT, v.loc, DRONE_SPEED)
            depart_time = max(0, v.arrive - (t_oneway + DELTA_PRIME))
            total_flight = 2*t_oneway + 2*DELTA_PRIME
            if total_flight > DRONE_FLIGHT_ENDURANCE_H:
                continue
            chosen = None
            for d in range(NUM_DRONES):
                if drones_busy[d] <= depart_time:
                    chosen=d
                    drones_busy[d]=depart_time + total_flight
                    break
            if chosen is not None:
                drone_trips.append(DroneTrip(chosen,
                                             depart_time,
                                             depart_time + t_oneway + DELTA_PRIME,
                                             v.loc,
                                             depart_time + total_flight,
                                             v.req_id))
                v.note += f" | drone_{chosen}"

    return trucks, drone_trips, log
