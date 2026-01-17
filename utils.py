# utils.py
import math

def euclid(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def travel_time(a, b, speed):
    return euclid(a, b) / speed if speed > 0 else float('inf')
