# ==========================================
# INSTANCE CONFIGURATION: Static Drone Resupply System
# Reference: Archetti et al. (2018, 2020), Pina-Pardo et al. (2024)
# ==========================================

# ------------------------
# Depot configuration
# ------------------------
Depot_positions:
  - Center: (10, 10)
  - Border: (0, 10)
Comment: Depot positions represent two spatial scenarios — central and border locations in the 20×20 km service area.

# ------------------------
# Order release dates
# ------------------------
Release_dates:
  Generation_method: Archetti et al. (2018)
  Formula: Uniform integer random values in [0, β × zTSP]
  zTSP:
    Definition: Optimal TSP length visiting all customers once (without release dates)
    Distance_metric: Manhattan
    Truck_speed: 30 km/h
    Depot_location_for_zTSP: (10, 10)
  Beta_values: [0.5, 1.0, 1.5]
  Comment: β defines the width of the release-time window. Larger β → higher spread of order readiness.

# ------------------------
# Truck parameters
# ------------------------
Truck:
  Speed: 30 km/h
  Service_time_per_customer: 3 min
  Receive_time_at_depot (δt): 5 min

# ------------------------
# Drone parameters
# ------------------------
Drone:
  Model: Avidrone 210TL
  Manufacturer: Avidrone Aerospace (2021)
  Payload_capacity: 25 kg
  Flight_endurance: 90 min
  Working_speed: 60 km/h
  Distance_metric: Euclidean
  Handling_times:
    δm (en-route meet): 5 min
    δd (depot meet): 5 min
  Load_capacity_Q:
    Small_instances (≤ 20 customers): 2 orders
    Large_instances: 10 orders
  Order_weight: qi = 1, ∀i ∈ N
  Comment: Each drone can carry up to Q orders (average parcel weight ≈ 2.3 kg (Poikonen & Golden, 2020))
  
  Lưu ý: mỗi lần truck “phục vụ” tại depot (tức là ghé depot giữa chừng hoặc ở đầu/cuối) thì chỉ mất đúng δt thời gian

  

