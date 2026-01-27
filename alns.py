import numpy as np
import random
import math
import copy
from typing import List, Dict, Tuple, Set
import time

from model import Instance, Parameters
from initial_solution import create_initial_solution
from destroy import random_removal, worst_removal, related_removal
from repair import greedy_insertion, regret_insertion
from solution import Solution

def alns(instance: Instance, params: Parameters) -> Solution:
    """ALNS algorithm - OPTIMIZED"""
    print("Creating initial solution...")
    current = create_initial_solution(instance, params)
    best = current.copy()

    print(f"Initial makespan: {best.makespan:.2f} hours")

    # ALNS parameters
    temp = params.temp_start
    weights_destroy = params.weights['destroy'].copy()
    weights_repair = params.weights['repair'].copy()

    destroy_ops = [random_removal, worst_removal, related_removal]
    repair_ops = [greedy_insertion, regret_insertion]

    # Adaptive parameters
    no_improvement_count = 0
    best_makespan_history = [best.makespan]
    
    # Dynamic destroy rate
    destroy_rate = params.destroy_rate

    print("\nRunning ALNS...")
    start_time = time.time()
    
    for iter in range(params.max_iterations):
        # Adaptive destroy rate
        if no_improvement_count > 50:
            destroy_rate = min(0.5, destroy_rate * 1.1)  # Increase destruction
            no_improvement_count = 0
        elif no_improvement_count > 0 and no_improvement_count % 20 == 0:
            destroy_rate = max(0.2, destroy_rate * 0.9)  # Decrease destruction

        # Select operators using roulette wheel
        destroy_idx = random.choices(range(len(destroy_ops)), weights=weights_destroy)[0]
        repair_idx = random.choices(range(len(repair_ops)), weights=weights_repair)[0]

        # Destroy - adaptive number of customers
        q = max(1, int(len(instance.customers) * destroy_rate))
        destroyed, removed = destroy_ops[destroy_idx](current, q)

        # Repair
        new_sol = repair_ops[repair_idx](destroyed, removed)

        # Acceptance criterion (Simulated Annealing)
        delta = new_sol.makespan - current.makespan

        accept = False
        if delta < 0:
            # Improvement
            current = new_sol
            weights_destroy[destroy_idx] += params.scores[0]
            weights_repair[repair_idx] += params.scores[0]
            accept = True

            if new_sol.makespan < best.makespan:
                improvement = best.makespan - new_sol.makespan
                best = new_sol.copy()
                best_makespan_history.append(best.makespan)
                no_improvement_count = 0
                
                print(f"Iter {iter}: New best = {best.makespan:.2f} hours "
                      f"(improved by {improvement:.2f}h)")
            else:
                no_improvement_count += 1
                
        elif random.random() < math.exp(-delta / temp):
            # Accept worse solution
            current = new_sol
            weights_destroy[destroy_idx] += params.scores[2]
            weights_repair[repair_idx] += params.scores[2]
            accept = True
            no_improvement_count += 1
        else:
            no_improvement_count += 1

        # Cool down
        temp *= params.cooling_rate

        # Periodic reporting
        if (iter + 1) % 100 == 0:
            elapsed = time.time() - start_time
            print(f"Iter {iter + 1}: Best = {best.makespan:.2f}, "
                  f"Current = {current.makespan:.2f}, "
                  f"Temp = {temp:.2f}, "
                  f"DestroyRate = {destroy_rate:.2f}, "
                  f"Time = {elapsed:.1f}s")
            
            # Normalize weights periodically
            if sum(weights_destroy) > 100:
                weights_destroy = [w / sum(weights_destroy) * 10 for w in weights_destroy]
            if sum(weights_repair) > 100:
                weights_repair = [w / sum(weights_repair) * 10 for w in weights_repair]

        # Restart mechanism - if stuck, restart from best
        if no_improvement_count > 200:
            print(f"Iter {iter}: No improvement for 200 iters, restarting from best...")
            current = best.copy()
            temp = params.temp_start * 0.5  # Lower temperature
            no_improvement_count = 0
            destroy_rate = params.destroy_rate

        # Early termination if solution is very good
        if iter > 100 and best.makespan < 1.0:  # Less than 1 hour
            print(f"Iter {iter}: Excellent solution found, early termination")
            break

    total_time = time.time() - start_time
    print(f"\nALNS completed in {total_time:.2f} seconds")
    print(f"Final best makespan: {best.makespan:.2f} hours")
    
    return best