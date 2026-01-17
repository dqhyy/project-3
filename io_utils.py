# io_utils.py

from data_structures import Node, Request
from config import ORDER_WEIGHT
import os

def load_nodes(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    nodes=[]
    with open(path,'r') as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            pid,x,y,typ,rt,pair = s.split()[:6]
            nodes.append(Node(int(pid), float(x), float(y), typ, float(rt), int(pair)))
    return nodes

def build_requests(nodes):
    requests=[]
    by_pair={}
    for n in nodes:
        by_pair.setdefault(n.pair_id, []).append(n)

    used=set()

    # C2
    for pid, group in by_pair.items():
        P=[g for g in group if g.typ=="P"]
        DL=[g for g in group if g.typ in ("DL","D")]
        if P and DL:
            p, dl = P[0], DL[0]
            requests.append(Request(pid, "C2", ORDER_WEIGHT, 0,
                                    pickup=(p.x,p.y),
                                    delivery=(dl.x,dl.y)))
            used.add(pid)

    # C1 = D with pair_id=0
    for n in nodes:
        if n.typ=="D" and n.pair_id==0:
            requests.append(Request(n.id,"C1",ORDER_WEIGHT,n.ready_time,
                                    pickup=None,
                                    delivery=(n.x,n.y)))

    # C1 = unmatched DL/D
    for pid, group in by_pair.items():
        if pid==0 or pid in used: continue
        DL=[g for g in group if g.typ in ("DL","D")]
        for dl in DL:
            requests.append(Request(dl.id,"C1",ORDER_WEIGHT,dl.ready_time,
                                    pickup=None,
                                    delivery=(dl.x,dl.y)))
    requests.sort(key=lambda r:(r.type, r.ready_time, r.id))
    return requests
