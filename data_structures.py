# data_structures.py

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class Node:
    id: int; x: float; y: float; typ: str; ready_time: float; pair_id: int

@dataclass
class Request:
    id: int; type: str; demand: float; ready_time: float
    pickup: Optional[Tuple[float,float]] = None
    delivery: Optional[Tuple[float,float]] = None
    pair_id: Optional[int] = None

@dataclass
class TruckVisit:
    req_id: int; loc: Tuple[float,float]
    arrive: float; depart: float; load_after: float
    note: str = ''

@dataclass
class TruckRoute:
    truck_id: int
    visits: List[TruckVisit] = field(default_factory=list)
    current_time: float = 0.0
    current_loc: Tuple[float,float] = (0.0, 0.0)
    current_load: float = 0.0

@dataclass
class DroneTrip:
    drone_id: int
    depart_time: float
    meet_time: float
    meet_loc: Tuple[float,float]
    return_time: float
    payload_req: int
