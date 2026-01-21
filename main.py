import numpy as np
import random
import math
import copy
from typing import List, Dict, Tuple, Set
import time


from model import Parameters, Instance
from alns import alns

def main():
    import os
    import glob

    # Specify the instance file or folder
    instance_path = "data/Instance/U_10_1.0_Num_10_pd.txt"
    selected_files = [instance_path]  

    # Run ALNS on selected instances
    params = Parameters()

    for instance_file in selected_files:
        print("\n" + "="*70)
        print(f"SOLVING INSTANCE: {os.path.basename(instance_file)}")
        print("="*70)

        try:
            # Load instance
            instance = Instance(instance_file)
            print(f"Depot at ({instance.depot.x}, {instance.depot.y})")

            # Run ALNS
            start_time = time.time()
            solution = alns(instance, params)
            elapsed = time.time() - start_time

            print("\n" + "="*70)
            print("FINAL SOLUTION")
            print("="*70)
            print(f"Makespan: {solution.makespan:.2f} hours ({solution.makespan*60:.1f} minutes)")
            print(f"Computation time: {elapsed:.2f} seconds")

            # Truck routes
            print("\n" + "-"*70)
            print("TRUCK ROUTES:")
            print("-"*70)
            for i, route in enumerate(solution.truck_routes):
                if route:
                    route_str = " -> ".join([str(0)] + [str(c) for c in route] + [str(0)])
                    print(f"  Truck {i}: {route_str}")
                    print(f"           ({len(route)} customers)")
                else:
                    print(f"  Truck {i}: Empty")

            # Drone trips
            print("\n" + "-"*70)
            print("DRONE TRIPS:")
            print("-"*70)
            if solution.drone_trips:
                for i, trip in enumerate(solution.drone_trips):
                    items_str = ", ".join([str(c) for c in trip.items])
                    print(f"  Drone trip {i+1}:")
                    print(f"    Items to resupply: [{items_str}]")
                    print(f"    Meet truck {trip.meet_truck} at customer {trip.meet_node}")
                    print(f"    Depart depot: {trip.depart_time:.2f}h ({trip.depart_time*60:.1f} min)")
                    print(f"    Return depot: {trip.return_time:.2f}h ({trip.return_time*60:.1f} min)")
                    print(f"    Flight time: {trip.flight_time:.2f}h ({trip.flight_time*60:.1f} min)")

                    # Show customers being resupplied
                    for cust_id in trip.items:
                        cust = instance.customers[cust_id - 1]
                        print(f"      - Customer {cust_id} (type {cust.type}, ready={cust.ready_time:.2f}h)")
            else:
                print("  No drone trips scheduled (all deliveries handled by trucks)")

            # Show customer details in routes
            print("\n" + "-"*70)
            print("DETAILED ROUTE INFORMATION:")
            print("-"*70)
            for truck_id, route in enumerate(solution.truck_routes):
                if not route:
                    continue
                print(f"\n  Truck {truck_id}:")
                current_time = 0
                load = 0
                prev = 0

                for cust_id in route:
                    cust = instance.customers[cust_id - 1]

                    # Travel time
                    travel = instance.dist_matrix[prev][cust_id] / params.truck_speed
                    current_time += travel

                    # Wait for ready time
                    wait = 0
                    if cust.type in ['D', 'DL']:
                        if current_time < cust.ready_time:
                            wait = cust.ready_time - current_time
                            current_time = cust.ready_time

                    arrival_time = current_time

                    # Update load
                    if cust.type == 'P':
                        load += cust.weight
                        action = "PICKUP"
                    elif cust.type == 'DL':
                        load -= cust.weight
                        action = "DELIVERY (from pickup)"
                    else:  # 'D'
                        action = "DELIVERY (resupplied by drone)"

                    # Service
                    current_time += params.delta

                    # Check if drone meets here
                    drone_meet = ""
                    for trip_idx, trip in enumerate(solution.drone_trips):
                        if trip.meet_truck == truck_id and trip.meet_node == cust_id:
                            drone_meet = f" [DRONE MEET #{trip_idx+1}]"
                            break

                    print(f"    -> Customer {cust_id:2d} ({cust.type:2s}): "
                          f"arrive={arrival_time:5.2f}h, {action:30s}, "
                          f"load={load:2d}{drone_meet}")

                    if wait > 0.01:
                        print(f"       (waited {wait:.2f}h for ready time)")

                    prev = cust_id

                # Return to depot
                travel = instance.dist_matrix[prev][0] / params.truck_speed
                current_time += travel
                print(f"    -> Depot: arrive={current_time:.2f}h (completion time)")

            # Summary statistics
            print("\n" + "-"*70)
            print("SUMMARY:")
            print("-"*70)
            total_customers = sum(len(r) for r in solution.truck_routes)
            delivery_d = len([c for c in instance.customers if c.type == 'D'])
            pickup_p = len([c for c in instance.customers if c.type == 'P'])
            delivery_dl = len([c for c in instance.customers if c.type == 'DL'])

            print(f"  Total customers served: {total_customers}")
            print(f"  - Type D (delivery from depot): {delivery_d}")
            print(f"  - Type P (pickup): {pickup_p}")
            print(f"  - Type DL (delivery from pickup): {delivery_dl}")
            print(f"  Number of trucks used: {sum(1 for r in solution.truck_routes if r)}")
            print(f"  Number of drone trips: {len(solution.drone_trips)}")
            print(f"  Makespan: {solution.makespan:.2f}h = {solution.makespan*60:.1f} minutes")

        except Exception as e:
            print(f"Error processing {instance_file}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
