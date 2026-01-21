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
    """ALNS algorithm"""
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

    print("\nRunning ALNS...")
    for iter in range(params.max_iterations):
        # Select operators
        destroy_idx = random.choices(range(len(destroy_ops)), weights=weights_destroy)[0]
        repair_idx = random.choices(range(len(repair_ops)), weights=weights_repair)[0]

        # Destroy
        q = max(1, int(len(instance.customers) * params.destroy_rate))
        destroyed, removed = destroy_ops[destroy_idx](current, q)

        # Repair
        new_sol = repair_ops[repair_idx](destroyed, removed)

        # Acceptance criterion (Simulated Annealing)
        delta = new_sol.makespan - current.makespan

        if delta < 0:
            current = new_sol
            weights_destroy[destroy_idx] += params.scores[0]
            weights_repair[repair_idx] += params.scores[0]

            if new_sol.makespan < best.makespan:
                best = new_sol.copy()
                print(f"Iter {iter}: New best = {best.makespan:.2f} hours")
        elif random.random() < math.exp(-delta / temp):
            current = new_sol
            weights_destroy[destroy_idx] += params.scores[2]
            weights_repair[repair_idx] += params.scores[2]

        # Cool down
        temp *= params.cooling_rate

        if (iter + 1) % 100 == 0:
            print(f"Iter {iter + 1}: Best = {best.makespan:.2f}, Current = {current.makespan:.2f}, Temp = {temp:.2f}")

    return best