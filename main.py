# main.py

from io_utils import load_nodes, build_requests
from greedy import greedy_solution
from alns import run_alns
import json

INPUT_FILE = "data/Instance/U_10_0.5_Num_1_pd.txt"

def to_json(trucks, drones):
    out={
        "trucks":[
            {
                "truck_id":tr.truck_id,
                "visits":[{
                    "req":v.req_id,
                    "loc":v.loc,
                    "arrive":v.arrive,
                    "depart":v.depart,
                    "load":v.load_after,
                    "note":v.note
                } for v in tr.visits]
            } for tr in trucks
        ],
        "drones":[{
            "drone_id":d.drone_id,
            "depart":d.depart_time,
            "meet":d.meet_time,
            "loc":d.meet_loc,
            "return":d.return_time,
            "req":d.payload_req
        } for d in drones]
    }
    return out

def main():
    nodes=load_nodes(INPUT_FILE)
    requests=build_requests(nodes)

    print("Running greedy baseline...")
    tr, dr, _ = greedy_solution(requests)
    print("Greedy done.")

    print("Running ALNS...")
    tr2, dr2, cost = run_alns(requests)
    print("ALNS done. Best cost:", cost)

    with open("output_solution.json","w") as f:
        json.dump(to_json(tr2,dr2), f, indent=2)

if __name__=="__main__":
    main()
